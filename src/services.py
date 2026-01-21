import json
import logging

import pandas as pd
from pandas import DataFrame

from src.utils import BASE_DIR, get_period_full_month, get_slice_df_full_month, get_xlsx_path

logger = logging.getLogger("services.py")
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)


def get_full_df() -> DataFrame:
    """Функция открывает Excel файл и возвращает отсортированный по дате Dataframe"""
    try:
        logger.info("Открываем Excel файл ")
        excel_name = get_xlsx_path()
        data_path = BASE_DIR.joinpath("data", excel_name)
    except ValueError:
        logger.error("Ошибка чтения имени файла. Путь передан неверно")
        return pd.DataFrame()
    logger.info("Имя файла прочитано, путь создан. Начинаем чтение файла")
    try:
        df = pd.read_excel(data_path, sheet_name="Отчет по операциям")
        df["Номер карты"] = df["Номер карты"].fillna("SPB pay or transfers between accounts")
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
        sorted_df = df.sort_values(by="Дата операции")
        return sorted_df
    except (ValueError, TypeError, FileNotFoundError):
        logger.error("Ошибка чтения файла. Возвращаем пустой Датафрейм")
        return pd.DataFrame()


def get_increased_cashback(data: DataFrame, year: int, month: int) -> str:
    """Функция для анализа выгодности категорий повышенного кешбэка.
    На вход функции поступают данные для анализа, год и месяц.
    data — данные с транзакциями.
    year — год, за который проводится анализ.
    month — месяц, за который проводится анализ.
    Возвращает JSON ответ:
    "Категория 1": 1000,
    "Категория 2": 2000,
    "Категория 3": 500"""
    # Находим и возвращаем период List[начало месяца, конец месяца]
    try:
        logger.info("Находим и возвращаем период начала и конца месяца")
        month_period = get_period_full_month(year, month)
    except Exception as ex:
        logger.error(f"Период найти не удалось. {ex}")
        return "{}"

    # Обрезаем датафрейм по полному месяцу
    try:
        logger.info("Обрезаем датафрейм по периоду(начало-конец месяца)")
        df = get_slice_df_full_month(data, month_period)
    except Exception as ex:
        logger.error(f"Ошибка. Обрезать датафрейм не удалось. {ex}")
        return "{}"

    # Группируем по категориям датафрейм, находим сумму кешбэка и возвращаем json ответ
    try:
        logger.info("Группируем по категориям датафрейм, находим сумму кешбэка и возвращаем json ответ")
        group_df = df.groupby("Категория")["Кэшбэк"].sum()
        sort_category_cashback = group_df.sort_values(ascending=False)
        not_nan_df = {x: y for x, y in sort_category_cashback.items() if y > 0}
        to_json_data = json.dumps(not_nan_df, ensure_ascii=False, indent=4)
        return to_json_data
    except Exception as ex:
        logger.error(f"Ошибка. Обработать JSON файл не удалось. {ex}")
        return "{}"
