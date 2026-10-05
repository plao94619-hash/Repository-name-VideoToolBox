using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.Text;
using System.Text.Json;
using System.Windows.Forms;
using WinCare.Models;
using WinCare.Services;

namespace WinCare;

public sealed class MainForm : Form
{
    private static readonly Color Ink = Color.FromArgb(28, 35, 49);
    private static readonly Color Muted = Color.FromArgb(99, 109, 126);
    private static readonly Color Accent = Color.FromArgb(39, 103, 210);
    private readonly DataGridView _startupGrid = new();
    private readonly DataGridView _cleanupGrid = new();
    private readonly TextBox _search = new();
    private readonly ComboBox _category = new();
    private readonly CheckBox _showHidden = new();
    private readonly Label _startupSummary = new();
    private readonly Label _startupWarnings = new();
    private readonly Label _cleanupSummary = new();
    private readonly Button _refreshStartup = new();
    private readonly Button _refreshCleanup = new();
    private readonly List<StartupEntry> _entries = [];
    private List<StartupEntry> _visibleEntries = [];
    private IReadOnlyList<CleanupTarget> _cleanupTargets = [];
    private readonly TabControl _tabs = new();
    private readonly System.Windows.Forms.Timer _searchDebounce = new() { Interval = 180 };
    private bool _startupActionInProgress;
    private bool _cleanupActionInProgress;

    public MainForm()
    {
        Text = "WinCare · 启动项管理与 C 盘清理";
        StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = new Size(1000, 650);
        Size = new Size(1240, 780);
        BackColor = Color.FromArgb(245, 247, 250);
        ForeColor = Ink;
        Font = new Font("Segoe UI", 9.5F);
        AutoScaleMode = AutoScaleMode.Dpi;

        BuildUi();
        _searchDebounce.Tick += (_, _) =>
        {
            _searchDebounce.Stop();
            ApplyStartupFilters();
        };
        FormClosed += (_, _) => _searchDebounce.Dispose();
        Shown += async (_, _) =>
        {
            await ReloadStartupAsync();
            await ReloadCleanupAsync();
        };
    }

    private void BuildUi()
    {
        var appHeader = new Panel { Dock = DockStyle.Top, Height = 76, BackColor = Color.White, Padding = new Padding(22, 13, 18, 8) };
        var title = new Label { Text = "WinCare", Font = new Font("Segoe UI Semibold", 18F, FontStyle.Bold), ForeColor = Ink, AutoSize = true, Location = new Point(22, 9) };
        var subtitle = new Label { Text = "Windows 启动项管理与 C 盘清理", Font = new Font("Segoe UI", 9.5F), ForeColor = Muted, AutoSize = true, Location = new Point(126, 22) };
        appHeader.Controls.Add(title);
        appHeader.Controls.Add(subtitle);

        _tabs.Dock = DockStyle.Fill;
        _tabs.Font = new Font("Segoe UI Semibold", 10F, FontStyle.Bold);
        _tabs.TabPages.Add(BuildStartupPage());
        _tabs.TabPages.Add(BuildCleanupPage());
        Controls.Add(_tabs);
        Controls.Add(appHeader);
    }

    private TabPage BuildStartupPage()
    {
        var page = new TabPage("启动项管理") { BackColor = Color.FromArgb(245, 247, 250), Padding = new Padding(14) };
        var layout = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 4, BackColor = page.BackColor };
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 64));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 48));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 58));

        var heading = new Panel { Dock = DockStyle.Fill };
        var headingTitle = new Label { Text = "启动项", Font = new Font("Segoe UI Semibold", 16F, FontStyle.Bold), AutoSize = true, ForeColor = Ink, Location = new Point(2, 3) };
        var headingCaption = new Label { Text = "覆盖常见登录 / 开机入口；隐藏项默认显示，系统关键项只读。", Font = new Font("Segoe UI", 9F), AutoSize = true, ForeColor = Muted, Location = new Point(2, 34) };
        _refreshStartup.Text = "重新扫描";
        StyleButton(_refreshStartup, filled: false);
        _refreshStartup.Size = new Size(108, 34);
        _refreshStartup.Anchor = AnchorStyles.Right | AnchorStyles.Top;
        _refreshStartup.Location = new Point(Width - 185, 12);
        _refreshStartup.Click += async (_, _) => await ReloadStartupAsync();
        heading.Resize += (_, _) => _refreshStartup.Location = new Point(heading.ClientSize.Width - _refreshStartup.Width - 4, 14);
        heading.Controls.Add(headingTitle);
        heading.Controls.Add(headingCaption);
        heading.Controls.Add(_refreshStartup);

        var toolbar = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.LeftToRight, WrapContents = false, Padding = new Padding(0, 5, 0, 0) };
        _search.PlaceholderText = "搜索名称、路径或启动命令";
        _search.Width = 290;
        _search.Height = 32;
        _search.BorderStyle = BorderStyle.FixedSingle;
        _search.TextChanged += (_, _) =>
        {
            _searchDebounce.Stop();
            _searchDebounce.Start();
        };
        _category.DropDownStyle = ComboBoxStyle.DropDownList;
        _category.Width = 220;
        _category.Height = 32;
        _category.Items.Add("全部来源");
        _category.SelectedIndex = 0;
        _category.SelectedIndexChanged += (_, _) => ApplyStartupFilters();
        _showHidden.Text = "显示隐藏项";
        _showHidden.Checked = true;
        _showHidden.AutoSize = true;
        _showHidden.Margin = new Padding(12, 8, 4, 0);
        _showHidden.CheckedChanged += (_, _) => ApplyStartupFilters();
        toolbar.Controls.Add(_search);
        toolbar.Controls.Add(_category);
        toolbar.Controls.Add(_showHidden);

        ConfigureGrid(_startupGrid);
        _startupGrid.Columns.Add(TextColumn("Name", "名称", 185));
        _startupGrid.Columns.Add(TextColumn("Category", "入口", 170));
        _startupGrid.Columns.Add(TextColumn("MarkText", "标记", 135));
        _startupGrid.Columns.Add(TextColumn("StateText", "状态", 140));
        _startupGrid.Columns.Add(TextColumn("DisplayDetails", "路径 / 命令", 500, fill: true));
        var action = new DataGridViewButtonColumn { Name = "Action", HeaderText = "操作", DataPropertyName = "ActionText", Width = 100, FlatStyle = FlatStyle.Flat, UseColumnTextForButtonValue = false };
        _startupGrid.Columns.Add(action);
        _startupGrid.VirtualMode = true;
        _startupGrid.CellValueNeeded += StartupCellValueNeeded;
        _startupGrid.CellFormatting += StartupCellFormatting;
        _startupGrid.CellContentClick += async (_, e) =>
        {
            if (e.RowIndex < 0 || e.ColumnIndex < 0 || _startupGrid.Columns[e.ColumnIndex].Name != "Action") return;
            if (e.RowIndex < _visibleEntries.Count)
                await ToggleStartupEntryAsync(_visibleEntries[e.RowIndex]);
        };
        _startupGrid.CellToolTipTextNeeded += (_, e) =>
        {
            if (e.RowIndex >= 0 && e.RowIndex < _visibleEntries.Count)
            {
                var item = _visibleEntries[e.RowIndex];
                e.ToolTipText = item.Warning ?? item.Details;
            }
        };

        var footer = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 2, RowCount = 1, Padding = new Padding(2, 8, 2, 0) };
        footer.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
        footer.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
        _startupSummary.AutoSize = true;
        _startupSummary.ForeColor = Muted;
        _startupWarnings.AutoSize = true;
        _startupWarnings.ForeColor = Accent;
        _startupWarnings.Cursor = Cursors.Hand;
        _startupWarnings.Click += (_, _) => ShowScanWarnings();
        footer.Controls.Add(_startupSummary, 0, 0);
        footer.Controls.Add(_startupWarnings, 1, 0);

        layout.Controls.Add(heading, 0, 0);
        layout.Controls.Add(toolbar, 0, 1);
        layout.Controls.Add(_startupGrid, 0, 2);
        layout.Controls.Add(footer, 0, 3);
        page.Controls.Add(layout);
        return page;
    }

    private TabPage BuildCleanupPage()
    {
        var page = new TabPage("C 盘清理") { BackColor = Color.FromArgb(245, 247, 250), Padding = new Padding(14) };
        var layout = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 4, BackColor = page.BackColor };
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 64));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 94));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 48));

        var heading = new Panel { Dock = DockStyle.Fill };
        var headingTitle = new Label { Text = "C 盘临时文件", Font = new Font("Segoe UI Semibold", 16F, FontStyle.Bold), AutoSize = true, ForeColor = Ink, Location = new Point(2, 3) };
        var headingCaption = new Label { Text = "先扫描预估空间，再逐项清理。", Font = new Font("Segoe UI", 9F), AutoSize = true, ForeColor = Muted, Location = new Point(2, 34) };
        _refreshCleanup.Text = "重新扫描";
        StyleButton(_refreshCleanup, filled: false);
        _refreshCleanup.Size = new Size(108, 34);
        _refreshCleanup.Click += async (_, _) => await ReloadCleanupAsync();
        var storageSettings = new Button { Text = "Windows 存储设置", Size = new Size(152, 34) };
        StyleButton(storageSettings, filled: false);
        storageSettings.Click += (_, _) =>
        {
            try { Process.Start(new ProcessStartInfo("ms-settings:storage") { UseShellExecute = true }); }
            catch (Exception ex) { MessageBox.Show(this, ex.Message, "无法打开 Windows 存储设置", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        };
        heading.Resize += (_, _) =>
        {
            _refreshCleanup.Location = new Point(heading.ClientSize.Width - _refreshCleanup.Width - 4, 14);
            storageSettings.Location = new Point(_refreshCleanup.Left - storageSettings.Width - 10, 14);
        };
        _refreshCleanup.Location = new Point(Width - _refreshCleanup.Width - 30, 14);
        storageSettings.Location = new Point(_refreshCleanup.Left - storageSettings.Width - 10, 14);
        heading.Controls.Add(storageSettings);
        heading.Controls.Add(headingTitle);
        heading.Controls.Add(headingCaption);
        heading.Controls.Add(_refreshCleanup);

        var guidance = new Label
        {
            Dock = DockStyle.Fill,
            AutoSize = false,
            Padding = new Padding(14, 11, 12, 8),
            BackColor = Color.FromArgb(235, 242, 252),
            ForeColor = Color.FromArgb(45, 67, 98),
            Text = "仅扫描 C 盘的当前用户 TEMP 与 Windows\\Temp，默认只清理修改时间超过 7 天的文件。清理会永久删除文件（不进入回收站），并跳过链接、正在使用或无权限访问的文件。不会触碰下载、文档、浏览器数据、回收站或 WinSxS。"
        };

        ConfigureGrid(_cleanupGrid);
        _cleanupGrid.Columns.Add(TextColumn("Name", "区域", 190));
        _cleanupGrid.Columns.Add(TextColumn("Path", "路径", 540, fill: true));
        _cleanupGrid.Columns.Add(TextColumn("EligibleFiles", "可清理文件", 110));
        _cleanupGrid.Columns.Add(TextColumn("EstimatedSize", "预计释放", 115));
        var cleanAction = new DataGridViewButtonColumn { Name = "Clean", HeaderText = "操作", DataPropertyName = "ActionText", Width = 164, FlatStyle = FlatStyle.Flat, UseColumnTextForButtonValue = false };
        _cleanupGrid.Columns.Add(cleanAction);
        _cleanupGrid.CellFormatting += (_, e) =>
        {
            if (e.RowIndex < 0 || e.ColumnIndex < 0) return;
            if (_cleanupGrid.Columns[e.ColumnIndex].Name == "Clean" && _cleanupGrid.Rows[e.RowIndex].DataBoundItem is CleanupRow row)
            {
                e.Value = row.ActionText;
                e.CellStyle.ForeColor = row.Target.EligibleFiles > 0 ? Accent : Muted;
                e.CellStyle.BackColor = Color.White;
            }
        };
        _cleanupGrid.CellContentClick += async (_, e) =>
        {
            if (e.RowIndex < 0 || e.ColumnIndex < 0 || _cleanupGrid.Columns[e.ColumnIndex].Name != "Clean") return;
            if (_cleanupGrid.Rows[e.RowIndex].DataBoundItem is CleanupRow row && row.Target.EligibleFiles > 0)
                await CleanTargetAsync(row.Target);
        };

        _cleanupSummary.AutoSize = true;
        _cleanupSummary.ForeColor = Muted;
        var footer = new Panel { Dock = DockStyle.Fill, Padding = new Padding(2, 11, 0, 0) };
        footer.Controls.Add(_cleanupSummary);
        layout.Controls.Add(heading, 0, 0);
        layout.Controls.Add(guidance, 0, 1);
        layout.Controls.Add(_cleanupGrid, 0, 2);
        layout.Controls.Add(footer, 0, 3);
        page.Controls.Add(layout);
        return page;
    }

    private static void ConfigureGrid(DataGridView grid)
    {
        grid.Dock = DockStyle.Fill;
        grid.BackgroundColor = Color.White;
        grid.BorderStyle = BorderStyle.None;
        grid.EnableHeadersVisualStyles = false;
        grid.ColumnHeadersDefaultCellStyle.BackColor = Color.FromArgb(239, 243, 249);
        grid.ColumnHeadersDefaultCellStyle.ForeColor = Ink;
        grid.ColumnHeadersDefaultCellStyle.Font = new Font("Segoe UI Semibold", 9.5F, FontStyle.Bold);
        grid.ColumnHeadersHeight = 38;
        grid.DefaultCellStyle.BackColor = Color.White;
        grid.DefaultCellStyle.ForeColor = Ink;
        grid.DefaultCellStyle.SelectionBackColor = Color.FromArgb(229, 239, 253);
        grid.DefaultCellStyle.SelectionForeColor = Ink;
        grid.DefaultCellStyle.Padding = new Padding(6, 2, 6, 2);
        grid.RowTemplate.Height = 42;
        grid.GridColor = Color.FromArgb(232, 236, 242);
        grid.RowHeadersVisible = false;
        grid.AllowUserToAddRows = false;
        grid.AllowUserToDeleteRows = false;
        grid.AllowUserToResizeRows = false;
        grid.MultiSelect = false;
        grid.ReadOnly = true;
        grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
        grid.AutoGenerateColumns = false;
        grid.ShowCellToolTips = true;
    }

    private static DataGridViewTextBoxColumn TextColumn(string property, string heading, int width, bool fill = false) =>
        new() { Name = property, DataPropertyName = property, HeaderText = heading, Width = width, AutoSizeMode = fill ? DataGridViewAutoSizeColumnMode.Fill : DataGridViewAutoSizeColumnMode.None, SortMode = DataGridViewColumnSortMode.NotSortable };

    private static void StyleButton(Button button, bool filled)
    {
        button.FlatStyle = FlatStyle.Flat;
        button.FlatAppearance.BorderSize = filled ? 0 : 1;
        button.FlatAppearance.BorderColor = Color.FromArgb(208, 216, 227);
        button.BackColor = filled ? Accent : Color.White;
        button.ForeColor = filled ? Color.White : Ink;
        button.Cursor = Cursors.Hand;
    }

    private void StartupCellFormatting(object? sender, DataGridViewCellFormattingEventArgs e)
    {
        if (e.RowIndex < 0 || e.RowIndex >= _visibleEntries.Count || e.ColumnIndex < 0) return;
        var entry = _visibleEntries[e.RowIndex];
        if (_startupGrid.Columns[e.ColumnIndex].Name == "Action")
        {
            e.Value = entry.ActionText;
            e.CellStyle.ForeColor = entry.CanToggle ? Accent : Muted;
            e.CellStyle.BackColor = Color.White;
        }
        if (_startupGrid.Columns[e.ColumnIndex].Name == "MarkText" && entry.Hidden)
            e.CellStyle.ForeColor = Color.FromArgb(171, 92, 33);
    }

    private void StartupCellValueNeeded(object? sender, DataGridViewCellValueEventArgs e)
    {
        if (e.RowIndex < 0 || e.RowIndex >= _visibleEntries.Count || e.ColumnIndex < 0) return;
        var entry = _visibleEntries[e.RowIndex];
        e.Value = _startupGrid.Columns[e.ColumnIndex].Name switch
        {
            "Name" => entry.Name,
            "Category" => entry.Category,
            "MarkText" => entry.MarkText,
            "StateText" => entry.StateText,
            "DisplayDetails" => entry.DisplayDetails,
            "Action" => entry.ActionText,
            _ => null
        };
    }

    private async Task ReloadStartupAsync()
    {
        _refreshStartup.Enabled = false;
        _startupSummary.Text = "正在扫描启动入口…";
        try
        {
            var result = await Task.Run(StartupScanner.Scan);
            _entries.Clear();
            _entries.AddRange(result.Entries);
            _scanWarnings = result.Warnings;
            RefreshCategoryChoices();
            ApplyStartupFilters();
            _startupWarnings.Text = result.Warnings.Count == 0 ? "未发现扫描错误" : $"扫描提示：{result.Warnings.Count}";
        }
        catch (Exception ex)
        {
            _startupSummary.Text = "扫描失败";
            MessageBox.Show(this, ex.Message, "WinCare", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        finally { _refreshStartup.Enabled = true; }
    }

    private List<string> _scanWarnings = [];

    private void RefreshCategoryChoices()
    {
        var selected = _category.SelectedItem?.ToString() ?? "全部来源";
        _category.Items.Clear();
        _category.Items.Add("全部来源");
        foreach (var item in _entries.Select(e => e.Category).Distinct(StringComparer.CurrentCultureIgnoreCase).OrderBy(x => x, StringComparer.CurrentCultureIgnoreCase))
            _category.Items.Add(item);
        var index = _category.Items.IndexOf(selected);
        _category.SelectedIndex = index >= 0 ? index : 0;
    }

    private void ApplyStartupFilters()
    {
        _searchDebounce.Stop();
        if (_startupGrid.Columns.Count == 0) return;
        var category = _category.SelectedItem?.ToString() ?? "全部来源";
        var query = _search.Text.Trim();
        _visibleEntries = _entries.Where(entry =>
                (_showHidden.Checked || !entry.Hidden) &&
                (category == "全部来源" || string.Equals(category, entry.Category, StringComparison.CurrentCultureIgnoreCase)) &&
                (query.Length == 0 || entry.SearchText.Contains(query, StringComparison.CurrentCultureIgnoreCase)))
            .ToList();
        _startupGrid.RowCount = _visibleEntries.Count;
        _startupGrid.Invalidate();
        var hiddenCount = _entries.Count(e => e.Hidden);
        _startupSummary.Text = $"显示 {_visibleEntries.Count} 项 · 共 {_entries.Count} 项 · 隐藏项 {hiddenCount} 项 · 可操作 {_visibleEntries.Count(e => e.CanToggle)} 项";
    }

    private void ShowScanWarnings()
    {
        if (_scanWarnings.Count == 0)
        {
            MessageBox.Show(this, "本次扫描未报告读取错误。", "扫描提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        var lines = _scanWarnings.Take(35).ToList();
        if (_scanWarnings.Count > lines.Count) lines.Add($"… 另有 {_scanWarnings.Count - lines.Count} 条未显示。");
        MessageBox.Show(this, string.Join(Environment.NewLine, lines), "扫描提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    private async Task ToggleStartupEntryAsync(StartupEntry entry)
    {
        if (_startupActionInProgress || !entry.CanToggle) return;
        var enable = !entry.Enabled;
        var sensitive = entry.Kind == StartupEntryKind.Service || (entry.Kind == StartupEntryKind.ScheduledTask && entry.SystemItem);
        if (sensitive && !entry.RequiresAdmin)
        {
            var warning = entry.Warning ?? "此启动项可能影响 Windows 功能或依赖它的程序。";
            var verb = enable ? "恢复" : "关闭";
            if (MessageBox.Show(this, $"{warning}{Environment.NewLine}{Environment.NewLine}{verb}：{entry.Name}{Environment.NewLine}{entry.Location}", "请确认启动项操作", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes)
                return;
        }

        _startupActionInProgress = true;
        _startupGrid.Enabled = false;
        _refreshStartup.Enabled = false;
        try
        {
            var request = new StartupActionRequest { Entry = entry, Enable = enable };
            if (entry.RequiresAdmin)
                await RunElevatedActionAsync(request);
            else
                StartupActions.Apply(request);
            await ReloadStartupAsync();
        }
        catch (System.ComponentModel.Win32Exception ex) when (ex.NativeErrorCode == 1223)
        {
            // UAC was cancelled.
        }
        catch (Exception ex)
        {
            MessageBox.Show(this, ex.Message, "操作未完成", MessageBoxButtons.OK, MessageBoxIcon.Error);
            await ReloadStartupAsync();
        }
        finally
        {
            _startupActionInProgress = false;
            _startupGrid.Enabled = true;
            _refreshStartup.Enabled = true;
        }
    }

    private async Task RunElevatedActionAsync(StartupActionRequest request)
    {
        var json = JsonSerializer.Serialize(request);
        var encoded = Convert.ToBase64String(Encoding.UTF8.GetBytes(json));
        var process = StartElevated($"--admin-action {encoded}");
        await process.WaitForExitAsync();
        if (process.ExitCode != 0) throw new InvalidOperationException("管理员操作未成功，请查看刚才显示的错误信息。");
    }

    private async Task ReloadCleanupAsync()
    {
        _refreshCleanup.Enabled = false;
        _cleanupSummary.Text = "正在扫描临时文件…";
        try
        {
            _cleanupTargets = await Task.Run(CleanupService.ScanCDrive);
            var rows = _cleanupTargets.Select(t => new CleanupRow(
                t.Name, t.Path, t.EligibleFiles.ToString("N0"),
                StartupScanner.FormatSize(t.EstimatedBytes),
                t.EligibleFiles > 0 ? "清理 7 天前文件" : "暂无可清理项", t)).ToList();
            _cleanupGrid.DataSource = new BindingList<CleanupRow>(rows);
            var total = _cleanupTargets.Sum(t => t.EstimatedBytes);
            var files = _cleanupTargets.Sum(t => t.EligibleFiles);
            _cleanupSummary.Text = $"共发现 {files:N0} 个符合条件的文件，预计释放 {StartupScanner.FormatSize(total)}。";
        }
        catch (Exception ex)
        {
            _cleanupSummary.Text = "扫描失败";
            MessageBox.Show(this, ex.Message, "WinCare", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        finally { _refreshCleanup.Enabled = true; }
    }

    private async Task CleanTargetAsync(CleanupTarget target)
    {
        if (_cleanupActionInProgress) return;
        if (!target.RequiresAdmin)
        {
            var confirm = MessageBox.Show(this,
                $"将永久删除“{target.Name}”中修改时间超过 {CleanupService.MinimumAgeDays} 天的临时文件，不会进入回收站。{Environment.NewLine}{target.Path}{Environment.NewLine}{Environment.NewLine}预估 {target.EligibleFiles:N0} 个文件、{StartupScanner.FormatSize(target.EstimatedBytes)}。继续前请关闭可能正在使用这些临时文件的程序。",
                "确认清理", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
            if (confirm != DialogResult.Yes) return;
        }
        _cleanupActionInProgress = true;
        _cleanupGrid.Enabled = false;
        _refreshCleanup.Enabled = false;
        try
        {
            if (target.RequiresAdmin)
            {
                var encodedPath = Convert.ToBase64String(Encoding.UTF8.GetBytes(target.Path));
                var process = StartElevated($"--admin-cleanup {encodedPath}");
                await process.WaitForExitAsync();
                if (process.ExitCode != 0) throw new InvalidOperationException("管理员清理未完成，请查看刚才显示的错误信息。");
            }
            else
            {
                var result = await Task.Run(() => CleanupService.Clean(target.Path));
                MessageBox.Show(this, $"已删除 {result.DeletedFiles:N0} 个文件，释放约 {StartupScanner.FormatSize(result.DeletedBytes)}。跳过 {result.SkippedFiles:N0} 个文件。",
                    "清理完成", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            await ReloadCleanupAsync();
        }
        catch (System.ComponentModel.Win32Exception ex) when (ex.NativeErrorCode == 1223)
        {
            // UAC was cancelled.
        }
        catch (Exception ex)
        {
            MessageBox.Show(this, ex.Message, "清理未完成", MessageBoxButtons.OK, MessageBoxIcon.Error);
            await ReloadCleanupAsync();
        }
        finally
        {
            _cleanupActionInProgress = false;
            _cleanupGrid.Enabled = true;
            _refreshCleanup.Enabled = true;
        }
    }

    private static Process StartElevated(string arguments)
    {
        var start = new ProcessStartInfo
        {
            FileName = Application.ExecutablePath,
            Arguments = arguments,
            UseShellExecute = true,
            Verb = "runas"
        };
        return Process.Start(start) ?? throw new InvalidOperationException("无法启动管理员操作。");
    }

    private sealed record CleanupRow(string Name, string Path, string EligibleFiles, string EstimatedSize, string ActionText, CleanupTarget Target);
}
