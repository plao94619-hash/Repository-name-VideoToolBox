using System.Diagnostics;
using System.Text;
using System.Text.Json;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using WinCare.Models;
using WinCare.Services;
namespace WinCare;
public sealed partial class MainWindow : Window
{
    private readonly List<StartupEntry> _entries = [];
    private List<StartupEntry> _visible = [];
    private List<string> _warnings = [];
    private bool _initialized, _busy;
    private DispatcherTimer? _debounce;
    public MainWindow()
    {
        InitializeComponent();
        Title = "WinCare · 启动项管理与 C 盘清理";
        SystemBackdrop = new MicaBackdrop();
        Navigation.SelectedItem = Navigation.MenuItems[0];
        Activated += FirstActivated;
    }
    private async void FirstActivated(object sender, WindowActivatedEventArgs e)
    {
        if (_initialized) return;
        _initialized = true;
        await ReloadStartupAsync();
        await ReloadCleanupAsync();
    }
    private void Navigation_SelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs args)
    {
        var tag = (args.SelectedItem as NavigationViewItem)?.Tag?.ToString();
        StartupPage.Visibility = tag == "startup" ? Visibility.Visible : Visibility.Collapsed;
        CleanupPage.Visibility = tag == "cleanup" ? Visibility.Visible : Visibility.Collapsed;
    }
    private async Task ReloadStartupAsync()
    {
        StartupSummary.Text = "正在扫描启动入口…";
        try
        {
            var scan = await Task.Run(StartupScanner.Scan);
            _entries.Clear(); _entries.AddRange(scan.Entries); _warnings = scan.Warnings;
            CategoryBox.Items.Clear(); CategoryBox.Items.Add("全部来源");
            foreach (var category in _entries.Select(x => x.Category).Distinct(StringComparer.CurrentCultureIgnoreCase).OrderBy(x => x)) CategoryBox.Items.Add(category);
            CategoryBox.SelectedIndex = 0;
            WarningsButton.Content = _warnings.Count == 0 ? "未发现扫描错误" : $"扫描提示：{_warnings.Count} 条";
            RenderStartupRows();
        }
        catch (Exception ex) { StartupSummary.Text = "扫描失败"; await AlertAsync("WinCare", ex.Message); }
    }
    private void RenderStartupRows()
    {
        var category = CategoryBox.SelectedItem?.ToString() ?? "全部来源";
        var query = SearchBox.Text.Trim();
        _visible = _entries.Where(x => (ShowHiddenBox.IsChecked == true || !x.Hidden) && (category == "全部来源" || string.Equals(category, x.Category, StringComparison.CurrentCultureIgnoreCase)) && (query.Length == 0 || x.SearchText.Contains(query, StringComparison.CurrentCultureIgnoreCase))).ToList();
        StartupRows.Children.Clear();
        foreach (var entry in _visible)
        {
            var row = new Grid { Margin = new Thickness(14, 11, 14, 11), ColumnSpacing = 12 };
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1.3, GridUnitType.Star) });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(140) });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1.8, GridUnitType.Star) });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            var name = new StackPanel();
            name.Children.Add(new TextBlock { Text = entry.Name, FontWeight = Microsoft.UI.Text.FontWeights.SemiBold, TextTrimming = TextTrimming.CharacterEllipsis });
            name.Children.Add(new TextBlock { Text = $"{entry.Category} · {entry.StateText}{(entry.Hidden ? " · 隐藏项" : "")}{(entry.SystemItem ? " · 系统项" : "")}", Foreground = B("MutedTextBrush"), FontSize = 12, TextTrimming = TextTrimming.CharacterEllipsis });
            var cat = new TextBlock { Text = entry.Category, VerticalAlignment = VerticalAlignment.Center, Foreground = B("MutedTextBrush"), TextTrimming = TextTrimming.CharacterEllipsis };
            var details = new TextBlock { Text = entry.DisplayDetails, VerticalAlignment = VerticalAlignment.Center, Foreground = B("MutedTextBrush"), TextTrimming = TextTrimming.CharacterEllipsis };
            var button = new Button { Content = entry.ActionText, IsEnabled = entry.CanToggle && !_busy, MinWidth = 96, VerticalAlignment = VerticalAlignment.Center, Tag = entry };
            button.Click += async (_, _) => await ToggleEntryAsync((StartupEntry)button.Tag);
            Grid.SetColumn(cat, 1); Grid.SetColumn(details, 2); Grid.SetColumn(button, 3);
            row.Children.Add(name); row.Children.Add(cat); row.Children.Add(details); row.Children.Add(button);
            var card = new Border { CornerRadius = new CornerRadius(17), Background = B("CardBrush"), BorderBrush = B("CardStrokeBrush"), BorderThickness = new Thickness(1), Padding = new Thickness(12), Child = row };
            ToolTipService.SetToolTip(card, entry.Warning ?? entry.Details);
            StartupRows.Children.Add(card);
        }
        StartupSummary.Text = $"显示 {_visible.Count} 项 · 共 {_entries.Count} 项 · 隐藏项 {_entries.Count(x => x.Hidden)} 项 · 可操作 {_visible.Count(x => x.CanToggle)} 项";
    }
    private async Task ToggleEntryAsync(StartupEntry entry)
    {
        if (_busy || !entry.CanToggle) return;
        var enable = !entry.Enabled;
        if (!entry.RequiresAdmin && (entry.Kind == StartupEntryKind.Service || entry.Kind == StartupEntryKind.ScheduledTask && entry.SystemItem) && !await ConfirmAsync($"{entry.Warning ?? "此启动项可能影响 Windows 功能或依赖它的程序。"}\n\n{(enable ? "恢复" : "关闭")}：{entry.Name}\n{entry.Location}", "请确认启动项操作")) return;
        _busy = true;
        try
        {
            var request = new StartupActionRequest { Entry = entry, Enable = enable };
            if (entry.RequiresAdmin)
            {
                var data = Convert.ToBase64String(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(request)));
                using var p = Process.Start(new ProcessStartInfo(Environment.ProcessPath!, $"--admin-action {data}") { UseShellExecute = true, Verb = "runas" }) ?? throw new InvalidOperationException("无法启动管理员操作。");
                await p.WaitForExitAsync();
                if (p.ExitCode != 0) throw new InvalidOperationException("管理员操作未成功，请查看刚才显示的错误信息。");
            }
            else StartupActions.Apply(request);
            await ReloadStartupAsync();
        }
        catch (System.ComponentModel.Win32Exception ex) when (ex.NativeErrorCode == 1223) { }
        catch (Exception ex) { await AlertAsync("操作未完成", ex.Message); await ReloadStartupAsync(); }
        finally { _busy = false; }
    }
    private async Task ReloadCleanupAsync()
    {
        CleanupSummary.Text = "正在扫描临时文件…";
        try
        {
            var targets = await Task.Run(CleanupService.ScanCDrive);
            CleanupRows.Children.Clear();
            foreach (var target in targets)
            {
                var grid = new Grid { Margin = new Thickness(15, 12, 15, 12), ColumnSpacing = 14 };
                grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1.2, GridUnitType.Star) });
                grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(2, GridUnitType.Star) });
                grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(125) });
                grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(130) });
                grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
                grid.Children.Add(new TextBlock { Text = target.Name, VerticalAlignment = VerticalAlignment.Center });
                var path = new TextBlock { Text = target.Path, VerticalAlignment = VerticalAlignment.Center, TextTrimming = TextTrimming.CharacterEllipsis, Foreground = B("MutedTextBrush") };
                var files = new TextBlock { Text = $"{target.EligibleFiles:N0} 个文件", VerticalAlignment = VerticalAlignment.Center };
                var size = new TextBlock { Text = StartupScanner.FormatSize(target.EstimatedBytes), VerticalAlignment = VerticalAlignment.Center };
                var button = new Button { Content = target.EligibleFiles > 0 ? "清理 7 天前文件" : "暂无可清理项", IsEnabled = target.EligibleFiles > 0, Tag = target, VerticalAlignment = VerticalAlignment.Center };
                button.Click += async (_, _) => await CleanTargetAsync((CleanupTarget)button.Tag);
                Grid.SetColumn(path, 1); Grid.SetColumn(files, 2); Grid.SetColumn(size, 3); Grid.SetColumn(button, 4);
                grid.Children.Add(path); grid.Children.Add(files); grid.Children.Add(size); grid.Children.Add(button);
                CleanupRows.Children.Add(new Border { CornerRadius = new CornerRadius(17), Background = B("CardBrush"), BorderBrush = B("CardStrokeBrush"), BorderThickness = new Thickness(1), Padding = new Thickness(8), Child = grid });
            }
            CleanupSummary.Text = $"共发现 {targets.Sum(x => x.EligibleFiles):N0} 个符合条件的文件，预计释放 {StartupScanner.FormatSize(targets.Sum(x => x.EstimatedBytes))}。";
        }
        catch (Exception ex) { CleanupSummary.Text = "扫描失败"; await AlertAsync("WinCare", ex.Message); }
    }
    private async Task CleanTargetAsync(CleanupTarget target)
    {
        try
        {
            if (target.RequiresAdmin)
            {
                var data = Convert.ToBase64String(Encoding.UTF8.GetBytes(target.Path));
                using var p = Process.Start(new ProcessStartInfo(Environment.ProcessPath!, $"--admin-cleanup {data}") { UseShellExecute = true, Verb = "runas" }) ?? throw new InvalidOperationException("无法启动管理员清理。");
                await p.WaitForExitAsync();
                if (p.ExitCode != 0) throw new InvalidOperationException("管理员清理未完成，请查看刚才显示的错误信息。");
            }
            else
            {
                if (!await ConfirmAsync($"将永久删除“{target.Name}”中修改时间超过 7 天的临时文件，不会进入回收站。\n{target.Path}\n\n预估 {target.EligibleFiles:N0} 个文件、{StartupScanner.FormatSize(target.EstimatedBytes)}。", "确认清理")) return;
                var result = await Task.Run(() => CleanupService.Clean(target.Path));
                await AlertAsync("清理完成", $"已删除 {result.DeletedFiles:N0} 个文件，释放约 {StartupScanner.FormatSize(result.DeletedBytes)}。跳过 {result.SkippedFiles:N0} 个文件。");
            }
            await ReloadCleanupAsync();
        }
        catch (System.ComponentModel.Win32Exception ex) when (ex.NativeErrorCode == 1223) { }
        catch (Exception ex) { await AlertAsync("清理未完成", ex.Message); }
    }
    private async Task<bool> ConfirmAsync(string text, string title)
    {
        var d = new ContentDialog { Title = title, Content = text, PrimaryButtonText = "继续", CloseButtonText = "取消", DefaultButton = ContentDialogButton.Close, XamlRoot = Content.XamlRoot };
        return await d.ShowAsync() == ContentDialogResult.Primary;
    }
    private async Task AlertAsync(string title, string text)
    {
        var d = new ContentDialog { Title = title, Content = text, CloseButtonText = "确定", XamlRoot = Content.XamlRoot };
        await d.ShowAsync();
    }
    private static Brush B(string key) => (Brush)Application.Current.Resources[key];
    private async void RefreshStartup_Click(object sender, RoutedEventArgs e) => await ReloadStartupAsync();
    private async void RefreshCleanup_Click(object sender, RoutedEventArgs e) => await ReloadCleanupAsync();
    private void SearchBox_TextChanged(object sender, TextChangedEventArgs e)
    {
        _debounce ??= new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(180) };
        _debounce.Tick -= Debounce_Tick; _debounce.Tick += Debounce_Tick; _debounce.Stop(); _debounce.Start();
    }
    private void Debounce_Tick(object? sender, object e) { _debounce?.Stop(); RenderStartupRows(); }
    private void CategoryBox_SelectionChanged(object sender, SelectionChangedEventArgs e) { if (_initialized) RenderStartupRows(); }
    private void ShowHidden_Changed(object sender, RoutedEventArgs e) { if (_initialized) RenderStartupRows(); }
    private async void Warnings_Click(object sender, RoutedEventArgs e) => await AlertAsync("扫描提示", _warnings.Count == 0 ? "本次扫描未报告读取错误。" : string.Join("\n", _warnings.Take(35)));
    private void StorageSettings_Click(object sender, RoutedEventArgs e) => Process.Start(new ProcessStartInfo("ms-settings:storage") { UseShellExecute = true });
    private void LargeFiles_Click(object sender, RoutedEventArgs e) { var w = new LargeFileWindow(); w.Activate(); }
}
