@echo off
rem ---------------------------------------------------------------------------
rem Dawn and Dusk: placeholder flags for the four new ideology groups.
rem (The other four reuse vanilla keys, so vanilla already has their flags.)
rem
rem HOI4 looks for one flag per country per ruling ideology, for example
rem gfx/flags/SAF_social_democrat.tga. Until real flags exist, this copies
rem each vanilla base flag (SAF.tga) under every new ideology name.
rem
rem The copies are made in YOUR local mod folder only and are ignored by git,
rem because they are Paradox art and the repository is public.
rem
rem Usage: double-click, or run with your HOI4 install folder as argument:
rem   make_placeholder_flags.bat "D:\SteamLibrary\steamapps\common\Hearts of Iron IV"
rem ---------------------------------------------------------------------------
setlocal

set "HOI4=C:\Steam\steamapps\common\Hearts of Iron IV"
if not "%~1"=="" set "HOI4=%~1"
set "MOD=%~dp0.."

if not exist "%HOI4%\gfx\flags" (
	echo Could not find "%HOI4%\gfx\flags".
	echo Run this again with your HOI4 install folder as the first argument.
	pause
	exit /b 1
)

echo Making placeholder flags from "%HOI4%" ...
call :copyset ""
call :copyset "\medium"
call :copyset "\small"
echo Done.
pause
exit /b 0

:copyset
set "SRC=%HOI4%\gfx\flags%~1"
set "DST=%MOD%\gfx\flags%~1"
if not exist "%DST%" mkdir "%DST%"
for %%F in ("%SRC%\???.tga") do (
	for %%I in (socialist social_democrat conservative authoritarian_democrat) do (
		if not exist "%DST%\%%~nF_%%I.tga" copy /Y "%%F" "%DST%\%%~nF_%%I.tga" >nul
	)
)
exit /b 0
