# entry point — auto-creates venv, installs deps, then runs app inside it
import os
import subprocess
import sys

# path to local venv in project folder
VENV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv")
REQUIREMENTS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "requirements.txt"
)


def _ensure_venv():
    # if we are already inside the venv, just proceed
    venv_pyvenv = os.path.join(sys.prefix, "pyvenv.cfg")
    if os.path.isfile(venv_pyvenv) or sys.prefix.endswith(".venv"):
        return

    # create venv if it doesn't exist yet
    if not os.path.isdir(VENV_DIR):
        print("First run — creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])

    # pick the python executable inside the venv
    if sys.platform == "win32":
        venv_python = os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        venv_python = os.path.join(VENV_DIR, "bin", "python")

    # install requirements into the venv
    if os.path.isfile(REQUIREMENTS):
        print("Installing dependencies...")
        subprocess.check_call(
            [venv_python, "-m", "pip", "install", "-q", "--upgrade", "pip"]
        )
        subprocess.check_call(
            [venv_python, "-m", "pip", "install", "-q", "-r", REQUIREMENTS]
        )

    # re-launch this exact script using the venv python
    print("Starting app...\n")
    subprocess.run([venv_python] + sys.argv)
    sys.exit(0)


_ensure_venv()

from app import App

if __name__ == "__main__":
    App().run()
