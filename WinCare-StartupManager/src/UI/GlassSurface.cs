using System.ComponentModel;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace WinCare.UI;

internal sealed class GlassSurface : Panel
{
    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    public int CornerRadius { get; set; } = 22;

    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    public Color TopColor { get; set; } = WinCareTheme.GlassTop;

    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    public Color BottomColor { get; set; } = WinCareTheme.GlassBottom;

    [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
    public Color OutlineColor { get; set; } = WinCareTheme.GlassOutline;

    public GlassSurface()
    {
        SetStyle(
            ControlStyles.AllPaintingInWmPaint |
            ControlStyles.OptimizedDoubleBuffer |
            ControlStyles.ResizeRedraw |
            ControlStyles.SupportsTransparentBackColor |
            ControlStyles.UserPaint,
            true);
        BackColor = Color.Transparent;
        Padding = new Padding(14);
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        if (ClientSize.Width < 3 || ClientSize.Height < 3) return;

        e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
        e.Graphics.PixelOffsetMode = PixelOffsetMode.HighQuality;
        var bounds = new Rectangle(1, 1, ClientSize.Width - 3, ClientSize.Height - 3);
        using var outline = CreateRoundedPath(bounds, CornerRadius);
        using var fill = new LinearGradientBrush(bounds, TopColor, BottomColor, 90F);
        e.Graphics.FillPath(fill, outline);

        using var border = new Pen(OutlineColor, 1F);
        e.Graphics.DrawPath(border, outline);

        var highlightLeft = bounds.Left + CornerRadius;
        var highlightRight = bounds.Right - CornerRadius;
        if (highlightRight > highlightLeft)
        {
            using var highlight = new Pen(Color.FromArgb(125, Color.White), 1F);
            e.Graphics.DrawLine(highlight, highlightLeft, bounds.Top + 1, highlightRight, bounds.Top + 1);
        }
    }

    private static GraphicsPath CreateRoundedPath(Rectangle bounds, int radius)
    {
        var diameter = Math.Max(2, Math.Min(radius * 2, Math.Min(bounds.Width, bounds.Height)));
        var path = new GraphicsPath();
        path.AddArc(bounds.Left, bounds.Top, diameter, diameter, 180F, 90F);
        path.AddArc(bounds.Right - diameter, bounds.Top, diameter, diameter, 270F, 90F);
        path.AddArc(bounds.Right - diameter, bounds.Bottom - diameter, diameter, diameter, 0F, 90F);
        path.AddArc(bounds.Left, bounds.Bottom - diameter, diameter, diameter, 90F, 90F);
        path.CloseFigure();
        return path;
    }
}
