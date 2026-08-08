import os
import subprocess
import sys

def build():
    print("Starting build process for PencilTrace...")
    
    # We use PyInstaller to build a one-folder distribution.
    # --windowed removes the console window.
    # --add-data includes the frontend and templates directories.
    
    backend_script = os.path.join("backend", "app.py")
    
    # Platform specific separator for add-data
    sep = ";" if sys.platform.startswith("win") else ":"
    
    command = [
        "pyinstaller",
        "--name=PencilTrace",
        "--onedir",
        "--windowed",
        f"--add-data=frontend{sep}frontend",
        f"--add-data=templates{sep}templates",
        f"--add-data=uploads{sep}uploads",
        backend_script
    ]
    
    print("Running command:", " ".join(command))
    result = subprocess.run(command)
    
    if result.returncode == 0:
        print("Build completed successfully. Check the 'dist/PencilTrace' folder.")
    else:
        print("Build failed.")

if __name__ == "__main__":
    build()
