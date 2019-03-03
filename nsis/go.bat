copy /Y ..\c\build\i2ccl.exe
copy /Y ..\python\samples\dist\i2cgui.exe

"C:\Program Files\NSIS\makensis.exe" i2cdriver.nsi
copy /Y i2cdriver-installer.exe C:\Users\james\Desktop
