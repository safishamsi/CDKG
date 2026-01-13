@echo off
echo ==================================
echo CDKG RAG System - Installation
echo ==================================
echo.

echo Checking Python version...
python --version

echo.
echo Creating virtual environment...
python -m venv venv

echo.
echo Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ==================================
echo Installation complete!
echo ==================================
echo.
echo Next steps:
echo 1. Activate virtual environment:
echo    venv\Scripts\activate.bat
echo.
echo 2. Copy .env.template to .env and configure:
echo    copy .env.template .env
echo    (Then edit .env with your credentials)
echo.
echo 3. Copy your cdl_db data:
echo    xcopy /E /I \path\to\cdl_db data\cdl_db
echo.
echo 4. Run setup validation:
echo    python setup.py
echo.
echo 5. Run the pipeline:
echo    python run_pipeline.py
echo.
pause
