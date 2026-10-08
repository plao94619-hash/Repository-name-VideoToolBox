# WinCare · Windows 启动项与 C 盘空间管理

[下载 WinCare 1.12.0](https://github.com/plao94619-hash/Repository-name-VideoToolBox/releases/tag/wincare-v1.12.0) · [Windows 构建状态](https://github.com/plao94619-hash/Repository-name-VideoToolBox/actions/workflows/build.yml)

此仓库的主线专用于 WinCare。原“万能音视频工具箱”源码及说明保留在 [`legacy/videotoolbox`](https://github.com/plao94619-hash/Repository-name-VideoToolBox/tree/legacy/videotoolbox) 分支；旧版本 Release 保留。

一个面向 Windows 10 / 11 x64 的轻量桌面工具。它扫描常见的登录和开机启动入口，可逐项关闭并恢复；C 盘清理页只处理安全范围内的临时文件。

自 1.8.0 起，界面迁移到 WinUI 3 与 Windows App SDK，并继续使用 Windows 原生窗口和 XAML 控件。Windows 11 上主窗口使用系统 Mica backdrop；导航与信息卡片使用 AcrylicBrush 在应用窗口内呈现真实的背景模糊和着色。系统浅色、深色主题会切换材质色调；高对比度资源和不支持背景模糊的环境回退为纯色，保留文字对比度和控件可读性。设计参考 iOS 26/27 Liquid Glass 的层次、留白和材质，但采用 Windows Fluent 控件和 Windows 原生材质，不仿制 Apple 系统控件。

## 功能

- **启动项扫描**：当前用户与所有用户的 Run / RunOnce / RunServices / 策略 Run 注册表项，32 位和 64 位注册表视图，以及当前加载的其他用户配置单元。
- **文件夹和计划任务**：当前用户与所有用户的启动文件夹；递归查看任务计划程序中的隐藏任务，并显示登录、开机、注册、事件和会话触发项。
- **服务与系统项**：列出自动启动服务、Boot / System 启动服务和驱动，以及 Windows 的 Winlogon / Load / Run 关键值。Boot / System 驱动和关键注册表值只读。
- **隐藏项标记**：标记计划任务中的隐藏任务、启动文件夹中的隐藏文件、无显示名称的服务，以及 Windows 关键启动位置。列表默认包含这些项目。
- **逐项关闭与恢复**：注册表值会移至同一位置下的 `WinCareDisabled` 子项；启动文件会移至用户配置目录的恢复区；新版本的计划任务和服务恢复标记存放在管理员保护的注册表位置。管理员操作会在 UAC 后再次显示对象名称、位置和动作供确认。WinCare 不会替用户重新启用由 Windows 或其他工具禁用的项目。
- **安全清理**：扫描 C 盘的当前用户临时目录和 `Windows\\Temp`，预览超过 7 天未修改的文件和预计空间。链接、被占用和无权访问的文件会跳过。也可打开 Windows 存储设置。
- **大文件查找**：按 100 MiB、250 MiB、500 MiB、1 GiB 或 2 GiB 磁盘分配空间门槛只读扫描 C 盘文件，包含隐藏和系统项；分别显示 Windows 报告的分配空间和逻辑大小，并合并扫描范围内可识别的硬链接。仅保留最大的 2,000 项，支持取消和资源管理器定位，不提供从结果列表直接删除。
- **微信专项清理**：扫描用户选择的微信文件目录，按账号、文件系统创建日期和媒体类型筛选 FileStorage\Video 视频及 FileStorage\MsgAttach\…\Image 下的 .dat 原图。先显示文件清单和空间，再将勾选项移动到指定归档目录；可一键尝试还原，不覆盖同名原文件。不会读取聊天数据库、解密图片、删除聊天记录或自动后台清理。

## 微信专项清理

微信页默认使用 Windows“文档”目录下的 WeChat Files。若微信数据放在其他位置，可在路径框粘贴实际根目录。此版本只识别账号文件夹下的 FileStorage\Video 与 FileStorage\MsgAttach\…\Image\*.dat 结构；微信版本或自定义目录结构可能不同，扫描结果为空时请先核对根目录。

按 30、90、180、365 或 730 天筛选时，日期以文件系统创建时间为准，不等同于聊天发送时间。微信图片 .dat 文件保持原样移动，不尝试解密。归档会让对应图片或视频暂时无法从聊天记录打开；“还原全部归档”把文件移回原路径。若原位置已存在同名文件，WinCare 会跳过并保留归档副本。请先退出微信再归档。默认归档目录为 `%LOCALAPPDATA%\WinCare\WeChatArchive`。如微信文件和归档都在 C 盘，归档**不会释放 C 盘空间**；要腾出 C 盘空间，请在界面中把归档保存目录设为其他磁盘的专用文件夹，例如 `D:\WinCare-WeChatArchive`，并确保该磁盘有足够空间。WinCare 记录归档位置，还原时检查所有已记录且可访问的目录；外接磁盘离线时请重新连接。手动删除归档文件会永久丢失尚未还原的数据。

此功能参考 [StevenQi7/wechatClean](https://github.com/StevenQi7/wechatClean) 的按时间筛选、移动媒体文件和还原工作流；WinCare 独立实现文件扫描、校验和归档，不包含该项目的 .dat 解密功能。

## 覆盖范围说明

Windows 程序可以通过许多机制自动运行，因此任何独立清理工具都不应声称能枚举每一种启动方式。WinCare 覆盖上面列出的常见注册表、启动文件夹、计划任务和服务入口；它**不枚举** WMI 永久事件消费者、组策略启动/登录脚本、每个应用的专有启动机制、所有 Store/UWP `StartupTask` 或驱动程序内部配置。配置单元未加载、权限不足或 Task Scheduler 无法访问的项目也可能无法读取。若扫描发生读取错误，页面会显示“扫描提示”。

启动项“隐藏”表示该项目在其来源中带有隐藏/系统标记，或位于关键系统启动位置；不是对所有软件厂商私有机制的完整判定。

## C 盘清理边界

清理动作仅处理修改时间超过 7 天的白名单临时文件；不会删除下载、文档、浏览器数据、回收站或 WinSxS 中的文件。正在使用或权限不足的文件会跳过。清理系统临时目录会由 Windows 请求管理员权限。组件存储清理请使用 Windows 自带维护入口；本工具不会接管 WinSxS 权限、修改 ACL 或使用 `/ResetBase`。

大文件分析是独立的只读功能：它会检查当前账户有权限枚举的 C 盘路径，包括用户文件夹，但不读取文件内容、不移动或删除文件。它通过文件句柄查询 Windows 报告的分配空间和文件 ID，结果按分配空间排序；相同卷序列号与文件 ID 的硬链接在扫描范围内只计一次。分析跳过链接及其他重解析点，权限不足或无法读取文件 ID 的项目会记录为读取错误；列表最多显示最大的 2,000 个唯一文件。文件 ID 不会识别扫描范围之外的其他硬链接，因此分配空间不等于删除某一路径后一定能释放的空间。稀疏文件和云端占位文件也可能令逻辑大小与本地磁盘占用不同；清理前请核实文件用途。

**1.3.0 性能优化：** 临时目录按需逐项枚举文件和子目录，不再为每个目录一次性建立完整数组；大目录扫描时可减少额外内存占用。此前 1.2.0 的单目标重新校验和管理员单目录预估也继续保留。清理年龄、目录白名单、跳过规则和确认步骤不变。

**1.4.0 性能优化：** 启动项清单改为虚拟化表格；搜索输入增加短暂防抖，并缓存每项的搜索文本，减少大清单下的行对象、临时字符串和重复刷新。

**1.5.0 存储分析：** 增加可取消的 C 盘大文件扫描、文件大小门槛、最大的 2,000 项结果和资源管理器定位。分析与清理分开，扫描结果不会自动删除。

**1.6.0 文件系统统计：** 按微软 `FILE_STANDARD_INFO.AllocationSize` 显示和排序文件的分配空间，同时保留逻辑大小；逐个查询文件分配信息，不按逻辑长度预筛，以免漏掉预留空间大于 EOF 的文件。对 `NumberOfLinks` 大于 1 的文件使用 `FILE_ID_INFO` 按卷和 128 位 ID 合并扫描范围内的硬链接。用 `CreateFileW` 的零访问请求查询元数据，并以 `FILE_FLAG_OPEN_REPARSE_POINT` 打开后识别重解析点，避免把链接目标当作普通文件跟随。目录枚举显式设置 `AttributesToSkip = 0`，避免 .NET 默认跳过隐藏和系统项；不可访问路径不静默忽略，而是计入读取错误。

**1.7.0 界面优化：** 提供 WinForms 侧边栏、深浅色和 DWM 窗口外观尝试；内容玻璃层为绘制模拟。

**1.8.0 原生界面：** 将主界面和大文件窗口迁移到 WinUI 3，使用 Windows App SDK 的 MicaBackdrop、XAML AcrylicBrush、NavigationView、TextBox、ComboBox、CheckBox、Button、ListView 和 ContentDialog。启动扫描、临时目录清理、文件元数据读取和逐项恢复逻辑继续复用原服务层；高权限确认使用 Windows 原生 MessageBoxW。发布仍提供单文件便携 EXE 和 Inno Setup 安装包。便携版采用 Windows App SDK 自包含部署，会比纯 WinForms 版本更大，并在首次启动时从单文件中解包运行时内容。

**1.9.0 微信专项清理：** 新增微信媒体文件按时间和类型扫描、空间预览、手动选择归档、归档记录及还原。归档后不删除副本，跨磁盘复制会校验 SHA-256 后才移除源文件；还原时检查来源白名单、链接目录和目标冲突。操作期间需退出微信。

**1.9.1 启动修复：** 补齐 WinUI 3 默认控件资源 `XamlControlsResources`，修复创建主窗口时缺少 `TabViewButtonBackground` 导致的启动崩溃；将无效的导航图标 `Storage` 改为 WinUI 支持的 `Folder`。便携版保留发布时的原始文件名 `WinCare.exe`；安装版包含完整的自包含发布目录，同时提供解压即用的完整目录 ZIP。Windows 构建会实际启动两种发布形式并加载主窗口 XAML；启动异常写入 `%LOCALAPPDATA%\WinCare\Logs\startup.log`，不上传日志。

**1.10.0 仓库与归档优化：** 仓库主线整理为 WinCare 专用，源码、安装脚本、Windows CI 和验证程序位于根目录。微信归档可以选择独立磁盘；归档位置持久记录供还原。界面区分同盘移动与跨盘移动，不再把同盘归档误写成释放磁盘空间。CI 除启动两种发布形式，还验证微信媒体归档、同名文件保护与还原。

**1.11.0 启动扫描优化：** 启动项扫描增加可取消令牌，并在注册表、启动文件夹、隐藏计划任务和自动启动服务的遍历中检查取消状态。取消时保留上一次完整结果，不用半份清单覆盖；注册表无法列出其他已加载用户时显示扫描提示并继续检查其余入口。修复启动项操作后列表按钮可能因忙碌状态而一直禁用的问题。

**1.12.0 UI 优化：** 重新梳理主窗口与大文件分析窗口的视觉层级，增加启动项概览数字、卡片式状态标记、分组筛选和更清晰的操作区；清理页用空间摘要突出扫描结果，微信归档页将路径、筛选和归档状态分区展示。统一浅色、深色与高对比度材质资源，保留 WinUI 3、Windows Mica/Acrylic 及原有操作确认与恢复逻辑。

## 使用

1. 从 [WinCare 1.12.0 发布页](https://github.com/plao94619-hash/Repository-name-VideoToolBox/releases/tag/wincare-v1.12.0) 下载 `WinCare-Setup-x64.exe` 安装版，或下载 `WinCare.exe` 单文件便携版。也可下载 `WinCare-Portable-Folder-x64.zip`，完整解压后运行其中的 `WinCare.exe`。便携版无需安装，单文件 EXE 请保留 `WinCare.exe` 原名。
2. 程序以普通权限启动，仅在需要修改系统范围启动项或清理 Windows 临时目录时请求 UAC。
3. 在“启动项管理”页查看入口；用每行的“一键关闭”关闭单项，已由 WinCare 关闭的项目可按“恢复”。
4. 在“C 盘清理”页查看临时文件预估，逐个目录确认后清理；选择“查找大文件”可单独进行只读分析。

便携版不在 EXE 所在目录保存状态；启动文件恢复数据保存在 `%LOCALAPPDATA%\\WinCare`，系统级服务和任务恢复标记保存在受保护的注册表位置。

修改系统范围启动项和清理 Windows 临时目录前，WinCare 会在 UAC 授权后再次显示确认提示。服务设置一般在下次启动时生效；请先检查说明和任务动作。

## 构建

项目使用 .NET 10、WinUI 3 和 Windows App SDK。请在仓库根目录运行。GitHub Actions 分别发布自包含的完整目录与单文件 EXE：

```powershell
dotnet publish src/WinCare.csproj -c Release -r win-x64 --self-contained true `
  -p:PublishSingleFile=false -o publish-folder
dotnet publish src/WinCare.csproj -c Release -r win-x64 --self-contained true `
  -p:PublishSingleFile=true -p:IncludeAllContentForSelfExtract=true -o publish-single
```

先运行 `dotnet run --project tests/WinCare.ServiceChecks.csproj -c Release` 验证微信归档与还原，随后用 Inno Setup 将 `publish-folder` 的全部文件编入安装包；单文件便携版沿用 `publish-single/WinCare.exe` 原名。工作流分别运行两个版本的启动验证，通过后才上传 Release。

## 安全与隐私

- 默认以普通用户运行，不常驻、不联网、不收集遥测。
- 系统范围操作按需请求 UAC。
- 启动文件备份和旧版服务/任务恢复记录保存在 `%LOCALAPPDATA%\\WinCare`。
- 新版本的计划任务和服务恢复标记写入 `HKLM\\SOFTWARE\\WinCare\\StartupRestore`，避免把用户可改写的恢复文件直接当作管理员操作依据。旧版 JSON 恢复记录仍可识别；恢复前会标出旧记录并要求在管理员确认框中核对对象。
- 服务和系统任务具有依赖关系；只对单项提供操作，不提供批量禁用按钮。
- 安装包未进行代码签名，Windows SmartScreen 可能显示未知发布者提示。

## 设计参考

- [BleachBit](https://github.com/bleachbit/bleachbit)：借鉴删除前预览、逐项确认和清理边界说明。本项目只清理列明的两个临时目录，不扩大到浏览器、下载或系统组件。
- [autostart-audit](https://github.com/rwrife/autostart-audit)：借鉴按来源呈现启动入口、可筛选清单、保留恢复依据和明确显示扫描限制的做法。本项目自行实现 WinUI 3 界面和逐项恢复，没有复制其代码。
- [Microsoft Sysinternals Autoruns](https://learn.microsoft.com/sysinternals/downloads/autoruns)：参考其分类和筛选大量自动启动项的方式。WinCare 保持自己的覆盖范围，不宣称具备 Autoruns 的全部扫描能力或签名验证功能。
- [Microsoft PC Manager](https://pcmanager.microsoft.com/)：参考其把存储管理作为独立入口的产品组织方式；WinCare 清理仍限定于明确列出的临时目录。
- [WinDirStat](https://github.com/windirstat/windirstat)：参考其按大小检查磁盘文件并提供文件列表的思路。WinCare 当前提供可取消的最大文件列表和资源管理器定位，不包含 WinDirStat 的 treemap 可视化。
- [Windows 存储设置与存储感知](https://support.microsoft.com/windows/manage-drive-space-with-storage-sense)：参考 Windows 对临时文件、存储类别和清理建议的区分。WinCare 将临时文件清理与大文件分析分开，避免把大文件误当成垃圾文件。

## Microsoft 技术文档

- [FILE_STANDARD_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_standard_info)：使用 `AllocationSize` 显示文件系统报告的已分配字节，并保留 `EndOfFile` 作为逻辑大小。
- [FILE_ALLOCATION_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_allocation_info)：文件系统分配大小可独立于 EOF，因而扫描器不依赖逻辑长度过滤候选文件。
- [GetFileInformationByHandleEx](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileinformationbyhandleex)：通过已打开的文件句柄查询标准信息、属性和文件 ID。
- [FILE_ID_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_info)：卷序列号与 128 位文件 ID 组合，用于识别重复目录项所指向的同一文件。
- [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)：零访问请求可在适当权限下查询文件元数据；`FILE_FLAG_OPEN_REPARSE_POINT` 用于打开重解析点本身。
- [Hard Links and Junctions](https://learn.microsoft.com/en-us/windows/win32/fileio/hard-links-and-junctions)：说明多个路径可以指向同一文件，因此不能简单把每个路径的大小都累加为独立磁盘占用。
- [.NET EnumerationOptions.AttributesToSkip](https://learn.microsoft.com/en-us/dotnet/api/system.io.enumerationoptions.attributestoskip?view=net-10.0)：其默认值包含 Hidden 和 System；扫描器显式设为零以枚举这些项，并自行跳过重解析点。
- [Maximum Path Length Limitation](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation)：为清单加入 `longPathAware` 声明，并在原生文件句柄调用中使用扩展路径形式。
- [DwmSetWindowAttribute](https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/nf-dwmapi-dwmsetwindowattribute)：通过 Windows Desktop Window Manager 设置系统窗口属性。
- [DWM_SYSTEMBACKDROP_TYPE](https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwm_systembackdrop_type)：`DWMSBT_MAINWINDOW` 在 Windows 11 映射为系统 Mica 窗口材质。
- [Windows 窗口圆角](https://learn.microsoft.com/en-us/windows/apps/desktop/modernize/ui/apply-rounded-corners)：WinForms 可通过 DWM 原生窗口角属性请求系统圆角。
- [Apple Liquid Glass](https://developer.apple.com/documentation/technologyoverviews/liquid-glass) 与 [Adopting Liquid Glass](https://developer.apple.com/documentation/TechnologyOverviews/adopting-liquid-glass)：参考其系统材质、前景控件层与背景内容之间的视觉层次；WinCare 使用 Windows 原生窗口 API 实现本平台界面。
- [Windows App SDK system backdrops](https://learn.microsoft.com/windows/apps/develop/ui/system-backdrops)：主窗口用 Mica 系统背景材质，并依系统能力回退。
- [WinUI 3 AcrylicBrush](https://learn.microsoft.com/windows/apps/develop/ui/controls/acrylic)：信息卡片在窗口内用 AcrylicBrush 实现半透明背景模糊和色调。
- [Unpackaged WinUI 3 single-file deployment](https://learn.microsoft.com/windows/apps/package-and-deploy/unpackage-winui-app)：便携包以自包含 Windows App SDK 和单文件发布；首次启动会解包部分运行内容到临时目录。
- [XamlControlsResources](https://learn.microsoft.com/windows/apps/winui/winui3/desktop-winui3-app-with-basic-interop)：在应用资源中合并 WinUI 3 控件默认样式，避免启动时缺少控件资源键。

## 许可证

本项目按 MIT License 发布。
