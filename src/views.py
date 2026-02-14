import json
import logging
from typing import Any, Dict, List

from src.utils import (BASE_DIR, currency_api, current_stock_prise, get_time_period, get_top_transactions,
                       get_xlsx_name, open_json, slice_period_and_sort_df, spending_on_the_card, time_for_greeting)

logger = logging.getLogger("views.py")
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)


def main_response(date_time: str) -> str | dict:
    """Главная функция, принимающая на вход строку с датой и временем в формате
    YYYY-MM-DD HH:MM:SS и возвращающую JSON-ответ
    Пример аргумента: 2025-04-20 16:20:00"""

    logger.info("Начало работы")
    # 1. Функция автоматического считывания названия файла Excel.
    # Здороваемся в зависимости от времени суток

    logger.info("Старт get_xlsx_path()")
    excel_name = get_xlsx_name()
    if excel_name == "Файла не существует":
        logger.warning("Файла не существует")
    elif "error" in excel_name:
        logger.error(f"Фундаментальная ошибка - {excel_name}")
    else:
        logger.info("Выполнено")

    data_dir = BASE_DIR.joinpath("data", excel_name)

    logger.info("Старт time_for_greeting()")
    greeting = time_for_greeting()
    if (
        greeting == "Добрый день"
        or greeting == "Добрый вечер"
        or greeting == "Доброе утро"
        or greeting == "Доброй ночи"
    ):
        logger.info("Выполнено")
    else:
        logger.error("Ошибка")

    # 2.1. Находим период дат (от начала месяца до указанной границы date_time)
    # и сортируем датафрейм по указанному периоду дат
    logger.info("Старт get_time_period(date_time)")
    time_period = get_time_period(date_time)
    if isinstance(time_period, str) and "error" in time_period:
        logger.error(f"Фундаментальная ошибка {time_period} c датой ({date_time})")
    else:
        logger.info("Выполнено")

    logger.info("Старт slice_period_and_sort_df(data_dir, time_period)")
    sorted_df = slice_period_and_sort_df(data_dir, time_period)
    if isinstance(sorted_df, str) or "error" in sorted_df:
        logger.error(f"Ошибка - {sorted_df}")
    else:
        logger.info("Выполнено")

    # 2.2. Извлекает из датафрейма данные о транзакциях по карте и возвращает в виде списка словарей
    logger.info("Старт spending_on_the_card(sorted_df)")
    cards = spending_on_the_card(sorted_df)
    if isinstance(cards, str) or "error" in cards:
        logger.error(f"Ошибка - {cards}")
    else:
        logger.info("Выполнено")

    # 3. Возвращает топ 5 транзакций по сумме платежа. Вторым аргументом можно передать int (цифра топа)
    logger.info("Старт get_top_transactions(sorted_df)")
    top_transactions = get_top_transactions(sorted_df)
    if isinstance(top_transactions, str) or "error" in top_transactions:
        logger.error(f"Ошибка - {top_transactions}")
    else:
        logger.info("Выполнено")

    # 4.1 Читаем json с данными о необходимых курсах валют и акций
    logger.info("Старт open_json()")
    opened_json = open_json()
    if isinstance(opened_json, str) or "error" in opened_json:
        logger.error(f"Ошибка - {opened_json}")
    else:
        logger.info("Выполнено")

    # 4.2 Делаем запрос к API для получения актуальных курсов валют и актуальной стоимости USD для
    # функции stock_prices
    logger.info("Старт currency_api(opened_json)")
    success_currency_api = currency_api(opened_json)
    currency_rates: List[Dict[str, Any]] = []
    real_price_usd: float = 0.0
    if isinstance(success_currency_api, str):
        logger.error(f"Ошибка в currency_api: {success_currency_api}")
    else:
        currency_rates, real_price_usd = success_currency_api
        logger.info("Выполнено")

    # 4.3 Делаем запрос к API для получения актуальных курсов акций
    logger.info("Старт current_stock_prise(opened_json, real_price_usd)")
    stock_prices = current_stock_prise(opened_json, real_price_usd)
    if isinstance(stock_prices, str) or "Ошибка" in stock_prices:
        logger.error(f"Ошибка в current_stock_prise: {stock_prices}")
    else:
        logger.info("Выполнено")

    logger.info("Формирование словаря с финальным ответом в виде JSON")
    data = {
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    try:
        to_json_data = json.dumps(data, ensure_ascii=False, indent=4)
        logger.info("Выполнено")
        return to_json_data
    except Exception as ex:
        logger.error(f"Ошибка {ex}")
        return {}
