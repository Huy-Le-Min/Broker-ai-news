@echo off
REM Automation 1 shortcut. Usage:  kw CPI GDP HPG VCB
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
py "%~dp0scripts\automation1_keyword.py" %*
