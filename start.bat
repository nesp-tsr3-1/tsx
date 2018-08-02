@echo off

set PYTHON_HOME=C:\Python27

if not defined in_subprocess (cmd /k set in_subprocess=y ^& %0 %*) & exit)

set PATH=%PATH%;%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%CD%\env\lib\python2.7\site-packages\osgeo

if not exist env (
	pip install virtualenv
	virtualenv env
	call env\Scripts\activate
	python setup\install_windows_deps.py
)

call env\Scripts\activate
call pip install -r requirements.txt

rem Add MySQL to PATH
call python setup\mysql_path.py tmp.bat
tmp.bat
del tmp.bat
