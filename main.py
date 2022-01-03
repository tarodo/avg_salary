import os

import requests
from dotenv import load_dotenv


def get_access_token(client_id: str, client_secret: str):
    url_auth = "https://hh.ru/oauth/token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    request_body = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(url_auth, data=request_body, headers=headers)
    try:
        response.raise_for_status()
        return response.json()["access_token"]

    except requests.exceptions.HTTPError:
        return None


def test_hh_token(access_token: str):
    url = "https://api.hh.ru/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True

    return False


def get_all_vacancies(access_token, area, languages):
    url = "https://api.hh.ru/vacancies"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    language_vacancies = {}
    for language in languages:
        params = {
            "text": language,
            "area": area
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        vacancies = response.json()
        language_vacancies[language] = vacancies

    return language_vacancies


def get_language_salary(access_token, language, area):
    url = "https://api.hh.ru/vacancies"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "text": language,
        "area": area
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    vacancies = response.json()
    vacancies_salary = []
    for vacancy in vacancies["items"]:
        vacancies_salary.append(vacancy["salary"])
    return vacancies_salary


def predict_rub_salary(vacancy):
    salary = vacancy["salary"]
    if not salary:
        return None
    if salary["currency"] != "RUR":
        return None
    if salary["from"] is None:
        if salary["to"] is None:
            return None
        return int(salary["to"] * 0.8)
    if salary["to"] is None:
        return int(salary["from"] * 1.2)
    return int(salary["from"] + (salary["to"] - salary["from"]) / 2)


if __name__ == "__main__":
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    hh_token = os.getenv("CLIENT_TOKEN")
    if hh_token is None:
        hh_token = get_access_token(client_id, client_secret)

    languages = (
        "Python",
    )
    all_vacancies = get_all_vacancies(hh_token, 1, languages)
    for language, language_vacancies in all_vacancies.items():
        for vacancy in language_vacancies["items"]:
            avg_salary = predict_rub_salary(vacancy)
            print(f"{avg_salary}")
