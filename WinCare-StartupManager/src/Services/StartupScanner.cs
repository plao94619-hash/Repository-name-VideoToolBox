using Microsoft.Win32;
using System.Runtime.InteropServices;
using WinCare.Models;

namespace WinCare.Services;

public static class StartupScanner
{
    private const string DisabledChild = "WinCareDisabled";
    private sealed record RegistryLocation(RegistryHive Hive, RegistryView View, string Path, string Category, bool Writable, bool Hidden, bool System);

    public static ScanResult Scan()
    {
        var result = new ScanResult();
        ScanRegistry(result);
        ScanStartupFolders(result);
        StartupActions.RestoreSnapshot restoreSnapshot;
        try { restoreSnapshot = StartupActions.LoadRestoreSnapshot(); }
        catch (Exception ex)
        {
            result.Warnings.Add($"无法读取 WinCare 的恢复记录，已关闭项目将保持只读：{ex.Message}");
            restoreSnapshot = new StartupActions.RestoreSnapshot();
        }
        ScanScheduledTasks(result, restoreSnapshot);
        ScanServices(result, restoreSnapshot);
        result.Entries.Sort((a, b) =>
        {
            var enabled = b.Enabled.CompareTo(a.Enabled);
            if (enabled != 0) return enabled;
            var category = string.Compare(a.Category, b.Category, StringComparison.CurrentCultureIgnoreCase);
            return category != 0 ? category : string.Compare(a.Name, b.Name, StringComparison.CurrentCultureIgnoreCase);
        });
        return result;
    }

    private static IEnumerable<RegistryLocation> GetRegistryLocations()
    {
        var views = Environment.Is64BitOperatingSystem
            ? new[] { RegistryView.Registry64, RegistryView.Registry32 }
            : new[] { RegistryView.Default };
        var currentSid = System.Security.Principal.WindowsIdentity.GetCurrent().User?.Value;

        foreach (var view in views)
        {
            foreach (var hive in new[] { RegistryHive.CurrentUser, RegistryHive.LocalMachine })
            {
                var scope = hive == RegistryHive.CurrentUser ? "当前用户" : "所有用户";
                foreach (var leaf in new[] { "Run", "RunOnce", "RunServices", "RunServicesOnce" })
                {
                    var path = $"Software\\Microsoft\\Windows\\CurrentVersion\\{leaf}";
                    yield return new(hive, view, path, $"注册表 {leaf} · {scope}", true, false, hive == RegistryHive.LocalMachine);
                }
                yield return new(hive, view, "Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer\\Run",
                    $"策略启动项 · {scope}", true, false, hive == RegistryHive.LocalMachine);
            }

            if (Environment.Is64BitOperatingSystem)
            {
                using var users = RegistryKey.OpenBaseKey(RegistryHive.Users, view);
                foreach (var sid in users.GetSubKeyNames().Where(s =>
                             s.Contains('-') &&
                             !s.EndsWith("_Classes", StringComparison.OrdinalIgnoreCase) &&
                             !string.Equals(s, currentSid, StringComparison.OrdinalIgnoreCase)))
                {
                    var prefix = $"{sid}\\Software\\Microsoft\\Windows\\CurrentVersion";
                    foreach (var leaf in new[] { "Run", "RunOnce", "RunServices", "RunServicesOnce" })
                        yield return new(RegistryHive.Users, view, $"{prefix}\\{leaf}", $"注册表 {leaf} · 已加载的其他用户", true, false, true);
                    yield return new(RegistryHive.Users, view, $"{prefix}\\Policies\\Explorer\\Run", "策略启动项 · 已加载的其他用户", true, false, true);
                }
            }
        }

        foreach (var hive in new[] { RegistryHive.LocalMachine, RegistryHive.CurrentUser })
        {
            yield return new(hive, RegistryView.Registry64, "Software\\Microsoft\\Windows NT\\CurrentVersion\\Windows",
                "Windows Load/Run（系统位置）", false, true, hive == RegistryHive.LocalMachine);
            yield return new(hive, RegistryView.Registry64, "Software\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon",
                "Winlogon Shell/Userinit（关键项）", false, true, true);
        }
    }

    private static void ScanRegistry(ScanResult result)
    {
        foreach (var location in GetRegistryLocations())
        {
            try
            {
                using var root = RegistryKey.OpenBaseKey(location.Hive, location.View);
                using var active = root.OpenSubKey(location.Path, writable: false);
                using var disabled = location.Writable ? root.OpenSubKey($"{location.Path}\\{DisabledChild}", writable: false) : null;
                AddRegistryValues(result, location, active, isWinCareDisabled: false);
                if (location.Writable) AddRegistryValues(result, location, disabled, isWinCareDisabled: true);
            }
            catch (Exception ex) when (ex is UnauthorizedAccessException or System.Security.SecurityException or IOException)
            {
                result.Warnings.Add($"无法读取注册表位置 {location.Path}：{ex.Message}");
            }
        }
    }

    private static void AddRegistryValues(ScanResult result, RegistryLocation location, RegistryKey? key, bool isWinCareDisabled)
    {
        if (key is null) return;
        foreach (var valueName in key.GetValueNames())
        {
            try
            {
                var value = key.GetValue(valueName, null, RegistryValueOptions.DoNotExpandEnvironmentNames);
                var data = value switch
                {
                    string s => s,
                    string[] a => string.Join("; ", a),
                    byte[] b => $"二进制数据（{b.Length} 字节）",
                    null => "",
                    _ => Convert.ToString(value, System.Globalization.CultureInfo.InvariantCulture) ?? ""
                };
                if (string.IsNullOrWhiteSpace(data)) data = "（空值）";
                var displayName = string.IsNullOrWhiteSpace(valueName) ? "（默认值）" : valueName;
                var windowsDisabled = !isWinCareDisabled && StartupApprovedState.IsDisabled(location.Hive, location.View, location.Path, valueName);
                var path = isWinCareDisabled ? $"{location.Path}\\{DisabledChild}" : location.Path;
                var hiveText = location.Hive switch { RegistryHive.CurrentUser => "HKCU", RegistryHive.LocalMachine => "HKLM", _ => "HKEY_USERS" };
                var viewText = location.View == RegistryView.Registry32 ? "32 位" : "64 位";
                result.Entries.Add(new StartupEntry
                {
                    Id = $"reg|{location.Hive}|{location.View}|{location.Path}|{valueName}|{isWinCareDisabled}",
                    Name = displayName,
                    Category = location.Category,
                    Location = $"{hiveText} [{viewText}]\\{path}",
                    Details = windowsDisabled ? $"{data} · Windows 启动应用设置为关闭" : data,
                    Kind = StartupEntryKind.RegistryValue,
                    Enabled = !isWinCareDisabled && !windowsDisabled,
                    Hidden = location.Hidden,
                    SystemItem = location.System,
                    CanToggle = location.Writable && (isWinCareDisabled || !windowsDisabled),
                    RequiresAdmin = location.Hive != RegistryHive.CurrentUser,
                    Hive = location.Hive.ToString(),
                    View = location.View.ToString(),
                    RegistryPath = location.Path,
                    RegistryValueName = valueName,
                    Warning = !location.Writable ? "系统关键启动值仅展示，不提供一键关闭。" :
                        windowsDisabled ? "此项已在 Windows 的启动应用设置中关闭；WinCare 只显示状态，不修改 Windows 内部状态。" : null
                });
            }
            catch (Exception ex) when (ex is UnauthorizedAccessException or System.Security.SecurityException or IOException)
            {
                result.Warnings.Add($"无法读取 {location.Path} 下的注册表值 {valueName}：{ex.Message}");
            }
        }
    }

    private static void ScanStartupFolders(ScanResult result)
    {
        AddStartupFolder(result, Environment.GetFolderPath(Environment.SpecialFolder.Startup), "当前用户启动文件夹", false);
        AddStartupFolder(result, Environment.GetFolderPath(Environment.SpecialFolder.CommonStartup), "所有用户启动文件夹", true);

        try
        {
            if (!Directory.Exists(StartupActions.DisabledFilesRoot)) return;
            foreach (var metadataPath in Directory.EnumerateFiles(StartupActions.DisabledFilesRoot, "*.entry.json", SearchOption.TopDirectoryOnly))
            {
                try
                {
                    var meta = System.Text.Json.JsonSerializer.Deserialize<StartupActions.DisabledFile>(File.ReadAllText(metadataPath));
                    if (meta is null || !File.Exists(meta.BackupPath)) continue;
                    result.Entries.Add(new StartupEntry
                    {
                        Id = $"file|{meta.OriginalPath}",
                        Name = Path.GetFileName(meta.OriginalPath),
                        Category = meta.CommonFolder ? "所有用户启动文件夹" : "当前用户启动文件夹",
                        Location = $"已关闭：{meta.OriginalPath}",
                        Details = "文件已移到 WinCare 可恢复区。",
                        Kind = StartupEntryKind.StartupFile,
                        Enabled = false,
                        CanToggle = true,
                        RequiresAdmin = meta.CommonFolder,
                        Hidden = false,
                        SystemItem = meta.CommonFolder,
                        OriginalPath = meta.OriginalPath
                    });
                }
                catch (Exception ex) when (ex is IOException or System.Text.Json.JsonException or UnauthorizedAccessException)
                {
                    result.Warnings.Add($"读取启动文件备份记录失败：{Path.GetFileName(metadataPath)}");
                }
            }
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            result.Warnings.Add($"无法读取 WinCare 的启动文件恢复区：{ex.Message}");
        }
    }

    private static void AddStartupFolder(ScanResult result, string folder, string category, bool common)
    {
        if (string.IsNullOrWhiteSpace(folder) || !Directory.Exists(folder)) return;
        try
        {
            foreach (var path in Directory.EnumerateFiles(folder, "*", SearchOption.TopDirectoryOnly))
            {
                try
                {
                    var info = new FileInfo(path);
                    var attrs = info.Attributes;
                    var windowsDisabled = StartupApprovedState.IsStartupFolderDisabled(path);
                    result.Entries.Add(new StartupEntry
                    {
                        Id = $"file|{path}",
                        Name = info.Name,
                        Category = category,
                        Location = path,
                        Details = $"{StartupScanner.FormatSize(info.Length)} · 修改于 {info.LastWriteTime:g}" +
                                  (windowsDisabled ? " · Windows 启动应用设置为关闭" : ""),
                        Kind = StartupEntryKind.StartupFile,
                        Enabled = !windowsDisabled,
                        Hidden = (attrs & FileAttributes.Hidden) != 0,
                        SystemItem = common || (attrs & FileAttributes.System) != 0,
                        CanToggle = (attrs & FileAttributes.ReparsePoint) == 0 && !windowsDisabled,
                        RequiresAdmin = common,
                        OriginalPath = path,
                        Warning = windowsDisabled ? "此项已在 Windows 的启动应用设置中关闭；WinCare 只显示状态。" :
                            (attrs & FileAttributes.ReparsePoint) != 0 ? "链接文件不支持移动关闭。" : null
                    });
                }
                catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
                {
                    result.Warnings.Add($"无法读取启动文件：{Path.GetFileName(path)}");
                }
            }
        }
        catch (Exception ex) when (ex is IOException or UnauthorizedAccessException)
        {
            result.Warnings.Add($"无法读取启动文件夹 {folder}：{ex.Message}");
        }
    }

    private static void ScanScheduledTasks(ScanResult result, StartupActions.RestoreSnapshot restoreSnapshot)
    {
        object? serviceObject = null;
        try
        {
            var serviceType = Type.GetTypeFromProgID("Schedule.Service");
            if (serviceType is null)
            {
                result.Warnings.Add("系统未提供 Task Scheduler COM 接口，未扫描计划任务。");
                return;
            }
            serviceObject = Activator.CreateInstance(serviceType);
            dynamic service = serviceObject!;
            service.Connect();
            dynamic root = service.GetFolder("\\");
            WalkTaskFolder(result, root, "\\", restoreSnapshot);
        }
        catch (Exception ex)
        {
            result.Warnings.Add($"计划任务扫描不完整：{Unwrap(ex).Message}");
        }
        finally
        {
            if (serviceObject is not null && Marshal.IsComObject(serviceObject)) Marshal.FinalReleaseComObject(serviceObject);
        }
    }

    private static void WalkTaskFolder(ScanResult result, dynamic folder, string folderPath, StartupActions.RestoreSnapshot restoreSnapshot)
    {
        try
        {
            dynamic tasks = folder.GetTasks(1); // TASK_ENUM_HIDDEN
            for (int i = 1; i <= (int)tasks.Count; i++)
            {
                try
                {
                    dynamic task = tasks.Item(i);
                    dynamic definition = task.Definition;
                    dynamic triggers = definition.Triggers;
                    var triggerNames = new List<string>();
                    for (int j = 1; j <= (int)triggers.Count; j++)
                    {
                        dynamic trigger = triggers.Item(j);
                        int type = (int)trigger.Type;
                        if (type is 0 or 7 or 8 or 9 or 11)
                            triggerNames.Add(type switch { 0 => "事件触发", 7 => "注册时", 8 => "开机时", 9 => "登录时", _ => "会话变化" });
                    }
                    if (triggerNames.Count == 0) continue;
                    var taskPath = (string)task.Path;
                    var enabled = (bool)task.Enabled;
                    bool hidden = false;
                    try { hidden = (bool)definition.Settings.Hidden; } catch { }
                    bool microsoft = taskPath.StartsWith("\\Microsoft\\Windows\\", StringComparison.OrdinalIgnoreCase);
                    bool appDisabled = restoreSnapshot.IsTaskManaged(taskPath);
                    bool legacyRestore = !enabled && restoreSnapshot.IsTaskLegacy(taskPath);
                    bool staleRestore = enabled && appDisabled;
                    result.Entries.Add(new StartupEntry
                    {
                        Id = $"task|{taskPath}",
                        Name = (string)task.Name,
                        Category = $"计划任务 · {string.Join("、", triggerNames.Distinct())}",
                        Location = taskPath,
                        Details = GetTaskActions(definition),
                        Kind = StartupEntryKind.ScheduledTask,
                        Enabled = enabled,
                        Hidden = hidden,
                        SystemItem = microsoft,
                        CanToggle = enabled != appDisabled,
                        RequiresAdmin = true,
                        Warning = staleRestore ? "WinCare 恢复记录与当前任务状态不一致；请手动核对任务和恢复记录后再操作。" :
                            legacyRestore ? "此任务由旧版 WinCare 关闭；恢复记录保存在用户目录。恢复前请核对任务名称和动作。" :
                            !enabled && !appDisabled ? "该任务已由 Windows 或其他工具关闭；WinCare 不会擅自重新启用。" :
                            microsoft ? "Microsoft 任务可能影响 Windows 功能，关闭前请核对动作。" : null
                    });
                }
                catch (Exception ex)
                {
                    result.Warnings.Add($"计划任务读取失败：{Unwrap(ex).Message}");
                }
            }
            dynamic folders = folder.GetFolders(0);
            for (int i = 1; i <= (int)folders.Count; i++)
            {
                dynamic child = folders.Item(i);
                string childPath = folderPath == "\\" ? $"\\{child.Name}" : $"{folderPath}\\{child.Name}";
                WalkTaskFolder(result, child, childPath, restoreSnapshot);
            }
        }
        catch (Exception ex)
        {
            result.Warnings.Add($"读取计划任务目录 {folderPath} 失败：{Unwrap(ex).Message}");
        }
    }

    private static string GetTaskActions(dynamic definition)
    {
        try
        {
            dynamic actions = definition.Actions;
            var values = new List<string>();
            for (int i = 1; i <= (int)actions.Count; i++)
            {
                dynamic action = actions.Item(i);
                try
                {
                    var path = Convert.ToString(action.Path) ?? "";
                    var args = Convert.ToString(action.Arguments) ?? "";
                    values.Add(string.IsNullOrWhiteSpace(args) ? path : $"{path} {args}");
                }
                catch { values.Add("非程序动作"); }
            }
            return string.Join(" | ", values);
        }
        catch { return "任务动作不可读"; }
    }

    private static void ScanServices(ScanResult result, StartupActions.RestoreSnapshot restoreSnapshot)
    {
        try
        {
            using var root = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, Environment.Is64BitOperatingSystem ? RegistryView.Registry64 : RegistryView.Default)
                .OpenSubKey(@"SYSTEM\CurrentControlSet\Services", writable: false);
            if (root is null) return;
            foreach (var name in root.GetSubKeyNames())
            {
                try
                {
                    using var key = root.OpenSubKey(name, writable: false);
                    if (key is null) continue;
                    var start = Convert.ToInt32(key.GetValue("Start", 3));
                    if (start is not (0 or 1 or 2 or 4)) continue;
                    var type = Convert.ToInt32(key.GetValue("Type", 0));
                    var driver = (type & 0x0F) is 1 or 2;
                    var display = Convert.ToString(key.GetValue("DisplayName")) ?? name;
                    var image = Convert.ToString(key.GetValue("ImagePath")) ?? "";
                    var delayed = Convert.ToInt32(key.GetValue("DelayedAutoStart", 0)) == 1;
                    var enabled = start != 4;
                    var appDisabled = restoreSnapshot.IsServiceManaged(name);
                    var legacyRestore = start == 4 && restoreSnapshot.IsServiceLegacy(name);
                    var staleRestore = appDisabled && start != 4;
                    var protectedStart = start is 0 or 1;
                    result.Entries.Add(new StartupEntry
                    {
                        Id = $"service|{name}",
                        Name = display,
                        Category = driver ? "驱动/系统启动" : "Windows 服务",
                        Location = $"HKLM\\SYSTEM\\CurrentControlSet\\Services\\{name}",
                        Details = $"{StartDescription(start, delayed)} · {(string.IsNullOrWhiteSpace(image) ? "无 ImagePath" : image)}",
                        Kind = StartupEntryKind.Service,
                        Enabled = enabled,
                        Hidden = string.IsNullOrWhiteSpace(Convert.ToString(key.GetValue("DisplayName"))) || name.StartsWith(".", StringComparison.Ordinal),
                        SystemItem = protectedStart || driver || name.StartsWith("Win", StringComparison.OrdinalIgnoreCase),
                        CanToggle = (start == 2 && !driver && !appDisabled) || (start == 4 && appDisabled),
                        RequiresAdmin = true,
                        ServiceName = name,
                        DelayedAutoStart = delayed,
                        Warning = staleRestore ? "WinCare 恢复记录与当前服务状态不一致；请手动核对服务和恢复记录后再操作。" :
                            legacyRestore ? "此服务由旧版 WinCare 关闭；恢复记录保存在用户目录。恢复前请核对服务名称和映像路径。" :
                            protectedStart ? "Boot/System 驱动属于关键启动项，列出供检查但不提供关闭按钮。" :
                            enabled ? "关闭后下次启动生效；请先确认没有其他服务依赖它。" :
                            start == 4 && !appDisabled ? "该服务原本已禁用；WinCare 不会擅自重新启用。" : null
                    });
                }
                catch (Exception ex) when (ex is UnauthorizedAccessException or IOException or System.Security.SecurityException)
                {
                    result.Warnings.Add($"读取服务 {name} 失败：{ex.Message}");
                }
            }
        }
        catch (Exception ex)
        {
            result.Warnings.Add($"服务扫描不完整：{ex.Message}");
        }
    }

    private static string StartDescription(int start, bool delayed) => start switch
    {
        0 => "Boot 启动",
        1 => "System 启动",
        2 when delayed => "自动（延迟）",
        2 => "自动启动",
        4 => "已禁用",
        _ => "未知"
    };

    private static Exception Unwrap(Exception ex) => ex is System.Reflection.TargetInvocationException { InnerException: not null } tie ? tie.InnerException : ex;

    public static string FormatSize(long bytes)
    {
        string[] units = ["B", "KB", "MB", "GB", "TB"];
        double size = bytes;
        var i = 0;
        while (size >= 1024 && i < units.Length - 1) { size /= 1024; i++; }
        return $"{size:0.##} {units[i]}";
    }
}

internal static class StartupApprovedState
{
    public static bool IsDisabled(RegistryHive hive, RegistryView view, string startupPath, string valueName)
    {
        if (string.IsNullOrWhiteSpace(valueName)) return false;
        var leaf = startupPath[(startupPath.LastIndexOf('\\') + 1)..];
        if (!string.Equals(leaf, "Run", StringComparison.OrdinalIgnoreCase)) return false;
        var root = hive == RegistryHive.Users ? startupPath[..startupPath.IndexOf('\\')] + "\\" : "";
        var path = $"{root}Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\{(view == RegistryView.Registry32 ? "Run32" : "Run")}";
        try
        {
            using var key = RegistryKey.OpenBaseKey(hive, view).OpenSubKey(path, writable: false);
            return key?.GetValue(valueName) is byte[] bytes && bytes.Length > 0 && bytes[0] == 0x03;
        }
        catch { return false; }
    }

    public static bool IsStartupFolderDisabled(string path)
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder", writable: false);
            return key?.GetValue(Path.GetFileName(path)) is byte[] bytes && bytes.Length > 0 && bytes[0] == 0x03;
        }
        catch { return false; }
    }
}
