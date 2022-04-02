; 用于打包 exe 安装程序
; Inno Setup: https://zaxtyson.lanzouf.com/iVTrC02i5lzc

#define MyAppName "蓝奏云控制台"
#define MyAppVersion "2.6.7"
#define MyAppPublisher "zaxtyson"
#define MyAppURL "https://github.com/zaxtyson/LanZouCloud-CMD"

#define MyAppExeName "lanzou-cmd.exe"
#define PackSourceDir "C:\Users\zaxtyson\PycharmProjects\LanZouCloud-CMD\dist\lanzou-cmd"
#define PackOutputDir "C:\Users\zaxtyson\PycharmProjects\LanZouCloud-CMD\dist"
#define PackOutputAppName "lanzou-cmd_x64_v2.6.7"

[Setup]
AppId={{27D10ED2-13D0-420D-A602-39D1386872D0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\lanzou
DisableDirPage=no
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#PackOutputDir}
OutputBaseFilename={#PackOutputAppName}
SetupIconFile={#PackSourceDir}\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#PackSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#PackSourceDir}\user.dat"; DestDir: "{app}"; Flags: ignoreversion; Permissions: users-modify

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
