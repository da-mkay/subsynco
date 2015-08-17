[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{33D229FF-B24A-482A-9C59-45092174AB64}
AppName=SubSynco
AppVersion=0.1.0
;AppVerName=SubSynco 0.1.0
AppPublisher=da-mkay
AppPublisherURL=http://subsynco.org
AppSupportURL=http://subsynco.org
AppUpdatesURL=http://subsynco.org
DefaultDirName={pf}\SubSynco
DefaultGroupName=SubSynco
AllowNoIcons=yes
LicenseFile=tmp\LICENSE
OutputDir=tmp\dist
OutputBaseFilename=SubSynco-0.1.0
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "tmp\build\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\SubSynco"; Filename: "{app}\subsynco-gtk.exe"
Name: "{commondesktop}\SubSynco"; Filename: "{app}\subsynco-gtk.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\subsynco-gtk.exe"; Description: "{cm:LaunchProgram,SubSynco}"; Flags: nowait postinstall skipifsilent

