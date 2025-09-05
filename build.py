#!/usr/bin/env python3
"""
Build script for MarketMiner Pro executable
Creates a standalone Windows executable with proper icon and configuration
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """Build the MarketMiner Pro executable using PyInstaller"""
    
    # Project paths
    project_root = Path(__file__).parent
    icon_path = project_root / "market_miner" / "assets" / "miner.png"
    main_script = project_root / "main.py"
    
    # Verify files exist
    if not icon_path.exists():
        print(f"ERROR: Icon file not found: {icon_path}")
        return 1
    
    if not main_script.exists():
        print(f"ERROR: Main script not found: {main_script}")
        return 1
    
    print("Building MarketMiner Pro executable...")
    print(f"Project root: {project_root}")
    print(f"Icon: {icon_path}")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                           # Single executable file
        "--windowed",                          # No console window
        f"--icon={icon_path}",                 # Application icon
        "--name=MarketMiner Pro",              # Executable name
        "--clean",                             # Clean cache
        "--noconfirm",                         # Overwrite without asking
        f"--distpath={project_root / 'dist'}", # Output directory
        f"--workpath={project_root / 'build'}",# Work directory
        str(main_script)                       # Main script
    ]
    
    try:
        print("Running PyInstaller...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            exe_path = project_root / "dist" / "MarketMiner Pro.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print("Build successful!")
                print(f"Executable created: {exe_path}")
                print(f"Size: {size_mb:.1f} MB")
                return 0
            else:
                print("Build completed but executable not found")
                return 1
        else:
            print(f"PyInstaller failed with return code {result.returncode}")
            print(f"Error output: {result.stderr}")
            return 1
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return 1
    except FileNotFoundError:
        print("PyInstaller not found. Install with: pip install pyinstaller")
        return 1

if __name__ == "__main__":
    sys.exit(main())