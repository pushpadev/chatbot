@echo off
REM Get the directory where this batch file is located
set "batch_dir=%~dp0"
set "output_file=%batch_dir%system_info_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt"
set "output_file=%output_file: =0%"

REM Check if we can write to the directory
if not exist "%batch_dir%" (
    echo Error: Cannot access directory: %batch_dir%
    pause
    exit /b 1
)

echo Creating report in: %batch_dir%
echo =============================================== > "%output_file%"
echo System Information Report - %date% %time% >> "%output_file%"
echo =============================================== >> "%output_file%"
echo. >> "%output_file%"

echo System Information: >> "%output_file%"
echo ================= >> "%output_file%"
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type" /C:"Total Physical Memory" >> "%output_file%"
echo. >> "%output_file%"

echo Network Information: >> "%output_file%"
echo ================== >> "%output_file%"
ipconfig | findstr "IPv4" >> "%output_file%"
echo. >> "%output_file%"

echo =============================================== >> "%output_file%"
echo Report generated successfully! >> "%output_file%"
echo =============================================== >> "%output_file%"

if exist "%output_file%" (
    echo.
    echo Command completed successfully!
    echo Report saved to: %output_file%
    echo Full path: %batch_dir%%output_file%
) else (
    echo Error: Failed to create report file
)

pause 