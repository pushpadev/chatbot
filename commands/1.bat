@echo off
setlocal enabledelayedexpansion
set OUTFILE=args_output.txt
echo Arguments: > %OUTFILE%
set i=1
:loop
set arg=%~1
if "%~1"=="" goto end
echo Arg !i!: %~1 >> %OUTFILE%
shift
set /a i+=1
goto loop
:end
echo Done. >> %OUTFILE%