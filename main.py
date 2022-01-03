import os
from typing import Optional, Callable

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def get_hh_access_token(client_id: str, client_secret: str) -> Optional[str]:
    """Get access token to HeadHunter api service"""
    url_auth = "https://hh.ru/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    request_body = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    response = requests.post(url_auth, data=request_body, headers=headers)
    try:
        response.raise_for_status()
        return response.json()["access_token"]

    except requests.exceptions.HTTPError:
        return None


def get_sj_access_token(
    email, password, client_id: str, client_secret: str
) -> Optional[str]:
    """Get access token to SuperJob api service"""
    url_auth = "https://api.superjob.ru/2.0/oauth2/password/"
    headers = {"X-Api-App-Id": client_secret}
    params = {
        "login": email,
        "password": password,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    response = requests.post(url_auth, params=params, headers=headers)
    try:
        response.raise_for_status()
        return response.json()["access_token"]

    except requests.exceptions.HTTPError:
        return None


def get_all_hh_vacancies(access_token: str, area: int, hh_languages: tuple) -> dict:
    """Collect vacancies from HeadHunter"""
    url = "https://api.hh.ru/vacancies"
    headers = {"Authorization": f"Bearer {access_token}"}
    language_vacancies = {}
    for language in hh_languages:
        language_vacancies[language] = {}
        language_vacancies[language]["items"] = []
        language_vacancies[language]["found"] = 0
        page = 0
        pages = 1
        while page < pages:
            params = {"text": language, "area": area, "per_page": 100, "page": page}
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            hh_vacancies = response.json()
            pages = hh_vacancies["pages"]
            language_vacancies[language]["items"] += hh_vacancies["items"]
            language_vacancies[language]["found"] += len(hh_vacancies["items"])
            page += 1

    return language_vacancies


def get_all_sj_vacancies(
    access_token: str, client_secret: str, town: int, sj_languages: tuple
) -> dict:
    """Collect vacancies from SuperJob"""
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {"X-Api-App-Id": client_secret, "Authorization": f"Bearer {access_token}"}
    language_vacancies = {}
    for language in sj_languages:
        language_vacancies[language] = {}
        language_vacancies[language]["items"] = []
        language_vacancies[language]["found"] = 0

        is_more = True
        page = 0
        while is_more:
            params = {
                "town": town,
                "keyword": language,
                "count": 100,
                "page": page,
            }
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            sj_vacancies = response.json()
            is_more = sj_vacancies["more"]
            page += 1
            language_vacancies[language]["items"] += sj_vacancies["objects"]
            language_vacancies[language]["found"] += len(sj_vacancies["objects"])

    return language_vacancies


def predict_hh_rub_salary(vacancy: dict) -> Optional[int]:
    """Handle salary from one vacancy from HeadHunter"""
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


def predict_sj_rub_salary(vacancy: dict) -> Optional[int]:
    """Handle salary from one vacancy from SuperJob"""
    if not vacancy["payment_from"]:
        if not vacancy["payment_to"]:
            return None
        return int(vacancy["payment_to"] * 0.8)
    if not vacancy["payment_to"]:
        return int(vacancy["payment_from"] * 1.2)
    return int(
        vacancy["payment_from"] + (vacancy["payment_to"] - vacancy["payment_from"]) / 2
    )


def collect_average_salary(vacancies: dict, predictor: Callable) -> dict:
    """
    Handle all vacancies from the platform.
    :param vacancies: vacancies from platform language
    :param predictor: function to predict salary of vacancy
    :return: language: {vacancies_found: int, vacancies_processed: int, average_salary: int}
    """
    language_salary = {}
    for language, language_vacancies in vacancies.items():
        language_stat = {"vacancies_found": language_vacancies["found"]}
        sum_salary = 0
        salary_num = 0
        for vacancy in language_vacancies["items"]:
            rub_salary = predictor(vacancy)
            if rub_salary is not None:
                sum_salary += rub_salary
                salary_num += 1
        language_stat["vacancies_processed"] = salary_num
        language_stat["average_salary"] = int(sum_salary / salary_num)
        language_salary[language] = language_stat
    return language_salary


def print_statistic(stats, title):
    headers = [
        "Язык программирования",
        "Вакансий найдено",
        "Вакансий обработано",
        "Средняя зарплата",
    ]

    rows = [headers]

    for language, vacancies_params in stats.items():
        rows.append([language, *vacancies_params.values()])

    table_instance = AsciiTable(rows, title)
    print(table_instance.table)


if __name__ == "__main__":
    load_dotenv()
    client_hh_id = os.getenv("HH_CLIENT_ID")
    client_hh_secret = os.getenv("HH_CLIENT_SECRET")
    hh_token = os.getenv("HH_CLIENT_TOKEN")
    if hh_token is None:
        hh_token = get_hh_access_token(client_hh_id, client_hh_secret)

    languages = (
        "Python",
        "Java",
        "C#",
        "PHP",
        "Go",
        "JavaScript",
        "Java",
        "VBA",
        "1С",
        "SQL",
    )
    all_hh_vacancies = get_all_hh_vacancies(hh_token, 1, languages)
    hh_average_salary = collect_average_salary(all_hh_vacancies, predict_hh_rub_salary)

    client_sj_id = os.getenv("SJ_CLIENT_ID")
    client_sj_secret = os.getenv("SJ_CLIENT_SECRET")
    sj_email = os.getenv("SJ_EMAIL")
    sj_pass = os.getenv("SJ_PASSWORD")
    sj_token = get_sj_access_token(sj_email, sj_pass, client_sj_id, client_sj_secret)
    all_sj_vacancies = get_all_sj_vacancies(sj_token, client_sj_secret, 4, languages)
    sj_average_salary = collect_average_salary(all_sj_vacancies, predict_sj_rub_salary)

    print_statistic(hh_average_salary, "HeadHunter Moscow")
    print_statistic(sj_average_salary, "SuperJob Moscow")
