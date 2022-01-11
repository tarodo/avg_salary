import itertools
import os
from typing import Optional, Callable

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def get_hh_vacancy(area: int, language: str) -> dict:
    """Retrieve info about salary for one language from HeadHunter."""
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


def get_hh_vacancies(area: int, languages: tuple) -> dict:
    """Collect vacancies from HeadHunter."""
    language_vacancies = {}
    for language in languages:
        language_vacancies[language] = get_hh_vacancy(area, language)

    return language_vacancies


def get_sj_vacancy(client_secret: str, town: int, language: str) -> dict:
    """Retrieve info about salary for one language from SuperJob."""
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {"X-Api-App-Id": client_secret}
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


def get_sj_vacancies(
        client_secret: str, town: int, languages: tuple
) -> dict:
    """Collect vacancies from SuperJob."""
    language_vacancies = {}
    for language in languages:
        language_vacancies[language] = get_sj_vacancy(client_secret, town, language)

    return language_vacancies


def get_average_salary(payment_from: int, payment_to: int) -> Optional[int]:
    """Return average value for two payments level."""
    if not payment_from:
        if not payment_to:
            return None
        return int(payment_to * 0.8)
    if not payment_to:
        return int(payment_from * 1.2)
    return (payment_from + payment_to) // 2


def predict_hh_rub_salary(vacancy: dict) -> Optional[int]:
    """Handle salary from one vacancy from HeadHunter."""
    salary = vacancy["salary"]
    if not salary or salary["currency"] != "RUR":
        return None
    return get_average_salary(salary["from"], salary["to"])


def predict_sj_rub_salary(vacancy: dict) -> Optional[int]:
    """Handle salary from one vacancy from SuperJob."""
    if vacancy['currency'] == 'rub':
        return get_average_salary(vacancy["payment_from"], vacancy["payment_to"])
    return None


def collect_average_salary(vacancies: dict, predictor: Callable) -> dict:
    """
    Handle all vacancies from the platform;
    :param vacancies: vacancies from platform;
    :param predictor: function to predict salary of vacancy;
    :return: language: {vacancies_found: int, vacancies_processed: int, average_salary: int}.
    """
    language_salary = {}
    for language, language_vacancies in vacancies.items():
        sum_salary = 0
        salary_num = 0
        for vacancy in language_vacancies["items"]:
            rub_salary = predictor(vacancy)
            if rub_salary:
                sum_salary += rub_salary
                salary_num += 1
        language_stat = {"vacancies_found": language_vacancies["found"],
                         "vacancies_processed": salary_num}
        if not salary_num:
            language_stat["average_salary"] = 0
        else:
            language_stat["average_salary"] = int(sum_salary / salary_num)
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

    return AsciiTable(rows, title).table


if __name__ == "__main__":
    load_dotenv()

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
    all_hh_vacancies = get_hh_vacancies(1, languages)
    hh_average_salary = collect_average_salary(all_hh_vacancies, predict_hh_rub_salary)

    sj_secret = os.getenv("SJ_SECRET")
    all_sj_vacancies = get_sj_vacancies(sj_secret, 4, languages)
    sj_average_salary = collect_average_salary(all_sj_vacancies, predict_sj_rub_salary)

    print(get_statistic_table(hh_average_salary, "HeadHunter Moscow"))
    print(get_statistic_table(sj_average_salary, "SuperJob Moscow"))
