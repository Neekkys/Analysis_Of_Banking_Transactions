import json
import logging
from datetime import datetime
from functools import wraps
from typing import Optional

import pandas as pd
from pandas import DataFrame, option_context

from src.utils import BASE_DIR, get_expenses_by_category, get_period_last_3_month, get_slice_df_full_month

logger = logging.getLogger("reports.py")
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)


def save_result_in_file(file_name: Optional[str] = None):
    """Декоратор, который записывает результат работы функции в указанный файл,
    или в файл по умолчанию"""
    def _save_result_in_file(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            call_time = datetime.now().strftime("%d.%m.%Y %H-%M-%S")

            func_name = func.__name__
            try:
                result_func = func(*args, **kwargs)
                log_message = f"{call_time} - {func_name} - ok\n"
                formatted_content = ""

                # Форматируем первый элемент (JSON)
                if len(result_func) > 0:
                    first_json = json.loads(result_func[0])
                    formatted_content += json.dumps(first_json, indent=4, ensure_ascii=False)
                    formatted_content += "\n\n"

                # Форматируем второй элемент (JSON)
                if len(result_func) > 1:
                    second_json = json.loads(result_func[1])
                    formatted_content += json.dumps(second_json, indent=4, ensure_ascii=False)
                    formatted_content += "\n\n"

                # Форматируем третий элемент (DataFrame)
                if len(result_func) > 2:
                    df = result_func[2]

                    with option_context('display.max_columns', None,
                                        'display.width', None,
                                        'display.max_colwidth', None):
                        formatted_content += df.to_string(index=False)

            except Exception as ex:
                log_message = f"Error - {func_name} - error message - {ex}"
                result_func = None
                formatted_content = ""
            if file_name:
                data_dir = BASE_DIR.joinpath("log_result", f"{file_name} {call_time}.txt")
            else:
                data_dir = BASE_DIR.joinpath("log_result", f"{func_name} {call_time}.txt")

            data_dir.parent.mkdir(parents=True, exist_ok=True)

            with open(data_dir, "w", encoding="UTF8") as f:
                f.write(formatted_content)
                f.write("\n\n")
                f.write(log_message)
            return result_func
        return wrapper
    return _save_result_in_file


def spending_by_category(df: DataFrame, category_name: str, date: Optional[str] = None) -> DataFrame:
    """Функция, которая возвращает траты по заданной категории
    за последние три месяца (от переданной даты)"""
    # Находим период в 3 месяца
    logger.info("Запуск функции spending_by_category. Ищем период")
    try:
        period = get_period_last_3_month(date)
    except Exception as ex:
        logger.error(f"Ошибка {ex}")
        return pd.DataFrame()
    logger.info("Успешно")

    # Обрезаем Датафрейм по периоду
    logger.info("Обрезаем Датафрейм по периоду")
    try:
        cut_df = get_slice_df_full_month(df, period)
    except Exception as ex:
        logger.error(f"Ошибка {ex}")
        return pd.DataFrame()
    logger.info("Успешно")

    # Вырезаем из датафрейма все категории кроме указанной в category_name
    logger.info("Вырезаем из датафрейма все категории кроме указанного периода")
    try:
        result = get_expenses_by_category(cut_df, category_name)
    except Exception as ex:
        logger.error(f"Ошибка {ex}")
        return pd.DataFrame()
    logger.info("Успешно")
    return result
