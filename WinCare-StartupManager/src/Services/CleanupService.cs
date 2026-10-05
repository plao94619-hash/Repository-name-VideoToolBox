using WinCare.Models;

namespace WinCare.Services;

public sealed record CleanupTarget(string Name, string Path, bool RequiresAdmin, int EligibleFiles, long EstimatedBytes);
public sealed record CleanupResult(int DeletedFiles, long DeletedBytes, int SkippedFiles);

public static class CleanupService
{
    public const int MinimumAgeDays = 7;
    private static readonly StringComparison PathComparison = OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal;

    public static IReadOnlyList<CleanupTarget> ScanCDrive()
    {
        var candidates = new[]
        {
            (Name: "当前用户临时文件", Path: Path.GetTempPath(), RequiresAdmin: false),
            (Name: "Windows 临时文件", Path: Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows), "Temp"), RequiresAdmin: true)
        };
        var targets = new List<CleanupTarget>();
        foreach (var candidate in candidates)
        {
            string fullPath;
            try { fullPath = Path.GetFullPath(candidate.Path); }
            catch { continue; }
            if (!IsOnCDrive(fullPath) || targets.Any(t => string.Equals(t.Path, fullPath, PathComparison))) continue;
            if (Directory.Exists(fullPath) && IsReparsePoint(fullPath)) continue;
            var (count, bytes) = Directory.Exists(fullPath) ? Measure(fullPath, DateTime.UtcNow.AddDays(-MinimumAgeDays)) : (0, 0L);
            targets.Add(new CleanupTarget(candidate.Name, fullPath, candidate.RequiresAdmin, count, bytes));
        }
        return targets;
    }

    public static CleanupResult Clean(string targetPath)
    {
        var known = ScanCDrive().FirstOrDefault(t => string.Equals(t.Path, Path.GetFullPath(targetPath), PathComparison));
        if (known is null) throw new InvalidOperationException("清理路径不在 WinCare 的安全清理清单中。");
        if (!Directory.Exists(known.Path)) return new CleanupResult(0, 0, 0);
        if (IsReparsePoint(known.Path)) throw new InvalidOperationException("为避免跟随链接，WinCare 不会清理重解析点目录。");
        var cutoff = DateTime.UtcNow.AddDays(-MinimumAgeDays);
        var deleted = 0;
        long bytes = 0;
        var skipped = 0;
        foreach (var filePath in EnumerateFilesWithoutFollowingLinks(known.Path))
        {
            try
            {
                var info = new FileInfo(filePath);
                info.Refresh();
                if (!info.Exists) continue;
                if (info.LastWriteTimeUtc > cutoff || (info.Attributes & FileAttributes.ReparsePoint) != 0)
                {
                    skipped++;
                    continue;
                }
                var length = info.Length;
                File.Delete(filePath);
                deleted++;
                bytes += length;
            }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException)
            {
                skipped++;
            }
        }
        return new CleanupResult(deleted, bytes, skipped);
    }

    private static (int Count, long Bytes) Measure(string root, DateTime cutoff)
    {
        var count = 0;
        long bytes = 0;
        foreach (var path in EnumerateFilesWithoutFollowingLinks(root))
        {
            try
            {
                var info = new FileInfo(path);
                info.Refresh();
                if (info.Exists && info.LastWriteTimeUtc <= cutoff && (info.Attributes & FileAttributes.ReparsePoint) == 0)
                {
                    count++;
                    bytes += info.Length;
                }
            }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { }
        }
        return (count, bytes);
    }

    private static IEnumerable<string> EnumerateFilesWithoutFollowingLinks(string root)
    {
        var pending = new Stack<string>();
        pending.Push(root);
        while (pending.Count > 0)
        {
            var directory = pending.Pop();
            string[] files;
            try { files = Directory.GetFiles(directory, "*", SearchOption.TopDirectoryOnly); }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { continue; }
            foreach (var file in files) yield return file;

            string[] subdirectories;
            try { subdirectories = Directory.GetDirectories(directory, "*", SearchOption.TopDirectoryOnly); }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { continue; }
            foreach (var child in subdirectories)
            {
                try
                {
                    if ((File.GetAttributes(child) & FileAttributes.ReparsePoint) == 0) pending.Push(child);
                }
                catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { }
            }
        }
    }

    private static bool IsOnCDrive(string path)
    {
        var root = Path.GetPathRoot(path);
        return string.Equals(root, @"C:\", PathComparison) && path.Length > root.Length;
    }

    private static bool IsReparsePoint(string path)
    {
        try { return (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0; }
        catch { return true; }
    }
}
