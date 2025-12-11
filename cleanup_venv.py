"""
Script to analyze and reduce virtual environment size
"""
import os
import subprocess
import sys
from pathlib import Path

def get_venv_size(venv_path):
    """Calculate the size of the virtual environment"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(venv_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except (OSError, FileNotFoundError):
                pass
    return total_size

def get_installed_packages(venv_path):
    """Get list of installed packages in virtual environment"""
    pip_path = os.path.join(venv_path, 'Scripts', 'pip.exe')
    try:
        result = subprocess.run([pip_path, 'list'], 
                              capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')[2:]  # Skip header lines
        packages = []
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    packages.append((parts[0], parts[1]))
        return packages
    except subprocess.CalledProcessError as e:
        print(f"Error getting package list: {e}")
        return []

def identify_unnecessary_packages(packages):
    """Identify packages that are likely not needed for this project"""
    # Packages that seem unnecessary for a Django-based facial recognition library system
    unnecessary_packages = [
        'Flask', 'flask-cors', 'Flask-Limiter', 'Flask-Login', 
        'Flask-Mail', 'Flask-Principal', 'Flask-Security', 
        'Flask-SQLAlchemy', 'Flask-WTF', 'Werkzeug', 'Jinja2',
        'click', 'blinker', 'itsdangerous', 'WTForms',
        'SQLAlchemy', 'greenlet', 'cffi', 'pycparser'
    ]
    
    # Packages that are essential
    essential_packages = [
        'Django', 'opencv-python', 'face-recognition-models',
        'numpy', 'pillow'  # These are dependencies of OpenCV
    ]
    
    identified = []
    for package, version in packages:
        if package in unnecessary_packages:
            identified.append((package, version, 'Unnecessary'))
        elif package in essential_packages:
            identified.append((package, version, 'Essential'))
        else:
            identified.append((package, version, 'Uncertain'))
    
    return identified

def main():
    venv_path = '.venv'
    
    if not os.path.exists(venv_path):
        print(f"Virtual environment not found at {venv_path}")
        return
    
    print("Virtual Environment Size Analysis")
    print("=" * 40)
    
    # Get size
    size_bytes = get_venv_size(venv_path)
    size_mb = size_bytes / (1024 * 1024)
    print(f"Current size: {size_mb:.1f} MB")
    
    # Get packages
    packages = get_installed_packages(venv_path)
    print(f"\nTotal packages installed: {len(packages)}")
    
    # Identify unnecessary packages
    analysis = identify_unnecessary_packages(packages)
    
    print("\nPackage Analysis:")
    print("-" * 50)
    print(f"{'Package':<25} {'Version':<15} {'Status':<15}")
    print("-" * 50)
    
    unnecessary_count = 0
    for package, version, status in analysis:
        print(f"{package:<25} {version:<15} {status:<15}")
        if status == 'Unnecessary':
            unnecessary_count += 1
    
    print("-" * 50)
    print(f"Unnecessary packages: {unnecessary_count}")
    
    # Calculate potential savings
    # This is a rough estimate - removing Flask ecosystem could save ~50-100MB
    potential_savings = unnecessary_count * 5  # Estimate 5MB per package
    print(f"Potential savings: {potential_savings}-{-potential_savings*2} MB")
    
    print("\nRecommendation:")
    print("-" * 20)
    if unnecessary_count > 0:
        print("You can reduce the size of your virtual environment by:")
        print("1. Running the reduce_venv_size.bat script")
        print("2. Or manually removing unnecessary packages:")
        print("   .venv\\Scripts\\pip.exe uninstall Flask Flask-* WTForms SQLAlchemy greenlet cffi pycparser")
    else:
        print("Your virtual environment appears to be relatively optimized already.")

if __name__ == "__main__":
    main()