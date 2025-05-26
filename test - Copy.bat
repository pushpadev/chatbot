@echo off
set "output_file=%~dp0system_info_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt"
set "output_file=%output_file: =0%"

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

echo Command completed successfully! Report saved to: %output_file%
echo You can find the report at: %output_file%
pause 