using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;
using WinCare.Services;

namespace WinCare;

public sealed class LargeFileScanForm : Form
{
    private sealed record SizeOption(string Name, long Bytes)
    {
        public override string ToString() => Name;
    }

    private static readonly Color Ink = Color.FromArgb(28, 35, 49);
    private static readonly Color Muted = Color.FromArgb(99, 109, 126);
    private static readonly Color Accent = Color.FromArgb(39, 103, 210);
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
        MinimumSize = new Size(900, 580);
        Size = new Size(1180, 760);
        BackColor = Color.FromArgb(245, 247, 250);
        ForeColor = Ink;
        Font = new Font("Segoe UI", 9.5F);
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
            RowCount = 4,
            Padding = new Padding(14),
            BackColor = BackColor
        };
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 48));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 64));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 48));

        var toolbar = new FlowLayoutPanel
        {
            Dock = DockStyle.Fill,
            FlowDirection = FlowDirection.LeftToRight,
            WrapContents = false,
            Padding = new Padding(0, 5, 0, 0)
        };
        toolbar.Controls.Add(new Label { Text = "最小文件大小", AutoSize = true, Margin = new Padding(0, 8, 6, 0), ForeColor = Ink });
        _minimumSize.DropDownStyle = ComboBoxStyle.DropDownList;
        _minimumSize.Width = 150;
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

        var guidance = new Label
        {
            Dock = DockStyle.Fill,
            AutoSize = false,
            Padding = new Padding(12, 8, 12, 6),
            BackColor = Color.FromArgb(235, 242, 252),
            ForeColor = Color.FromArgb(45, 67, 98),
            Text = "只读扫描 C 盘当前账户可访问的文件；跳过目录链接，不会删除文件。只保留最大的 2,000 项。显示逻辑文件大小，硬链接可能重复计数，数值不代表可释放空间。"
        };

        _grid.Dock = DockStyle.Fill;
        _grid.BackgroundColor = Color.White;
        _grid.BorderStyle = BorderStyle.None;
        _grid.EnableHeadersVisualStyles = false;
        _grid.ColumnHeadersDefaultCellStyle.BackColor = Color.FromArgb(239, 243, 249);
        _grid.ColumnHeadersDefaultCellStyle.ForeColor = Ink;
        _grid.ColumnHeadersDefaultCellStyle.Font = new Font("Segoe UI Semibold", 9.5F, FontStyle.Bold);
        _grid.ColumnHeadersHeight = 38;
        _grid.DefaultCellStyle.BackColor = Color.White;
        _grid.DefaultCellStyle.ForeColor = Ink;
        _grid.DefaultCellStyle.SelectionBackColor = Color.FromArgb(229, 239, 253);
        _grid.DefaultCellStyle.SelectionForeColor = Ink;
        _grid.DefaultCellStyle.Padding = new Padding(6, 2, 6, 2);
        _grid.RowTemplate.Height = 36;
        _grid.GridColor = Color.FromArgb(232, 236, 242);
        _grid.RowHeadersVisible = false;
        _grid.AllowUserToAddRows = false;
        _grid.AllowUserToDeleteRows = false;
        _grid.AllowUserToResizeRows = false;
        _grid.MultiSelect = false;
        _grid.ReadOnly = true;
        _grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
        _grid.AutoGenerateColumns = false;
        _grid.ShowCellToolTips = true;
        _grid.VirtualMode = true;
        _grid.Columns.Add(TextColumn("Name", "文件", 260));
        _grid.Columns.Add(TextColumn("Path", "完整路径", 570, fill: true));
        _grid.Columns.Add(TextColumn("Size", "逻辑大小", 125));
        _grid.Columns.Add(TextColumn("Modified", "修改时间", 165));
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

        _status.AutoSize = true;
        _status.ForeColor = Muted;
        _status.Text = "准备扫描；扫描过程可随时取消。";
        var footer = new Panel { Dock = DockStyle.Fill, Padding = new Padding(2, 10, 0, 0) };
        footer.Controls.Add(_status);

        layout.Controls.Add(toolbar, 0, 0);
        layout.Controls.Add(guidance, 0, 1);
        layout.Controls.Add(_grid, 0, 2);
        layout.Controls.Add(footer, 0, 3);
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
        _status.Text = $"正在只读扫描 C 盘，筛选 {option.Name} 及以上的文件…";

        var progress = new Progress<LargeFileScanProgress>(value =>
        {
            if (!IsDisposed && ReferenceEquals(_scanCancellation, cancellation))
                _status.Text = $"正在扫描：已检查 {value.ScannedFiles:N0} 个文件，匹配 {value.MatchingFiles:N0} 个，读取错误 {value.ReadErrors:N0} 次。";
        });

        try
        {
            var result = await Task.Run(
                () => DiskUsageService.ScanLargeFiles(option.Bytes, progress, cancellation.Token),
                cancellation.Token);
            _items.AddRange(result.LargestFiles);
            _grid.RowCount = _items.Count;
            _grid.Invalidate();
            var shown = result.ResultsTruncated ? $"；列表显示最大的 {_items.Count:N0} 项" : $"；列出 {_items.Count:N0} 项";
            _status.Text = $"完成：检查 {result.ScannedFiles:N0} 个文件，找到 {result.MatchingFiles:N0} 个 {option.Name} 及以上的文件，逻辑大小合计 {StartupScanner.FormatSize(result.MatchingBytes)}{shown}；读取错误 {result.ReadErrors:N0} 次。";
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
            "Size" => StartupScanner.FormatSize(item.Bytes),
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
        button.FlatStyle = FlatStyle.Flat;
        button.FlatAppearance.BorderSize = filled ? 0 : 1;
        button.FlatAppearance.BorderColor = Color.FromArgb(208, 216, 227);
        button.BackColor = filled ? Accent : Color.White;
        button.ForeColor = filled ? Color.White : Ink;
        button.Cursor = Cursors.Hand;
        button.Margin = new Padding(8, 0, 0, 0);
    }
}
