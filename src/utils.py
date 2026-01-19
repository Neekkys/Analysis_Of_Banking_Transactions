import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import pandas as pd
import requests
from dotenv import load_dotenv
from pandas import DataFrame

BASE_DIR = Path(__file__).resolve().parent.parent


# Функции для модуля views.py
def get_xlsx_path() -> str:
    data_dir = BASE_DIR.joinpath("data")
    if not data_dir.exists():
        return "Файла не существует"
    excel_extensions = [".xlsx", ".xls", ".xlsm", ".xlsb"]
    try:
        for item in data_dir.iterdir():
            if item.is_file() and item.suffix.lower() in excel_extensions:
                return item.name
        return "error"
    except Exception as ex:
        return f"error {ex}"


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


def get_time_period(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> List[str] | str:
    """Функция принимает на вход вторую границу периода даты и возвращает
    1 границу периода - начало месяца, и 2 границу периода в виде списка"""
    try:
        dt = datetime.strptime(date_time, date_format)
        first_day = dt.replace(day=1, hour=0, minute=0, microsecond=0)
        return [
            first_day.strftime("%d.%m.%Y %H:%M:%S"),
            dt.strftime("%d.%m.%Y %H:%M:%S"),
        ]
    except Exception as ex:
        return f"error {ex}"


def slice_period_and_sort_df(data_path: Path, period: List[str] | str) -> DataFrame | str:
    """Функция принимает путь к Excel файлу и период, состоящий из 2 дат.
    Функция читает xlsx, обрезает по указанному периоду(инд 0 - начало месяца, инд 1 - до какого дня)
    и преобразует xlsx файл в виде словаря"""
    try:
        if isinstance(period, str):
            return "Ошибка"
        df = pd.read_excel(data_path, sheet_name="Отчет по операциям")
        df["Номер карты"] = df["Номер карты"].fillna("SPB pay or transfers between accounts")
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)

        start_time = datetime.strptime(period[0], "%d.%m.%Y %H:%M:%S")
        last_time = datetime.strptime(period[1], "%d.%m.%Y %H:%M:%S")

        filtered_df = df[(df["Дата операции"] >= start_time) & (df["Дата операции"] <= last_time)]

        sorted_df = filtered_df.sort_values(by="Дата операции")
        return sorted_df
    except Exception as ex:
        return f"error {ex}"


def spending_on_the_card(sorted_df: DataFrame | str) -> List[Dict[str, Any]] | str:
    """Функция принимает отсортированный по дате и периоду DataFrame и извлекает из него:
    last_digits - последние 4 цифры номера карты,
    total_spent - общая сумма расходов по карте,
    cashback - общая сумма кешбека"""
    if isinstance(sorted_df, str):
        return []
    try:
        df = sorted_df.copy()
        transactions_for_card = []
        expenses = df[df["Сумма операции"] < 0]
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
    except Exception as ex:
        return f"error {ex}"


def get_top_transactions(sorted_df: DataFrame | str, count: int = 5) -> List[Dict[str, Any]] | str:
    """Функция принимает отсортированный по периоду даты датафрейм и ищет топ (сount) транзакций
    по сумме платежа. Затем выводит в виде словаря:
    "date": Дата
    "amount": Сумма операции
    "category": Категория
    "description": Описание"""
    if isinstance(sorted_df, str):
        return []
    try:
        result = []
        df = sorted_df.copy()
        df["Сумма операции"] = df["Сумма операции"].abs()
        top_transactions = df.sort_values(by="Сумма операции", ascending=False).head(count)
        for transactions in top_transactions.to_dict("records"):
            date_time_timestamp = transactions.get("Дата платежа")
            if date_time_timestamp is None:
                date_time = "Не указана"
            else:
                try:
                    date_time = date_time_timestamp.strftime("%d.%m.%Y")
                except AttributeError:
                    # Если это не timestamp, пытаемся преобразовать в строку
                    date_time = str(date_time_timestamp)

            amount = transactions.get("Сумма операции")
            category_ = transactions.get("Категория", "None category")
            description = transactions.get("Описание", "None description")
            result.append(
                {
                    "date": date_time,
                    "amount": amount,
                    "category": category_,
                    "description": description,
                }
            )
        return result
    except Exception as ex:
        return f"error {ex}"


def open_json() -> Union[Any, str]:
    """Функция распаковки json файла. Возвращает пример:
    {
      "user_currencies": ["USD", "EUR"],
      "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
    }"""
    try:
        data_dir = BASE_DIR.joinpath("user_settings.json")
        with open(data_dir, "r", encoding="utf8") as f:
            unpacked_json = json.load(f)
        return unpacked_json
    except Exception as ex:
        return f"error {ex}"


load_dotenv()
api_key_currency = os.getenv("API_KEY_CURRENCIES")
api_url_currency: str = os.getenv("API_URL_CURRENCIES", "")


def currency_api(opened_json: Union[Dict[str, Any], str]) -> Tuple[List[Dict[str, Any]], float] | str:
    """Функция запрашивает у внешнего API курс валют, указанных в распакованном json файле.
     Возвращает список словарей с указанными:
    {"currency": "Валюта", "rate": "Стоимость"}"""
    if isinstance(opened_json, str):
        return [], 0
    try:
        user_currencies = opened_json.get("user_currencies", "Ошибка")
        if user_currencies == "Ошибка":
            currency_value = user_currencies
        else:
            currency_value = ",".join(user_currencies)
        payload = {"base": "RUB", "symbols": currency_value}
        headers = {"apikey": api_key_currency}

        response = requests.request("GET", api_url_currency, headers=headers, params=payload)
        response.raise_for_status()
        json_response = response.json()

        result_list_dict = []
        real_price_usd = 0

        for value, count in json_response["rates"].items():
            if count == 0:
                continue
            rate = round(1 / count, 2)
            if value == "USD":
                real_price_usd = rate
            result_list_dict.append(
                {
                    "currency": value,
                    "rate": rate,
                }
            )
        return result_list_dict, real_price_usd
    except requests.exceptions.RequestException as e:
        return f"Ошибка запроса к API: {e}"
    except (KeyError, ValueError, ZeroDivisionError, TypeError) as e:
        return f"Ошибка обработки данных: {e}"


load_dotenv()
api_key_stocks = os.getenv("API_KEY_STOCKS")


def current_stock_prise(opened_json: Union[Dict[str, Any], str], real_price_usd: float) -> List[Dict[str, Any]] | str:
    """Функция запрашивает у внешнего API курс акций, указанных в распакованном json файле.
    Возвращает список словарей с указанными:
    {"stock": "Акция", "price": "Стоимость"}"""
    if isinstance(opened_json, str):
        return []
    try:
        user_stocks = opened_json.get("user_stocks", [])

        result_list_dict = []

        for stock in user_stocks:
            url = f"https://api.finage.co.uk/last/stock/{stock}?apikey={api_key_stocks}"

            response = requests.request("GET", url)
            response.raise_for_status()
            response_json = response.json()
            stock = response_json.get("symbol")
            price_usd = response_json.get("ask")
            price_rub = round(float(price_usd) * float(real_price_usd), 2)

            result = {"stock": stock, "price": price_rub}
            result_list_dict.append(result)
        return result_list_dict
    except (ValueError, KeyError, TypeError) as ex:
        return f"Ошибка обработки данных: {ex}"
    except requests.exceptions.RequestException as ex:
        return f"Ошибка запроса к API: {ex}"


# Функции для модуля services.py
