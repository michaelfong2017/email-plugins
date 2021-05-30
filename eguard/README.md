# eguard

## Prerequisite
1. Have python3 installed.
2. Have pip for python3 installed.
3. Have python3 virtual environment installed.  

For instance, Ubuntu 18.04 ships with python3 and apt. Running only the below command suffices to fulfill the prerequisite.  

```sudo apt update && sudo apt install python3-pip python3-venv -y```

## Installation
1. Acquire the `eguard` folder from one of the Eguard distributors.

2. Put the entire `eguard` folder anywhere in the mail server that stores the user mail directories.

3. Configure eguard.toml.  
The entire `[Path]` section is required to be examined and configured.

4. Start / Restart EGuard by executing
```sh
    python3 start.py
```
- Stop EGuard by executing
```sh
    python3 stop.py
```