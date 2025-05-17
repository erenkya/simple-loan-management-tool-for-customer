@echo off

REM Anaconda conda'nın tam yolu
set CONDA_PATH=anaconda_installed_path\anaconda3\Scripts\conda.exe
set STREAMLIT_PATH=anaconda_installed_path\anaconda3\Scripts\streamlit.exe

REM Ortamı aktif et
call "%CONDA_PATH%" activate acik_hesap_env

REM Proje klasörüne geç
cd /d "%~dp0"

REM Streamlit'i çalıştır
"%STREAMLIT_PATH%" run Acik_Hesap_Ekle.py

pause
