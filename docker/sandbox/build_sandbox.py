"""Helper script to build and export the Sovereign AI Workbench hardened sandbox image.

Builds sovereign-sandbox:local and optionally saves to data/models/sandbox_image.tar.
"""

import argparse
from pathlib import Path
import subprocess
import sys


def build_image(tag: str = "sovereign-sandbox:local", dockerfile_dir: str = "docker/sandbox") -> bool:
    """Build the sandbox Docker image locally."""
    cmd = ["docker", "build", "-t", tag, dockerfile_dir]
    print(f"Executing: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, check=True)
        print(f"Successfully built image '{tag}' (exit code {res.returncode})")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error building sandbox image: {e}", file=sys.stderr)
        return False


def save_image(tag: str = "sovereign-sandbox:local", output_tar: str = "data/models/sandbox_image.tar") -> bool:
    """Save the Docker image to a tarball for air-gapped distribution."""
    out_path = Path(output_tar)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["docker", "save", tag, "-o", str(out_path)]
    print(f"Exporting image '{tag}' to '{output_tar}'...")
    try:
        subprocess.run(cmd, check=True)
        print(f"Export complete: {out_path} ({out_path.stat().st_size / (1024 * 1024):.1f} MB)")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error saving image: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build and export Sovereign AI Workbench sandbox image.")
    parser.add_argument("--save", action="store_true", help="Also save image to data/models/sandbox_image.tar")
    parser.add_argument("--tag", default="sovereign-sandbox:local", help="Image tag")
    args = parser.parse_args()

    success = build_image(tag=args.tag)
    if success and args.save:
        save_image(tag=args.tag)
