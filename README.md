# Salary collector
Service to collect information about average salary for programmers from HeadHunter and SuperJob. 

## Install
Python3 should be already installed. Then use pip (or pip3, if there is a conflict with Python2) to install dependencies:
```
pip install -r requirements.txt
```
## Env Settings
Create `.env` from `.env.Example`
1. HH_CLIENT_ID - str, your application id from [HH API](https://dev.hh.ru/)
2. HH_CLIENT_SECRET - str, your secret from [HH API](https://dev.hh.ru/)
3. HH_CLIENT_TOKEN - Optional[str], your access token
4. SJ_CLIENT_ID - str, your id from [SuperJob API](https://api.superjob.ru/info/)
5. SJ_CLIENT_SECRET - str, your secret key from [SuperJob API](https://api.superjob.ru/info/)
6. SJ_EMAIL - str, your credential from [SuperJob](https://superjob.ru/)
7. SJ_PASSWORD - str, your credential from [SuperJob](https://superjob.ru/)

## Start
```
python main.py
```