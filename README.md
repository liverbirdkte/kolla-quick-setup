# kolla-quick-setup

Script for quickly setting up a kolla deployment.

Only Python3 is supported.

## Usage:

Firstly create a virtual environment, and activate:
```
python3 -m venv {{env_path}}
source {{env_path}}/bin/activate
```

Install python dependencies:
```
pip3 install -r requirements.txt
```

Execute the script with your config file, the scripts come with
an example conf you could consult:
```
python3 scripts/deploy.py --config-file example.ini
```
