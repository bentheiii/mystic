python -m pip install "cryptography>=2.2"
@echo off
IF errorlevel 1 (
	echo ERROR
) ELSE (
	echo on
	python -m pip install "pyperclip>=1.6"
	@echo off
	IF errorlevel 1 echo SOME OPTIONAL PACKAGES WERE NOT INSTALLED
	echo DONE!
)
pause