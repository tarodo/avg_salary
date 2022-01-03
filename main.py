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
        language_vacancies[language] = {}
        language_vacancies[language]["items"] = []
        language_vacancies[language]["found"] = 0
        page = 0
        pages = 1
        while page < pages:
            params = {
                "text": language,
                "area": area,
                "per_page": 100,
                "page": page
            }
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            vacancies = response.json()
            pages = vacancies["pages"]
            language_vacancies[language]["items"] += vacancies["items"]
            language_vacancies[language]["found"] += len(vacancies["items"])
            page += 1
            print(f"{language} :: {page} of {pages} :: Done")

    return language_vacancies


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


def collect_average_salary(vacancies):
    language_salary = {}
    for language, language_vacancies in all_vacancies.items():
        language_stat = {
            "vacancies_found": language_vacancies["found"]
        }
        sum_salary = 0
        salary_num = 0
        for vacancy in language_vacancies["items"]:
            rub_salary = predict_rub_salary(vacancy)
            if rub_salary is not None:
                sum_salary += rub_salary
                salary_num += 1
        language_stat["vacancies_processed"] = salary_num
        language_stat["average_salary"] = int(sum_salary/salary_num)
        language_salary[language] = language_stat
    return language_salary


if __name__ == "__main__":
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    hh_token = os.getenv("CLIENT_TOKEN")
    if hh_token is None:
        hh_token = get_access_token(client_id, client_secret)

    languages = (
        "Python", "Java"
    )
    all_vacancies = get_all_vacancies(hh_token, 1, languages)

    print(collect_average_salary(all_vacancies))
