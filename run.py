import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    app_path = Path(__file__).resolve().parent / "streamlit_app.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.headless", "true"],
        check=True,
    )
