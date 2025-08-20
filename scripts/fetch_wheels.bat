@echo off
setlocal

rem
pushd "%~dp0.." >nul 2>&1

if not exist wheels mkdir wheels

set "PYVER=3.11"

echo Downloading wheels for Linux (manylinux2014 x64)
pip download -r constraints\base.txt --dest .\wheels --only-binary=:all: --python-version=%PYVER% --platform=manylinux2014_x86_64

echo Downloading wheels for Windows x64
pip download -r constraints\base.txt --dest .\wheels --only-binary=:all: --python-version=%PYVER% --platform=win_amd64

echo Downloading wheels for macOS Intel x64
pip download -r constraints\macos-x64.txt --dest .\wheels --only-binary=:all: --python-version=%PYVER% --platform=macosx_11_0_x86_64

echo Downloading wheels for macOS Apple Silicon arm64
pip download -r constraints\macos-arm64.txt --dest .\wheels --only-binary=:all: --python-version=%PYVER% --platform=macosx_11_0_arm64

popd >nul 2>&1

exit /b 0


