

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

	Includes universal wheels (``*-none-any.whl``) and platform-specific wheels.
	Supports both nested structure (``wheels/common/``, ``wheels/<target>/``) and
	flat structure (all wheels in ``wheels/`` directory).

	Search order for the wheels root is both ``SciBlend/wheels/`` and the
	repository top-level ``wheels/``. Results are merged with de-duplication by
	filename. NumPy wheels are excluded as Blender bundles NumPy.

	Args:
		target: Platform key from PLATFORM_TAGS.

	Returns:
		List of wheel file paths selected from the local ``wheels/`` directory.
	"""
	wheel_root_candidates = [ROOT / "SciBlend" / "wheels", ROOT / "wheels"]
	selected: List[Path] = []
	seen_names = set()
	any_root_found = False
	
	platform_tags = PLATFORM_TAGS.get(target, ())
	
	for wheel_root in wheel_root_candidates:
		if not wheel_root.is_dir():
			continue
		any_root_found = True
		
		common_dir = wheel_root / "common"
		plat_dir = wheel_root / target
		
		if common_dir.is_dir():
			for fn in common_dir.glob("*.whl"):
				name = fn.name
				if name in seen_names:
					continue
				if name.startswith("numpy-"):
					continue
				if name.endswith("-none-any.whl"):
					selected.append(fn)
					seen_names.add(name)
		
		if plat_dir.is_dir():
			for fn in plat_dir.glob("*.whl"):
				name = fn.name
				if name in seen_names:
					continue
				if name.startswith("numpy-"):
					continue
				selected.append(fn)
				seen_names.add(name)
		
		for fn in wheel_root.glob("*.whl"):
			name = fn.name
			if name in seen_names:
				continue
			if name.startswith("numpy-"):
				continue
			
			if name.endswith("-none-any.whl"):
				selected.append(fn)
				seen_names.add(name)
			elif any(tag in name for tag in platform_tags):
				selected.append(fn)
				seen_names.add(name)

	if not any_root_found:
		raise SystemExit("wheels folder not found (looked in 'wheels/' and 'SciBlend/wheels/')")
	
	if not selected:
		raise SystemExit(f"No wheels found for target '{target}'. Check that wheels are present in the wheels directory.")

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




def make_zip(target: str, outdir: Path) -> Path:
	"""Create a platform-specific extension zip archive.

	Args:
		target: Platform identifier (one of PLATFORM_TAGS keys).
		outdir: Output directory where the zip file will be written.

	Returns:
		The path to the created zip archive.
	"""
	outdir.mkdir(parents=True, exist_ok=True)
	name = f"sciblend-1.1.1-{target}.zip"
	zip_path = outdir / name
	with tempfile.TemporaryDirectory() as td:
		tmp = Path(td)

		copy_minimal_payload(tmp)

		selected = collect_wheels(target)
		if not selected:
			raise SystemExit(f"No wheels selected for target '{target}'")
		
		wheels_dst = tmp / "wheels"
		wheels_dst.mkdir(parents=True, exist_ok=True)
		for wf in selected:
			shutil.copy2(wf, wheels_dst / wf.name)
		
		copied_wheels = list(wheels_dst.glob("*.whl"))
		if not copied_wheels:
			raise SystemExit(f"No wheels were copied to zip for target '{target}'")


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