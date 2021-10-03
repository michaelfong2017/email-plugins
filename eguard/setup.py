import subprocess
import platform
ENV_NAME = '.env'
subprocess.run(['python3', '-m', 'venv', '.env'])
if platform.system() == 'Linux' or platform.system() == 'Darwin':
    subprocess.run([f"{ENV_NAME}/bin/pip3", "install", "mail-parser"]) # subprocess.run / subprocess.call (old) waits this subprocess to return before proceeding
    subprocess.run([f"{ENV_NAME}/bin/pip3", "install", "toml"])
    subprocess.run([f"{ENV_NAME}/bin/pip3", "install", "watchdog"])
    