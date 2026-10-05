using Microsoft.Win32;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Runtime.InteropServices;
using WinCare.Models;

namespace WinCare.Services;

public static class StartupActions
{
    private const string DisabledRegistryChild = "WinCareDisabled";
    private const string TaskRestoreRoot = @"SOFTWARE\WinCare\StartupRestore\Tasks";
    private const string ServiceRestoreRoot = @"SOFTWARE\WinCare\StartupRestore\Services";
    private static string DataRoot => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "WinCare");
    private static string LegacyStatePath => Path.Combine(DataRoot, "state.json");
    public static string DisabledFilesRoot => Path.Combine(DataRoot, "DisabledFiles");

    public sealed record DisabledFile(string OriginalPath, string BackupPath, bool CommonFolder);
    private sealed record ServiceRestore(bool DelayedAutoStart, bool Legacy = false);
    private sealed class LegacyState
    {
        public HashSet<string> DisabledTaskPaths { get; set; } = new(StringComparer.OrdinalIgnoreCase);
        public Dictionary<string, ServiceRestore> DisabledServices { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    }
    public sealed class RestoreSnapshot
    {
        private readonly HashSet<string> _managedTasks = new(StringComparer.OrdinalIgnoreCase);
        private readonly HashSet<string> _managedServices = new(StringComparer.OrdinalIgnoreCase);
        private readonly HashSet<string> _legacyTasks = new(StringComparer.OrdinalIgnoreCase);
        private readonly HashSet<string> _legacyServices = new(StringComparer.OrdinalIgnoreCase);

        internal void AddManagedTask(string path) => _managedTasks.Add(path);
        internal void AddManagedService(string name) => _managedServices.Add(name);
        internal void AddLegacyTask(string path) => _legacyTasks.Add(path);
        internal void AddLegacyService(string name) => _legacyServices.Add(name);
        public bool IsTaskManaged(string path) => _managedTasks.Contains(path) || _legacyTasks.Contains(path);
        public bool IsTaskLegacy(string path) => _legacyTasks.Contains(path);
        public bool IsServiceManaged(string name) => _managedServices.Contains(name) || _legacyServices.Contains(name);
        public bool IsServiceLegacy(string name) => _legacyServices.Contains(name);
    }

    public static RestoreSnapshot LoadRestoreSnapshot()
    {
        var legacy = ReadLegacyState();
        var snapshot = new RestoreSnapshot();
        foreach (var path in legacy.DisabledTaskPaths) snapshot.AddLegacyTask(path);
        foreach (var name in legacy.DisabledServices.Keys) snapshot.AddLegacyService(name);
        foreach (var path in ReadMarkerValues(TaskRestoreRoot, "TaskPath")) snapshot.AddManagedTask(path);
        foreach (var name in ReadMarkerValues(ServiceRestoreRoot, "ServiceName")) snapshot.AddManagedService(name);
        return snapshot;
    }

    private static bool HasLegacyTaskRestore(string taskPath) =>
        ReadLegacyState().DisabledTaskPaths.Any(path => string.Equals(path, taskPath, StringComparison.OrdinalIgnoreCase));

    public static void Apply(StartupActionRequest request)
    {
        if (!request.Entry.CanToggle) throw new InvalidOperationException("该启动项只读或已被外部禁用，WinCare 不会更改它。");
        if (request.Enable == request.Entry.Enabled)
            throw new InvalidOperationException("启动项状态已变化，请重新扫描后再操作。");
        switch (request.Entry.Kind)
        {
            case StartupEntryKind.RegistryValue:
                ChangeRegistryValue(request.Entry, request.Enable);
                break;
            case StartupEntryKind.StartupFile:
                ChangeStartupFile(request.Entry, request.Enable);
                break;
            case StartupEntryKind.ScheduledTask:
                ChangeScheduledTask(request.Entry.Location, request.Enable);
                break;
            case StartupEntryKind.Service:
                ChangeService(request.Entry, request.Enable);
                break;
            default:
                throw new NotSupportedException("不支持的启动项类型。");
        }
    }

    private static void ChangeRegistryValue(StartupEntry entry, bool enable)
    {
        var hive = Enum.Parse<RegistryHive>(entry.Hive ?? throw new InvalidOperationException("缺少注册表 Hive。"));
        var view = Enum.Parse<RegistryView>(entry.View ?? throw new InvalidOperationException("缺少注册表视图。"));
        var path = entry.RegistryPath ?? throw new InvalidOperationException("缺少注册表路径。");
        var name = entry.RegistryValueName ?? "";
        using var root = RegistryKey.OpenBaseKey(hive, view);
        var sourcePath = enable ? $"{path}\\{DisabledRegistryChild}" : path;
        var destinationPath = enable ? path : $"{path}\\{DisabledRegistryChild}";
        using var source = root.OpenSubKey(sourcePath, writable: true) ?? throw new IOException($"找不到启动项注册表位置：{sourcePath}");
        using var destination = root.CreateSubKey(destinationPath, writable: true) ?? throw new IOException($"无法创建注册表位置：{destinationPath}");
        if (!source.GetValueNames().Contains(name, StringComparer.OrdinalIgnoreCase))
            throw new IOException($"启动项注册表值已不存在：{sourcePath}\\{name}");
        if (destination.GetValueNames().Contains(name, StringComparer.OrdinalIgnoreCase))
            throw new IOException($"目标位置中已存在名为“{name}”的值，操作已停止以避免覆盖。");
        var value = source.GetValue(name, null, RegistryValueOptions.DoNotExpandEnvironmentNames);
        var kind = source.GetValueKind(name);
        destination.SetValue(name, value ?? "", kind);
        try
        {
            var latestValue = source.GetValue(name, null, RegistryValueOptions.DoNotExpandEnvironmentNames);
            var latestKind = source.GetValueKind(name);
            if (latestKind != kind || !RegistryDataEquals(value, latestValue))
                throw new IOException("注册表启动项在操作期间发生变化，WinCare 已停止移动它。");
            source.DeleteValue(name, throwOnMissingValue: true);
        }
        catch (Exception moveError)
        {
            try { destination.DeleteValue(name, throwOnMissingValue: false); }
            catch (Exception rollbackError)
            {
                throw new AggregateException("移动注册表启动项失败，自动回滚也未完成。请重新扫描并核对两处注册表值。", moveError, rollbackError);
            }
            throw;
        }
    }

    private static bool RegistryDataEquals(object? left, object? right) => (left, right) switch
    {
        (byte[] a, byte[] b) => a.AsSpan().SequenceEqual(b),
        (string[] a, string[] b) => a.SequenceEqual(b, StringComparer.Ordinal),
        _ => object.Equals(left, right)
    };

    private static void ChangeStartupFile(StartupEntry entry, bool enable)
    {
        var originalPath = entry.OriginalPath ?? throw new InvalidOperationException("缺少启动文件原路径。");
        var common = GetStartupFolderScope(originalPath);
        if (entry.RequiresAdmin != common)
            throw new InvalidOperationException("启动文件权限范围已变化，请重新扫描后再操作。");
        if (!enable)
        {
            var fullOriginalPath = Path.GetFullPath(originalPath);
            var info = new FileInfo(originalPath);
            info.Refresh();
            if (!info.Exists) throw new FileNotFoundException("启动文件已不存在。", originalPath);
            if ((info.Attributes & FileAttributes.ReparsePoint) != 0)
                throw new InvalidOperationException("为避免更改链接目标，WinCare 不会移动重解析点文件。");
            EnsureSafeRecoveryDirectory(createRecoveryDirectory: true);
            var backupPath = Path.Combine(DisabledFilesRoot, $"{Guid.NewGuid():N}{info.Extension}");
            var metadataPath = GetMetadataPath(originalPath);
            if (File.Exists(metadataPath)) throw new IOException("该启动文件已有备份记录，请先恢复或检查 WinCare 可恢复区。");
            File.Move(fullOriginalPath, backupPath);
            try
            {
                WriteJson(metadataPath, new DisabledFile(fullOriginalPath, backupPath, common), overwrite: false);
            }
            catch
            {
                if (File.Exists(backupPath) && !File.Exists(fullOriginalPath)) File.Move(backupPath, fullOriginalPath);
                throw;
            }
            return;
        }

        var metaPath = GetMetadataPath(originalPath);
        EnsureSafeRecoveryDirectory(createRecoveryDirectory: false);
        if (IsReparsePoint(metaPath)) throw new InvalidOperationException("恢复记录是链接文件，WinCare 不会读取或移动它。");
        var meta = JsonSerializer.Deserialize<DisabledFile>(File.ReadAllText(metaPath))
                   ?? throw new InvalidDataException("启动文件备份记录无效。");
        var fullBackupPath = Path.GetFullPath(meta.BackupPath);
        if (!string.Equals(Path.GetFullPath(meta.OriginalPath), Path.GetFullPath(originalPath), StringComparison.OrdinalIgnoreCase) ||
            meta.CommonFolder != common ||
            !string.Equals(Path.GetDirectoryName(fullBackupPath), Path.GetFullPath(DisabledFilesRoot), StringComparison.OrdinalIgnoreCase) ||
            !IsGeneratedBackupName(Path.GetFileName(fullBackupPath)))
            throw new InvalidDataException("启动文件恢复记录与当前启动文件不匹配，WinCare 已停止操作。");
        if (IsReparsePoint(fullBackupPath)) throw new InvalidOperationException("恢复文件是链接文件，WinCare 不会移动它。");
        if (!File.Exists(fullBackupPath)) throw new FileNotFoundException("找不到可恢复的启动文件备份。", fullBackupPath);
        if (File.Exists(originalPath)) throw new IOException("原启动文件位置已被占用。请先手动检查，WinCare 不会覆盖文件。");
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(originalPath))!);
        File.Move(fullBackupPath, Path.GetFullPath(originalPath));
        File.Delete(metaPath);
    }

    private static void ChangeScheduledTask(string taskPath, bool enable)
    {
        object? serviceObject = null;
        try
        {
            var type = Type.GetTypeFromProgID("Schedule.Service") ?? throw new InvalidOperationException("无法连接 Windows 任务计划程序。");
            serviceObject = Activator.CreateInstance(type);
            dynamic service = serviceObject!;
            service.Connect();
            var parts = taskPath.Trim('\\').Split('\\', StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length == 0) throw new InvalidOperationException("计划任务路径无效。");
            dynamic folder = service.GetFolder("\\");
            for (var i = 0; i < parts.Length - 1; i++) folder = folder.GetFolder(parts[i]);
            dynamic task = folder.GetTask(parts[^1]);
            var currentlyEnabled = (bool)task.Enabled;
            if (currentlyEnabled == enable)
                throw new InvalidOperationException("计划任务状态已变化，请重新扫描后再操作。");

            if (!enable)
            {
                CreateMarker(TaskRestoreRoot, taskPath, "TaskPath", taskPath);
                try { task.Enabled = false; }
                catch (Exception operationError)
                {
                    try { DeleteMarker(TaskRestoreRoot, taskPath); }
                    catch (Exception markerError)
                    {
                        throw new AggregateException("关闭计划任务失败，清除管理员恢复记录也失败。请重新扫描并核对任务状态。", operationError, markerError);
                    }
                    throw;
                }
            }
            else
            {
                var hasMarker = HasTaskRegistryMarker(taskPath);
                var hasLegacy = !hasMarker && HasLegacyTaskRestore(taskPath);
                if (!hasMarker && !hasLegacy)
                    throw new InvalidOperationException("WinCare 没有此计划任务的管理员恢复记录，不会擅自启用它。");
                task.Enabled = true;
                try
                {
                    if (hasMarker) DeleteMarker(TaskRestoreRoot, taskPath);
                    else RemoveLegacyTaskRestore(taskPath);
                }
                catch (Exception markerError)
                {
                    try { task.Enabled = false; }
                    catch (Exception rollbackError)
                    {
                        throw new AggregateException("计划任务已启用，但清除恢复记录及自动回滚均失败。请重新扫描并核对任务状态。", markerError, rollbackError);
                    }
                    throw new IOException("清除计划任务恢复记录失败，WinCare 已尝试将任务恢复为关闭状态。", markerError);
                }
            }
        }
        finally
        {
            if (serviceObject is not null && Marshal.IsComObject(serviceObject)) Marshal.FinalReleaseComObject(serviceObject);
        }
    }

    private static void ChangeService(StartupEntry entry, bool enable)
    {
        var name = entry.ServiceName ?? throw new InvalidOperationException("缺少服务名称。");
        if (!enable)
        {
            if (entry.Kind != StartupEntryKind.Service || !entry.Enabled)
                throw new InvalidOperationException("服务状态已改变，请重新扫描后再操作。");
            var original = ReadServiceStart(name);
            if (original.StartType != 2) throw new InvalidOperationException("服务启动类型已变化，请重新扫描后再操作。");
            CreateServiceRestoreMarker(name, new ServiceRestore(original.DelayedAutoStart));
            try { RunScConfig(name, "disabled"); }
            catch (Exception operationError)
            {
                try { DeleteMarker(ServiceRestoreRoot, name); }
                catch (Exception markerError)
                {
                    throw new AggregateException("关闭服务失败，清除管理员恢复记录也失败。请重新扫描并核对服务状态。", operationError, markerError);
                }
                throw;
            }
        }
        else
        {
            var current = ReadServiceStart(name);
            if (current.StartType != 4) throw new InvalidOperationException("服务启动类型已变化，请重新扫描后再操作。");
            var restore = ReadServiceRestoreMarker(name);
            RunScConfig(name, restore.DelayedAutoStart ? "delayed-auto" : "auto");
            try
            {
                if (restore.Legacy) RemoveLegacyServiceRestore(name);
                else DeleteMarker(ServiceRestoreRoot, name);
            }
            catch (Exception markerError)
            {
                try { RunScConfig(name, "disabled"); }
                catch (Exception rollbackError)
                {
                    throw new AggregateException("服务已恢复，但清除恢复记录和自动回滚均失败。请重新扫描并核对服务状态。", markerError, rollbackError);
                }
                throw new IOException("清除服务恢复记录失败，WinCare 已尝试将服务恢复为禁用状态。", markerError);
            }
        }
    }

    private static (int StartType, bool DelayedAutoStart) ReadServiceStart(string serviceName)
    {
        using var root = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, Environment.Is64BitOperatingSystem ? RegistryView.Registry64 : RegistryView.Default);
        using var key = root.OpenSubKey($@"SYSTEM\CurrentControlSet\Services\{serviceName}", writable: false)
                        ?? throw new IOException($"找不到 Windows 服务：{serviceName}");
        var start = Convert.ToInt32(key.GetValue("Start", 3));
        var delayed = Convert.ToInt32(key.GetValue("DelayedAutoStart", 0)) == 1;
        return (start, delayed);
    }

    private static void CreateServiceRestoreMarker(string serviceName, ServiceRestore restore)
    {
        var path = GetMarkerPath(ServiceRestoreRoot, serviceName);
        using var root = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, Environment.Is64BitOperatingSystem ? RegistryView.Registry64 : RegistryView.Default);
        using var marker = root.CreateSubKey(path, writable: true) ?? throw new IOException("无法创建服务管理员恢复记录。");
        var existing = Convert.ToString(marker.GetValue("ServiceName"));
        if (!string.IsNullOrEmpty(existing))
            throw new IOException("此服务已有 WinCare 恢复记录，请先重新扫描并核对服务状态。");
        marker.SetValue("OriginalStartType", 2, RegistryValueKind.DWord);
        marker.SetValue("OriginalDelayedAutoStart", restore.DelayedAutoStart ? 1 : 0, RegistryValueKind.DWord);
        marker.SetValue("ServiceName", serviceName, RegistryValueKind.String); // Written last: it marks a complete restore record.
    }

    private static ServiceRestore ReadServiceRestoreMarker(string serviceName)
    {
        using var marker = OpenMarker(ServiceRestoreRoot, serviceName, writable: false);
        if (marker is not null)
        {
            if (!string.Equals(Convert.ToString(marker.GetValue("ServiceName")), serviceName, StringComparison.OrdinalIgnoreCase) ||
                Convert.ToInt32(marker.GetValue("OriginalStartType", 0)) != 2)
                throw new InvalidDataException("服务管理员恢复记录无效，WinCare 已停止操作。");
            var delayed = Convert.ToInt32(marker.GetValue("OriginalDelayedAutoStart", -1));
            if (delayed is not (0 or 1)) throw new InvalidDataException("服务管理员恢复记录无效，WinCare 已停止操作。");
            return new ServiceRestore(delayed == 1);
        }

        var legacy = ReadLegacyState().DisabledServices.FirstOrDefault(pair =>
            string.Equals(pair.Key, serviceName, StringComparison.OrdinalIgnoreCase));
        if (legacy.Key is null) throw new InvalidOperationException("WinCare 没有此服务的管理员恢复记录，不会擅自启用它。");
        return legacy.Value with { Legacy = true };
    }

    private static bool HasTaskRegistryMarker(string taskPath)
    {
        using var marker = OpenMarker(TaskRestoreRoot, taskPath, writable: false);
        return marker is not null && string.Equals(Convert.ToString(marker.GetValue("TaskPath")), taskPath, StringComparison.OrdinalIgnoreCase);
    }

    private static void RemoveLegacyTaskRestore(string taskPath)
    {
        var state = ReadLegacyState();
        state.DisabledTaskPaths.RemoveWhere(path => string.Equals(path, taskPath, StringComparison.OrdinalIgnoreCase));
        WriteLegacyState(state);
    }

    private static void RemoveLegacyServiceRestore(string serviceName)
    {
        var state = ReadLegacyState();
        var key = state.DisabledServices.Keys.FirstOrDefault(name => string.Equals(name, serviceName, StringComparison.OrdinalIgnoreCase));
        if (key is null) throw new InvalidOperationException("旧版服务恢复记录已变化，请重新扫描后再操作。");
        state.DisabledServices.Remove(key);
        WriteLegacyState(state);
    }

    private static RegistryKey? OpenMarker(string markerRoot, string identity, bool writable)
    {
        using var root = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, Environment.Is64BitOperatingSystem ? RegistryView.Registry64 : RegistryView.Default);
        return root.OpenSubKey(GetMarkerPath(markerRoot, identity), writable);
    }

    private static IEnumerable<string> ReadMarkerValues(string markerRoot, string valueName)
    {
        using var root = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, Environment.Is64BitOperatingSystem ? RegistryView.Registry64 : RegistryView.Default);
        using var markers = root.OpenSubKey(markerRoot, writable: false);
        if (markers is null) yield break;
        foreach (var subkeyName in markers.GetSubKeyNames())
        {
            using var marker = markers.OpenSubKey(subkeyName, writable: false);
            var value = Convert.ToString(marker?.GetValue(valueName));
            if (!string.IsNullOrWhiteSpace(value)) yield return value;
        }
    }

    private static string GetMarkerPath(string markerRoot, string identity)
    {
        var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(identity.ToUpperInvariant())));
        return $"{markerRoot}\\{hash}";
    }

    private static void CreateMarker(string markerRoot, string identity, string valueName, string value)
    {
        using var root = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, Environment.Is64BitOperatingSystem ? RegistryView.Registry64 : RegistryView.Default);
        using var marker = root.CreateSubKey(GetMarkerPath(markerRoot, identity), writable: true)
                           ?? throw new IOException("无法创建管理员恢复记录。");
        var existing = Convert.ToString(marker.GetValue(valueName));
        if (!string.IsNullOrEmpty(existing)) throw new IOException("此启动项已有 WinCare 恢复记录，请先重新扫描并核对状态。");
        marker.SetValue(valueName, value, RegistryValueKind.String);
    }

    private static void DeleteMarker(string markerRoot, string identity)
    {
        using var root = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, Environment.Is64BitOperatingSystem ? RegistryView.Registry64 : RegistryView.Default);
        root.DeleteSubKeyTree(GetMarkerPath(markerRoot, identity), throwOnMissingSubKey: false);
    }

    private static void RunScConfig(string serviceName, string startupType)
    {
        var startInfo = new ProcessStartInfo
        {
            FileName = Path.Combine(Environment.SystemDirectory, "sc.exe"),
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true
        };
        startInfo.ArgumentList.Add("config");
        startInfo.ArgumentList.Add(serviceName);
        startInfo.ArgumentList.Add("start=");
        startInfo.ArgumentList.Add(startupType);
        using var process = Process.Start(startInfo) ?? throw new InvalidOperationException("无法启动 Windows Service Control 命令。");
        var stdout = process.StandardOutput.ReadToEnd();
        var stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();
        if (process.ExitCode != 0)
            throw new InvalidOperationException($"Windows 服务配置失败：{(string.IsNullOrWhiteSpace(stderr) ? stdout : stderr).Trim()}");
    }

    private static string GetMetadataPath(string originalPath)
    {
        var canonical = Path.GetFullPath(originalPath).ToUpperInvariant();
        var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(canonical)));
        return Path.Combine(DisabledFilesRoot, $"{hash}.entry.json");
    }

    private static bool GetStartupFolderScope(string originalPath)
    {
        var fullPath = Path.GetFullPath(originalPath);
        var userStartup = Environment.GetFolderPath(Environment.SpecialFolder.Startup);
        var commonStartup = Environment.GetFolderPath(Environment.SpecialFolder.CommonStartup);
        if (IsDirectChildOf(fullPath, userStartup)) return false;
        if (IsDirectChildOf(fullPath, commonStartup)) return true;
        throw new InvalidOperationException("启动文件已移出受支持的启动文件夹，WinCare 已停止操作。");
    }

    private static bool IsDirectChildOf(string fullPath, string folder) =>
        !string.IsNullOrWhiteSpace(folder) &&
        string.Equals(Path.GetDirectoryName(fullPath), Path.GetFullPath(folder).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar), StringComparison.OrdinalIgnoreCase);

    private static void EnsureSafeRecoveryDirectory(bool createRecoveryDirectory)
    {
        var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        if (string.IsNullOrWhiteSpace(localAppData) || IsReparsePoint(localAppData))
            throw new InvalidOperationException("当前用户配置目录不可用或包含链接，WinCare 已停止文件操作。");
        var dataRoot = DataRoot;
        Directory.CreateDirectory(dataRoot);
        if (IsReparsePoint(dataRoot))
            throw new InvalidOperationException("WinCare 恢复目录包含链接或重解析点，已停止文件操作。");
        if (createRecoveryDirectory) Directory.CreateDirectory(DisabledFilesRoot);
        if (Directory.Exists(DisabledFilesRoot) && IsReparsePoint(DisabledFilesRoot))
            throw new InvalidOperationException("WinCare 恢复目录包含链接或重解析点，已停止文件操作。");
    }

    private static bool IsGeneratedBackupName(string fileName)
    {
        var stem = Path.GetFileNameWithoutExtension(fileName);
        return Guid.TryParseExact(stem, "N", out _);
    }

    private static bool IsReparsePoint(string path)
    {
        try { return (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0; }
        catch (FileNotFoundException) { return false; }
        catch (DirectoryNotFoundException) { return false; }
    }

    private static LegacyState ReadLegacyState()
    {
        if (!File.Exists(LegacyStatePath)) return new LegacyState();
        if (IsReparsePoint(LegacyStatePath))
            throw new InvalidDataException("旧版 WinCare 恢复记录是链接文件。请保留该文件并手动核对恢复区。");
        try
        {
            var state = JsonSerializer.Deserialize<LegacyState>(File.ReadAllText(LegacyStatePath));
            if (state?.DisabledTaskPaths is null || state.DisabledServices is null)
                throw new InvalidDataException("旧版 WinCare 恢复记录为空或格式无效。请保留 state.json 并检查恢复区。");
            return state;
        }
        catch (JsonException ex)
        {
            throw new InvalidDataException("旧版 WinCare 恢复记录损坏。为避免丢失已关闭项目的恢复信息，WinCare 不会自动重置记录。", ex);
        }
    }

    private static void WriteLegacyState(LegacyState state)
    {
        EnsureSafeRecoveryDirectory(createRecoveryDirectory: false);
        WriteJson(LegacyStatePath, state);
    }

    private static void WriteJson<T>(string path, T value, bool overwrite = true)
    {
        var directory = Path.GetDirectoryName(path)!;
        Directory.CreateDirectory(directory);
        if (IsReparsePoint(directory) || IsReparsePoint(path))
            throw new InvalidOperationException("恢复记录目标包含链接或重解析点，WinCare 已停止写入。");
        var temporary = path + $".{Guid.NewGuid():N}.tmp";
        try
        {
            using (var stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                JsonSerializer.Serialize(stream, value, new JsonSerializerOptions { WriteIndented = true });
            File.Move(temporary, path, overwrite);
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
        }
    }
}
