

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]

PLATFORM_TAGS = {
	"linux-x64": ("manylinux",),
	"windows-x64": ("win_amd64",),
	"macos-x64": ("macosx_10_9_x86_64", "macosx_10_", "macosx_11_0_x86_64"),
	"macos-arm64": ("macosx_11_0_arm64", "macosx_12_0_arm64", "macosx_13_0_arm64"),
}

ALLOW_FILES = {
	"blender_manifest.toml",
	"LICENSE",
	"README.md",
	"__init__.py",
}
ALLOW_DIRS = {
	"SciBlend",
}


def collect_wheels(target: str) -> List[Path]:
	"""Select wheel files for a given target platform.

	Includes universal wheels from ``wheels/common`` (``*-none-any.whl``) and
	platform-specific wheels from ``wheels/<target>``. NumPy wheels are excluded
	as Blender bundles NumPy.

	Args:
		target: Platform key from PLATFORM_TAGS.

	Returns:
		List of wheel file paths selected from the local ``wheels/`` directory.
	"""
	wheel_root = ROOT / "wheels"
	if not wheel_root.is_dir():
		raise SystemExit("wheels/ folder not found")

	selected: List[Path] = []
	common_dir = wheel_root / "common"
	plat_dir = wheel_root / target

	if common_dir.is_dir():
		for fn in common_dir.glob("*.whl"):
			name = fn.name
			if name.startswith("numpy-"):
				continue
			if name.endswith("-none-any.whl"):
				selected.append(fn)

	if plat_dir.is_dir():
		for fn in plat_dir.glob("*.whl"):
			name = fn.name
			if name.startswith("numpy-"):
				continue
			if not name.endswith("-none-any.whl"):
				selected.append(fn)

	return selected


def copy_minimal_payload(dst: Path) -> None:
	"""Copy only the add-on minimal payload into `dst`.

	Creates missing directories and copies allowlisted files and directories
	from the repository root into the temporary packaging location.
	"""
	dst.mkdir(parents=True, exist_ok=True)


	for fname in ALLOW_FILES:
		src = ROOT / fname
		if src.exists():
			shutil.copy2(src, dst / fname)

	for dname in ALLOW_DIRS:
		src_dir = ROOT / dname
		if not src_dir.is_dir():
			continue
		for root, dirs, files in os.walk(src_dir):
			root_p = Path(root)
			rel = root_p.relative_to(ROOT)
			(dst / rel).mkdir(parents=True, exist_ok=True)
			for f in files:
				if f.endswith(".pyc"):
					continue
				shutil.copy2(root_p / f, dst / rel / f)


def rewrite_manifest_wheels(tmp_root: Path, selected: List[Path]) -> None:
	"""Rewrite wheels section in the manifest to match ``selected`` wheels.

	If a wheels block is present, it is replaced. If not present, a new block
	is appended at the end of the file.
	"""
	manifest = tmp_root / "blender_manifest.toml"
	if not manifest.exists():
		return
	lines = manifest.read_text(encoding="utf-8").splitlines()
	start = None
	end = None
	for i, line in enumerate(lines):
		if line.strip().startswith("wheels = ["):
			start = i
			break
	if start is None:
		block = ["wheels = ["]
		for wf in selected:
			block.append(f"  \"./wheels/{wf.name}\",")
		block.append("]")
		lines.extend(block)
		manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
		return
	for j in range(start, len(lines)):
		if lines[j].strip() == "]":
			end = j
			break
	if end is None:
		end = start
	new_block = [lines[start].split("[")[0] + "["]
	for wf in selected:
		new_block.append(f"  \"./wheels/{wf.name}\",")
	new_block.append("]")
	lines = lines[:start] + new_block + lines[end+1:]
	manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def rewrite_manifest_platforms(tmp_root: Path, target: str) -> None:
	"""Replace ``platforms`` list with the single ``target`` in staged manifest."""
	manifest = tmp_root / "blender_manifest.toml"
	if not manifest.exists():
		return
	lines = manifest.read_text(encoding="utf-8").splitlines()
	rewrote = False
	for i, line in enumerate(lines):
		if line.strip().startswith("platforms"):
			lines[i] = f'platforms = ["{target}"]'
			rewrote = True
			break
	if not rewrote:
		lines.append(f'platforms = ["{target}"]')
	manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_zip(target: str, outdir: Path) -> Path:
	"""Create a platform-specific extension zip archive.

	Args:
		target: Platform identifier (one of PLATFORM_TAGS keys).
		outdir: Output directory where the zip file will be written.

	Returns:
		The path to the created zip archive.
	"""
	outdir.mkdir(parents=True, exist_ok=True)
	name = f"sciblend-1.1.0-{target}.zip"
	zip_path = outdir / name
	with tempfile.TemporaryDirectory() as td:
		tmp = Path(td)

		copy_minimal_payload(tmp)

		selected = collect_wheels(target)
		wheels_dst = tmp / "wheels"
		wheels_dst.mkdir(parents=True, exist_ok=True)
		for wf in selected:
			shutil.copy2(wf, wheels_dst / wf.name)

		rewrite_manifest_platforms(tmp, target)
		rewrite_manifest_wheels(tmp, selected)

		shutil.make_archive(str(zip_path.with_suffix("")), 'zip', root_dir=tmp)
	return zip_path


def main() -> int:
	"""CLI entry point to build a platform-targeted SciBlend zip."""
	parser = argparse.ArgumentParser()
	parser.add_argument('--target', required=True, choices=list(PLATFORM_TAGS.keys()))
	parser.add_argument('--outdir', default='dist')
	args = parser.parse_args()
	zp = make_zip(args.target, Path(args.outdir))
	print("created:", zp)
	return 0

if __name__ == '__main__':
	sys.exit(main()) 