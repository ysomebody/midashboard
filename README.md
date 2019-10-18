# MI dashbaord

This is MI dashbaord.

## Build
```
python3.7 -m venv env
env\Scripts\activate
pip install -r requirements_dev.txt
python setup.py sdist bdist_wheel
```

## Upload
```
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

## Install
```
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple midashboard-ysomebody
```
## Run
```
python -m midashboard
```

### Notes:
Make sure nijenkins is resolvable. (If not, probably need to add amer.corp.natinst.com to DNS suffix)
