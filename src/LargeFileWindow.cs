using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using WinCare.Services;
namespace WinCare;
internal sealed class LargeFileWindow : Window
{
    private readonly ComboBox _threshold = new();
    private readonly Button _scan = new() { Content = "开始扫描", Padding = new Thickness(16, 9, 16, 9) };
    private readonly Button _cancel = new() { Content = "取消扫描", IsEnabled = false, Padding = new Thickness(14, 9, 14, 9) };
    private readonly TextBlock _status = new() { Text = "准备扫描；扫描过程可随时取消。", Foreground = B("MutedTextBrush"), TextWrapping = TextWrapping.Wrap };
    private readonly ListView _results = new();
    private CancellationTokenSource? _cts;
    private sealed record Option(string Text, long Bytes) { public override string ToString() => Text; }
    public LargeFileWindow()
    {
        Title = "大文件分析 · WinCare";
        SystemBackdrop = new MicaBackdrop();
        foreach (var (text, bytes) in new[] { ("100 MiB", 100L), ("250 MiB", 250L), ("500 MiB", 500L), ("1 GiB", 1024L), ("2 GiB", 2048L) })
            _threshold.Items.Add(new Option(text, bytes * 1024 * 1024));
        _threshold.SelectedIndex = 0;
        _scan.Click += async (_, _) => await StartScanAsync();
        _cancel.Click += (_, _) => _cts?.Cancel();
        _scan.Background = B("AccentBrush");
        _scan.Foreground = B("AccentOnBrush");
        _scan.BorderThickness = new Thickness(0);
        _threshold.MinWidth = 130;

        var title = new StackPanel { Spacing = 4 };
        title.Children.Add(new TextBlock { Text = "大文件分析", FontSize = 26, FontWeight = Microsoft.UI.Text.FontWeights.SemiBold });
        title.Children.Add(new TextBlock
        {
            Text = "用只读扫描找出占用空间较大的文件，不会打开或删除文件内容。",
            Foreground = B("MutedTextBrush"),
            TextWrapping = TextWrapping.Wrap
        });
        var toolbar = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10 };
        toolbar.Children.Add(new TextBlock { Text = "最小分配空间", VerticalAlignment = VerticalAlignment.Center, Foreground = B("MutedTextBrush") });
        toolbar.Children.Add(_threshold);
        toolbar.Children.Add(_scan);
        toolbar.Children.Add(_cancel);
        var controls = new Border
        {
            Padding = new Thickness(14),
            CornerRadius = new CornerRadius(18),
            Background = B("CardBrush"),
            BorderBrush = B("CardStrokeBrush"),
            BorderThickness = new Thickness(1),
            Child = toolbar
        };
        var info = new Border
        {
            Padding = new Thickness(14, 11, 14, 11),
            CornerRadius = new CornerRadius(16),
            Background = B("AccentSoftBrush"),
            Child = new TextBlock
            {
                Text = "只读查询文件系统元数据；包含隐藏和系统项，跳过链接，扫描范围内可识别的硬链接只计一次。双击结果可在资源管理器中定位。",
                TextWrapping = TextWrapping.Wrap,
                Foreground = B("AppTextBrush")
            }
        };
        var headings = CreateResultGrid();
        headings.Children.Add(HeaderCell("文件名", 0));
        headings.Children.Add(HeaderCell("位置", 1));
        headings.Children.Add(HeaderCell("占用空间", 2));
        headings.Children.Add(HeaderCell("文件大小", 3));
        headings.Children.Add(HeaderCell("修改时间", 4));
        var root = new Grid { Margin = new Thickness(24), RowSpacing = 12 };
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        root.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
        _results.Background = new SolidColorBrush(Microsoft.UI.Colors.Transparent);
        _results.BorderThickness = new Thickness(0);
        Grid.SetRow(controls, 1);
        Grid.SetRow(info, 2);
        Grid.SetRow(headings, 3);
        Grid.SetRow(_results, 4);
        Grid.SetRow(_status, 5);
        root.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
        root.Children.Add(title);
        root.Children.Add(controls);
        root.Children.Add(info);
        root.Children.Add(headings);
        root.Children.Add(_results);
        root.Children.Add(_status);
        Content = root;
    }

    private static Grid CreateResultGrid()
    {
        var grid = new Grid { ColumnSpacing = 14, Margin = new Thickness(12, 0, 12, 0) };
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(180) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(115) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(115) });
        grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(155) });
        return grid;
    }

    private static TextBlock HeaderCell(string text, int column)
    {
        var block = new TextBlock
        {
            Text = text,
            FontSize = 11,
            FontWeight = Microsoft.UI.Text.FontWeights.SemiBold,
            Foreground = B("MutedTextBrush"),
            VerticalAlignment = VerticalAlignment.Center
        };
        Grid.SetColumn(block, column);
        return block;
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
                var row = CreateResultGrid();
                var name = new TextBlock { Text = item.Name, TextTrimming = TextTrimming.CharacterEllipsis, VerticalAlignment = VerticalAlignment.Center };
                var path = new TextBlock { Text = item.Path, TextTrimming = TextTrimming.CharacterEllipsis, VerticalAlignment = VerticalAlignment.Center, Foreground = B("MutedTextBrush"), FontSize = 11 };
                var alloc = new TextBlock { Text = StartupScanner.FormatSize(item.AllocatedBytes), VerticalAlignment = VerticalAlignment.Center, FontWeight = Microsoft.UI.Text.FontWeights.SemiBold, Foreground = B("AccentBrush") };
                var logical = new TextBlock { Text = StartupScanner.FormatSize(item.LogicalBytes), VerticalAlignment = VerticalAlignment.Center };
                var modified = new TextBlock { Text = item.ModifiedUtc.ToLocalTime().ToString("g"), VerticalAlignment = VerticalAlignment.Center, Foreground = B("MutedTextBrush"), FontSize = 11 };
                Grid.SetColumn(path, 1);
                Grid.SetColumn(alloc, 2);
                Grid.SetColumn(logical, 3);
                Grid.SetColumn(modified, 4);
                row.Children.Add(name);
                row.Children.Add(path);
                row.Children.Add(alloc);
                row.Children.Add(logical);
                row.Children.Add(modified);
                var border = new Border { Child = row, CornerRadius = new CornerRadius(15), Background = B("RowBrush"), BorderBrush = B("CardStrokeBrush"), BorderThickness = new Thickness(1), Padding = new Thickness(12, 10, 12, 10), Tag = item.Path };
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
