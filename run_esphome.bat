@echo off
rem ============================================================
rem   Clean Windows ESPHome launcher
rem   1) Pure Windows PATH (no Git-Bash/MSys/mingw dirs)
rem   2) Blanks all inherited MSys/Git-Bash environment vars
rem   Usage: run_esphome.bat <subcommand>   e.g. run_esphome.bat run
rem ============================================================

rem ------------------------------------------------------------------
rem   本机路径(可选)
rem   仅当 esphome / git 安装在非系统 PATH 的目录时才需要填写;
rem   保持为空则使用系统默认 PATH。
rem   例如:
rem     set "LOCAL_PYTHON_DIR=C:\Python314"
rem     set "LOCAL_GIT_DIR=C:\Program Files\Git"
rem ------------------------------------------------------------------
set "LOCAL_PYTHON_DIR="
set "LOCAL_GIT_DIR="

set "PATH=C:\Windows\System32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0;C:\Windows\System32\OpenSSH"

if not "%LOCAL_PYTHON_DIR%"=="" set "PATH=%PATH%;%LOCAL_PYTHON_DIR%;%LOCAL_PYTHON_DIR%\Scripts"
if not "%LOCAL_GIT_DIR%"=="" set "PATH=%PATH%;%LOCAL_GIT_DIR%\cmd;%LOCAL_GIT_DIR%\bin;%LOCAL_GIT_DIR%\usr\bin"

rem ---- blank MSys / Git-Bash leftovers ----
set "MSYSTEM="
set "MSYSTEM_CARCH="
set "MSYSTEM_CHOST="
set "MSYSTEM_PREFIX="
set "MSYS2_PATH_TYPE="
set "EXEPATH="
set "MINGW_PREFIX="
set "MINGW_CHOST="
set "MINGW_PACKAGE_PREFIX="
set "OSTYPE="
set "SHELL="
set "TERM="
set "SHLVL="
set "OLDPWD="
set "HOME=%USERPROFILE%"

cd /d "%~dp0"
echo [bat] Clean environment ready. Running: esphome %*
esphome %*