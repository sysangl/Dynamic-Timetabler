#!/usr/bin/env python3
"""
installer.py

* Downloads the latest release of sysangl/Dynamic‑Timetabler from GitHub
* Extracts the zipball to a temporary folder
* (optionally) creates a virtual‑env inside the extracted project and
  installs the project's requirements
* Detects the correct Flask entry‑point
* Runs the three Flask‑Migrate commands:
        flask db init
        flask db migrate -m "initial"
        flask db upgrade
* Copies the ready‑to‑run source tree to the current working directory

The script works both as a normal .py file and as a frozen executable
produced with PyInstaller.
"""

# ----------------------------------------------------------------------
# ONLY STANDARD‑LIBRARY IMPORTS – keeps the frozen exe small
# ----------------------------------------------------------------------
import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError

# ----------------------------------------------------------------------
# USER‑CONFIGURABLE SETTINGS
# ----------------------------------------------------------------------
REPO_OWNER = "sysangl"
REPO_NAME = "Dynamic-Timetabler"

# If you know the exact Flask entry point, set it here.
# Leave empty for auto‑detect (run.py, app.py, wsgi.py, main.py …)
FLASK_APP_MODULE = ""          # e.g. "run.py" or "app:create_app()"

# When True the installer will create an isolated venv inside the extracted
# project and run `pip install -r requirements.txt`.  The frozen exe **cannot**
# create a venv (because `sys.executable` points to the exe), so the flag is
# automatically disabled when the script runs frozen.
CREATE_VENV = True

# ----------------------------------------------------------------------
# CONSTANTS (no need to edit)
# ----------------------------------------------------------------------
GITHUB_API_RELEASE_URL = (
    f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
)

# ----------------------------------------------------------------------
# Tiny logger
# ----------------------------------------------------------------------
def _log(msg: str) -> None:
    print(msg, flush=True)


# ----------------------------------------------------------------------
# Network helpers
# ----------------------------------------------------------------------
def _download_json(url: str) -> dict:
    """GET a JSON document (GitHub API)."""
    _log(f"Fetching JSON from {url} …")
    req = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github.v3+json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _pick_download_url(release: dict) -> tuple[str, str]:
    """
    Return (download_url, tag_name).
    Preference order:
      1️⃣ First asset whose name ends with ".zip"
      2️⃣ Otherwise the generic zipball_url supplied by GitHub.
    """
    tag = release.get("tag_name", "unknown")
    for asset in release.get("assets", []):
        name = asset.get("name", "")
        if name.lower().endswith(".zip"):
            url = asset.get("browser_download_url")
            if url:
                _log(f"Found zip asset '{name}' → {url}")
                return url, tag

    zipball = release.get("zipball_url")
    if zipball:
        _log("No .zip asset found – using generic zipball_url")
        return zipball, tag

    raise RuntimeError("Could not locate a downloadable .zip for the latest release.")


def _download_file(url: str, dest: Path) -> None:
    """Stream‑download *url* into *dest* (binary) and display a simple ASCII bar."""
    _log(f"Downloading {url}")
    with urllib.request.urlopen(url) as resp, open(dest, "wb") as out:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        block = 8192
        while True:
            chunk = resp.read(block)
            if not chunk:
                break
            out.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                # plain ASCII space – works on every Windows console
                print(f"\r  {downloaded}/{total} bytes ({pct:5.1f} %) ", end="", flush=True)
        print()  # newline after progress


# ----------------------------------------------------------------------
# Archive handling
# ----------------------------------------------------------------------
def _extract_zip(zip_path: Path, out_dir: Path) -> Path:
    """
    Extract the zip into *out_dir*.
    GitHub release zips always contain a **single** top‑level folder.
    Returns the Path to that folder.
    """
    _log(f"Extracting {zip_path} → {out_dir}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out_dir)

    tops = [p for p in out_dir.iterdir() if p.is_dir()]
    if len(tops) != 1:
        raise RuntimeError(
            f"Expected exactly one top‑level directory in the zip, found {len(tops)}."
        )
    _log(f"Project source root is {tops[0]}")
    return tops[0]


# ----------------------------------------------------------------------
# Virtual‑env handling (optional)
# ----------------------------------------------------------------------
def _make_venv(project_root: Path) -> Path:
    """
    Create a venv at <project_root>/.dtm_venv,
    install the project's requirements (if any) and return the *bin/Scripts*
    directory that holds the interpreter and the ``flask`` entry‑point.
    """
    venv_path = project_root / ".dtm_venv"
    _log(f"Creating virtual‑env at {venv_path}")

    # ------------------------------------------------------------------
    # NEVER call "python -m venv" from a frozen exe – it would re‑execute
    # the exe itself and cause an infinite loop.  The caller disables venv
    # creation when the script is frozen.
    # ------------------------------------------------------------------
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)

    # Platform‑specific locations
    if os.name == "nt":
        bin_dir = venv_path / "Scripts"
        pip_exe = bin_dir / "pip.exe"
    else:
        bin_dir = venv_path / "bin"
        pip_exe = bin_dir / "pip"

    # Install dependencies if the repo ships a requirements.txt
    req_file = project_root / "requirements.txt"
    if req_file.is_file():
        _log("Installing project requirements …")
        subprocess.run([str(pip_exe), "install", "-r", str(req_file)], check=True)
    else:
        _log("No requirements.txt found – skipping pip install.")
    return bin_dir


# ----------------------------------------------------------------------
# Flask‑CLI runner (runs *inside* the same interpreter)
# ----------------------------------------------------------------------
def _run_flask_cli(project_root: Path, python_bin_dir: Path) -> None:
    """
    Execute the three Flask‑Migrate commands inside *project_root*.
    *python_bin_dir* is the directory that contains the ``flask`` script
    (either the current interpreter's bin or the venv's Scripts folder).
    """
    # --------------------------------------------------------------
    # 1️⃣  Choose the correct FLASK_APP value
    # --------------------------------------------------------------
    global FLASK_APP_MODULE
    if not FLASK_APP_MODULE:
        # Preferred order – first file that exists wins
        if (project_root / "run.py").is_file():
            FLASK_APP_MODULE = "run.py"
        elif (project_root / "app.py").is_file():
            # ``app.py`` in this repo does **not** create the app.
            # Fallback to the factory that definitely exists.
            FLASK_APP_MODULE = "app:create_app()"
        else:
            FLASK_APP_MODULE = "app:create_app()"

    _log(f"Using FLASK_APP = {FLASK_APP_MODULE}")

    # --------------------------------------------------------------
    # 2️⃣  Ensure the correct interpreter is first on PATH (so the
    #     ``flask`` script from the venv or from the bundled exe is found)
    # --------------------------------------------------------------
    env = os.environ.copy()
    env["PATH"] = str(python_bin_dir) + os.pathsep + env.get("PATH", "")
    env["FLASK_APP"] = FLASK_APP_MODULE

    # --------------------------------------------------------------
    # 3️⃣  Run the Flask commands **inside the project directory**
    # --------------------------------------------------------------
    old_cwd = os.getcwd()
    os.chdir(project_root)
    try:
        # Ensure the project root is on sys.path so imports work
        sys.path.insert(0, str(project_root))

        from flask.cli import main as flask_main

        def _flask(args: list[str]) -> None:
            saved_argv = sys.argv
            sys.argv = ["flask"] + args
            try:
                flask_main()
            finally:
                sys.argv = saved_argv

        # ---- 1️⃣  flask db init -----------------------------------------
        _log("Running: flask db init")
        _flask(["db", "init"])

        # ---- 2️⃣  flask db migrate -m "initial" -------------------------
        _log('Running: flask db migrate -m "initial"')
        _flask(["db", "migrate", "-m", "initial"])

        # ---- 3️⃣  flask db upgrade --------------------------------------
        _log("Running: flask db upgrade")
        _flask(["db", "upgrade"])

        _log("Flask‑Migrate steps completed successfully.")
    finally:
        # Clean up
        os.chdir(old_cwd)
        if str(project_root) in sys.path:
            sys.path.remove(str(project_root))


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    # --------------------------------------------------------------
    # 1️⃣  Get the latest release information from GitHub
    # --------------------------------------------------------------
    try:
        release = _download_json(GITHUB_API_RELEASE_URL)
    except (HTTPError, URLError) as exc:
        _log(f"Error contacting GitHub API: {exc}")
        sys.exit(1)

    download_url, tag = _pick_download_url(release)
    _log(f"Latest release tag: {tag}")

    # --------------------------------------------------------------
    # 2️⃣  Do everything inside a temporary directory (auto‑cleaned)
    # --------------------------------------------------------------
    with tempfile.TemporaryDirectory(prefix="dtm_") as tmp_dir:
        tmp_path = Path(tmp_dir)

        # ---- 2a – download the zip ---------------------------------
        zip_path = tmp_path / f"{REPO_NAME}-{tag}.zip"
        _download_file(download_url, zip_path)

        # ---- 2b – extract -------------------------------------------
        project_root = _extract_zip(zip_path, tmp_path)

        # --------------------------------------------------------------
        # 3️⃣  (optional) create a virtual‑env and install deps
        # --------------------------------------------------------------
        if CREATE_VENV:
            if getattr(sys, "frozen", False):
                # Frozen binary cannot create a venv – warn and fall back to the
                # interpreter that bundled Flask (the exe itself).
                _log(
                    "WARNING: Installer is frozen – virtual‑env creation is disabled. "
                    "Make sure the required packages are already bundled."
                )
                python_bin_dir = Path(sys.executable).parent
            else:
                python_bin_dir = _make_venv(project_root)
        else:
            python_bin_dir = Path(sys.executable).parent  # current interpreter

        # --------------------------------------------------------------
        # 4️⃣  Run the Flask‑Migrate commands
        # --------------------------------------------------------------
        _run_flask_cli(project_root, python_bin_dir)

        # --------------------------------------------------------------
        # 5️⃣  Copy the ready‑to‑run project out of the temp folder
        # --------------------------------------------------------------
        dest = Path.cwd() / f"{REPO_NAME}-{tag}"
        if dest.exists():
            _log(f"Removing previous folder {dest}")
            shutil.rmtree(dest)

        _log(f"Copying project to {dest}")
        shutil.copytree(project_root, dest)

        _log("\n=== DONE ===")
        _log(f"The project is now available at: {dest.resolve()}")
        _log("To start it:")
        _log(f"    cd {dest}")
        if CREATE_VENV:
            if os.name == "nt":
                _log(r"    .dtm_venv\Scripts\activate   # Windows")
            else:
                _log("    source .dtm_venv/bin/activate  # macOS / Linux")
        _log("    flask run")
        _log("Enjoy!")


if __name__ == "__main__":
    # ------------------------------------------------------------------
    # When the script runs as a frozen binary, we *must* disable venv
    # creation because the bootloader cannot act as a Python interpreter.
    # ------------------------------------------------------------------
    if getattr(sys, "frozen", False):
        _log("Running in frozen mode – virtual‑env creation is disabled.")
        CREATE_VENV = False

    main()
