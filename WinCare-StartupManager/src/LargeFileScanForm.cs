using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;
using WinCare.Services;
using WinCare.UI;

namespace WinCare;

public sealed class LargeFileScanForm : GlassForm
{
    private sealed record SizeOption(string Name, long MinimumAllocatedBytes)
    {
        public override string ToString() => Name;
    }

    private static readonly Color Ink = WinCareTheme.Ink;
    private static readonly Color Muted = WinCareTheme.Muted;
    private static readonly Color Accent = WinCareTheme.Accent;
    private readonly ComboBox _minimumSize = new();
    private readonly Button _scan = new();
    private readonly Button _cancel = new();
    private readonly Button _openLocation = new();
    private readonly Label _status = new();
    private readonly DataGridView _grid = new();
    private readonly List<LargeFileItem> _items = [];
    private CancellationTokenSource? _scanCancellation;

    public LargeFileScanForm()
    {
        Text = "C 盘大文件分析 · WinCare";
        StartPosition = FormStartPosition.CenterParent;
        MinimumSize = new Size(1000, 640);
        Size = new Size(1240, 800);
        BackColor = WinCareTheme.Canvas;
        ForeColor = Ink;
        Font = SystemFonts.MessageBoxFont;
        AutoScaleMode = AutoScaleMode.Dpi;

        BuildUi();
        Shown += async (_, _) => await StartScanAsync();
        FormClosing += (_, _) => _scanCancellation?.Cancel();
    }

    private void BuildUi()
    {
        var layout = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 1,
            RowCount = 5,
            Padding = new Padding(18),
            BackColor = Color.Transparent
        };
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 72));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 58));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 64));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));

        var heading = new GlassSurface { Dock = DockStyle.Fill, Margin = new Padding(0, 0, 0, 7), Padding = new Padding(16, 10, 14, 8), CornerRadius = 22 };
        heading.Controls.Add(new Label
        {
            Text = "大文件分析",
            AutoSize = true,
            Location = new Point(16, 8),
            ForeColor = Ink,
            Font = new Font(SystemFonts.MessageBoxFont.FontFamily, 17F, FontStyle.Bold),
            BackColor = Color.Transparent
        });
        heading.Controls.Add(new Label
        {
            Text = "只读查询文件系统元数据，不打开内容、不执行删除。",
            AutoSize = true,
            Location = new Point(17, 40),
            ForeColor = Muted,
            Font = SystemFonts.MessageBoxFont,
            BackColor = Color.Transparent
        });

        var toolbarSurface = new GlassSurface
        {
            Dock = DockStyle.Fill,
            Margin = new Padding(0, 0, 0, 7),
            Padding = new Padding(12, 6, 12, 4),
            CornerRadius = 18,
            TopColor = WinCareTheme.GlassTop,
            BottomColor = WinCareTheme.GlassBottom
        };
        var toolbar = new FlowLayoutPanel
        {
            Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = false,
            Padding = Padding.Empty,
            BackColor = Color.Transparent
        };
        toolbar.Controls.Add(new Label { Text = "最小磁盘占用", AutoSize = true, Margin = new Padding(0, 9, 8, 0), ForeColor = Ink });
        _minimumSize.DropDownStyle = ComboBoxStyle.DropDownList;
        _minimumSize.Width = 156;
        _minimumSize.FlatStyle = FlatStyle.Flat;
        _minimumSize.BackColor = WinCareTheme.Field;
        _minimumSize.ForeColor = Ink;
        _minimumSize.Items.AddRange(
        [
            new SizeOption("100 MiB", 100L * 1024 * 1024),
            new SizeOption("250 MiB", 250L * 1024 * 1024),
            new SizeOption("500 MiB", 500L * 1024 * 1024),
            new SizeOption("1 GiB", 1024L * 1024 * 1024),
            new SizeOption("2 GiB", 2L * 1024 * 1024 * 1024)
        ]);
        _minimumSize.SelectedIndex = 0;
        toolbar.Controls.Add(_minimumSize);

        _scan.Text = "重新扫描 C 盘";
        _scan.Size = new Size(126, 34);
        StyleButton(_scan, filled: true);
        _scan.Click += async (_, _) => await StartScanAsync();
        toolbar.Controls.Add(_scan);

        _cancel.Text = "取消扫描";
        _cancel.Size = new Size(96, 34);
        _cancel.Enabled = false;
        StyleButton(_cancel, filled: false);
        _cancel.Click += (_, _) => _scanCancellation?.Cancel();
        toolbar.Controls.Add(_cancel);

        _openLocation.Text = "在资源管理器中定位";
        _openLocation.Size = new Size(160, 34);
        _openLocation.Enabled = false;
        StyleButton(_openLocation, filled: false);
        _openLocation.Click += (_, _) => OpenSelectedLocation();
        toolbar.Controls.Add(_openLocation);
        toolbarSurface.Controls.Add(toolbar);

        var guidanceSurface = new GlassSurface
        {
            Dock = DockStyle.Fill,
            Margin = new Padding(0, 0, 0, 7),
            Padding = new Padding(13, 8, 13, 7),
            CornerRadius = 19,
            TopColor = WinCareTheme.GuideTop,
            BottomColor = WinCareTheme.GuideBottom
        };
        guidanceSurface.Controls.Add(new Label
        {
            Dock = DockStyle.Fill,
            AutoSize = false,
            Padding = Padding.Empty,
            BackColor = Color.Transparent,
            ForeColor = WinCareTheme.GuideText,
            Font = SystemFonts.MessageBoxFont,
            Text = "包含隐藏和系统项，按 Windows 报告的分配空间筛选；用卷序列号和文件 ID 合并可识别的硬链接。跳过链接，不读取内容、不删除文件。分配空间不等于删除某个路径后一定能释放的空间。"
        });

        WinCareTheme.StyleGrid(_grid, rowHeight: 40);
        _grid.VirtualMode = true;
        _grid.Columns.Add(TextColumn("Name", "文件", 230));
        _grid.Columns.Add(TextColumn("Path", "完整路径", 480, fill: true));
        _grid.Columns.Add(TextColumn("Allocated", "磁盘占用", 135));
        _grid.Columns.Add(TextColumn("Logical", "逻辑大小", 135));
        _grid.Columns.Add(TextColumn("Modified", "修改时间", 150));
        _grid.CellValueNeeded += GridCellValueNeeded;
        _grid.CellToolTipTextNeeded += (_, e) =>
        {
            if (e.RowIndex >= 0 && e.RowIndex < _items.Count) e.ToolTipText = _items[e.RowIndex].Path;
        };
        _grid.CellDoubleClick += (_, e) =>
        {
            if (e.RowIndex >= 0) OpenSelectedLocation(e.RowIndex);
        };
        _grid.SelectionChanged += (_, _) => _openLocation.Enabled = _scanCancellation is null && _grid.CurrentCell is not null;

        _status.AutoSize = false;
        _status.Dock = DockStyle.Fill;
        _status.AutoEllipsis = true;
        _status.ForeColor = Muted;
        _status.Text = "准备扫描；扫描过程可随时取消。";
        var footer = new GlassSurface { Dock = DockStyle.Fill, Padding = new Padding(12, 7, 12, 6), CornerRadius = 18, Margin = new Padding(0, 6, 0, 0) };
        footer.Controls.Add(_status);
        var gridSurface = new GlassSurface { Dock = DockStyle.Fill, Padding = new Padding(12), CornerRadius = 23, Margin = new Padding(0, 0, 0, 4) };
        gridSurface.Controls.Add(_grid);

        layout.Controls.Add(heading, 0, 0);
        layout.Controls.Add(toolbarSurface, 0, 1);
        layout.Controls.Add(guidanceSurface, 0, 2);
        layout.Controls.Add(gridSurface, 0, 3);
        layout.Controls.Add(footer, 0, 4);
        Controls.Add(layout);
    }

    private async Task StartScanAsync()
    {
        if (_scanCancellation is not null) return;
        var option = _minimumSize.SelectedItem as SizeOption ?? new SizeOption("100 MiB", 100L * 1024 * 1024);
        var cancellation = new CancellationTokenSource();
        _scanCancellation = cancellation;
        _scan.Enabled = false;
        _minimumSize.Enabled = false;
        _cancel.Enabled = true;
        _openLocation.Enabled = false;
        _items.Clear();
        _grid.RowCount = 0;
        _status.Text = $"正在只读扫描 C 盘，筛选分配空间 {option.Name} 及以上的文件…";

        var progress = new Progress<LargeFileScanProgress>(value =>
        {
            if (!IsDisposed && ReferenceEquals(_scanCancellation, cancellation))
                _status.Text = $"正在扫描：已检查 {value.ScannedPaths:N0} 个路径，匹配 {value.MatchingFiles:N0} 个文件，合并硬链接路径 {value.DuplicateHardLinkPaths:N0} 个，读取错误 {value.ReadErrors:N0} 次。";
        });

        try
        {
            var result = await Task.Run(
                () => DiskUsageService.ScanLargeFiles(option.MinimumAllocatedBytes, progress, cancellation.Token),
                cancellation.Token);
            _items.AddRange(result.LargestFiles);
            _grid.RowCount = _items.Count;
            _grid.Invalidate();
            var shown = result.ResultsTruncated ? $"；列表显示磁盘占用最大的 {_items.Count:N0} 项" : $"；列出 {_items.Count:N0} 项";
            _status.Text = $"完成：检查 {result.ScannedPaths:N0} 个路径，找到 {result.MatchingFiles:N0} 个文件；磁盘占用 {StartupScanner.FormatSize(result.MatchingAllocatedBytes)}，逻辑大小 {StartupScanner.FormatSize(result.MatchingLogicalBytes)}；合并硬链接路径 {result.DuplicateHardLinkPaths:N0} 个{shown}；读取错误 {result.ReadErrors:N0} 次。";
        }
        catch (OperationCanceledException)
        {
            if (!IsDisposed) _status.Text = "扫描已取消，未生成完整结果；可以调整大小门槛后重新扫描。";
        }
        catch (Exception ex)
        {
            if (!IsDisposed) MessageBox.Show(this, ex.Message, "C 盘扫描失败", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
        finally
        {
            cancellation.Dispose();
            _scanCancellation = null;
            if (!IsDisposed)
            {
                _scan.Enabled = true;
                _minimumSize.Enabled = true;
                _cancel.Enabled = false;
                _openLocation.Enabled = _grid.CurrentCell is not null;
            }
        }
    }

    private void GridCellValueNeeded(object? sender, DataGridViewCellValueEventArgs e)
    {
        if (e.RowIndex < 0 || e.RowIndex >= _items.Count || e.ColumnIndex < 0) return;
        var item = _items[e.RowIndex];
        e.Value = _grid.Columns[e.ColumnIndex].Name switch
        {
            "Name" => item.Name,
            "Path" => item.Path,
            "Allocated" => StartupScanner.FormatSize(item.AllocatedBytes),
            "Logical" => StartupScanner.FormatSize(item.LogicalBytes),
            "Modified" => item.ModifiedUtc.ToLocalTime().ToString("g"),
            _ => null
        };
    }

    private void OpenSelectedLocation(int? rowIndex = null)
    {
        var index = rowIndex ?? _grid.CurrentCell?.RowIndex ?? -1;
        if (index < 0 || index >= _items.Count) return;
        var path = _items[index].Path;
        if (!File.Exists(path))
        {
            MessageBox.Show(this, "该文件已不存在，请重新扫描。", "文件不可用", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        try
        {
            Process.Start(new ProcessStartInfo("explorer.exe", $"/select,\"{path}\"") { UseShellExecute = true });
        }
        catch (Exception ex)
        {
            MessageBox.Show(this, ex.Message, "无法打开文件位置", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private static DataGridViewTextBoxColumn TextColumn(string name, string heading, int width, bool fill = false) =>
        new()
        {
            Name = name,
            HeaderText = heading,
            Width = width,
            AutoSizeMode = fill ? DataGridViewAutoSizeColumnMode.Fill : DataGridViewAutoSizeColumnMode.None,
            SortMode = DataGridViewColumnSortMode.NotSortable
        };

    private static void StyleButton(Button button, bool filled)
    {
        WinCareTheme.StyleButton(button, filled);
        button.Margin = new Padding(8, 0, 0, 0);
    }
}
