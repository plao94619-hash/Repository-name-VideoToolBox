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
        var targets = new List<CleanupTarget>();
        foreach (var candidate in GetCandidates())
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

    public static CleanupTarget PreviewTarget(string targetPath, bool requiresAdmin)
    {
        var known = ResolveTarget(targetPath, requiresAdmin);
        if (!Directory.Exists(known.Path)) return known;
        var (count, bytes) = Measure(known.Path, DateTime.UtcNow.AddDays(-MinimumAgeDays));
        return known with { EligibleFiles = count, EstimatedBytes = bytes };
    }

    public static CleanupResult Clean(string targetPath, bool requiresAdmin = false)
    {
        // Revalidate only the requested whitelist path. A full preview scan here
        // would traverse both temp trees again immediately before deletion.
        var known = ResolveTarget(targetPath, requiresAdmin);
        if (!Directory.Exists(known.Path)) return new CleanupResult(0, 0, 0);
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

    private static IEnumerable<(string Name, string Path, bool RequiresAdmin)> GetCandidates()
    {
        var userTemp = Path.GetTempPath();
        if (!string.IsNullOrWhiteSpace(userTemp))
            yield return ("当前用户临时文件", userTemp, false);

        var windows = Environment.GetFolderPath(Environment.SpecialFolder.Windows);
        if (!string.IsNullOrWhiteSpace(windows))
            yield return ("Windows 临时文件", Path.Combine(windows, "Temp"), true);
    }

    private static CleanupTarget ResolveTarget(string targetPath, bool requiresAdmin)
    {
        var requestedPath = Path.GetFullPath(targetPath);
        foreach (var candidate in GetCandidates())
        {
            string fullPath;
            try { fullPath = Path.GetFullPath(candidate.Path); }
            catch { continue; }
            if (candidate.RequiresAdmin != requiresAdmin || !string.Equals(fullPath, requestedPath, PathComparison))
                continue;
            if (!IsOnCDrive(fullPath)) break;
            if (Directory.Exists(fullPath) && IsReparsePoint(fullPath))
                throw new InvalidOperationException("为避免跟随链接，WinCare 不会清理重解析点目录。");
            return new CleanupTarget(candidate.Name, fullPath, candidate.RequiresAdmin, 0, 0);
        }
        throw new InvalidOperationException("清理路径不在 WinCare 对应权限范围的安全清理清单中。");
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
            foreach (var file in EnumerateDirectoryEntries(directory, files: true))
                yield return file;

            foreach (var child in EnumerateDirectoryEntries(directory, files: false))
            {
                try
                {
                    if ((File.GetAttributes(child) & FileAttributes.ReparsePoint) == 0) pending.Push(child);
                }
                catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { }
            }
        }
    }

    private static IEnumerable<string> EnumerateDirectoryEntries(string directory, bool files)
    {
        IEnumerator<string>? enumerator = null;
        try
        {
            var entries = files
                ? Directory.EnumerateFiles(directory, "*", SearchOption.TopDirectoryOnly)
                : Directory.EnumerateDirectories(directory, "*", SearchOption.TopDirectoryOnly);
            enumerator = entries.GetEnumerator();
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { }

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
                catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { }

                if (!hasNext) yield break;
                yield return current!;
            }
        }
        finally
        {
            try { enumerator.Dispose(); }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { }
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
