# CKN Daemon


### How to run

1. Create a python environment and install the requirements
```shell
python3 -m venv ./venv
source venv/bin/activate
pip3 install -r ckn/requirements.txt
```

2. Create uploads folder if it doesn't exist
```shell
mkdir uploads
```

2. Add the root ckn folder to PYTHONPATH
```shell
export PYTHONPATH='${PYTHONPATH}:<CKN_LOCATION>'
```

example:
```shell
export PYTHONPATH='${PYTHONPATH}:/home/exouser/git/system/ckn-edge'
```

Validate the python path by running:
```shell
echo $PYTHONPATH
```

