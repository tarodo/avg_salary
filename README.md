# Salary collector
Service to collect information about average salary for programmers from [HeadHunter](https://hh.ru/) and [SuperJob](https://superjob.ru/). 

## Install
Python3 should be already installed. Then use pip (or pip3, if there is a conflict with Python2) to install dependencies:
```
pip install -r requirements.txt
```
## Env Settings
Create `.env` from `.env.Example`
1. SJ_SECRET - str, your secret key from [SuperJob API](https://api.superjob.ru/info/)

## Start
```
python main.py
```