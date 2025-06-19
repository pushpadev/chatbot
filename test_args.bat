@echo off
REM Write all arguments to args_output.txt
setlocal enabledelayedexpansion
set OUTFILE=args_output.txt
echo Arguments: > %OUTFILE%
set i=1
:loop
set arg=%~%i
if "%~%i"=="" goto end
set arg=!%i!
echo Arg %i%: !arg! >> %OUTFILE%
set /a i+=1
goto loop
:end
echo Done. >> %OUTFILE% 