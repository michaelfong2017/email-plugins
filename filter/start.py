## Handle arguments
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', help='Debug level set from logging.WARNING to logging.DEBUG')
parser.add_argument('-s', '--sleep', help='Daemon process sleep duration (in seconds) between loops')
args = parser.parse_args()

# Store arguments in order to pass to the next script
debug_arg = ' --debug' if args.debug else ''
sleep_arg = f' --sleep {args.sleep}' if args.sleep else ''


import subprocess
import platform
import os
subprocess.run(['python3', '-m', 'venv', 'env'])
if platform.system() == 'Linux' or platform.system() == 'Darwin':
    subprocess.call("env/bin/pip3 install daemonize", shell=True) # subprocess.call waits this subprocess to return before proceeding
    subprocess.call("env/bin/pip3 install mail-parser", shell=True) # subprocess.call waits this subprocess to return before proceeding
    subprocess.Popen(["env/bin/python3", f"domain_history.py{debug_arg}{sleep_arg}"]) # subprocess.Popen does not wait this subprocess to return before proceeding
