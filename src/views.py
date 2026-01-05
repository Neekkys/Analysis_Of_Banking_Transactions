import json

from src.utils import BASE_DIR, get_time_period, slice_period_and_sort_df, spending_on_the_card, time_for_greeting


def main_response(date_time: str) -> str:
    """Главная функция, принимающая на вход строку с датой и временем в формате
    YYYY-MM-DD HH:MM:SS и возвращающую JSON-ответ
    Пример: 2025-04-20 16:20:00"""

    # 1. Принимаем путь. Тут будет функция автоматического считывания файлов Excel.
    # Здороваемся в зависимости от времени суток
    data_dir = BASE_DIR.joinpath("data", "operations.xlsx")
    greeting = time_for_greeting()

    # 2.1. Находим период дат (от начала месяца до указанной границы date_time)
    # и сортируем датафрейм по указанному периоду дат
    time_period = get_time_period(date_time)
    sorted_df = slice_period_and_sort_df(data_dir, time_period)

    # 2.2. Извлекает из датафрейма данные о транзакциях по карте и возвращает в виде списка словарей
    cards = spending_on_the_card(sorted_df)

    data = {
        "greeting": greeting,
        "cards": cards,
    }

    to_json_data = json.dumps(data, ensure_ascii=False, indent=4)

    return to_json_data
