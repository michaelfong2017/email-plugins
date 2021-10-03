import subprocess
import platform
## Handle arguments
import argparse
parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-r', '--restart', action='store_true', help='''
If True:
    Send "pkill -f eguard.py" to kill the current eguard process and then start a new eguard process.

If False:
    Start fail if eguard is already started in the same tmux session.

''')
parser.add_argument('-d', '--debug', action='store_true', help='Whether to set debug level from logging.CRITICAL to logging.DEBUG')
parser.add_argument('-s', '--sleep', type=int, help='Background process sleep duration (in seconds) between loops')
args = parser.parse_args()

# Store arguments in order to pass to the next script
restart = args.restart
debug_arg = ' --debug' if args.debug else ''
sleep_arg = f' --sleep {args.sleep}' if args.sleep else ''

ENV_NAME = '.env'
PY_FILEPATH = 'src/eguard.py'
if platform.system() == 'Linux' or platform.system() == 'Darwin':
    if restart:
        subprocess.run(['pkill', '-f', 'eguard.py'])
    subprocess.Popen(['tmux', 'new', '-d', '-s', 'eguard']) # subprocess.Popen does not wait this subprocess to return before proceeding
    subprocess.Popen(['tmux', 'send-keys', 'C-u', f"{ENV_NAME}/bin/python3 {PY_FILEPATH}{debug_arg}{sleep_arg}", 'C-m'])
