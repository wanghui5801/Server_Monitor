@echo off
setlocal enabledelayedexpansion

:: Check administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Please run this script with administrator privileges
    exit /b 1
)


where git >nul 2>nul
if %errorlevel% neq 0 (
    echo Please install Git: https://git-scm.com/download/win
    exit /b 1
)


where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Please install Python: https://www.python.org/downloads/
    exit /b 1
)


git clone https://github.com/wanghui5801/Server_Monitor.git vps-monitor
cd vps-monitor


python -m venv venv
call venv\Scripts\activate


pip install -r requirements.txt
pip install wmi pywin32

:: Configure server address and node name
set /p SERVER_URL="Enter server address (e.g., http://your-server:5000): "
set /p NODE_NAME="Enter node name: "
powershell -Command "(gc client/monitor.py) -replace 'SERVER_URL = .*', 'SERVER_URL = \"%SERVER_URL%/update_status\"' | Out-File -encoding UTF8 client/monitor.py"
powershell -Command "(gc client/monitor.py) -replace 'NODE_NAME = .*', 'NODE_NAME = \"%NODE_NAME%\"' | Out-File -encoding UTF8 client/monitor.py"


echo @echo off > start_client.bat
echo cd %cd% >> start_client.bat
echo call venv\Scripts\activate >> start_client.bat
echo start /B pythonw client/monitor.py >> start_client.bat


powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VPSMonitor-Client.lnk');$s.TargetPath='%cd%\start_client.bat';$s.WorkingDirectory='%cd%';$s.Save()"

start /B start_client.bat

echo Client installation completed and started!