@echo off
FOR /F "tokens=1-4 delims=/ " %%I IN ('DATE /t') DO SET thedate=%%L%%K%%J
set app_name=scummbler

E:\Utils\misc\asciidoc-8.6.0\asciidoc.py -a toc docs\scummbler_manual.txt

E:\Apps\Programming\Python2.5\python.exe setup.py py2exe %1 --bundle 2
rd build /S /Q
rename dist %app_name%
mkdir %app_name%\docs
copy docs\%app_name%_manual.html %app_name%\docs
copy docs\lgpl.txt %app_name%\docs

E:\Utils\Misc\7-Zip\7z.exe a -tzip -mx9 -r %app_name%_bin_%thedate%.zip %app_name%
rd %app_name% /s /q

mkdir %app_name%
copy *.py %app_name%
copy *.bat %app_name%
copy lgpl.txt %app_name%
mkdir %app_name%\docs
copy docs\*.html %app_name%\docs

E:\Utils\Misc\7-Zip\7z.exe a -tzip -mx9 -r %app_name%_src_%thedate%.zip %app_name%
rd %app_name% /s /q