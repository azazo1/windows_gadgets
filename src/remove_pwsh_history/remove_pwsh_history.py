import os
from pathlib import Path

appdata = Path(os.getenv("APPDATA"))
pwsh_hs_dir = appdata / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine"

def remove_history():
    if pwsh_hs_dir.exists():
        for f in pwsh_hs_dir.iterdir():
            if f.name.endswith("_history.txt"):
                f.unlink()
                print(f"Removing {f}")

def main():
    os.chdir(Path(__file__).parent)
    remove_history()