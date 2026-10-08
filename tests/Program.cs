using WinCare.Services;

using var canceledStartupScan = new CancellationTokenSource();
canceledStartupScan.Cancel();
try
{
    StartupScanner.Scan(canceledStartupScan.Token);
    throw new Exception("已取消的启动项扫描仍继续执行。");
}
catch (OperationCanceledException)
{
    Console.WriteLine("Startup scan cancellation verified.");
}

var fixture = Path.Combine(Path.GetTempPath(), "WinCare-archive-check-" + Guid.NewGuid().ToString("N"));
var root = Path.Combine(fixture, "WeChat Files");
var archive = Path.Combine(fixture, "Archive");
var image = Path.Combine(root, "account", "FileStorage", "MsgAttach", "message", "Image", "sample.dat");

try
{
    Directory.CreateDirectory(Path.GetDirectoryName(image)!);
    File.WriteAllBytes(image, [1, 2, 3, 4, 5]);
    File.SetCreationTimeUtc(image, DateTime.UtcNow.AddDays(-300));

    var scan = WechatCleanupService.Scan(root, 180, includeImages: true, includeVideos: false);
    Require(scan.Files.Count == 1 && scan.Files[0].Bytes == 5, "微信文件扫描应定位到测试原图。");

    try
    {
        WechatCleanupService.Archive(root, scan.Files, Path.Combine(root, "Archive"));
        throw new Exception("嵌套在微信目录中的归档位置未被拒绝。");
    }
    catch (InvalidOperationException) { }
    Require(File.Exists(image), "无效目标不得移动原文件。");

    var moved = WechatCleanupService.Archive(root, scan.Files, archive);
    Require(moved.Completed == 1 && moved.Bytes == 5 && !File.Exists(image), "归档必须保留可还原副本并移出原文件。");

    File.WriteAllBytes(image, [9, 9]);
    var conflicted = WechatCleanupService.RestoreFromLocations([archive]);
    Require(conflicted.Completed == 0 && conflicted.Skipped == 1 && File.ReadAllBytes(image).SequenceEqual(new byte[] { 9, 9 }), "同名文件冲突时不能覆盖数据。");

    File.Delete(image);
    var restored = WechatCleanupService.RestoreFromLocations([archive]);
    Require(restored.Completed == 1 && File.ReadAllBytes(image).SequenceEqual(new byte[] { 1, 2, 3, 4, 5 }), "归档还原必须保留原文件内容。");
    Console.WriteLine("WeChat archive, collision protection and restore verified.");
}
finally
{
    if (Directory.Exists(fixture)) Directory.Delete(fixture, recursive: true);
}

static void Require(bool condition, string message)
{
    if (!condition) throw new Exception(message);
}
