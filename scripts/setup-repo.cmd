@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-repo.ps1" %*
exit /b %ERRORLEVEL%
