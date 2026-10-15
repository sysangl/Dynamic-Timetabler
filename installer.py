#!/usr/bin/env python3
"""
installer.py

* Downloads the latest release of sysangl/Dynamic‑Timetabler from GitHub
* Extracts the zipball into a temporary folder
* (optionally) creates a virtual‑env inside the extracted project
* Detects the proper Flask entry point
* Runs the three Flask‑Migrate commands:
        flask db init
        flask db migrate -m "initial"
        flask db upgrade
* Copies the ready‑to‑run source tree to the current directory

Works both as a normal .py script and as a frozen executable built
with PyInstaller.
"""

# ----------------------------------------------------------------------
# 1️⃣  Dummy imports – force PyInstaller to bundle these modules.
# ----------------------------------------------------------------------
if False:          # pragma: no cover
    import flask                  # Flask core
    import flask_migrate          # Flask‑Migrate extension
    import flask_sqlalchemy       # Flask‑SQLAlchemy extension
    import pytz                   # timezone handling (used by the app)
    import sqlalchemy            # SQLAlchemy ORM
    import toml                   # reading *.toml* files
    import logging.config         # required sub‑module (was missing before)

# ----------------------------------------------------------------------
# 2️⃣  Standard‑library imports only (keeps the frozen exe small)
# ----------------------------------------------------------------------
import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
import importlib
from pathlib import Path
from urllib.error import HTTPError, URLError
import urllib.request

# ----------------------------------------------------------------------
# 3️⃣  User‑configurable settings
# ----------------------------------------------------------------------
REPO_OWNER = "sysangl"
REPO_NAME = "Dynamic-Timetabler"

# If you know the exact file that should be used as FLASK_APP,
# set it here.  Leave empty for automatic detection (run.py,
# app:create_app(), ...).
FLASK_APP_MODULE = ""          # e.g. "run.py" or "app:create_app()"

# When True the installer will create an isolated venv inside
# the extracted project and run `pip install -r requirements.txt`.
# The frozen binary cannot create a venv (it would recurse), so the flag
# is automatically disabled when the script runs frozen.
CREATE_VENV = True

# ----------------------------------------------------------------------
# 4️⃣  Constants (no need to edit)
# ----------------------------------------------------------------------
GITHUB_API_RELEASE_URL = (
    f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
)

# ----------------------------------------------------------------------
# 5️⃣  Tiny logger – ASCII only
# ----------------------------------------------------------------------
def _log(msg: str) -> None:
    """Print a message using only ASCII characters."""
    print(msg, flush=True)

# ----------------------------------------------------------------------
# 6️⃣  Network helpers
# ----------------------------------------------------------------------
def _download_json(url: str) -> dict:
    """GET a JSON document (GitHub API)."""
    _log(f"Fetching JSON from {url} ...")
    req = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github.v3+json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _pick_download_url(release: dict) -> tuple[str, str]:
    """
    Return (download_url, tag_name).
    Preference order:
        1) first asset ending with ".zip"
        2) otherwise the generic zipball_url supplied by GitHub
    """
    tag = release.get("tag_name", "unknown")
    for asset in release.get("assets", []):
        name = asset.get("name", "")
        if name.lower().endswith(".zip"):
            url = asset.get("browser_download_url")
            if url:
                _log(f"Found zip asset '{name}' -> {url}")
                return url, tag

    zipball = release.get("zipball_url")
    if zipball:
        _log("No .zip asset found - using generic zipball_url")
        return zipball, tag

    raise RuntimeError("Could not locate a downloadable .zip for the latest release.")

def _download_file(url: str, dest: Path) -> None:
    """Stream‑download *url* into *dest* and show a simple ASCII progress bar."""
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
                print(f"\r  {downloaded}/{total} bytes ({pct:5.1f} %) ", end="", flush=True)
        print()   # newline after progress

# ----------------------------------------------------------------------
# 7️⃣  Archive handling
# ----------------------------------------------------------------------
def _extract_zip(zip_path: Path, out_dir: Path) -> Path:
    """
    Extract the zip into *out_dir*.  GitHub release zips always contain a
    single top‑level folder.  Returns the path of that folder.
    """
    _log(f"Extracting {zip_path} -> {out_dir}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out_dir)

    tops = [p for p in out_dir.iterdir() if p.is_dir()]
    if len(tops) != 1:
        raise RuntimeError(
            f"Expected exactly one top-level directory in the zip, found {len(tops)}."
        )
    _log(f"Project source root is {tops[0]}")
    return tops[0]

# ----------------------------------------------------------------------
# 8️⃣  Virtual‑env handling (optional)
# ----------------------------------------------------------------------
def _make_venv(project_root: Path) -> Path:
    """
    Create a venv at <project_root>/.dtm_venv,
    install the project's requirements (if any) and return the directory
    that contains the interpreter (bin/Scripts).
    """
    venv_path = project_root / ".dtm_venv"
    _log(f"Creating virtual env at {venv_path}")
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)

    if os.name == "nt":
        bin_dir = venv_path / "Scripts"
        pip_exe = bin_dir / "pip.exe"
    else:
        bin_dir = venv_path / "bin"
        pip_exe = bin_dir / "pip"

    req_file = project_root / "requirements.txt"
    if req_file.is_file():
        _log("Installing project requirements ...")
        subprocess.run([str(pip_exe), "install", "-r", str(req_file)], check=True)
    else:
        _log("No requirements.txt found - skipping pip install.")
    return bin_dir

# ----------------------------------------------------------------------
# 9️⃣  Detect the Flask entry‑point (run.py, app:create_app(), …)
# ----------------------------------------------------------------------
def _detect_flask_app(project_root: Path) -> str:
    global FLASK_APP_MODULE
    if FLASK_APP_MODULE:
        return FLASK_APP_MODULE

    if (project_root / "run.py").is_file():
        FLASK_APP_MODULE = "run.py"
    elif (project_root / "app.py").is_file():
        FLASK_APP_MODULE = "app:create_app()"
    else:
        FLASK_APP_MODULE = "app:create_app()"
    return FLASK_APP_MODULE

# ----------------------------------------------------------------------
# 🔟  Run a Flask CLI command **directly** (no subprocess)
# ----------------------------------------------------------------------
def _run_flask_cli(project_root: Path, args: list[str]) -> None:
    """
    Execute ``flask <args...>`` by calling Flask's internal CLI entry point.
    The function catches the ``SystemExit`` that Flask normally raises so
    the installer can continue to the next command.
    """
    # Save current interpreter state
    old_cwd = os.getcwd()
    old_path = list(sys.path)

    # --------------------------------------------------------------
    # 1. Switch to the extracted project directory and make it importable
    # --------------------------------------------------------------
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))

    # --------------------------------------------------------------
    # 2. Tell Flask which app to load
    # --------------------------------------------------------------
    os.environ["FLASK_APP"] = FLASK_APP_MODULE

    # --------------------------------------------------------------
    # 3. Call Flask's CLI entry point
    # --------------------------------------------------------------
    from flask.cli import main as flask_main

    saved_argv = sys.argv
    sys.argv = ["flask"] + args
    try:
        _log(f"Running Flask command: {' '.join(args)}")
        flask_main()
    except SystemExit as exc:
        # Flask calls sys.exit() after a successful command (code == 0).
        # We ignore a clean exit but re‑raise on error.
        if exc.code != 0:
            raise RuntimeError(f"Flask command {' '.join(args)} failed (exit {exc.code})")
    finally:
        # Restore interpreter state
        sys.argv = saved_argv
        os.chdir(old_cwd)
        sys.path = old_path

# ----------------------------------------------------------------------
# 1️⃣1️⃣  Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    # --------------------------------------------------------------
    # 1. Get the latest release info from GitHub
    # --------------------------------------------------------------
    try:
        release = _download_json(GITHUB_API_RELEASE_URL)
    except (HTTPError, URLError) as exc:
        _log(f"Error contacting GitHub API: {exc}")
        sys.exit(1)

    download_url, tag = _pick_download_url(release)
    _log(f"Latest release tag: {tag}")

    # --------------------------------------------------------------
    # 2. Work inside a temporary directory (auto‑cleaned)
    # --------------------------------------------------------------
    with tempfile.TemporaryDirectory(prefix="dtm_") as tmp_dir:
        tmp_path = Path(tmp_dir)

        # 2a - download the zip
        zip_path = tmp_path / f"{REPO_NAME}-{tag}.zip"
        _download_file(download_url, zip_path)

        # 2b - extract
        project_root = _extract_zip(zip_path, tmp_path)

        # --------------------------------------------------------------
        # 3. (optional) create a venv and install requirements
        # --------------------------------------------------------------
        if CREATE_VENV:
            if getattr(sys, "frozen", False):
                _log(
                    "WARNING: Installer is frozen - virtual env creation disabled. "
                    "All needed packages must already be bundled."
                )
                # No venv – just continue; Flask and its extensions are already
                # inside the frozen binary thanks to the dummy‑import block.
            else:
                _make_venv(project_root)

        # --------------------------------------------------------------
        # 4. Detect FLASK_APP (must be set before any Flask command)
        # --------------------------------------------------------------
        _detect_flask_app(project_root)

        # --------------------------------------------------------------
        # 5. Run the three Flask‑Migrate commands
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # 6. Copy the ready‑to‑run project out of the temp folder
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
        _log( "    flask db init")
        _log( "    flask db migrate -m 'new db'")
        _log( "    flask db upgrade")
        if CREATE_VENV:
            if os.name == "nt":
                _log(r"    .dtm_venv\Scripts\activate   # Windows")
            else:
                _log("    source .dtm_venv/bin/activate  # macOS / Linux")
        _log("    python run.py")


if __name__ == "__main__":
    # When the script runs as a frozen exe we cannot safely create a venv,
    # because that would cause the recursive behaviour we observed before.
    if getattr(sys, "frozen", False):
        _log("Running in frozen mode - virtual env creation is disabled.")
        CREATE_VENV = False
    main()
