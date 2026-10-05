using System.Security.Cryptography;
using System.Text.Json;

namespace WinCare.Services;

public sealed record WechatMediaFile(string Account, string Kind, string Path, long Bytes, DateTime CreatedUtc, DateTime LastWriteUtc);
public sealed record WechatScanResult(IReadOnlyList<WechatMediaFile> Files, IReadOnlyList<string> Warnings, int Accounts);
public sealed record WechatOperationResult(int Completed, int Skipped, long Bytes, IReadOnlyList<string> Warnings);

public static class WechatCleanupService
{
    private const string ArchiveFolderName = "WeChatArchive";
    private static string ArchiveRoot => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "WinCare", ArchiveFolderName);
    private static readonly StringComparison PathComparison = OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal;
    private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };
    private static readonly HashSet<string> VideoExtensions = new(StringComparer.OrdinalIgnoreCase) { ".mp4", ".mov", ".m4v", ".avi", ".3gp", ".mkv", ".wmv", ".flv", ".webm" };

    private sealed class ArchiveManifest
    {
        public ArchiveManifest() { }
        public string Root { get; set; } = "";
        public DateTime CreatedUtc { get; set; }
        public List<ArchiveRecord> Files { get; set; } = [];
    }
    private sealed class ArchiveRecord
    {
        public ArchiveRecord() { }
        public string Id { get; set; } = "";
        public string OriginalPath { get; set; } = "";
        public string Kind { get; set; } = "";
        public long Bytes { get; set; }
        public DateTime CreatedUtc { get; set; }
        public string State { get; set; } = "Pending";
    }

    public static string DefaultRoot
    {
        get
        {
            var documents = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
            return Path.Combine(documents, "WeChat Files");
        }
    }

    public static WechatScanResult Scan(string root, int ageDays, bool includeImages, bool includeVideos, CancellationToken cancellationToken = default)
    {
        if (ageDays < 1 || ageDays > 3650) throw new ArgumentOutOfRangeException(nameof(ageDays), "时间范围应为 1 到 3650 天。");
        if (string.IsNullOrWhiteSpace(root)) throw new ArgumentException("请指定微信文件根目录。", nameof(root));
        var fullRoot = Path.GetFullPath(root.Trim());
        if (!Directory.Exists(fullRoot)) throw new DirectoryNotFoundException($"找不到微信文件目录：{fullRoot}");
        if (IsReparsePoint(fullRoot)) throw new InvalidOperationException("微信根目录是链接目录；为避免扫描到其他位置，WinCare 已停止扫描。");

        var files = new List<WechatMediaFile>();
        var warnings = new List<string>();
        var accounts = 0;
        var cutoff = DateTime.UtcNow.AddDays(-ageDays);
        foreach (var accountDir in EnumerateDirectories(fullRoot, warnings))
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (IsReparsePoint(accountDir)) continue;
            var accountName = Path.GetFileName(accountDir);
            var storage = Path.Combine(accountDir, "FileStorage");
            if (!Directory.Exists(storage) || IsReparsePoint(storage)) continue;
            accounts++;

            if (includeVideos)
            {
                var video = Path.Combine(storage, "Video");
                if (Directory.Exists(video) && !IsReparsePoint(video))
                    Collect(video, accountName, "视频", cutoff, files, warnings, cancellationToken, path => VideoExtensions.Contains(Path.GetExtension(path)));
            }

            if (includeImages)
            {
                var messageAttachments = Path.Combine(storage, "MsgAttach");
                if (Directory.Exists(messageAttachments) && !IsReparsePoint(messageAttachments))
                {
                    foreach (var imageDir in EnumerateDirectoriesRecursive(messageAttachments, warnings, cancellationToken))
                    {
                        if (!string.Equals(Path.GetFileName(imageDir), "Image", StringComparison.OrdinalIgnoreCase) || IsReparsePoint(imageDir)) continue;
                        Collect(imageDir, accountName, "图片（.dat 原图）", cutoff, files, warnings, cancellationToken,
                            path => string.Equals(Path.GetExtension(path), ".dat", StringComparison.OrdinalIgnoreCase));
                    }
                }
            }
        }
        return new WechatScanResult(files.OrderByDescending(x => x.Bytes).ToList(), warnings, accounts);
    }

    public static WechatOperationResult Archive(string root, IReadOnlyCollection<WechatMediaFile> selected, CancellationToken cancellationToken = default)
    {
        if (selected.Count == 0) return new WechatOperationResult(0, 0, 0, []);
        if (string.IsNullOrWhiteSpace(root)) throw new ArgumentException("请指定微信文件根目录。", nameof(root));
        var fullRoot = Path.GetFullPath(root.Trim());
        if (!Directory.Exists(fullRoot) || IsReparsePoint(fullRoot)) throw new InvalidOperationException("微信根目录不存在或是链接目录。");
        Directory.CreateDirectory(ArchiveRoot);
        if (IsReparsePoint(ArchiveRoot)) throw new InvalidOperationException("WinCare 微信归档目录是链接目录；操作已停止。");
        var session = Path.Combine(ArchiveRoot, Guid.NewGuid().ToString("N"));
        var payloadDir = Path.Combine(session, "payload");
        Directory.CreateDirectory(payloadDir);
        var manifestPath = Path.Combine(session, "manifest.json");
        var manifest = new ArchiveManifest { Root = fullRoot, CreatedUtc = DateTime.UtcNow };
        var warnings = new List<string>();
        var completed = 0;
        var skipped = 0;
        long bytes = 0;

        foreach (var item in selected)
        {
            cancellationToken.ThrowIfCancellationRequested();
            try
            {
                var source = Path.GetFullPath(item.Path);
                if (!IsSupportedSource(fullRoot, source, item.Kind) || !File.Exists(source) || IsReparsePoint(source) || HasReparseParent(fullRoot, source))
                    throw new IOException("文件已变化，或不在受支持的微信媒体目录中。");
                var info = new FileInfo(source);
                info.Refresh();
                if (!info.Exists || info.Length != item.Bytes || info.CreationTimeUtc != item.CreatedUtc || info.LastWriteTimeUtc != item.LastWriteUtc)
                    throw new IOException("文件在扫描后发生变化，请重新扫描再归档。");
                var record = new ArchiveRecord
                {
                    Id = Guid.NewGuid().ToString("N") + Path.GetExtension(source),
                    OriginalPath = source,
                    Kind = item.Kind,
                    Bytes = info.Length,
                    CreatedUtc = info.CreationTimeUtc,
                    State = "Pending"
                };
                manifest.Files.Add(record);
                SaveManifest(manifestPath, manifest);
                var archivedPath = Path.Combine(payloadDir, record.Id);
                TransferVerified(source, archivedPath, removeSource: true);
                record.State = File.Exists(source) ? "CopyRetained" : "Archived";
                SaveManifest(manifestPath, manifest);
                if (record.State == "Archived") { completed++; bytes += record.Bytes; }
                else { skipped++; warnings.Add($"已备份但未能从微信目录移除（保留了原件）：{source}"); }
            }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException or CryptographicException)
            {
                skipped++;
                warnings.Add($"{item.Path}：{ex.Message}");
            }
        }
        return new WechatOperationResult(completed, skipped, bytes, warnings);
    }

    public static WechatOperationResult RestoreAll(CancellationToken cancellationToken = default)
    {
        if (!Directory.Exists(ArchiveRoot)) return new WechatOperationResult(0, 0, 0, []);
        if (IsReparsePoint(ArchiveRoot)) throw new InvalidOperationException("WinCare 微信归档目录是链接目录；操作已停止。");
        var warnings = new List<string>();
        var restored = 0;
        var skipped = 0;
        long bytes = 0;
        foreach (var session in EnumerateDirectories(ArchiveRoot, warnings))
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (!Guid.TryParseExact(Path.GetFileName(session), "N", out _) || IsReparsePoint(session)) continue;
            var manifestPath = Path.Combine(session, "manifest.json");
            if (!File.Exists(manifestPath) || IsReparsePoint(manifestPath)) continue;
            ArchiveManifest? manifest;
            try { manifest = JsonSerializer.Deserialize<ArchiveManifest>(File.ReadAllText(manifestPath)); }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or JsonException)
            {
                skipped++;
                warnings.Add($"无法读取归档清单：{manifestPath}（{ex.Message}）");
                continue;
            }
            if (manifest is null) continue;
            string root;
            try { root = Path.GetFullPath(manifest.Root); }
            catch { skipped++; continue; }
            if (!Directory.Exists(root) || IsReparsePoint(root)) { skipped++; warnings.Add($"原微信根目录不存在或是链接目录，无法安全还原：{root}"); continue; }
            foreach (var record in manifest.Files.Where(x => x.State is "Archived" or "CopyRetained" or "Pending"))
            {
                cancellationToken.ThrowIfCancellationRequested();
                try
                {
                    if (!string.Equals(Path.GetFileName(record.Id), record.Id, StringComparison.Ordinal) ||
                        !Guid.TryParseExact(Path.GetFileNameWithoutExtension(record.Id), "N", out _))
                        throw new InvalidDataException("归档编号无效。");
                    var archived = Path.Combine(session, "payload", record.Id);
                    var original = Path.GetFullPath(record.OriginalPath);
                    if (!IsSupportedSource(root, original, record.Kind)) throw new InvalidDataException("清单中的原路径不在微信媒体目录白名单中。");
                    if (!File.Exists(archived) || IsReparsePoint(archived) || HasReparseParent(session, archived)) throw new FileNotFoundException("找不到安全的归档文件。");
                    if (new FileInfo(archived).Length != record.Bytes) throw new IOException("归档文件大小与清单记录不一致；已保留归档副本。");
                    if (File.Exists(original)) throw new IOException("原路径已有同名文件；为避免覆盖，已跳过。");
                    var parent = Path.GetDirectoryName(original)!;
                    EnsureSafeDirectories(root, parent);
                    TransferVerified(archived, original, removeSource: true);
                    record.State = "Restored";
                    SaveManifest(manifestPath, manifest);
                    restored++;
                    bytes += record.Bytes;
                }
                catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException or CryptographicException or InvalidDataException)
                {
                    skipped++;
                    warnings.Add($"{record.OriginalPath}：{ex.Message}");
                }
            }
        }
        return new WechatOperationResult(restored, skipped, bytes, warnings);
    }

    public static (int Files, long Bytes) GetArchivedSummary()
    {
        if (!Directory.Exists(ArchiveRoot) || IsReparsePoint(ArchiveRoot)) return (0, 0);
        var count = 0;
        long bytes = 0;
        var warnings = new List<string>();
        foreach (var session in EnumerateDirectories(ArchiveRoot, warnings))
        {
            if (!Guid.TryParseExact(Path.GetFileName(session), "N", out _) || IsReparsePoint(session)) continue;
            var manifestPath = Path.Combine(session, "manifest.json");
            try
            {
                if (!File.Exists(manifestPath) || IsReparsePoint(manifestPath)) continue;
                var manifest = JsonSerializer.Deserialize<ArchiveManifest>(File.ReadAllText(manifestPath));
                foreach (var record in manifest?.Files.Where(x => x.State is "Archived" or "CopyRetained" or "Pending") ?? [])
                {
                    var payload = Path.Combine(session, "payload", record.Id);
                    if (string.Equals(Path.GetFileName(record.Id), record.Id, StringComparison.Ordinal) &&
                        File.Exists(payload) && !IsReparsePoint(payload)) { count++; bytes += new FileInfo(payload).Length; }
                }
            }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or JsonException) { }
        }
        return (count, bytes);
    }

    private static bool IsSupportedSource(string root, string path, string kind)
    {
        if (!IsUnder(root, path)) return false;
        var relative = Path.GetRelativePath(root, path);
        var parts = relative.Split(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        if (parts.Length < 4 || !string.Equals(parts[1], "FileStorage", StringComparison.OrdinalIgnoreCase)) return false;
        if (kind == "视频")
            return parts.Length >= 4 && string.Equals(parts[2], "Video", StringComparison.OrdinalIgnoreCase) && VideoExtensions.Contains(Path.GetExtension(path));
        if (kind == "图片（.dat 原图）")
            return parts.Length >= 5 && string.Equals(parts[2], "MsgAttach", StringComparison.OrdinalIgnoreCase) &&
                   parts.Skip(3).Take(parts.Length - 4).Any(p => string.Equals(p, "Image", StringComparison.OrdinalIgnoreCase)) &&
                   string.Equals(Path.GetExtension(path), ".dat", StringComparison.OrdinalIgnoreCase);
        return false;
    }

    private static bool IsUnder(string root, string path)
    {
        var fullRoot = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        var fullPath = Path.GetFullPath(path);
        return fullPath.StartsWith(fullRoot + Path.DirectorySeparatorChar, PathComparison);
    }

    private static IEnumerable<string> EnumerateDirectories(string root, List<string> warnings)
    {
        IEnumerator<string>? it = null;
        try { it = Directory.EnumerateDirectories(root, "*", SearchOption.TopDirectoryOnly).GetEnumerator(); }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { warnings.Add($"{root}：{ex.Message}"); }
        if (it is null) yield break;
        using (it)
        {
            while (true)
            {
                var moved = false;
                string? current = null;
                try { moved = it.MoveNext(); if (moved) current = it.Current; }
                catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { warnings.Add($"{root}：{ex.Message}"); }
                if (!moved) yield break;
                yield return current!;
            }
        }
    }

    private static IEnumerable<string> EnumerateDirectoriesRecursive(string root, List<string> warnings, CancellationToken token)
    {
        var pending = new Stack<string>();
        pending.Push(root);
        while (pending.Count > 0)
        {
            token.ThrowIfCancellationRequested();
            var current = pending.Pop();
            foreach (var child in EnumerateDirectories(current, warnings))
            {
                if (IsReparsePoint(child)) continue;
                yield return child;
                pending.Push(child);
            }
        }
    }

    private static void Collect(string root, string account, string kind, DateTime cutoff, List<WechatMediaFile> output, List<string> warnings, CancellationToken token, Func<string, bool> filter)
    {
        var pending = new Stack<string>();
        pending.Push(root);
        while (pending.Count > 0)
        {
            token.ThrowIfCancellationRequested();
            var dir = pending.Pop();
            foreach (var child in EnumerateDirectories(dir, warnings))
                if (!IsReparsePoint(child)) pending.Push(child);
            IEnumerator<string>? files = null;
            try { files = Directory.EnumerateFiles(dir, "*", SearchOption.TopDirectoryOnly).GetEnumerator(); }
            catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { warnings.Add($"{dir}：{ex.Message}"); }
            if (files is null) continue;
            using (files)
            {
                while (true)
                {
                    token.ThrowIfCancellationRequested();
                    string path;
                    try { if (!files.MoveNext()) break; path = files.Current; }
                    catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { warnings.Add($"{dir}：{ex.Message}"); break; }
                    try
                    {
                        if (IsReparsePoint(path) || !filter(path)) continue;
                        var info = new FileInfo(path);
                        info.Refresh();
                        if (info.Exists && info.CreationTimeUtc <= cutoff)
                            output.Add(new WechatMediaFile(account, kind, Path.GetFullPath(path), info.Length, info.CreationTimeUtc, info.LastWriteTimeUtc));
                    }
                    catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { warnings.Add($"{path}：{ex.Message}"); }
                }
            }
        }
    }

    private static bool HasReparseParent(string root, string path)
    {
        var relative = Path.GetRelativePath(root, path);
        var current = Path.GetFullPath(root);
        if (IsReparsePoint(current)) return true;
        var parts = relative.Split(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        foreach (var part in parts)
        {
            current = Path.Combine(current, part);
            if (Directory.Exists(current) && IsReparsePoint(current)) return true;
        }
        return false;
    }

    private static void EnsureSafeDirectories(string root, string parent)
    {
        if (!IsUnder(root, parent)) throw new InvalidDataException("还原目录不在微信文件根目录中。");
        var relative = Path.GetRelativePath(root, parent);
        var current = Path.GetFullPath(root);
        foreach (var part in relative.Split(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar))
        {
            if (part.Length == 0) continue;
            current = Path.Combine(current, part);
            if (!Directory.Exists(current)) throw new DirectoryNotFoundException("微信账号或还原子目录已不存在；为避免重建错误的数据结构，已跳过。");
            if (IsReparsePoint(current)) throw new IOException("还原路径包含链接目录，已停止。");
        }
    }

    private static void TransferVerified(string source, string destination, bool removeSource)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
        if (File.Exists(destination)) throw new IOException("归档目标已存在。");
        var sourceRoot = Path.GetPathRoot(Path.GetFullPath(source));
        var destinationRoot = Path.GetPathRoot(Path.GetFullPath(destination));
        if (string.Equals(sourceRoot, destinationRoot, PathComparison))
        {
            File.Move(source, destination);
            return;
        }
        File.Copy(source, destination, overwrite: false);
        try
        {
            if (new FileInfo(source).Length != new FileInfo(destination).Length || !FilesEqual(source, destination))
                throw new CryptographicException("跨磁盘复制校验失败，原文件仍保留。");
            if (removeSource) File.Delete(source);
        }
        catch
        {
            if (File.Exists(destination)) File.Delete(destination);
            throw;
        }
    }

    private static bool FilesEqual(string left, string right)
    {
        using var a = File.OpenRead(left);
        using var b = File.OpenRead(right);
        return CryptographicOperations.FixedTimeEquals(SHA256.HashData(a), SHA256.HashData(b));
    }

    private static void SaveManifest(string path, ArchiveManifest manifest)
    {
        var temp = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            File.WriteAllText(temp, JsonSerializer.Serialize(manifest, JsonOptions));
            if (File.Exists(path)) File.Move(temp, path, overwrite: true);
            else File.Move(temp, path);
        }
        finally
        {
            if (File.Exists(temp) && !IsReparsePoint(temp)) File.Delete(temp);
        }
    }

    private static bool IsReparsePoint(string path)
    {
        try { return (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0; }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or System.Security.SecurityException) { return true; }
    }
}
