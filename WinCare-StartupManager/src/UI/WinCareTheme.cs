using System.Drawing.Drawing2D;
using Microsoft.Win32;
using System.Windows.Forms;

namespace WinCare.UI;

internal static class WinCareTheme
{
    public static readonly bool HighContrast = SystemInformation.HighContrast;
    public static readonly bool IsDark = !HighContrast && ReadDarkAppearance();
    public static readonly Color Ink = HighContrast ? SystemColors.WindowText : IsDark ? Color.FromArgb(239, 240, 250) : Color.FromArgb(29, 35, 58);
    public static readonly Color Muted = HighContrast ? SystemColors.GrayText : IsDark ? Color.FromArgb(166, 171, 193) : Color.FromArgb(101, 111, 137);
    public static readonly Color Accent = HighContrast ? SystemColors.Highlight : IsDark ? Color.FromArgb(169, 157, 255) : Color.FromArgb(105, 91, 232);
    public static readonly Color AccentHover = HighContrast ? SystemColors.Highlight : IsDark ? Color.FromArgb(143, 130, 250) : Color.FromArgb(88, 76, 215);
    public static readonly Color Canvas = HighContrast ? SystemColors.Window : IsDark ? Color.FromArgb(23, 25, 38) : Color.FromArgb(239, 243, 253);
    public static readonly Color GridLine = HighContrast ? SystemColors.WindowText : IsDark ? Color.FromArgb(62, 65, 87) : Color.FromArgb(228, 231, 243);
    public static readonly Color GridHeader = HighContrast ? SystemColors.Window : IsDark ? Color.FromArgb(40, 42, 61) : Color.FromArgb(239, 241, 251);
    public static readonly Color GridBackground = HighContrast ? SystemColors.Window : IsDark ? Color.FromArgb(31, 33, 49) : Color.FromArgb(250, 250, 255);
    public static readonly Color AlternatingRow = HighContrast ? SystemColors.Window : IsDark ? Color.FromArgb(35, 37, 55) : Color.FromArgb(246, 247, 253);
    public static readonly Color Selection = HighContrast ? SystemColors.Highlight : IsDark ? Color.FromArgb(69, 62, 106) : Color.FromArgb(232, 230, 255);
    public static readonly Color Field = HighContrast ? SystemColors.Window : IsDark ? Color.FromArgb(39, 41, 60) : Color.FromArgb(249, 250, 255);
    public static readonly Color GlassTop = HighContrast ? SystemColors.Window : IsDark ? Color.FromArgb(194, 57, 60, 83) : Color.FromArgb(230, 255, 255, 255);
    public static readonly Color GlassBottom = HighContrast ? SystemColors.Window : IsDark ? Color.FromArgb(169, 38, 41, 60) : Color.FromArgb(207, 244, 248, 255);
    public static readonly Color GlassOutline = HighContrast ? SystemColors.WindowText : IsDark ? Color.FromArgb(135, 210, 215, 240) : Color.FromArgb(174, 255, 255, 255);
    public static readonly Color GuideTop = HighContrast ? SystemColors.Window : IsDark ? Color.FromArgb(210, 49, 48, 77) : Color.FromArgb(209, 246, 246, 255);
    public static readonly Color GuideBottom = HighContrast ? SystemColors.Window : IsDark ? Color.FromArgb(184, 37, 43, 69) : Color.FromArgb(185, 233, 237, 254);
    public static readonly Color GuideText = HighContrast ? SystemColors.WindowText : IsDark ? Color.FromArgb(221, 221, 239) : Color.FromArgb(62, 68, 108);
    public static readonly Color NavSelected = HighContrast ? SystemColors.Highlight : IsDark ? Color.FromArgb(63, 57, 101) : Color.FromArgb(230, 228, 255);
    public static readonly Color NavSurface = HighContrast ? SystemColors.Window : IsDark ? Color.FromArgb(39, 41, 60) : Color.FromArgb(248, 249, 255);
    public static readonly Color NavBorder = HighContrast ? SystemColors.WindowText : IsDark ? Color.FromArgb(73, 76, 101) : Color.FromArgb(219, 220, 236);
    public static readonly Color NavHover = HighContrast ? SystemColors.Highlight : IsDark ? Color.FromArgb(55, 57, 82) : Color.FromArgb(240, 241, 250);

    public static void StyleButton(Button button, bool filled)
    {
        button.FlatStyle = FlatStyle.Flat;
        button.UseVisualStyleBackColor = false;
        button.FlatAppearance.BorderSize = filled ? 0 : 1;
        button.FlatAppearance.BorderColor = NavBorder;
        button.FlatAppearance.MouseOverBackColor = filled ? AccentHover : NavHover;
        button.FlatAppearance.MouseDownBackColor = filled ? Color.FromArgb(72, 61, 197) : Selection;
        button.BackColor = filled ? Accent : NavSurface;
        button.ForeColor = filled ? (HighContrast ? SystemColors.HighlightText : Color.White) : Ink;
        button.Cursor = Cursors.Hand;
        button.Font = SystemFonts.MessageBoxFont;
        button.Region = CreateButtonRegion(button);
        button.Resize += (_, _) =>
        {
            if (button.IsDisposed) return;
            var previous = button.Region;
            button.Region = CreateButtonRegion(button);
            previous?.Dispose();
        };
    }

    public static void StyleGrid(DataGridView grid, int rowHeight)
    {
        grid.Dock = DockStyle.Fill;
        grid.BackgroundColor = GridBackground;
        grid.BorderStyle = BorderStyle.None;
        grid.EnableHeadersVisualStyles = false;
        grid.ColumnHeadersDefaultCellStyle.BackColor = GridHeader;
        grid.ColumnHeadersDefaultCellStyle.ForeColor = Ink;
        grid.ColumnHeadersDefaultCellStyle.Font = new Font(SystemFonts.MessageBoxFont.FontFamily, 9.5F, FontStyle.Bold);
        grid.ColumnHeadersDefaultCellStyle.SelectionBackColor = GridHeader;
        grid.ColumnHeadersDefaultCellStyle.SelectionForeColor = Ink;
        grid.ColumnHeadersHeight = 42;
        grid.DefaultCellStyle.BackColor = GridBackground;
        grid.DefaultCellStyle.ForeColor = Ink;
        grid.DefaultCellStyle.SelectionBackColor = Selection;
        grid.DefaultCellStyle.SelectionForeColor = Ink;
        grid.DefaultCellStyle.Padding = new Padding(8, 3, 8, 3);
        grid.AlternatingRowsDefaultCellStyle.BackColor = AlternatingRow;
        grid.AlternatingRowsDefaultCellStyle.SelectionBackColor = Selection;
        grid.RowTemplate.Height = rowHeight;
        grid.GridColor = GridLine;
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

    private static Region CreateButtonRegion(Control control)
    {
        var rect = control.ClientRectangle;
        if (rect.Width < 2 || rect.Height < 2) return new Region(rect);
        rect.Width--;
        rect.Height--;
        var diameter = Math.Min(22, Math.Min(rect.Width, rect.Height));
        var path = new GraphicsPath();
        path.AddArc(rect.Left, rect.Top, diameter, diameter, 180F, 90F);
        path.AddArc(rect.Right - diameter, rect.Top, diameter, diameter, 270F, 90F);
        path.AddArc(rect.Right - diameter, rect.Bottom - diameter, diameter, diameter, 0F, 90F);
        path.AddArc(rect.Left, rect.Bottom - diameter, diameter, diameter, 90F, 90F);
        path.CloseFigure();
        var region = new Region(path);
        path.Dispose();
        return region;
    }

    private static bool ReadDarkAppearance()
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize");
            return Convert.ToInt32(key?.GetValue("AppsUseLightTheme", 1)) == 0;
        }
        catch (Exception ex) when (ex is UnauthorizedAccessException or System.Security.SecurityException or IOException)
        {
            return false;
        }
    }
}
