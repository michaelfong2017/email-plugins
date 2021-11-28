import subprocess
import argparse
import sys


def main():
    ENV_NAME = "venv"
    MODULE_NAME = "eguard"

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter, add_help=False
    )

    # Do not add the required positional argument 'command'
    # in the case -h or --help flag exists.
    # Also ensure that an error is raised to ask for the required
    # positional argument 'command' in the case 'python3 main.py'.
    if not (len(sys.argv) > 1 and ("-h" in sys.argv or "--help" in sys.argv)):
        parser.add_argument("command", choices={"start", "restart", "stop", "fetchandbuild", "updatebanners"})

    parser.add_argument("-h", "--help", action="store_true")
    args, other = parser.parse_known_args()

    """
    Since no error is raised above, either -h/--help option is present
    or "command" is valid.
    """
    if args.help:
        subprocess.Popen(
            [f"{ENV_NAME}/bin/python", "-m", f"src.{MODULE_NAME}", "--help"]
        )
        return

    # Merge user configuration file and default configuration file and write
    # to a single file for later processing.
    with open("config/eguard-merged.yml", "w") as f:
        subprocess.call(
            [
                "yq",
                "eval-all",
                ". as $item ireduce ({}; . * $item )",
                "config/eguard-default.yml",
                "config/eguard.yml",
            ],
            stdout=f
        )

    # Start a new tmux session or reuse the same tmux session with the given name.
    # subprocess.Popen does not wait this subprocess to return before proceeding
    subprocess.Popen(["tmux", "new", "-d", "-s", "eguard"])

    if args.command == "start":
        subprocess.Popen(
            [
                "tmux",
                "send-keys",
                "C-u",
                f"{ENV_NAME}/bin/python -m src.{MODULE_NAME} {args.command} {(' ').join(other)}",
                "C-m",
            ]
        )

    elif args.command == "restart":
        subprocess.Popen(
            [
                "tmux",
                "send-keys",
                "C-c",
                "C-m",  # This 'return' is needed because for some reason, the first character does not have effect without this.
                "C-u",
                f"{ENV_NAME}/bin/python -m src.{MODULE_NAME} {args.command} {(' ').join(other)}",
                "C-m",
            ]
        )

    elif args.command == "stop":
        subprocess.Popen(["tmux", "send-keys", "C-c"])

    elif args.command == "fetchandbuild":
        subprocess.Popen(
            [
                "tmux",
                "send-keys",
                "C-c",
                "C-m",  # This 'return' is needed because for some reason, the first character does not have effect without this.
                "C-u",
                f"{ENV_NAME}/bin/python -m src.{MODULE_NAME} {args.command} {(' ').join(other)}",
                "C-m",
            ]
        )

    elif args.command == "updatebanners":
        subprocess.Popen(
            [
                "tmux",
                "send-keys",
                "C-c",
                "C-m",  # This 'return' is needed because for some reason, the first character does not have effect without this.
                "C-u",
                f"{ENV_NAME}/bin/python -m src.{MODULE_NAME} {args.command} {(' ').join(other)}",
                "C-m",
            ]
        )


if __name__ == "__main__":
    main()
