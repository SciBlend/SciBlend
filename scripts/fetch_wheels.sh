set -euo pipefail

# Prepare directories
mkdir -p wheels/common wheels/linux-x64 wheels/windows-x64 wheels/macos-x64 wheels/macos-arm64

PYVER=3.11
PIP="python3 -m pip"

_download() {
	local_constraints="$1"
	platform_tag="$2"
	dest_dir="$3"
	${PIP} download -r "${local_constraints}" --dest "${dest_dir}" --only-binary=:all: \
		--python-version=${PYVER} --platform="${platform_tag}" || true
}

# Linux (manylinux2014 x64)
_download constraints/linux-x64.txt manylinux2014_x86_64 ./wheels/linux-x64

# Windows x64
_download constraints/base.txt win_amd64 ./wheels/windows-x64

# macOS Intel x64
_download constraints/macos-x64.txt macosx_11_0_x86_64 ./wheels/macos-x64

# macOS Apple Silicon arm64
_download constraints/macos-arm64.txt macosx_11_0_arm64 ./wheels/macos-arm64

# Move universal wheels to common and deduplicate
for plat in linux-x64 windows-x64 macos-x64 macos-arm64; do
	shopt -s nullglob
	for whl in ./wheels/${plat}/*-none-any.whl; do
		base=$(basename "$whl")
		if [[ ! -f "./wheels/common/${base}" ]]; then
			mv "$whl" ./wheels/common/
		else
			rm -f "$whl"
		fi
	done
	shopt -u nullglob
done

find ./wheels -type f -name 'numpy-*.whl' -print -delete || true 