# eguard

## Prerequisite
<br>

### Python virtual environment
---
1. Have python3 installed.
2. Have pip for python3 installed.
3. Have python3 virtual environment installed.  

For instance, Ubuntu 18.04 ships with python3 and apt. Running the below command suffices to install pip for python3 and python3 virtual environment.
```bash
sudo apt update && sudo apt install python3-pip python3-venv -y

```

<br>

### tmux command installed
---
Use tmux session for running eguard in the background having the ability of attaching/detaching the window anytime.

For Ubuntu and Debian,
```bash
sudo apt install tmux -y

```

For CentOS,
```bash
sudo yum install tmux -y

```

<br>

### yq command installed
---
Use yq for merging yml files.
```bash
YQ_VERSION=v4.13.3
YQ_BINARY=yq_linux_amd64
wget https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/${YQ_BINARY}.tar.gz -O - |\
tar xz && sudo mv ${YQ_BINARY} /usr/bin/yq

```

<br>

### Access right to all user directories for the current user who executes eguard (ignore this if no permission problem arises)
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

<br>

## Installation
1. Acquire the `eguard` folder from one of the eguard distributors.

2. Put the entire `eguard` folder anywhere in the mail server that stores the user mail directories.

3. Run below:
```bash
bash install.sh

```

<br>

## Configuration
Admin should configure only the file `eguard.yml` by reading `eguard-default.yml`
and figuring out what configurations should be overriden by `eguard.yml`.

### Configure paths
Essentially, configurations under the first level key `path` have to be configured
because the paths to different mail directories and even mailbox structure vary
from mail server to mail server. 

Use
```
tree -a <dir>
``` 
command to examine the directory structure of the machine and find the correct paths.


If paths are incorrectly configured, FileNotFoundError can be raised.

---

Beware of software update (if any) that changes `eguard-default.yml`. User configurations
may have to be rechecked.

1. Configure `eguard.yml`. Don't manually edit `eguard-default.yml` and the `eguard-merged.yml`, which are to be generated in the next step.

2. Start/Restart eguard every time `eguard.yml` has changed due to user configuration or `eguard-default.yml` has changed due to a software update, in order to generate `eguard-merged.yml` which is the only configuration file to be processed.

<br>

### Configure banners
Currently, it is needed to configure the target banners and the old banners directly in the source code `src/eguard/mutable_email.py`. Old banners will be replaced with target banners when email status is modified or when `eguard command` is called to update banners.

#### Example 1
For example, assume that below is a snippet of mutable_email.py.

```python
OLD_UNKNOWN_SUBJECT_BANNER = """[🟠🟠FROM NEW SENDER🟠🟠] """
UNKNOWN_SUBJECT_BANNER = OLD_UNKNOWN_SUBJECT_BANNER
```

In order to change the banner wording, one can change as follows.

```python
OLD_UNKNOWN_SUBJECT_BANNER = """[🟠🟠FROM NEW SENDER🟠🟠] """
UNKNOWN_SUBJECT_BANNER = """[⚠️⚠️FROM NEW SENDER⚠️⚠️] """
```

#### Example 2
For example, assume that below is a snippet of mutable_email.py.

```python
OLD_UNKNOWN_SUBJECT_BANNER = """[🟠🟠FROM NEW SENDER🟠🟠] """
UNKNOWN_SUBJECT_BANNER = """[⚠️⚠️FROM NEW SENDER⚠️⚠️] 
```

In order to change the banner wording, one should first run the eguard `updatebanners` command to ensure that `"""[🟠🟠FROM NEW SENDER🟠🟠] """` does not exist anymore in all emails of all users, before amending mutable_email.py.

1. 
```bash
python3 main.py updatebanners

```

2. Then, amend mutable_email.py as in Example 1.
```python
OLD_UNKNOWN_SUBJECT_BANNER = """[⚠️⚠️FROM NEW SENDER⚠️⚠️] """
UNKNOWN_SUBJECT_BANNER = """[❗❗FROM NEW SENDER❗❗] """
```

<br>

## Run eguard
- When new user email is registered or a user mail directory is removed, eguard has to be restarted. Reconfiguration of user
directory paths before restart may be needed.

### Start eguard
```bash
python3 main.py start

```

### Restart eguard
```bash
python3 main.py restart

```

### Stop eguard
```bash
python3 main.py stop

```

### Fetch and build known sender lists and junk list
Fetch existing unseen mail directory and junk mail directory of every user to build a known sender list for every user and build a common junk sender list for all users. This does not remove any existing records in the known sender lists and the junk sender list, if exist.

```bash
python3 main.py fetchandbuild

```

### Update all email banners (add, remove and replace)
Accomplish two tasks. First, add/remove banners depending on the current state of the database storing the known sender lists and the junk sender list. Second, update the wording and appearance of existing banners as configured in mutable_email.py. Banners with prefix OLD_ will be replaced with banners without prefix OLD_ correspondingly. This is applied to each email for every user.

```bash
python3 main.py updatebanners

```

### Get command help
```bash
python3 main.py -h

```

### Verify that eguard is / is not running
```bash
ps aux | grep src.eguard
```

### Options
Options:
  -d, --debug                     Debug level set from logging.ERROR to
                                  logging.DEBUG.
  -m, --monitor-user-dir          Monitor file system events of each user mail
                                  directory.

- For development, the command is usually:
```bash
python3 main.py restart --debug
```

## View the tmux session inside which eguard is run
Eguard is designed to run inside a tmux session which is automatically created.
Sometimes it can be convenient to attach to it and inspect.

### To list all tmux sessions in the host machine
```bash
tmux list-sessions
```
- A tmux session named 'eguard' should be found if eguard is run correctly.

### To attach to a tmux session

implicitly,
```bash
tmux attach
```

or

explicitly,
```bash
tmux attach -t eguard
```

### To detach from a tmux session
Press Ctrl-B (for mac: ^-B), release both keys and then press D.

### To go back to view the lines of text which have scrolled off the screen
The solution is to use tmux specific controls to access its own scrollback buffer: Press Ctrl-B, then [ to enter copy mode, use Down/Up arrows or PageDown and PageUp keys, q or Enter to exit copy mode.

## Working with eguard database
Admin should connect to eguard.db inside this directory to create, read, update and delete
records of known sender emails and junk sender emails.

For the working environment, VSCode together with VSCode extension `Remote - SSH` and VSCode extension `SQLite` is highly recommended.

example.sql contains examples of common database tasks that admin has to accomplish.

## Log
This directory contains three log files that record logs in different logging level.
Pass the --debug/-d flag to main.py to enable full logging.
