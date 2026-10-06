#define ProductName "WinCare 启动项管理与 C 盘清理"
#define ProductVersion "1.10.0"

[Setup]
AppId={{C3D00A46-3388-472A-8B6A-CC1B1051FB30}
AppName={#ProductName}
AppVersion={#ProductVersion}
AppPublisher=WinCare
DefaultDirName={localappdata}\Programs\WinCare
DefaultGroupName=WinCare
DisableProgramGroupPage=yes
OutputDir=..\artifacts
OutputBaseFilename=WinCare-Setup-x64
UninstallDisplayIcon={app}\WinCare.exe
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
Uninstallable=yes
VersionInfoVersion={#ProductVersion}.0
VersionInfoProductName={#ProductName}

[Files]
Source: "..\publish-folder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\WinCare"; Filename: "{app}\WinCare.exe"
Name: "{autodesktop}\WinCare"; Filename: "{app}\WinCare.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加快捷方式："; Flags: unchecked

[Run]
Filename: "{app}\WinCare.exe"; Description: "启动 WinCare"; Flags: postinstall nowait skipifsilent
