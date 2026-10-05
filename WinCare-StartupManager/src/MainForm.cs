using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.Text;
using System.Text.Json;
using System.Windows.Forms;
using WinCare.Models;
using WinCare.Services;
using WinCare.UI;

namespace WinCare;

public sealed class MainForm : GlassForm
{
    private static readonly Color Ink = WinCareTheme.Ink;
    private static readonly Color Muted = WinCareTheme.Muted;
    private static readonly Color Accent = WinCareTheme.Accent;
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
    private readonly Panel _pageHost = new();
    private readonly Button _startupNavigation = new();
    private readonly Button _cleanupNavigation = new();
    private Panel _startupPage = null!;
    private Panel _cleanupPage = null!;
    private readonly System.Windows.Forms.Timer _searchDebounce = new() { Interval = 180 };
    private bool _startupActionInProgress;
    private bool _cleanupActionInProgress;

    public MainForm()
    {
        Text = "WinCare · 启动项管理与 C 盘清理";
        StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = new Size(1080, 680);
        Size = new Size(1360, 860);
        BackColor = WinCareTheme.Canvas;
        ForeColor = Ink;
        Font = SystemFonts.MessageBoxFont;
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
        var canvas = new LiquidBackdropPanel { Dock = DockStyle.Fill, Padding = new Padding(18) };
        var shell = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 2,
            RowCount = 1,
            BackColor = Color.Transparent,
            Margin = Padding.Empty
        };
        shell.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 252));
        shell.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));

        var sidebar = BuildSidebar();
        sidebar.Dock = DockStyle.Fill;
        sidebar.Margin = new Padding(0, 0, 16, 0);

        _startupPage = BuildStartupPage();
        _cleanupPage = BuildCleanupPage();
        _startupPage.Dock = DockStyle.Fill;
        _cleanupPage.Dock = DockStyle.Fill;
        _cleanupPage.Visible = false;
        _pageHost.Dock = DockStyle.Fill;
        _pageHost.BackColor = Color.Transparent;
        _pageHost.Controls.Add(_cleanupPage);
        _pageHost.Controls.Add(_startupPage);

        shell.Controls.Add(sidebar, 0, 0);
        shell.Controls.Add(_pageHost, 1, 0);
        canvas.Controls.Add(shell);
        Controls.Add(canvas);
        SelectPage(startup: true);
    }

    private Control BuildSidebar()
    {
        var sidebar = new GlassSurface
        {
            CornerRadius = 28,
            TopColor = WinCareTheme.GlassTop,
            BottomColor = WinCareTheme.GlassBottom,
            Padding = new Padding(16)
        };
        var layout = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 1,
            RowCount = 6,
            BackColor = Color.Transparent,
            Margin = Padding.Empty
        };
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 91));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 36));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 52));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 52));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 92));

        var brand = new Panel { Dock = DockStyle.Fill, BackColor = Color.Transparent };
        var mark = new GlassSurface
        {
            Location = new Point(2, 12),
            Size = new Size(48, 48),
            CornerRadius = 16,
            TopColor = Color.FromArgb(255, 116, 105, 244),
            BottomColor = Color.FromArgb(255, 76, 93, 216),
            OutlineColor = Color.FromArgb(180, 255, 255, 255),
            Padding = Padding.Empty
        };
        mark.Controls.Add(new Label
        {
            Dock = DockStyle.Fill,
            Text = "W",
            TextAlign = ContentAlignment.MiddleCenter,
            ForeColor = Color.White,
            Font = new Font(SystemFonts.MessageBoxFont.FontFamily, 20F, FontStyle.Bold),
            BackColor = Color.Transparent
        });
        var brandTitle = new Label
        {
            Text = "WinCare",
            AutoSize = true,
            Location = new Point(60, 12),
            ForeColor = Ink,
            Font = new Font(SystemFonts.MessageBoxFont.FontFamily, 17F, FontStyle.Bold),
            BackColor = Color.Transparent
        };
        var brandCaption = new Label
        {
            Text = "Windows 系统管理",
            AutoSize = true,
            Location = new Point(61, 42),
            ForeColor = Muted,
            Font = new Font(SystemFonts.MessageBoxFont.FontFamily, 8.5F),
            BackColor = Color.Transparent
        };
        brand.Controls.Add(mark);
        brand.Controls.Add(brandTitle);
        brand.Controls.Add(brandCaption);

        var section = new Label
        {
            Text = "工具",
            Dock = DockStyle.Fill,
            TextAlign = ContentAlignment.BottomLeft,
            ForeColor = Muted,
            Font = new Font(SystemFonts.MessageBoxFont.FontFamily, 9F, FontStyle.Bold),
            Padding = new Padding(7, 0, 0, 7),
            BackColor = Color.Transparent
        };
        _startupNavigation.Text = "◉   启动项管理";
        _cleanupNavigation.Text = "◈   C 盘空间";
        StyleNavigationButton(_startupNavigation);
        StyleNavigationButton(_cleanupNavigation);
        _startupNavigation.Click += (_, _) => SelectPage(startup: true);
        _cleanupNavigation.Click += (_, _) => SelectPage(startup: false);

        var spacer = new Panel { Dock = DockStyle.Fill, BackColor = Color.Transparent };
        var note = new GlassSurface
        {
            Dock = DockStyle.Fill,
            CornerRadius = 20,
            Padding = new Padding(12, 10, 12, 8),
            TopColor = WinCareTheme.GlassTop,
            BottomColor = WinCareTheme.GlassBottom
        };
        note.Controls.Add(new Label
        {
            Dock = DockStyle.Fill,
            Text = "预览后再操作\n启动项逐项确认 · 清理范围固定",
            ForeColor = Muted,
            Font = SystemFonts.MessageBoxFont,
            TextAlign = ContentAlignment.MiddleLeft,
            BackColor = Color.Transparent
        });

        layout.Controls.Add(brand, 0, 0);
        layout.Controls.Add(section, 0, 1);
        layout.Controls.Add(_startupNavigation, 0, 2);
        layout.Controls.Add(_cleanupNavigation, 0, 3);
        layout.Controls.Add(spacer, 0, 4);
        layout.Controls.Add(note, 0, 5);
        sidebar.Controls.Add(layout);
        return sidebar;
    }

    private static void StyleNavigationButton(Button button)
    {
        button.Dock = DockStyle.Fill;
        button.TextAlign = ContentAlignment.MiddleLeft;
        button.Padding = new Padding(14, 0, 8, 0);
        button.Margin = new Padding(0, 3, 0, 3);
        WinCareTheme.StyleButton(button, filled: false);
    }

    private void SelectPage(bool startup)
    {
        _startupPage.Visible = startup;
        _cleanupPage.Visible = !startup;
        StyleNavigationState(_startupNavigation, startup);
        StyleNavigationState(_cleanupNavigation, !startup);
        _pageHost.AccessibleDescription = startup ? "启动项管理页面" : "C 盘清理和空间分析页面";
    }

    private static void StyleNavigationState(Button button, bool selected)
    {
        button.BackColor = selected ? WinCareTheme.NavSelected : WinCareTheme.NavSurface;
        button.ForeColor = selected ? WinCareTheme.Accent : WinCareTheme.Ink;
        button.FlatAppearance.BorderSize = selected ? 0 : 1;
        button.FlatAppearance.BorderColor = WinCareTheme.NavBorder;
        button.FlatAppearance.MouseOverBackColor = selected ? WinCareTheme.Selection : WinCareTheme.NavHover;
        button.AccessibleRole = AccessibleRole.PageTab;
        button.AccessibleDescription = selected ? "当前选中" : "切换页面";
    }

    private Panel BuildStartupPage()
    {
        var page = new Panel { BackColor = Color.Transparent, Padding = new Padding(2, 2, 2, 2) };
        var layout = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 4, BackColor = Color.Transparent };
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 78));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 60));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 48));

        var heading = new GlassSurface { Dock = DockStyle.Fill, Margin = new Padding(0, 0, 0, 7), Padding = new Padding(17, 11, 16, 10), CornerRadius = 22 };
        var headingTitle = new Label { Text = "启动项管理", Font = new Font(SystemFonts.MessageBoxFont.FontFamily, 17F, FontStyle.Bold), AutoSize = true, ForeColor = Ink, Location = new Point(17, 10), BackColor = Color.Transparent };
        var headingCaption = new Label { Text = "查看开机与登录入口；隐藏项默认显示，系统关键项保持只读。", Font = SystemFonts.MessageBoxFont, AutoSize = true, ForeColor = Muted, Location = new Point(18, 43), BackColor = Color.Transparent };
        _refreshStartup.Text = "重新扫描";
        StyleButton(_refreshStartup, filled: false);
        _refreshStartup.Size = new Size(116, 36);
        _refreshStartup.Anchor = AnchorStyles.Right | AnchorStyles.Top;
        _refreshStartup.Location = new Point(Width - 185, 12);
        _refreshStartup.Click += async (_, _) => await ReloadStartupAsync();
        heading.Resize += (_, _) => _refreshStartup.Location = new Point(heading.ClientSize.Width - _refreshStartup.Width - 14, 20);
        heading.Controls.Add(headingTitle);
        heading.Controls.Add(headingCaption);
        heading.Controls.Add(_refreshStartup);

        var toolbarSurface = new GlassSurface { Dock = DockStyle.Fill, Margin = new Padding(0, 0, 0, 7), Padding = new Padding(13, 7, 12, 5), CornerRadius = 18, TopColor = WinCareTheme.GlassTop, BottomColor = WinCareTheme.GlassBottom };
        var toolbar = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.LeftToRight, WrapContents = false, Padding = Padding.Empty, BackColor = Color.Transparent };
        _search.PlaceholderText = "搜索名称、路径或启动命令";
        _search.Width = 310;
        _search.Height = 36;
        _search.BorderStyle = BorderStyle.FixedSingle;
        _search.BackColor = WinCareTheme.Field;
        _search.ForeColor = Ink;
        _search.TextChanged += (_, _) =>
        {
            _searchDebounce.Stop();
            _searchDebounce.Start();
        };
        _category.DropDownStyle = ComboBoxStyle.DropDownList;
        _category.Width = 230;
        _category.Height = 36;
        _category.FlatStyle = FlatStyle.Flat;
        _category.BackColor = WinCareTheme.Field;
        _category.ForeColor = Ink;
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
        toolbarSurface.Controls.Add(toolbar);

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

        var gridSurface = new GlassSurface { Dock = DockStyle.Fill, Padding = new Padding(12), CornerRadius = 23, Margin = new Padding(0, 0, 0, 4) };
        gridSurface.Controls.Add(_startupGrid);

        layout.Controls.Add(heading, 0, 0);
        layout.Controls.Add(toolbarSurface, 0, 1);
        layout.Controls.Add(gridSurface, 0, 2);
        layout.Controls.Add(footer, 0, 3);
        page.Controls.Add(layout);
        return page;
    }

    private Panel BuildCleanupPage()
    {
        var page = new Panel { BackColor = Color.Transparent, Padding = new Padding(2, 2, 2, 2) };
        var layout = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 4, BackColor = Color.Transparent };
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 78));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 90));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 48));

        var heading = new GlassSurface { Dock = DockStyle.Fill, Margin = new Padding(0, 0, 0, 7), Padding = new Padding(17, 11, 16, 10), CornerRadius = 22 };
        var headingTitle = new Label { Text = "C 盘空间管理", Font = new Font(SystemFonts.MessageBoxFont.FontFamily, 17F, FontStyle.Bold), AutoSize = true, ForeColor = Ink, Location = new Point(17, 10), BackColor = Color.Transparent };
        var headingCaption = new Label { Text = "临时文件清理前预览确认；大文件分析保持只读。", Font = SystemFonts.MessageBoxFont, AutoSize = true, ForeColor = Muted, Location = new Point(18, 43), BackColor = Color.Transparent };
        _refreshCleanup.Text = "重新扫描";
        StyleButton(_refreshCleanup, filled: false);
        _refreshCleanup.Size = new Size(116, 36);
        _refreshCleanup.Click += async (_, _) => await ReloadCleanupAsync();
        var storageSettings = new Button { Text = "Windows 存储设置", Size = new Size(152, 36) };
        StyleButton(storageSettings, filled: false);
        storageSettings.Click += (_, _) =>
        {
            try { Process.Start(new ProcessStartInfo("ms-settings:storage") { UseShellExecute = true }); }
            catch (Exception ex) { MessageBox.Show(this, ex.Message, "无法打开 Windows 存储设置", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        };
        var largeFileSearch = new Button { Text = "查找大文件", Size = new Size(116, 36) };
        StyleButton(largeFileSearch, filled: false);
        largeFileSearch.Click += (_, _) =>
        {
            using var form = new LargeFileScanForm();
            form.ShowDialog(this);
        };
        heading.Resize += (_, _) =>
        {
            _refreshCleanup.Location = new Point(heading.ClientSize.Width - _refreshCleanup.Width - 14, 20);
            storageSettings.Location = new Point(_refreshCleanup.Left - storageSettings.Width - 10, 20);
            largeFileSearch.Location = new Point(storageSettings.Left - largeFileSearch.Width - 10, 20);
        };
        _refreshCleanup.Location = new Point(Width - _refreshCleanup.Width - 30, 20);
        storageSettings.Location = new Point(_refreshCleanup.Left - storageSettings.Width - 10, 20);
        largeFileSearch.Location = new Point(storageSettings.Left - largeFileSearch.Width - 10, 20);
        heading.Controls.Add(largeFileSearch);
        heading.Controls.Add(storageSettings);
        heading.Controls.Add(headingTitle);
        heading.Controls.Add(headingCaption);
        heading.Controls.Add(_refreshCleanup);

        var guidanceSurface = new GlassSurface
        {
            Dock = DockStyle.Fill,
            Margin = new Padding(0, 0, 0, 8),
            Padding = new Padding(14, 10, 14, 8),
            CornerRadius = 19,
            TopColor = WinCareTheme.GuideTop,
            BottomColor = WinCareTheme.GuideBottom
        };
        var guidance = new Label
        {
            Dock = DockStyle.Fill,
            AutoSize = false,
            Padding = new Padding(1, 1, 1, 1),
            BackColor = Color.Transparent,
            ForeColor = WinCareTheme.GuideText,
            Font = SystemFonts.MessageBoxFont,
            Text = "仅扫描 C 盘的当前用户 TEMP 与 Windows\\Temp，默认只清理修改时间超过 7 天的文件。清理会永久删除文件（不进入回收站），并跳过链接、正在使用或无权限访问的文件。不会触碰下载、文档、浏览器数据、回收站或 WinSxS。"
        };
        guidanceSurface.Controls.Add(guidance);

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
                e.CellStyle.BackColor = WinCareTheme.GridBackground;
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
        var footer = new Panel { Dock = DockStyle.Fill, Padding = new Padding(2, 11, 0, 0), BackColor = Color.Transparent };
        footer.Controls.Add(_cleanupSummary);
        var gridSurface = new GlassSurface { Dock = DockStyle.Fill, Padding = new Padding(12), CornerRadius = 23, Margin = new Padding(0, 0, 0, 4) };
        gridSurface.Controls.Add(_cleanupGrid);
        layout.Controls.Add(heading, 0, 0);
        layout.Controls.Add(guidanceSurface, 0, 1);
        layout.Controls.Add(gridSurface, 0, 2);
        layout.Controls.Add(footer, 0, 3);
        page.Controls.Add(layout);
        return page;
    }

    private static void ConfigureGrid(DataGridView grid)
    {
        WinCareTheme.StyleGrid(grid, rowHeight: 44);
    }

    private static DataGridViewTextBoxColumn TextColumn(string property, string heading, int width, bool fill = false) =>
        new() { Name = property, DataPropertyName = property, HeaderText = heading, Width = width, AutoSizeMode = fill ? DataGridViewAutoSizeColumnMode.Fill : DataGridViewAutoSizeColumnMode.None, SortMode = DataGridViewColumnSortMode.NotSortable };

    private static void StyleButton(Button button, bool filled)
    {
        WinCareTheme.StyleButton(button, filled);
    }

    private void StartupCellFormatting(object? sender, DataGridViewCellFormattingEventArgs e)
    {
        if (e.RowIndex < 0 || e.RowIndex >= _visibleEntries.Count || e.ColumnIndex < 0) return;
        var entry = _visibleEntries[e.RowIndex];
        if (_startupGrid.Columns[e.ColumnIndex].Name == "Action")
        {
            e.Value = entry.ActionText;
            e.CellStyle.ForeColor = entry.CanToggle ? Accent : Muted;
            e.CellStyle.BackColor = WinCareTheme.GridBackground;
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
