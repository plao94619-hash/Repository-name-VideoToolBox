using Microsoft.UI.Xaml;
using WinCare.Services;

namespace WinCare;

public partial class App : Application
{
    private Window? _window;

    public App()
    {
        UnhandledException += (_, e) => LogStartupFailure(e.Exception);
        try { InitializeComponent(); }
        catch (Exception ex) { LogStartupFailure(ex); throw; }
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        try
        {
            var commandLine = Environment.GetCommandLineArgs().Skip(1).ToArray();
            if (commandLine.Length == 1 && commandLine[0] == "--verify-startup")
            {
                _window = new MainWindow();
                Environment.Exit(0);
                return;
            }
            if (commandLine.Length == 2 && commandLine[0] is "--admin-action" or "--admin-cleanup")
            {
                Environment.Exit(AdminActionRunner.Run(commandLine[0], commandLine[1]));
                return;
            }

            _window = new MainWindow();
            _window.Activate();
        }
        catch (Exception ex) { LogStartupFailure(ex); throw; }
    }

    private static void LogStartupFailure(Exception ex)
    {
        try
        {
            var directory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "WinCare", "Logs");
            Directory.CreateDirectory(directory);
            File.AppendAllText(Path.Combine(directory, "startup.log"), $"{DateTimeOffset.Now:O}{Environment.NewLine}{ex}{Environment.NewLine}{Environment.NewLine}");
        }
        catch { /* A logging failure must not hide the original startup error. */ }
    }
}
