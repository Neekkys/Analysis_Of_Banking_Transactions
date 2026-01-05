from datetime import datetime
from pathlib import Path
from typing import List, Any, Dict

import pandas as pd
from pandas import DataFrame

BASE_DIR = Path(__file__).resolve().parent.parent


def time_for_greeting() -> str:
    """Функция возвращает «Доброе утро» / «Добрый день» /
    «Добрый вечер» / «Доброй ночи» в зависимости от текущего времени."""
    now_time_hour = datetime.now().hour
    if 5 <= now_time_hour < 12:
        return "Доброе утро"
    elif 12 <= now_time_hour < 18:
        return "Добрый день"
    elif 18 <= now_time_hour < 22:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_time_period(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> List[str]:
    """Функция принимает на вход вторую границу периода даты и возвращает
    1 границу периода - начало месяца, и 2 границу периода в виде списка"""
    dt = datetime.strptime(date_time, date_format)
    first_day = dt.replace(day=1, hour=0, minute=0, microsecond=0)
    return [
        first_day.strftime("%d.%m.%Y %H:%M:%S"),
        dt.strftime("%d.%m.%Y %H:%M:%S"),
    ]


def slice_period_and_sort_df(data_path: Path, period: List[str]) -> DataFrame:
    """Функция принимает путь к Exel файлу и период, состоящий из 2 дат.
    Функция читает xlsx, обрезает по указанному периоду(инд 0 - начало месяца, инд 1 - до какого дня)
    и преобразует xlsx файл в виде словаря"""
    df = pd.read_excel(data_path, sheet_name="Отчет по операциям")
    df["Номер карты"] = df["Номер карты"].fillna("SPB pay or transfers between accounts")
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)

    start_time = datetime.strptime(period[0], "%d.%m.%Y %H:%M:%S")
    last_time = datetime.strptime(period[1], "%d.%m.%Y %H:%M:%S")

    filtered_df = df[(df["Дата операции"] >= start_time) & (df["Дата операции"] <= last_time)]

    sorted_df = filtered_df.sort_values(by="Дата операции")
    return sorted_df


def spending_on_the_card(sorted_df: DataFrame) -> List[Dict[str, Any]]:
    """Функция принимает отсортированный по дате и периоду DataFrame и извлекает из него:
    last_digits - последние 4 цифры номера карты,
    total_spent - общая сумма расходов по карте
    cashback - общая сумма кешбека"""
    transactions_for_card = []
    expenses = sorted_df[sorted_df["Сумма операции"] < 0]
    sorted_by_group = expenses.groupby("Номер карты")

    for card_number, group in sorted_by_group:
        card_number = str(card_number)
        if "SPB" not in card_number and len(card_number) >= 4:
            last_digits = str(card_number[-4:])
        else:
            last_digits = str(card_number)
        total_spent = abs(group["Сумма операции"].sum())
        cashback = group["Кэшбэк"].fillna(0).sum()
        transactions_for_card.append(
            {
                "last_digits": last_digits,
                "total_spent": round(total_spent, 2),
                "cashback": cashback,
            }
        )
    return transactions_for_card
