namespace WinCare.Services;

public sealed record LargeFileItem(string Name, string Path, long Bytes, DateTime ModifiedUtc);
public sealed record LargeFileScanProgress(long ScannedFiles, long MatchingFiles, int ReadErrors);
public sealed record LargeFileScanResult(
    long ScannedFiles,
    long MatchingFiles,
    long MatchingBytes,
    int ReadErrors,
    IReadOnlyList<LargeFileItem> LargestFiles,
    bool ResultsTruncated);

public static class DiskUsageService
{
    public const int MaximumResults = 2_000;
    private static readonly string CDriveRoot = @"C:\";

    public static LargeFileScanResult ScanLargeFiles(
        long minimumBytes,
        IProgress<LargeFileScanProgress>? progress = null,
        CancellationToken cancellationToken = default)
    {
        if (minimumBytes <= 0) throw new ArgumentOutOfRangeException(nameof(minimumBytes));
        if (!Directory.Exists(CDriveRoot)) throw new DirectoryNotFoundException("找不到 C:\\ 根目录。");

        var largest = new PriorityQueue<LargeFileItem, long>();
        var pending = new Stack<string>();
        pending.Push(CDriveRoot);
        long scannedFiles = 0;
        long matchingFiles = 0;
        long matchingBytes = 0;
        int readErrors = 0;
        long nextProgressAt = 1_024;

        while (pending.Count > 0)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var directory = pending.Pop();

            foreach (var filePath in EnumerateEntriesSafely(directory, files: true, () => readErrors++))
            {
                cancellationToken.ThrowIfCancellationRequested();
                try
                {
                    var info = new FileInfo(filePath);
                    info.Refresh();
                    if (!info.Exists) continue;

                    scannedFiles++;
                    var attributes = info.Attributes;
                    var size = info.Length;
                    if ((attributes & FileAttributes.ReparsePoint) == 0 && size >= minimumBytes)
                    {
                        matchingFiles++;
                        matchingBytes = SaturatingAdd(matchingBytes, size);
                        var item = new LargeFileItem(info.Name, info.FullName, size, info.LastWriteTimeUtc);
                        if (largest.Count < MaximumResults)
                        {
                            largest.Enqueue(item, item.Bytes);
                        }
                        else if (largest.TryPeek(out _, out var smallestRetained) && item.Bytes > smallestRetained)
                        {
                            largest.Dequeue();
                            largest.Enqueue(item, item.Bytes);
                        }
                    }
                }
                catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException)
                {
                    readErrors++;
                }

                if (scannedFiles >= nextProgressAt)
                {
                    progress?.Report(new LargeFileScanProgress(scannedFiles, matchingFiles, readErrors));
                    nextProgressAt = scannedFiles + 1_024;
                }
            }

            foreach (var child in EnumerateEntriesSafely(directory, files: false, () => readErrors++))
            {
                cancellationToken.ThrowIfCancellationRequested();
                try
                {
                    if ((File.GetAttributes(child) & FileAttributes.ReparsePoint) == 0)
                        pending.Push(child);
                }
                catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException)
                {
                    readErrors++;
                }
            }
        }

        progress?.Report(new LargeFileScanProgress(scannedFiles, matchingFiles, readErrors));
        var results = largest.UnorderedItems
            .Select(entry => entry.Element)
            .OrderByDescending(item => item.Bytes)
            .ThenBy(item => item.Path, StringComparer.OrdinalIgnoreCase)
            .ToArray();
        return new LargeFileScanResult(
            scannedFiles,
            matchingFiles,
            matchingBytes,
            readErrors,
            results,
            matchingFiles > results.Length);
    }

    private static IEnumerable<string> EnumerateEntriesSafely(string directory, bool files, Action onReadError)
    {
        IEnumerator<string>? enumerator = null;
        try
        {
            var paths = files
                ? Directory.EnumerateFiles(directory, "*", SearchOption.TopDirectoryOnly)
                : Directory.EnumerateDirectories(directory, "*", SearchOption.TopDirectoryOnly);
            enumerator = paths.GetEnumerator();
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException)
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
                catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException)
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
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { onReadError(); }
        }
    }

    private static long SaturatingAdd(long left, long right) =>
        left > long.MaxValue - right ? long.MaxValue : left + right;
}
