using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace WinCare.Services;

public sealed record LargeFileItem(
    string Name,
    string Path,
    long LogicalBytes,
    long AllocatedBytes,
    DateTime ModifiedUtc);

public sealed record LargeFileScanProgress(
    long ScannedPaths,
    long MatchingFiles,
    long DuplicateHardLinkPaths,
    int ReadErrors);

public sealed record LargeFileScanResult(
    long ScannedPaths,
    long MatchingFiles,
    long MatchingLogicalBytes,
    long MatchingAllocatedBytes,
    long DuplicateHardLinkPaths,
    int ReadErrors,
    IReadOnlyList<LargeFileItem> LargestFiles,
    bool ResultsTruncated);

public static class DiskUsageService
{
    public const int MaximumResults = 2_000;
    private const uint FileShareRead = 0x0001;
    private const uint FileShareWrite = 0x0002;
    private const uint FileShareDelete = 0x0004;
    private const uint OpenExisting = 3;
    private const uint FileFlagOpenReparsePoint = 0x00200000;
    private static readonly EnumerationOptions ScanEnumerationOptions = new()
    {
        AttributesToSkip = (FileAttributes)0,
        IgnoreInaccessible = false,
        RecurseSubdirectories = false,
        ReturnSpecialDirectories = false
    };
    private static readonly string CDriveRoot = @"C:\";

    private enum FileInfoByHandleClass
    {
        FileAttributeTagInfo = 9,
        FileStandardInfo = 1,
        FileIdInfo = 18
    }

    private readonly record struct FileIdentity(ulong VolumeSerialNumber, ulong FileIdLow, ulong FileIdHigh);
    private readonly record struct FileMetrics(
        long LogicalBytes,
        long AllocatedBytes,
        DateTime ModifiedUtc,
        FileIdentity? Identity);

    [StructLayout(LayoutKind.Sequential)]
    private struct FileAttributeTagInfo
    {
        public uint FileAttributes;
        public uint ReparseTag;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct FileStandardInfo
    {
        public long AllocationSize;
        public long EndOfFile;
        public uint NumberOfLinks;
        public byte DeletePending;
        public byte Directory;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct FileId128
    {
        public ulong Low;
        public ulong High;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct FileIdInfo
    {
        public ulong VolumeSerialNumber;
        public FileId128 FileId;
    }

    [DllImport("kernel32.dll", EntryPoint = "CreateFileW", CharSet = CharSet.Unicode, SetLastError = true, ExactSpelling = true)]
    private static extern SafeFileHandle CreateFileForMetadata(
        string fileName,
        uint desiredAccess,
        uint shareMode,
        IntPtr securityAttributes,
        uint creationDisposition,
        uint flagsAndAttributes,
        IntPtr templateFile);

    [DllImport("kernel32.dll", EntryPoint = "GetFileInformationByHandleEx", SetLastError = true, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetFileAttributeTagInfo(
        SafeFileHandle file,
        FileInfoByHandleClass fileInformationClass,
        out FileAttributeTagInfo fileInformation,
        uint bufferSize);

    [DllImport("kernel32.dll", EntryPoint = "GetFileInformationByHandleEx", SetLastError = true, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetFileStandardInfo(
        SafeFileHandle file,
        FileInfoByHandleClass fileInformationClass,
        out FileStandardInfo fileInformation,
        uint bufferSize);

    [DllImport("kernel32.dll", EntryPoint = "GetFileInformationByHandleEx", SetLastError = true, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetFileIdInfo(
        SafeFileHandle file,
        FileInfoByHandleClass fileInformationClass,
        out FileIdInfo fileInformation,
        uint bufferSize);

    public static LargeFileScanResult ScanLargeFiles(
        long minimumAllocatedBytes,
        IProgress<LargeFileScanProgress>? progress = null,
        CancellationToken cancellationToken = default)
    {
        if (minimumAllocatedBytes <= 0) throw new ArgumentOutOfRangeException(nameof(minimumAllocatedBytes));
        if (!Directory.Exists(CDriveRoot)) throw new DirectoryNotFoundException("找不到 C:\\ 根目录。");

        var largest = new PriorityQueue<LargeFileItem, long>();
        var seenHardLinks = new HashSet<FileIdentity>();
        var pending = new Stack<string>();
        pending.Push(CDriveRoot);
        long scannedPaths = 0;
        long matchingFiles = 0;
        long matchingLogicalBytes = 0;
        long matchingAllocatedBytes = 0;
        long duplicateHardLinkPaths = 0;
        int readErrors = 0;
        long nextProgressAt = 1_024;

        while (pending.Count > 0)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var directory = pending.Pop();

            foreach (var filePath in EnumerateEntriesSafely(directory, files: true, () => readErrors++))
            {
                cancellationToken.ThrowIfCancellationRequested();
                scannedPaths++;
                try
                {
                    var info = new FileInfo(filePath);
                    info.Refresh();
                    if (!info.Exists) continue;

                    var attributes = info.Attributes;
                    if ((attributes & FileAttributes.ReparsePoint) != 0) continue;

                    var metrics = ReadFileMetrics(filePath, info.LastWriteTimeUtc);
                    if (metrics is null || metrics.Value.AllocatedBytes < minimumAllocatedBytes) continue;

                    var itemMetrics = metrics.Value;
                    if (itemMetrics.Identity is { } identity && !seenHardLinks.Add(identity))
                    {
                        duplicateHardLinkPaths++;
                        continue;
                    }

                    matchingFiles++;
                    matchingLogicalBytes = SaturatingAdd(matchingLogicalBytes, itemMetrics.LogicalBytes);
                    matchingAllocatedBytes = SaturatingAdd(matchingAllocatedBytes, itemMetrics.AllocatedBytes);
                    var item = new LargeFileItem(
                        info.Name,
                        info.FullName,
                        itemMetrics.LogicalBytes,
                        itemMetrics.AllocatedBytes,
                        itemMetrics.ModifiedUtc);
                    if (largest.Count < MaximumResults)
                    {
                        largest.Enqueue(item, item.AllocatedBytes);
                    }
                    else if (largest.TryPeek(out _, out var smallestRetained) && item.AllocatedBytes > smallestRetained)
                    {
                        largest.Dequeue();
                        largest.Enqueue(item, item.AllocatedBytes);
                    }
                }
                catch (Exception ex) when (IsExpectedReadFailure(ex))
                {
                    readErrors++;
                }
                finally
                {
                    ReportProgressIfDue(
                        progress, ref nextProgressAt, scannedPaths, matchingFiles, duplicateHardLinkPaths, readErrors);
                }
            }

            foreach (var child in EnumerateEntriesSafely(directory, files: false, () => readErrors++))
            {
                cancellationToken.ThrowIfCancellationRequested();
                scannedPaths++;
                try
                {
                    if ((File.GetAttributes(child) & FileAttributes.ReparsePoint) == 0)
                        pending.Push(child);
                }
                catch (Exception ex) when (IsExpectedReadFailure(ex))
                {
                    readErrors++;
                }
                finally
                {
                    ReportProgressIfDue(
                        progress, ref nextProgressAt, scannedPaths, matchingFiles, duplicateHardLinkPaths, readErrors);
                }
            }
        }

        progress?.Report(new LargeFileScanProgress(
            scannedPaths, matchingFiles, duplicateHardLinkPaths, readErrors));
        var results = largest.UnorderedItems
            .Select(entry => entry.Element)
            .OrderByDescending(item => item.AllocatedBytes)
            .ThenBy(item => item.Path, StringComparer.OrdinalIgnoreCase)
            .ToArray();
        return new LargeFileScanResult(
            scannedPaths,
            matchingFiles,
            matchingLogicalBytes,
            matchingAllocatedBytes,
            duplicateHardLinkPaths,
            readErrors,
            results,
            matchingFiles > results.Length);
    }

    private static FileMetrics? ReadFileMetrics(string path, DateTime modifiedUtc)
    {
        using var handle = CreateFileForMetadata(
            ToExtendedPath(path),
            0,
            FileShareRead | FileShareWrite | FileShareDelete,
            IntPtr.Zero,
            OpenExisting,
            FileFlagOpenReparsePoint,
            IntPtr.Zero);
        if (handle.IsInvalid)
            throw new Win32Exception(Marshal.GetLastWin32Error());

        if (!GetFileAttributeTagInfo(
                handle,
                FileInfoByHandleClass.FileAttributeTagInfo,
                out var attributes,
                (uint)Marshal.SizeOf<FileAttributeTagInfo>()))
            throw new Win32Exception(Marshal.GetLastWin32Error());
        if ((attributes.FileAttributes & (uint)FileAttributes.ReparsePoint) != 0)
            return null;

        if (!GetFileStandardInfo(
                handle,
                FileInfoByHandleClass.FileStandardInfo,
                out var standardInfo,
                (uint)Marshal.SizeOf<FileStandardInfo>()))
            throw new Win32Exception(Marshal.GetLastWin32Error());
        if (standardInfo.Directory != 0) return null;
        if (standardInfo.AllocationSize < 0 || standardInfo.EndOfFile < 0)
            throw new IOException("文件系统返回了无效的文件大小。");

        FileIdentity? identity = null;
        if (standardInfo.NumberOfLinks > 1)
        {
            if (!GetFileIdInfo(
                    handle,
                    FileInfoByHandleClass.FileIdInfo,
                    out var idInfo,
                    (uint)Marshal.SizeOf<FileIdInfo>()))
                throw new Win32Exception(Marshal.GetLastWin32Error());
            identity = new FileIdentity(idInfo.VolumeSerialNumber, idInfo.FileId.Low, idInfo.FileId.High);
        }

        return new FileMetrics(
            standardInfo.EndOfFile,
            standardInfo.AllocationSize,
            modifiedUtc,
            identity);
    }

    private static string ToExtendedPath(string path)
    {
        if (path.StartsWith(@"\\?\", StringComparison.Ordinal))
            return path;
        var fullPath = Path.GetFullPath(path);
        if (fullPath.StartsWith(@"\\", StringComparison.Ordinal))
            return @"\\?\UNC\" + fullPath[2..];
        return @"\\?\" + fullPath;
    }

    private static IEnumerable<string> EnumerateEntriesSafely(string directory, bool files, Action onReadError)
    {
        IEnumerator<string>? enumerator = null;
        try
        {
            var paths = files
                ? Directory.EnumerateFiles(directory, "*", ScanEnumerationOptions)
                : Directory.EnumerateDirectories(directory, "*", ScanEnumerationOptions);
            enumerator = paths.GetEnumerator();
        }
        catch (Exception ex) when (IsExpectedReadFailure(ex))
        {
            onReadError();
        }

        if (enumerator is null) yield break;
        try
        {
            while (true)
            {
                var hasNext = false;
                string? current = null;
                try
                {
                    hasNext = enumerator.MoveNext();
                    if (hasNext) current = enumerator.Current;
                }
                catch (Exception ex) when (IsExpectedReadFailure(ex))
                {
                    onReadError();
                }

                if (!hasNext) yield break;
                yield return current!;
            }
        }
        finally
        {
            try { enumerator.Dispose(); }
            catch (Exception ex) when (IsExpectedReadFailure(ex)) { onReadError(); }
        }
    }

    private static bool IsExpectedReadFailure(Exception ex) =>
        ex is IOException or UnauthorizedAccessException or System.Security.SecurityException or Win32Exception;

    private static void ReportProgressIfDue(
        IProgress<LargeFileScanProgress>? progress,
        ref long nextProgressAt,
        long scannedPaths,
        long matchingFiles,
        long duplicateHardLinkPaths,
        int readErrors)
    {
        if (scannedPaths < nextProgressAt) return;
        progress?.Report(new LargeFileScanProgress(scannedPaths, matchingFiles, duplicateHardLinkPaths, readErrors));
        nextProgressAt = scannedPaths + 1_024;
    }

    private static long SaturatingAdd(long left, long right) =>
        left > long.MaxValue - right ? long.MaxValue : left + right;
}
