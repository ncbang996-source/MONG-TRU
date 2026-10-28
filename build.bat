@echo off
REM Tu build tren may Windows (can Python 3.12): bam dup file nay
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm VE_MONGTRU.spec
echo.
echo Xong: dist\VE_MONGTRU.exe
pause
