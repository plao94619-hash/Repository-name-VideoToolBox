using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using WinCare.Services;
namespace WinCare;
internal sealed class LargeFileWindow : Window
{
    private readonly ComboBox _threshold = new();
    private readonly Button _scan = new() { Content = "开始扫描" };
    private readonly Button _cancel = new() { Content = "取消", IsEnabled = false };
    private readonly TextBlock _status = new() { Text = "准备扫描；扫描过程可随时取消。" };
    private readonly ListView _results = new();
    private CancellationTokenSource? _cts;
    private sealed record Option(string Text, long Bytes) { public override string ToString() => Text; }
    public LargeFileWindow()
    {
        Title = "C 盘大文件分析 · WinCare";
        SystemBackdrop = new MicaBackdrop();
        foreach (var (text, bytes) in new[] { ("100 MiB", 100L), ("250 MiB", 250L), ("500 MiB", 500L), ("1 GiB", 1024L), ("2 GiB", 2048L) })
            _threshold.Items.Add(new Option(text, bytes * 1024 * 1024));
        _threshold.SelectedIndex = 0;
        _scan.Click += async (_, _) => await StartScanAsync();
        _cancel.Click += (_, _) => _cts?.Cancel();
        var toolbar = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, Children = { new TextBlock { Text = "分配空间门槛", VerticalAlignment = VerticalAlignment.Center }, _threshold, _scan, _cancel } };
        var info = new TextBlock { Text = "只读查询文件系统元数据，不打开内容、不执行删除。包含隐藏和系统项；链接会跳过，扫描范围内可识别的硬链接只计一次。", TextWrapping = TextWrapping.Wrap, Foreground = B("MutedTextBrush") };
        var root = new Grid { Margin = new Thickness(20), RowSpacing = 12 };
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        root.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        Grid.SetRow(info, 1); Grid.SetRow(_results, 2); Grid.SetRow(_status, 3);
        root.Children.Add(toolbar); root.Children.Add(info); root.Children.Add(_results); root.Children.Add(_status);
        Content = root;
    }
    private async Task StartScanAsync()
    {
        if (_cts is not null) return;
        var selected = (Option)_threshold.SelectedItem;
        var cts = new CancellationTokenSource(); _cts = cts;
        _scan.IsEnabled = false; _threshold.IsEnabled = false; _cancel.IsEnabled = true; _results.Items.Clear();
        var progress = new Progress<LargeFileScanProgress>(p => _status.Text = $"正在扫描：已检查 {p.ScannedPaths:N0} 个路径，匹配 {p.MatchingFiles:N0} 个文件，合并硬链接路径 {p.DuplicateHardLinkPaths:N0} 个，读取错误 {p.ReadErrors:N0} 次。");
        try
        {
            var result = await Task.Run(() => DiskUsageService.ScanLargeFiles(selected.Bytes, progress, cts.Token), cts.Token);
            foreach (var item in result.LargestFiles)
            {
                var row = new Grid { ColumnSpacing = 14, Margin = new Thickness(12, 8, 12, 8) };
                row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(180) });
                row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
                row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(115) });
                row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(115) });
                row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(155) });
                row.Children.Add(new TextBlock { Text = item.Name, TextTrimming = TextTrimming.CharacterEllipsis });
                var path = new TextBlock { Text = item.Path, TextTrimming = TextTrimming.CharacterEllipsis }; Grid.SetColumn(path, 1); row.Children.Add(path);
                var alloc = new TextBlock { Text = StartupScanner.FormatSize(item.AllocatedBytes) }; Grid.SetColumn(alloc, 2); row.Children.Add(alloc);
                var logical = new TextBlock { Text = StartupScanner.FormatSize(item.LogicalBytes) }; Grid.SetColumn(logical, 3); row.Children.Add(logical);
                var modified = new TextBlock { Text = item.ModifiedUtc.ToLocalTime().ToString("g") }; Grid.SetColumn(modified, 4); row.Children.Add(modified);
                var border = new Border { Child = row, CornerRadius = new CornerRadius(13), Background = B("CardBrush"), BorderBrush = B("CardStrokeBrush"), BorderThickness = new Thickness(1), Padding = new Thickness(8), Tag = item.Path };
                border.DoubleTapped += (_, _) => System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo("explorer.exe", $"/select,\"{item.Path}\"") { UseShellExecute = true });
                _results.Items.Add(border);
            }
            var shown = result.ResultsTruncated ? $"；仅显示最大 {result.LargestFiles.Count:N0} 项" : "";
            _status.Text = $"完成：检查 {result.ScannedPaths:N0} 个路径，找到 {result.MatchingFiles:N0} 个文件；分配空间 {StartupScanner.FormatSize(result.MatchingAllocatedBytes)}，逻辑大小 {StartupScanner.FormatSize(result.MatchingLogicalBytes)}{shown}；读取错误 {result.ReadErrors:N0} 次。双击定位文件。";
        }
        catch (OperationCanceledException) { _status.Text = "扫描已取消，未生成完整结果。"; }
        catch (Exception ex) { _status.Text = $"扫描失败：{ex.Message}"; }
        finally { cts.Dispose(); _cts = null; _scan.IsEnabled = true; _threshold.IsEnabled = true; _cancel.IsEnabled = false; }
    }
    private static Brush B(string key) => (Brush)Application.Current.Resources[key];
}
