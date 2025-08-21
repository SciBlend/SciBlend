@echo off
setlocal enabledelayedexpansion

rem Change to repo root
pushd "%~dp0.." >nul 2>&1

rem Prepare directories
if not exist wheels\common mkdir wheels\common
if not exist wheels\linux-x64 mkdir wheels\linux-x64
if not exist wheels\windows-x64 mkdir wheels\windows-x64
if not exist wheels\macos-x64 mkdir wheels\macos-x64
if not exist wheels\macos-arm64 mkdir wheels\macos-arm64

set "PYVER=3.11"

rem Linux (manylinux2014 x64)
pip download -r constraints\linux-x64.txt --dest .\wheels\linux-x64 --only-binary=:all: --python-version=%PYVER% --platform=manylinux2014_x86_64 || ver >nul

rem Windows x64
pip download -r constraints\base.txt --dest .\wheels\windows-x64 --only-binary=:all: --python-version=%PYVER% --platform=win_amd64 || ver >nul

rem macOS Intel x64
pip download -r constraints\macos-x64.txt --dest .\wheels\macos-x64 --only-binary=:all: --python-version=%PYVER% --platform=macosx_11_0_x86_64 || ver >nul

rem macOS Apple Silicon arm64
pip download -r constraints\macos-arm64.txt --dest .\wheels\macos-arm64 --only-binary=:all: --python-version=%PYVER% --platform=macosx_11_0_arm64 || ver >nul

rem Move universal wheels to common and deduplicate
for %%P in (linux-x64 windows-x64 macos-x64 macos-arm64) do (
  for %%F in (wheels\%%P\*-py3-none-any.whl) do (
    if exist "%%F" (
      for %%B in ("%%~nxF") do (
        if not exist "wheels\common\%%~nxF" (
          move /Y "%%F" "wheels\common\" >nul
        ) else (
          del /F /Q "%%F" >nul
        )
      )
    )
  )
)

rem Remove numpy wheels if any
for /r %%F in (wheels\numpy-*.whl) do (
  del /F /Q "%%F" >nul 2>&1
)

popd >nul 2>&1
exit /b 0


