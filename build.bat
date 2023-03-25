copy /Y ".\script\transcribe.py" ".\venv\Lib\site-packages\whisper\transcribe.py"

pyinstaller --noconfirm --clean .\config\main.spec

Xcopy /Y /E /I .\venv\Lib\site-packages\whisper .\dist\Whisper-API\whisper /EXCLUDE:.\exclude.txt
Xcopy /Y /E /I .\model .\dist\Whisper-API\model 

copy /Y ".\script\run.bat" ".\dist\Whisper-API\run.bat"
