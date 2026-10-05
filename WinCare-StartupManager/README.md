# WinCare · 启动项管理与 C 盘清理

一个面向 Windows 10 / 11 x64 的轻量桌面工具。它扫描常见的登录和开机启动入口，可逐项关闭并恢复；C 盘清理页只处理安全范围内的临时文件。

## 功能

- **启动项扫描**：当前用户与所有用户的 Run / RunOnce / RunServices / 策略 Run 注册表项，32 位和 64 位注册表视图，以及当前加载的其他用户配置单元。
- **文件夹和计划任务**：当前用户与所有用户的启动文件夹；递归查看任务计划程序中的隐藏任务，并显示登录、开机、注册、事件和会话触发项。
- **服务与系统项**：列出自动启动服务、Boot / System 启动服务和驱动，以及 Windows 的 Winlogon / Load / Run 关键值。Boot / System 驱动和关键注册表值只读。
- **隐藏项标记**：标记计划任务中的隐藏任务、启动文件夹中的隐藏文件、无显示名称的服务，以及 Windows 关键启动位置。列表默认包含这些项目。
- **逐项关闭与恢复**：注册表值会移至同一位置下的 `WinCareDisabled` 子项；启动文件会移至用户配置目录的恢复区；新版本的计划任务和服务恢复标记存放在管理员保护的注册表位置。管理员操作会在 UAC 后再次显示对象名称、位置和动作供确认。WinCare 不会替用户重新启用由 Windows 或其他工具禁用的项目。
- **安全清理**：扫描 C 盘的当前用户临时目录和 `Windows\\Temp`，预览超过 7 天未修改的文件和预计空间。链接、被占用和无权访问的文件会跳过。也可打开 Windows 存储设置。

## 覆盖范围说明

Windows 程序可以通过许多机制自动运行，因此任何独立清理工具都不应声称能枚举每一种启动方式。WinCare 覆盖上面列出的常见注册表、启动文件夹、计划任务和服务入口；它**不枚举** WMI 永久事件消费者、组策略启动/登录脚本、每个应用的专有启动机制、所有 Store/UWP `StartupTask` 或驱动程序内部配置。配置单元未加载、权限不足或 Task Scheduler 无法访问的项目也可能无法读取。若扫描发生读取错误，页面会显示“扫描提示”。

启动项“隐藏”表示该项目在其来源中带有隐藏/系统标记，或位于关键系统启动位置；不是对所有软件厂商私有机制的完整判定。

## C 盘清理边界

WinCare 默认仅删除修改时间超过 7 天的临时文件，不扫描或删除下载、文档、浏览器数据、回收站或 WinSxS。正在使用或权限不足的文件会跳过。清理系统临时目录会由 Windows 请求管理员权限。组件存储清理请使用 Windows 自带维护入口；本工具不会接管 WinSxS 权限、修改 ACL 或使用 `/ResetBase`。

## 使用

1. 从 GitHub Releases 下载 `WinCare-Setup-x64.exe` 安装版，或下载 `WinCare-Portable-x64.exe` 单文件便携版；便携版可直接运行，无需安装。
2. 程序以普通权限启动，仅在需要修改系统范围启动项或清理 Windows 临时目录时请求 UAC。
3. 在“启动项管理”页查看入口；用每行的“一键关闭”关闭单项，已由 WinCare 关闭的项目可按“恢复”。
4. 在“C 盘清理”页查看预估，逐个目录确认后清理。

便携版不在 EXE 所在目录保存状态；启动文件恢复数据保存在 `%LOCALAPPDATA%\\WinCare`，系统级服务和任务恢复标记保存在受保护的注册表位置。

修改系统范围启动项和清理 Windows 临时目录前，WinCare 会在 UAC 授权后再次显示确认提示。服务设置一般在下次启动时生效；请先检查说明和任务动作。

## 构建

项目使用 .NET 10 LTS WinForms。该自包含发布命令会生成可直接运行的单文件 EXE；GitHub Actions 再用 Inno Setup 生成安装版：

```powershell
dotnet publish src/WinCare.csproj -c Release -r win-x64 --self-contained true `
  -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o publish
```

随后使用 Inno Setup 编译 `installer/WinCare.iss`。现有仓库的 WinCare 工作流会同时发布安装版和便携版构建产物，并将便携版附加到 WinCare Release。

## 安全与隐私

- 默认以普通用户运行，不常驻、不联网、不收集遥测。
- 系统范围操作按需请求 UAC。
- 启动文件备份和旧版服务/任务恢复记录保存在 `%LOCALAPPDATA%\\WinCare`。
- 新版本的计划任务和服务恢复标记写入 `HKLM\\SOFTWARE\\WinCare\\StartupRestore`，避免把用户可改写的恢复文件直接当作管理员操作依据。旧版 JSON 恢复记录仍可识别；恢复前会标出旧记录并要求在管理员确认框中核对对象。
- 服务和系统任务具有依赖关系；只对单项提供操作，不提供批量禁用按钮。
- 安装包未进行代码签名，Windows SmartScreen 可能显示未知发布者提示。

## 设计参考

- [BleachBit](https://github.com/bleachbit/bleachbit)：借鉴删除前预览、逐项确认和清理边界说明。本项目只清理列明的两个临时目录，不扩大到浏览器、下载或系统组件。
- [autostart-audit](https://github.com/rwrife/autostart-audit)：借鉴按来源呈现启动入口、保留恢复依据和明确显示扫描限制的做法。本项目自行实现 WinForms 界面和逐项恢复，没有复制其代码。

## 许可证

本项目按 MIT License 发布。
