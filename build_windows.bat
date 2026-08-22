@echo off
REM
REM Build the rbMigrate Windows executable (.exe).
REM
REM MUST be run on Windows (PyInstaller does not cross-compile).
REM The recommended way to get a Windows build without a Windows box is the
REM GitHub Actions workflow (.github/workflows/build.yml).
REM
REM Requires:
REM   - Python 3.8+ installed and on PATH
REM
REM Usage:
REM   build_windows.bat
REM
setlocal

cd /d "%~dp0"

set VENV_DIR=.build-venv
set STAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set STAMP=%STAMP: =0%
set DIST_DIR=dist

echo ==^> Creating virtual environment...
python -m venv %VENV_DIR%
call %VENV_DIR%\Scripts\activate.bat
if errorlevel 1 goto :error

echo ==^> Installing build and runtime dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt
if errorlevel 1 goto :error

echo ==^> Building the executable with PyInstaller...
if exist build rmdir /s /q build
if exist %DIST_DIR% rmdir /s /q %DIST_DIR%
pyinstaller --noconfirm rbMigrate.spec
if errorlevel 1 goto :error

REM PyInstaller creates the exe in dist\rbMigrate\rbMigrate.exe (Windows)
REM or dist\rbMigrate\rbMigrate (macOS). Check both locations.
if exist "%DIST_DIR%\rbMigrate\rbMigrate.exe" (
    set EXE_PATH=%DIST_DIR%\rbMigrate\rbMigrate.exe
) else if exist "%DIST_DIR%\rbMigrate\rbMigrate" (
    set EXE_PATH=%DIST_DIR%\rbMigrate\rbMigrate
) else (
    echo ERROR: expected build output not found
    dir /b %DIST_DIR%
    goto :error
)

if not exist "%EXE_PATH%" (
    echo ERROR: expected build output not found at %EXE_PATH%
    goto :error
)

echo.
echo Done!
echo   Exe: %EXE_PATH%
goto :eof

:error
echo BUILD FAILED.
exit /b 1
