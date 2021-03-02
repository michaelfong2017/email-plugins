import subprocess
import platform
import os
subprocess.run(['python3', '-m', 'venv', 'env'])
if platform.system() == 'Linux' or platform.system() == 'Darwin':
    subprocess.call("env/bin/pip3 install daemonize", shell=True) # subprocess.call waits this subprocess to return before proceeding
    subprocess.call("env/bin/pip3 install mail-parser", shell=True) # subprocess.call waits this subprocess to return before proceeding
    subprocess.Popen(["env/bin/python3", "domain_history.py"]) # subprocess.Popen does not wait this subprocess to return before proceeding

elif platform.system() == 'Windows':
    subprocess.call("env\Scripts\pip3 install daemonize", shell=True) # subprocess.call waits this subprocess to return before proceeding
    subprocess.call("env\Scripts\pip3 install mail-parser", shell=True) # subprocess.call waits this subprocess to return before proceeding
    subprocess.Popen(["env\Scripts\python3", "domain_history.py"]) # subprocess.Popen does not wait this subprocess to return before proceeding