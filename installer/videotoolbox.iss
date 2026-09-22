#ifndef MyAppVersion
  #define MyAppVersion "1.12.0"
#endif

#define MyAppName "万能音视频工具箱"
#define MyAppExeName "万能音视频工具箱.exe"
#define MyAppPublisher "plao94619-hash"
#define MyAppURL "https://github.com/plao94619-hash/Repository-name-VideoToolBox"

[Setup]
AppId={{D29D1608-7D71-4E4E-A489-62176655BF00}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={localappdata}\Programs\Universal Media Toolbox
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\release
OutputBaseFilename=Universal-Media-Toolbox-Setup-{#MyAppVersion}
SetupIconFile=..\assets\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
MinVersion=10.0.17763
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} 安装程序
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinese"; MessagesFile: "languages\ChineseSimplified.isl"
Name: "traditional"; MessagesFile: "languages\ChineseTraditional.isl"

[CustomMessages]
english.DesktopIcon=Create a desktop shortcut
chinese.DesktopIcon=创建桌面快捷方式
traditional.DesktopIcon=建立桌面捷徑
english.ExtraIcons=Optional shortcuts:
chinese.ExtraIcons=附加图标：
traditional.ExtraIcons=其他捷徑：
english.LaunchApp=Launch {#MyAppName}
chinese.LaunchApp=启动 {#MyAppName}
traditional.LaunchApp=啟動 {#MyAppName}

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; GroupDescription: "{cm:ExtraIcons}"; Flags: unchecked

[Files]
Source: "..\dist\万能音视频工具箱\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchApp}"; Flags: nowait postinstall skipifsilent
