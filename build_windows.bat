cd src
python setup.py py2exe
mkdir dist\img
xcopy /S img dist\img
xcopy *.ttf dist
