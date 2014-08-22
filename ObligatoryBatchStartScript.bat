:: Disable output from commands
ECHO off
CLS

:: Check if python.exe is on the system path
:: If it is unavailable, link directly to python.exe
:: Otherwise, invoke the interpreter normally
IF %ERRORLEVEL% NEQ 0 ECHO python 
 C:/python27/python.exe main.py
ELSE
 python main.py