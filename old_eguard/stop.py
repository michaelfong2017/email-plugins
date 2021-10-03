import subprocess
import platform
import os
if platform.system() == 'Linux' or platform.system() == 'Darwin':
    subprocess.run("kill -9 `pgrep -f domain_history.py`", shell=True)
    subprocess.run("rm .process.pid", shell=True)
