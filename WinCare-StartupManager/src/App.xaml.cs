using Microsoft.UI.Xaml;
using WinCare.Services;

namespace WinCare;

public partial class App : Application
{
    private Window? _window;

    public App() => InitializeComponent();

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        var commandLine = Environment.GetCommandLineArgs().Skip(1).ToArray();
        if (commandLine.Length == 2 && commandLine[0] is "--admin-action" or "--admin-cleanup")
        {
            Environment.Exit(AdminActionRunner.Run(commandLine[0], commandLine[1]));
            return;
        }

        _window = new MainWindow();
        _window.Activate();
    }
}
