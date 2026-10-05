using System.Text;
using System.Text.Json;
using System.Windows.Forms;
using WinCare.Models;
using WinCare.Services;

namespace WinCare;

internal static class Program
{
    [STAThread]
    private static int Main(string[] args)
    {
        ApplicationConfiguration.Initialize();
        if (args.Length == 2 && string.Equals(args[0], "--admin-action", StringComparison.Ordinal))
            return RunAdminAction(args[1]);
        if (args.Length == 2 && string.Equals(args[0], "--admin-cleanup", StringComparison.Ordinal))
            return RunAdminCleanup(args[1]);

        Application.Run(new MainForm());
        return 0;
    }

    private static int RunAdminAction(string encodedRequest)
    {
        try
        {
            var json = Encoding.UTF8.GetString(Convert.FromBase64String(encodedRequest));
            var request = JsonSerializer.Deserialize<StartupActionRequest>(json)
                          ?? throw new InvalidDataException("管理员操作请求无效。");

            // Re-scan as the elevated account and use only a current, supported entry.
            var current = StartupScanner.Scan().Entries.FirstOrDefault(e => string.Equals(e.Id, request.Entry.Id, StringComparison.Ordinal))
                          ?? throw new InvalidOperationException("启动项已变化或不再受支持，请重新扫描。");
            if (!current.CanToggle) throw new InvalidOperationException("此启动项现在不可操作，请重新扫描确认当前状态。");
            if (request.Enable == current.Enabled) throw new InvalidOperationException("启动项状态已变化，请重新扫描后再操作。");

            var verb = request.Enable ? "恢复 / 启用" : "关闭";
            var warning = current.Warning ?? "此操作会更改系统范围的启动设置。请确认启动项名称和位置正确。";
            var details = $"{warning}{Environment.NewLine}{Environment.NewLine}{verb}：{current.Name}{Environment.NewLine}{current.Location}{Environment.NewLine}{current.Details}";
            if (MessageBox.Show(details, "请确认管理员启动项操作", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes)
                return 0;

            StartupActions.Apply(new StartupActionRequest { Entry = current, Enable = request.Enable });
            return 0;
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "WinCare 管理员操作失败", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }

    private static int RunAdminCleanup(string encodedPath)
    {
        try
        {
            var path = Encoding.UTF8.GetString(Convert.FromBase64String(encodedPath));
            var fullPath = Path.GetFullPath(path);
            var target = CleanupService.ScanCDrive().FirstOrDefault(t => t.RequiresAdmin &&
                string.Equals(t.Path, fullPath, StringComparison.OrdinalIgnoreCase))
                ?? throw new InvalidOperationException("清理路径不在 WinCare 的系统临时文件清单中。");
            var confirm = MessageBox.Show(
                $"将永久删除“{target.Name}”中修改时间超过 {CleanupService.MinimumAgeDays} 天的文件，不会进入回收站。{Environment.NewLine}{target.Path}{Environment.NewLine}{Environment.NewLine}重新扫描预估：{target.EligibleFiles:N0} 个文件、{StartupScanner.FormatSize(target.EstimatedBytes)}。正在使用或无法访问的文件会跳过。",
                "确认管理员清理", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
            if (confirm != DialogResult.Yes) return 0;

            var result = CleanupService.Clean(target.Path);
            MessageBox.Show($"已删除 {result.DeletedFiles:N0} 个文件，释放约 {StartupScanner.FormatSize(result.DeletedBytes)}。跳过 {result.SkippedFiles:N0} 个文件。",
                "清理完成", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return 0;
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "WinCare 管理员清理失败", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
