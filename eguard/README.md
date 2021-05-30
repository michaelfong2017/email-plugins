# eguard

## Prerequisite
### Python virtual environment

---

1. Have python3 installed.
2. Have pip for python3 installed.
3. Have python3 virtual environment installed.  

For instance, Ubuntu 18.04 ships with python3 and apt. Running the below command suffices to install pip for python3 and python3 virtual environment.
```
sudo apt update && sudo apt install python3-pip python3-venv -y
```
<br>

### Access right to all user directories for the current user

---

For instance, assume that `admin` is the current user and `/mailu/mail/` is the directory that contains all user directories. Assume that after running ```ls -la /mailu/mail/```, `man` is found to be the group of `/mailu/mail/` and its subdirectories.  

1. First, add `admin` to group `man`.
```
sudo usermod -aG man admin
```
2.  Second, verify.
```
groups admin
```
should show the newly added group `man`.  
However, 
```
id
```
does not show the newly added group `man` since this grouping has not taken effect yet. This command only shows the effective groups.  

3. Third, logout `admin` and then login `admin` again. For instance, if the mail server is hosted in an AWS EC2 instance, a viable way is to reboot the EC2 instance.

---

## Installation
1. Acquire the `eguard` folder from one of the Eguard distributors.

2. Put the entire `eguard` folder anywhere in the mail server that stores the user mail directories.

3. Configure eguard.toml.  
The entire `[Path]` section is required to be examined and configured.

4. Start / Restart EGuard by executing
```sh
python3 start.py
```
Stop EGuard by executing
```sh
python3 stop.py
```