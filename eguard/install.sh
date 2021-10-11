env_name="venv"
python3 -m venv $env_name
$env_name/bin/pip install --upgrade pip
$env_name/bin/pip install wheel
$env_name/bin/pip install black
$env_name/bin/pip install ipykernel
$env_name/bin/pip install typer
$env_name/bin/pip install dependency-injector
$env_name/bin/pip install pytz
$env_name/bin/pip install pyyaml
$env_name/bin/pip install watchdog
$env_name/bin/pip install mail-parser

touch config/eguard.yml