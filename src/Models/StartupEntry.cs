namespace WinCare.Models;

public enum StartupEntryKind
{
    RegistryValue,
    StartupFile,
    ScheduledTask,
    Service
}

public sealed class StartupEntry
{
    private string? _searchText;

    public required string Id { get; init; }
    public required string Name { get; init; }
    public required string Category { get; init; }
    public required string Location { get; init; }
    public required string Details { get; init; }
    public StartupEntryKind Kind { get; init; }
    public bool Enabled { get; init; }
    public bool Hidden { get; init; }
    public bool SystemItem { get; init; }
    public bool CanToggle { get; init; }
    public bool RequiresAdmin { get; init; }
    public string? Hive { get; init; }
    public string? View { get; init; }
    public string? RegistryPath { get; init; }
    public string? RegistryValueName { get; init; }
    public string? OriginalPath { get; init; }
    public string? ServiceName { get; init; }
    public bool DelayedAutoStart { get; init; }
    public string? Warning { get; init; }

    public string StateText => Enabled ? "已启用" : CanToggle ? "WinCare 已关闭" : "已关闭 / 外部禁用";
    public string MarkText => string.Join(" · ", new[] { Hidden ? "隐藏项" : null, SystemItem ? "系统项" : null, RequiresAdmin ? "需管理员" : null }.Where(x => x is not null));
    public string ActionText => !CanToggle ? "只读" : Enabled ? "一键关闭" : "恢复";
    public string DisplayDetails => $"{Location}  ·  {Details}";
    internal string SearchText => _searchText ??= $"{Name} {Category} {Location} {Details}";
}

public sealed class ScanResult
{
    public List<StartupEntry> Entries { get; } = [];
    public List<string> Warnings { get; } = [];
}

public sealed class StartupActionRequest
{
    public required StartupEntry Entry { get; init; }
    public bool Enable { get; init; }
}
