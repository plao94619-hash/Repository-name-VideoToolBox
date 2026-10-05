using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace WinCare.UI;

internal sealed class LiquidBackdropPanel : Panel
{
    public LiquidBackdropPanel()
    {
        SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw | ControlStyles.UserPaint, true);
        BackColor = WinCareTheme.Canvas;
    }

    protected override void OnPaintBackground(PaintEventArgs e)
    {
        if (ClientSize.Width <= 0 || ClientSize.Height <= 0) return;

        var bounds = ClientRectangle;
        using var wash = new LinearGradientBrush(
            bounds,
            WinCareTheme.IsDark ? Color.FromArgb(29, 31, 47) : Color.FromArgb(244, 248, 255),
            WinCareTheme.IsDark ? Color.FromArgb(23, 25, 38) : Color.FromArgb(235, 239, 251),
            36F);
        e.Graphics.FillRectangle(wash, bounds);

        DrawSoftGlow(e.Graphics, new RectangleF(-bounds.Width * 0.12F, -bounds.Height * 0.18F, bounds.Width * 0.8F, bounds.Height * 0.62F), WinCareTheme.IsDark ? Color.FromArgb(33, 108, 98, 205) : Color.FromArgb(33, 118, 139, 255));
        DrawSoftGlow(e.Graphics, new RectangleF(bounds.Width * 0.52F, bounds.Height * 0.54F, bounds.Width * 0.72F, bounds.Height * 0.7F), WinCareTheme.IsDark ? Color.FromArgb(24, 67, 145, 139) : Color.FromArgb(24, 101, 211, 202));
    }

    private static void DrawSoftGlow(Graphics graphics, RectangleF bounds, Color centerColor)
    {
        using var path = new GraphicsPath();
        path.AddEllipse(bounds);
        using var glow = new PathGradientBrush(path)
        {
            CenterColor = centerColor,
            SurroundColors = [Color.FromArgb(0, centerColor.R, centerColor.G, centerColor.B)]
        };
        graphics.FillEllipse(glow, bounds);
    }
}
