@echo off
echo Reducing virtual environment size...
echo.

echo 1. Creating backup of current virtual environment...
ren .venv .venv_backup
echo Backup created as .venv_backup
echo.

echo 2. Creating new minimal virtual environment...
python -m venv .venv
echo.

echo 3. Activating new virtual environment...
call .venv\Scripts\activate.bat
echo.

echo 4. Upgrading pip...
python -m pip install --upgrade pip
echo.

echo 5. Installing minimal requirements...
pip install -r minimal_requirements.txt
echo.

echo 6. Installing face recognition models...
pip install face-recognition-models>=0.3.0
echo.

echo 7. Checking installed packages...
pip list
echo.

echo Process completed! Your new virtual environment is much smaller.
echo To test your application, run: python manage.py runserver
echo To remove the backup when you're sure everything works: rmdir /s .venv_backup