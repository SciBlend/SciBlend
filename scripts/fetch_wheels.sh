
set -euo pipefail

mkdir -p wheels

PYVER=3.11

# Linux (manylinux2014 x64)
pip download -r constraints/base.txt --dest ./wheels --only-binary=:all: \
  --python-version=${PYVER} --platform=manylinux2014_x86_64 || true

# Windows x64
pip download -r constraints/base.txt --dest ./wheels --only-binary=:all: \
  --python-version=${PYVER} --platform=win_amd64 || true

# macOS Intel x64
pip download -r constraints/macos-x64.txt --dest ./wheels --only-binary=:all: \
  --python-version=${PYVER} --platform=macosx_11_0_x86_64 || true

# macOS Apple Silicon arm64
pip download -r constraints/macos-arm64.txt --dest ./wheels --only-binary=:all: \
  --python-version=${PYVER} --platform=macosx_11_0_arm64 || true 