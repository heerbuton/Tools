@echo off
echo ========================================
echo   Toolbox GUI 打包脚本
echo ========================================
echo.

REM 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
)

echo 正在打包...
pyinstaller --onefile --windowed --name "Toolbox" --icon=NUL toolbox_gui.py

echo.
echo 打包完成！
echo 输出文件: dist\Toolbox.exe
echo.
pause
