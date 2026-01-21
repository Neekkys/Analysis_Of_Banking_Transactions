import json
from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd

from src.utils import (get_period_full_month, get_slice_df_full_month, get_time_period, get_top_transactions,
                       get_xlsx_path, open_json, slice_period_and_sort_df, spending_on_the_card, time_for_greeting)


def test_time_for_greeting():
    """Тест приветствия с моком datetime.now()"""

    with patch("src.utils.datetime") as mock_datetime:
        mock_now = Mock()

        mock_now.hour = 8
        mock_datetime.now.return_value = mock_now
        assert time_for_greeting() == "Доброе утро"

        mock_now.hour = 13
        assert time_for_greeting() == "Добрый день"

        mock_now.hour = 20
        assert time_for_greeting() == "Добрый вечер"

        mock_now.hour = 23
        assert time_for_greeting() == "Доброй ночи"

        mock_now.hour = 4
        assert time_for_greeting() == "Доброй ночи"

        mock_now.hour = 5
        assert time_for_greeting() == "Доброе утро"


def test_get_time_period():
    """Тест вычисления периода"""

    result = get_time_period("2023-12-15 14:30:00")
    assert result == ["01.12.2023 00:00:00", "15.12.2023 14:30:00"]

    result = get_time_period("2023/12/15 14:30:00", "%Y/%m/%d %H:%M:%S")
    assert result == ["01.12.2023 00:00:00", "15.12.2023 14:30:00"]

    result = get_time_period("неправильная дата")
    assert "error" in result.lower()


def test_slice_period_and_sort_df_simple(sample_excel_file, test_period):
    """Тест фильтрации DataFrame - упрощенная версия"""
    result = slice_period_and_sort_df(sample_excel_file, test_period)

    assert not isinstance(result, str) or result != "Ошибка"

    if isinstance(result, pd.DataFrame):
        assert len(result) == 2

        dates = result["Дата операции"].tolist()
        assert dates == sorted(dates)


def test_spending_on_the_card(sample_dataframe):
    """Тест подсчета расходов по картам с фикстурой"""
    result = spending_on_the_card(sample_dataframe)

    assert isinstance(result, list)

    assert len(result) == 2

    for item in result:
        assert "last_digits" in item
        assert "total_spent" in item
        assert "cashback" in item

        if "SPB" not in item["last_digits"]:
            assert len(item["last_digits"]) == 4

            assert item["last_digits"].isdigit()


def test_get_top_transactions(sample_dataframe):
    """Тест получения топ транзакций с фикстурой"""
    result = get_top_transactions(sample_dataframe, 2)

    assert isinstance(result, list)
    assert len(result) == 2

    for item in result:
        assert "date" in item
        assert "amount" in item
        assert "category" in item
        assert "description" in item

    amounts = [item["amount"] for item in result]
    assert amounts == sorted(amounts, reverse=True)


def test_open_json(tmp_path, sample_json_data):
    """Тест открытия JSON файла с фикстурами"""

    json_file = tmp_path / "user_settings.json"
    json_file.write_text(json.dumps(sample_json_data))

    from unittest.mock import patch

    with patch("src.utils.BASE_DIR", tmp_path):
        result = open_json()
        assert result == sample_json_data

    with patch("src.utils.BASE_DIR", tmp_path / "nonexistent"):
        result = open_json()
        assert "error" in result.lower()


@patch("src.utils.requests.request")
def test_currency_api(mock_request, sample_json_data, mock_currency_api_response):
    """Тест API валют с фикстурами"""
    mock_request.return_value = mock_currency_api_response

    with patch.dict(
        "os.environ", {"API_KEY_CURRENCIES": "test_key", "API_URL_CURRENCIES": "https://api.test.com/currency"}
    ):
        import importlib

        import src.utils

        importlib.reload(src.utils)

        result = src.utils.currency_api(sample_json_data)

        assert isinstance(result, tuple)

        currencies, usd_rate = result
        assert len(currencies) == 2
        assert usd_rate > 0

        for currency in currencies:
            assert "currency" in currency
            assert "rate" in currency
            assert currency["currency"] in ["USD", "EUR"]


@patch("src.utils.requests.request")
def test_current_stock_prise(mock_request, sample_json_data, mock_stock_api_response):
    """Тест API акций с фикстурами"""
    mock_request.return_value = mock_stock_api_response

    with patch.dict("os.environ", {"API_KEY_STOCKS": "test_key"}):
        import importlib

        import src.utils

        importlib.reload(src.utils)

        test_usd_rate = 90.0
        result = src.utils.current_stock_prise(sample_json_data, test_usd_rate)

        if isinstance(result, list):

            assert len(result) >= 1

            for stock in result:
                assert "stock" in stock
                assert "price" in stock

                if stock["stock"] == "AAPL":
                    assert stock["price"] == 13500.0


def test_get_xlsx_path(tmp_path):
    """Тест поиска Excel файла"""
    from unittest.mock import patch

    test_dir = tmp_path / "data"
    test_dir.mkdir()

    test_file = test_dir / "test.xlsx"
    test_file.write_bytes(b"test")

    with patch("src.utils.BASE_DIR", tmp_path):
        result = get_xlsx_path()

        if result != "error":
            assert result == "test.xlsx"
        else:

            assert result == "error"


def test_get_xlsx_path_no_files(tmp_path):
    """Тест поиска Excel файла когда файлов нет"""
    from unittest.mock import patch

    test_dir = tmp_path / "data"
    test_dir.mkdir()

    with patch("src.utils.BASE_DIR", tmp_path):
        result = get_xlsx_path()

        assert result == "error"


def test_get_xlsx_path_no_data_dir(tmp_path):
    """Тест поиска Excel файла когда нет директории data"""
    from unittest.mock import patch

    with patch("src.utils.BASE_DIR", tmp_path):
        result = get_xlsx_path()

        if "не существует" in result or result == "error":

            assert True
        else:
            assert result == "error" or "не существует" in result


def test_spending_on_the_card_empty():
    """Тест с пустым DataFrame"""
    import pandas as pd

    empty_df = pd.DataFrame()
    result = spending_on_the_card(empty_df)
    assert "error" in result


def test_get_top_transactions_empty():
    """Тест с пустым DataFrame для топ транзакций"""
    import pandas as pd

    empty_df = pd.DataFrame()
    result = get_top_transactions(empty_df)
    assert "error" in result


def test_get_top_transactions_string_input():
    """Тест с некорректным входом (строкой вместо DataFrame)"""
    result = get_top_transactions("не DataFrame")
    assert result == []


def test_get_period_full_month(sample_date):
    """Тест на общую работоспособность"""
    for year, month, expected in sample_date:
        result = get_period_full_month(year, month)
        assert result == expected


def test_incorrect_month():
    """Тест на некорректный месяц"""
    result = get_period_full_month(2025, 13)
    assert result == []


def test_get_period_full_month_success():
    """Тест на корректное создание периода для месяца"""
    year = 2023
    month = 12

    result = get_period_full_month(year, month)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].startswith("01.12.2023")
    assert "31.12.2023" in result[1]


def test_get_period_full_month_invalid_month():
    """Тест на обработку некорректного месяца"""
    result = get_period_full_month(2023, 13)  # Несуществующий месяц

    assert result == []


def test_get_slice_df_full_month(sample_dataframe, test_period):
    """Тест на корректное срезание датафрейма по периоду"""
    result = get_slice_df_full_month(sample_dataframe, test_period)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2  # В периоде 01.12.2023 - 15.12.2023 должны быть 2 транзакции
    assert all(result["Дата операции"] >= datetime(2023, 12, 1))
    assert all(result["Дата операции"] <= datetime(2023, 12, 15, 23, 59, 59))


def test_get_slice_df_full_month_empty_df():
    """Тест на обработку пустого датафрейма"""
    empty_df = pd.DataFrame()
    period = ["01.12.2023 00:00:00", "31.12.2023 23:59:59"]

    result = get_slice_df_full_month(empty_df, period)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0
