using System.Windows.Forms;

namespace WinCare.UI;

public class GlassForm : Form
{
    protected override void OnHandleCreated(EventArgs e)
    {
        base.OnHandleCreated(e);
        NativeWindowChrome.Apply(this);
    }
}
