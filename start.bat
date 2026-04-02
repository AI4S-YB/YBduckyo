@echo off
cd /d "%~dp0"

python --version 2>nul
if %errorlevel% neq 0 (
    echo Downloading Python...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile 'python-setup.exe'"
    echo Installing Python...
    start /wait python-setup.exe /quiet PrependPath=1
    del python-setup.exe
)
set PATH=C:\my\bin;%PATH%

python -c "import PyQt5, requests, PIL, ddgs" 2>nul
if %errorlevel% neq 0 (
    echo Installing deps...
    pip install PyQt5 requests Pillow ddgs -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
)

echo Starting...
python main.py

pause
