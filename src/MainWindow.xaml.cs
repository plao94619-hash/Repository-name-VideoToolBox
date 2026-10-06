using System.Diagnostics;
using System.Text;
using System.Text.Json;
using Microsoft.UI.Xaml.Automation;
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
    private List<WechatMediaFile> _wechatFiles = [];
    private readonly HashSet<string> _wechatSelection = new(StringComparer.OrdinalIgnoreCase);
    private List<string> _warnings = [];
    private bool _initialized, _busy;
    private bool _wechatBusy;
    private CancellationTokenSource? _wechatScanCancellation;
    private DispatcherTimer? _debounce;
    public MainWindow()
    {
        InitializeComponent();
        Title = "WinCare · 启动项管理与 C 盘清理";
        SystemBackdrop = new MicaBackdrop();
        WechatRootBox.Text = WechatCleanupService.DefaultRoot;
        WechatArchiveRootBox.Text = WechatCleanupService.PreferredArchiveRoot;
        RefreshWechatArchiveSummary();
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
        WechatPage.Visibility = tag == "wechat" ? Visibility.Visible : Visibility.Collapsed;
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
    private void WechatDefaultPath_Click(object sender, RoutedEventArgs e) => WechatRootBox.Text = WechatCleanupService.DefaultRoot;
    private async void WechatScan_Click(object sender, RoutedEventArgs e)
    {
        if (_wechatBusy) return;
        var age = int.Parse(((ComboBoxItem)WechatAgeBox.SelectedItem).Tag.ToString()!);
        if (WechatImagesBox.IsChecked != true && WechatVideosBox.IsChecked != true)
        {
            await AlertAsync("微信专项清理", "至少选择一种媒体类型。");
            return;
        }
        _wechatBusy = true;
        var cancellation = new CancellationTokenSource();
        _wechatScanCancellation = cancellation;
        WechatCancelButton.IsEnabled = true;
        WechatStatus.Text = "正在扫描所选微信文件目录…";
        try
        {
            var root = WechatRootBox.Text;
            var includeImages = WechatImagesBox.IsChecked == true;
            var includeVideos = WechatVideosBox.IsChecked == true;
            var result = await Task.Run(() => WechatCleanupService.Scan(root, age, includeImages, includeVideos, cancellation.Token), cancellation.Token);
            _wechatFiles = result.Files.ToList();
            _wechatSelection.Clear();
            RenderWechatFiles();
            var total = _wechatFiles.Sum(x => x.Bytes);
            WechatStatus.Text = $"扫描完成：识别 {result.Accounts:N0} 个账号，找到 {_wechatFiles.Count:N0} 个符合条件的文件，共 {StartupScanner.FormatSize(total)}。时间按文件系统创建时间筛选；图片仅扫描 MsgAttach 下 Image 目录中的 .dat 文件。{(result.Warnings.Count > 0 ? $" 另有 {result.Warnings.Count} 条读取提示。" : "")}";
            if (result.Warnings.Count > 0) await AlertAsync("微信扫描提示", string.Join("\n", result.Warnings.Take(20)));
        }
        catch (OperationCanceledException) { WechatStatus.Text = "扫描已取消。"; }
        catch (Exception ex) { WechatStatus.Text = "扫描失败"; await AlertAsync("微信扫描失败", ex.Message); }
        finally { WechatCancelButton.IsEnabled = false; _wechatScanCancellation = null; cancellation.Dispose(); _wechatBusy = false; }
    }
    private void RenderWechatFiles()
    {
        WechatResults.Items.Clear();
        foreach (var media in _wechatFiles)
        {
            var grid = new Grid { ColumnSpacing = 12, Margin = new Thickness(10, 7, 10, 7) };
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(135) });
            var check = new CheckBox { IsChecked = _wechatSelection.Contains(media.Path), Tag = media.Path, VerticalAlignment = VerticalAlignment.Center };
            AutomationProperties.SetName(check, $"归档 {media.Account} {media.Kind} 文件");
            check.Checked += WechatFileSelection_Changed;
            check.Unchecked += WechatFileSelection_Changed;
            var details = new StackPanel { Spacing = 2 };
            details.Children.Add(new TextBlock { Text = $"{media.Account} · {media.Kind}", FontWeight = Microsoft.UI.Text.FontWeights.SemiBold });
            details.Children.Add(new TextBlock { Text = media.Path, FontSize = 12, Foreground = B("MutedTextBrush"), TextTrimming = TextTrimming.CharacterEllipsis });
            var metadata = new StackPanel { VerticalAlignment = VerticalAlignment.Center };
            metadata.Children.Add(new TextBlock { Text = StartupScanner.FormatSize(media.Bytes), HorizontalAlignment = HorizontalAlignment.Right });
            metadata.Children.Add(new TextBlock { Text = media.CreatedUtc.ToLocalTime().ToString("d"), FontSize = 12, Foreground = B("MutedTextBrush"), HorizontalAlignment = HorizontalAlignment.Right });
            Grid.SetColumn(details, 1); Grid.SetColumn(metadata, 2);
            grid.Children.Add(check); grid.Children.Add(details); grid.Children.Add(metadata);
            var card = new Border { CornerRadius = new CornerRadius(14), Background = B("CardBrush"), BorderBrush = B("CardStrokeBrush"), BorderThickness = new Thickness(1), Padding = new Thickness(6), Child = grid };
            WechatResults.Items.Add(new ListViewItem { Content = card, Tag = media });
        }
        UpdateWechatSelectionSummary();
    }
    private void WechatFileSelection_Changed(object sender, RoutedEventArgs e)
    {
        if (sender is not CheckBox { Tag: string path } check) return;
        if (check.IsChecked == true) _wechatSelection.Add(path); else _wechatSelection.Remove(path);
        UpdateWechatSelectionSummary();
    }
    private void UpdateWechatSelectionSummary()
    {
        var selected = _wechatFiles.Where(x => _wechatSelection.Contains(x.Path)).ToList();
        WechatSelectionSummary.Text = $"已选择 {selected.Count:N0} 项 · {StartupScanner.FormatSize(selected.Sum(x => x.Bytes))}";
    }
    private void WechatSelectAll_Click(object sender, RoutedEventArgs e)
    {
        _wechatSelection.Clear();
        foreach (var item in _wechatFiles) _wechatSelection.Add(item.Path);
        RenderWechatFiles();
    }
    private void WechatClearSelection_Click(object sender, RoutedEventArgs e)
    {
        _wechatSelection.Clear();
        RenderWechatFiles();
    }
    private async void WechatArchive_Click(object sender, RoutedEventArgs e)
    {
        if (_wechatBusy) return;
        var selected = _wechatFiles.Where(x => _wechatSelection.Contains(x.Path)).ToList();
        if (selected.Count == 0) { await AlertAsync("微信专项清理", "先扫描并选择要归档的文件。"); return; }
        var size = StartupScanner.FormatSize(selected.Sum(x => x.Bytes));
        var archiveRoot = WechatArchiveRootBox.Text.Trim();
        var sameDrive = string.Equals(Path.GetPathRoot(WechatRootBox.Text.Trim()), Path.GetPathRoot(archiveRoot), StringComparison.OrdinalIgnoreCase);
        var spaceNote = sameDrive ? "归档位于同一磁盘，不会腾出该磁盘的空间。" : "跨磁盘归档成功后可腾出源磁盘空间，具体大小以文件系统为准。";
        if (!await ConfirmAsync($"将把 {selected.Count:N0} 个文件（约 {size}）归档到 {archiveRoot}。{spaceNote}请先完全退出微信。归档期间，这些图片或视频可能无法从对应聊天中打开；可用“还原全部归档”恢复。原文件已不存在或正在使用时会跳过。继续吗？", "确认微信文件归档")) return;
        _wechatBusy = true;
        WechatStatus.Text = "正在归档所选文件…";
        try
        {
            var root = WechatRootBox.Text;
            var result = await Task.Run(() => WechatCleanupService.Archive(root, selected, archiveRoot));
            _wechatSelection.Clear();
            RefreshWechatArchiveSummary();
            WechatStatus.Text = $"归档完成：移动 {result.Completed:N0} 项（{StartupScanner.FormatSize(result.Bytes)}），跳过 {result.Skipped:N0} 项。{(sameDrive ? "同盘移动不释放磁盘空间。" : "跨盘移动已从源磁盘移出这些文件，实际可用空间请以 Windows 显示为准。")}";
            if (result.Warnings.Count > 0) await AlertAsync("归档提示", string.Join("\n", result.Warnings.Take(20)));
            await WechatScan_ClickRefresh();
        }
        catch (Exception ex) { await AlertAsync("微信归档失败", ex.Message); }
        finally { _wechatBusy = false; }
    }
    private async Task WechatScan_ClickRefresh()
    {
        try
        {
            var age = int.Parse(((ComboBoxItem)WechatAgeBox.SelectedItem).Tag.ToString()!);
            var root = WechatRootBox.Text;
            var includeImages = WechatImagesBox.IsChecked == true;
            var includeVideos = WechatVideosBox.IsChecked == true;
            var result = await Task.Run(() => WechatCleanupService.Scan(root, age, includeImages, includeVideos));
            _wechatFiles = result.Files.ToList();
            RenderWechatFiles();
        }
        catch { }
    }
    private async void WechatRestore_Click(object sender, RoutedEventArgs e)
    {
        var archived = WechatCleanupService.GetArchivedSummary();
        if (archived.Files == 0) { await AlertAsync("微信归档", "没有可访问的归档文件。若归档在移动硬盘，请连接磁盘后重试。"); return; }
        if (!await ConfirmAsync($"尝试还原 {archived.Files:N0} 个归档文件（约 {StartupScanner.FormatSize(archived.Bytes)}）到原微信目录。若原路径已有同名文件，将跳过且不会覆盖。继续吗？", "确认还原微信文件")) return;
        if (_wechatBusy) return;
        _wechatBusy = true;
        WechatStatus.Text = "正在还原归档文件…";
        try
        {
            var result = await Task.Run(() => WechatCleanupService.RestoreAll());
            RefreshWechatArchiveSummary();
            WechatStatus.Text = $"还原完成：恢复 {result.Completed:N0} 项，跳过 {result.Skipped:N0} 项。";
            if (result.Warnings.Count > 0) await AlertAsync("还原提示", string.Join("\n", result.Warnings.Take(20)));
            await WechatScan_ClickRefresh();
        }
        catch (Exception ex) { await AlertAsync("微信还原失败", ex.Message); }
        finally { _wechatBusy = false; }
    }
    private void RefreshWechatArchiveSummary()
    {
        var state = WechatCleanupService.GetArchivedSummary();
        var offline = WechatCleanupService.GetArchiveLocations().Count(x => !Directory.Exists(x));
        WechatArchiveSummary.Text = $"可访问归档 {state.Files:N0} 项 · {StartupScanner.FormatSize(state.Bytes)}{(offline > 0 ? $" · {offline} 个目录不可访问" : "")}";
    }
    private void WechatCancelScan_Click(object sender, RoutedEventArgs e) => _wechatScanCancellation?.Cancel();
}
