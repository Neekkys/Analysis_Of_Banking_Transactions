from typing import Any, Dict, List, Union

from pandas import DataFrame

from src.reports import save_result_in_file, spending_by_category
from src.services import get_full_df, get_increased_cashback
from src.views import main_response


@save_result_in_file("test_")
def main() -> List[Union[str, DataFrame, Dict[str, Any]]]:
    """Функция запускает основные функции views.py, services.py, reports.py."""
    # JSON ответ модуля views.py
    web_response = main_response("2025-04-20 16:20:00")
    print(web_response)
    print("-----------------")
    # Функция обрезает датафрейм для последующей обработки следующими функциями
    df = get_full_df()

    # Запуск модуля services.py
    services = get_increased_cashback(df, 2025, 4)
    print(services)
    print("------------------")

    # Запуск модуля reports.py
    reports = spending_by_category(df, "Супермаркеты", "2025-04-30 16:20:00")
    print(reports)
    print("------------------")

    return [
        web_response,
        services,
        reports
    ]
