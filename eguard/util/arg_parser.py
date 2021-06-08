# Handle arguments
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help='Debug level set from logging.WARNING to logging.DEBUG')
    parser.add_argument('-s', '--sleep', type=int, help='Daemon process sleep duration (in seconds) between loops')
    args = parser.parse_args()

    return args