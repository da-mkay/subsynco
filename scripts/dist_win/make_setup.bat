rem SubSynco - a tool for synchronizing subtitle files
rem Copyright (C) 2015  da-mkay
rem 
rem This program is free software: you can redistribute it and/or modify
rem it under the terms of the GNU General Public License as published by
rem the Free Software Foundation, either version 3 of the License, or
rem (at your option) any later version.
rem 
rem This program is distributed in the hope that it will be useful,
rem but WITHOUT ANY WARRANTY; without even the implied warranty of
rem MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
rem GNU General Public License for more details.
rem 
rem You should have received a copy of the GNU General Public License
rem along with this program.  If not, see <http://www.gnu.org/licenses/>.


SET SCRIPT_DIR=%~dp0
CD "%SCRIPT_DIR%"

SET WORKING_DIR=%SCRIPT_DIR%tmp
IF NOT EXIST "%$SCRIPT_DIR%tmp" GOTO NOTMPDIR
RMDIR /Q /S "%WORKING_DIR%"
:NOTMPDIR
MKDIR "%WORKING_DIR%"

COPY ..\..\LICENSE tmp\
XCOPY setup.py tmp\
XCOPY ..\..\src\* tmp\ /S

CD tmp
python setup.py build_exe

CD ..
"C:\Program Files (x86)\Inno Setup 5\ISCC.exe" setup.iss