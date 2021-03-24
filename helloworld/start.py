import subprocess
import platform
import os
subprocess.run(['python3', '-m', 'venv', 'env'])
if platform.system() == 'Linux' or platform.system() == 'Darwin':
    subprocess.run("env/bin/python3 -m pip install --upgrade pip", shell=True) # subprocess.run / subprocess.call (old) waits this subprocess to return before proceeding
    subprocess.run("env/bin/pip3 install grpcio grpcio-tools", shell=True) # subprocess.run / subprocess.call (old) waits this subprocess to return before proceeding
    subprocess.Popen(f"env/bin/python3 greeter_server.py", shell=True) # subprocess.Popen does not wait this subprocess to return before proceeding
