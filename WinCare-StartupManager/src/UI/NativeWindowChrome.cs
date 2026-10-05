using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace WinCare.UI;

/// <summary>
/// Uses documented Desktop Window Manager attributes while preserving the
/// standard Windows title bar, system menu, resize frame, and caption buttons.
/// Unsupported attributes are deliberately ignored for older Windows builds.
/// </summary>
internal static class NativeWindowChrome
{
    private const int DwmwaUseImmersiveDarkMode = 20;
    private const int DwmwaWindowCornerPreference = 33;
    private const int DwmwaSystemBackdropType = 38;
    private const int DwmWindowCornerRound = 2;
    private const int DwmSystemBackdropMainWindow = 2;

    [DllImport("dwmapi.dll", ExactSpelling = true)]
    private static extern int DwmSetWindowAttribute(
        IntPtr windowHandle,
        int attribute,
        ref int attributeValue,
        int attributeSize);

    public static void Apply(Form form)
    {
        if (!OperatingSystem.IsWindowsVersionAtLeast(10, 0, 22000)) return;
        // Leave accessibility colors and framing entirely under Windows control.
        if (WinCareTheme.HighContrast) return;

        try
        {
            var darkMode = WinCareTheme.IsDark ? 1 : 0;
            SetAttribute(form.Handle, DwmwaUseImmersiveDarkMode, ref darkMode);

            var corners = DwmWindowCornerRound;
            SetAttribute(form.Handle, DwmwaWindowCornerPreference, ref corners);

            if (OperatingSystem.IsWindowsVersionAtLeast(10, 0, 22621))
            {
                var backdrop = DwmSystemBackdropMainWindow;
                SetAttribute(form.Handle, DwmwaSystemBackdropType, ref backdrop);
            }
        }
        catch (DllNotFoundException)
        {
            // Keep the regular WinForms appearance if DWM is unavailable.
        }
        catch (EntryPointNotFoundException)
        {
            // Some older Windows builds do not expose every DWM attribute.
        }
    }

    private static void SetAttribute(IntPtr windowHandle, int attribute, ref int value) =>
        _ = DwmSetWindowAttribute(windowHandle, attribute, ref value, sizeof(int));
}
