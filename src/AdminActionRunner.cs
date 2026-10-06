using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using WinCare.Models;
using WinCare.Services;
namespace WinCare;
internal static class AdminActionRunner
{
    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern int MessageBoxW(IntPtr hwnd, string text, string caption, uint type);
    private const uint YesNoWarning = 0x00000004 | 0x00000030 | 0x00040000;
    private const uint ErrorIcon = 0x00000010 | 0x00040000;
    private const uint InformationIcon = 0x00000040 | 0x00040000;
    internal static int Run(string action, string payload) => action == "--admin-action" ? Startup(payload) : Cleanup(payload);
    private static int Startup(string encoded)
    {
        try
        {
            var req = JsonSerializer.Deserialize<StartupActionRequest>(Encoding.UTF8.GetString(Convert.FromBase64String(encoded))) ?? throw new InvalidDataException("管理员操作请求无效。");
            var current = StartupScanner.Scan().Entries.FirstOrDefault(e => e.Id == req.Entry.Id) ?? throw new InvalidOperationException("启动项已变化或不再受支持，请重新扫描。");
            if (!current.CanToggle || req.Enable == current.Enabled) throw new InvalidOperationException("启动项状态已变化，请重新扫描后再操作。");
            var verb = req.Enable ? "恢复 / 启用" : "关闭";
            var details = $"{current.Warning ?? "此操作会更改系统范围的启动设置。请确认启动项名称和位置正确。"}\n\n{verb}：{current.Name}\n{current.Location}\n{current.Details}";
            if (MessageBoxW(IntPtr.Zero, details, "请确认管理员启动项操作", YesNoWarning) != 6) return 0;
            StartupActions.Apply(new StartupActionRequest { Entry = current, Enable = req.Enable });
            return 0;
        }
        catch (Exception ex) { MessageBoxW(IntPtr.Zero, ex.Message, "WinCare 管理员操作失败", ErrorIcon); return 1; }
    }
    private static int Cleanup(string encoded)
    {
        try
        {
            var full = Path.GetFullPath(Encoding.UTF8.GetString(Convert.FromBase64String(encoded)));
            var target = CleanupService.PreviewTarget(full, true);
            var prompt = $"将永久删除“{target.Name}”中修改时间超过 7 天的文件，不会进入回收站。\n{target.Path}\n\n重新扫描预估：{target.EligibleFiles:N0} 个文件、{StartupScanner.FormatSize(target.EstimatedBytes)}。正在使用或无法访问的文件会跳过。";
            if (MessageBoxW(IntPtr.Zero, prompt, "确认管理员清理", YesNoWarning) != 6) return 0;
            var result = CleanupService.Clean(target.Path, true);
            MessageBoxW(IntPtr.Zero, $"已删除 {result.DeletedFiles:N0} 个文件，释放约 {StartupScanner.FormatSize(result.DeletedBytes)}。跳过 {result.SkippedFiles:N0} 个文件。", "清理完成", InformationIcon);
            return 0;
        }
        catch (Exception ex) { MessageBoxW(IntPtr.Zero, ex.Message, "WinCare 管理员清理失败", ErrorIcon); return 1; }
    }
}
