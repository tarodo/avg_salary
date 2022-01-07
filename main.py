import itertools
import os
from typing import Optional, Callable

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


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


def get_hh_vacancy(area: int, language: str) -> dict:
    """Retrieve info about salary for one language from HeadHunter"""
    url = "https://api.hh.ru/vacancies"
    vacancy = {"items": [], "found": 0}
    params = {"text": language, "area": area, "per_page": 100}
    for page in itertools.count(1, 1):
        params["page"] = page - 1
        response = requests.get(url, params=params)
        response.raise_for_status()
        hh_vacancies = response.json()
        vacancy["items"] += hh_vacancies["items"]
        if page == 1:
            vacancy["found"] = hh_vacancies["found"]
        if page >= hh_vacancies["pages"]:
            return vacancy


def get_all_hh_vacancies(area: int, hh_languages: tuple) -> dict:
    """Collect vacancies from HeadHunter"""
    language_vacancies = {}
    for language in hh_languages:
        language_vacancies[language] = get_hh_vacancy(area, language)

    return language_vacancies


def get_sj_vacancy(access_token: str, client_secret: str, town: int, language: str) -> dict:
    """Retrieve info about salary for one language from SuperJob"""
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {"X-Api-App-Id": client_secret, "Authorization": f"Bearer {access_token}"}
    vacancy = {"items": [], "found": 0}
    params = {"town": town,
              "keyword": language,
              "count": 100, }

    for page in itertools.count(1, 1):
        params["page"] = page - 1
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        sj_vacancies = response.json()
        vacancy["items"] += sj_vacancies["objects"]
        if page == 1:
            vacancy["found"] = sj_vacancies["total"]
        if not sj_vacancies["more"]:
            return vacancy


def get_all_sj_vacancies(
        access_token: str, client_secret: str, town: int, sj_languages: tuple
) -> dict:
    """Collect vacancies from SuperJob"""
    language_vacancies = {}
    for language in sj_languages:
        language_vacancies[language] = get_sj_vacancy(access_token, client_secret, town, language)

    return language_vacancies


def get_average_salary(payment_from: int, payment_to: int) -> Optional[int]:
    """Return average value for two payments level"""
    if not payment_from:
        if not payment_to:
            return None
        return int(payment_to * 0.8)
    if not payment_to:
        return int(payment_from * 1.2)
    return int(payment_from + (payment_to - payment_from) / 2)


def predict_hh_rub_salary(vacancy: dict) -> Optional[int]:
    """Handle salary from one vacancy from HeadHunter"""
    salary = vacancy["salary"]
    if not salary:
        return None
    if salary["currency"] != "RUR":
        return None
    return get_average_salary(salary["from"], salary["to"])


def predict_sj_rub_salary(vacancy: dict) -> Optional[int]:
    """Handle salary from one vacancy from SuperJob"""
    return get_average_salary(vacancy["payment_from"], vacancy["payment_to"])


def collect_average_salary(vacancies: dict, predictor: Callable) -> dict:
    """
    Handle all vacancies from the platform.
    :param vacancies: vacancies from platform
    :param predictor: function to predict salary of vacancy
    :return: language: {vacancies_found: int, vacancies_processed: int, average_salary: int}
    """
    language_salary = {}
    for language, language_vacancies in vacancies.items():
        sum_salary = 0
        salary_num = 0
        for vacancy in language_vacancies["items"]:
            rub_salary = predictor(vacancy)
            if rub_salary is not None:
                sum_salary += rub_salary
                salary_num += 1
        language_stat = {"vacancies_found": language_vacancies["found"],
                         "vacancies_processed": salary_num,
                         "average_salary": int(sum_salary / salary_num)}
        language_salary[language] = language_stat
    return language_salary


def get_statistic_table(stats: dict, title: str) -> AsciiTable:
    headers = [
        "Язык программирования",
        "Вакансий найдено",
        "Вакансий обработано",
        "Средняя зарплата",
    ]

    rows = [headers]

    for language, vacancies_params in stats.items():
        rows.append([language, *vacancies_params.values()])

    return AsciiTable(rows, title)


def print_statistic(stats, title):
    table_instance = get_statistic_table(stats, title)
    print(table_instance.table)


if __name__ == "__main__":
    load_dotenv()

    languages = (
        "Python",
        # "Java",
        # "C#",
        # "PHP",
        # "Go",
        # "JavaScript",
        # "Java",
        # "VBA",
        # "1С",
        # "SQL",
    )
    all_hh_vacancies = get_all_hh_vacancies(1, languages)
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
