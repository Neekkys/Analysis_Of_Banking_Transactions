import sys
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent / "src"))


@pytest.fixture
def sample_excel_file():
    """Фикстура с тестовым Excel файлом"""
    test_data = {
        "Номер карты": ["1234567890123456", "9876543210987654", "SPB pay"],
        "Дата операции": pd.to_datetime(["2023-12-01 10:00:00", "2023-12-15 14:30:00", "2023-12-20 09:15:00"]),
        "Сумма операции": [100, -200.5, 300],
        "Кэшбэк": [1.0, 2.5, 0],
        "Категория": ["Еда", "Транспорт", "Перевод"],
        "Описание": ["Ресторан", "Такси", "Между счетами"],
        "Дата платежа": pd.to_datetime(["2023-12-02", "2023-12-16", "2023-12-21"]),
    }
    df = pd.DataFrame(test_data)

    # В Windows нужно использовать другой подход для временных файлов
    import tempfile
    import uuid

    # Создаем уникальное имя файла
    temp_dir = tempfile.gettempdir()
    file_name = f"test_excel_{uuid.uuid4().hex}.xlsx"
    file_path = Path(temp_dir) / file_name

    # Сохраняем файл
    df.to_excel(file_path, sheet_name="Отчет по операциям", index=False)

    yield file_path

    # Удаляем файл после теста (без блокировки)
    try:
        if file_path.exists():
            # Добавляем небольшую задержку для Windows
            import time

            time.sleep(0.1)
            file_path.unlink()
    except Exception as e:
        print(f"Не удалось удалить файл {file_path}: {e}")


@pytest.fixture
def sample_json_data():
    """Фикстура с тестовыми JSON данными"""
    return {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "TSLA"]}


@pytest.fixture
def sample_dataframe():
    """Фикстура с тестовым DataFrame"""
    data = {
        "Номер карты": ["1234567890123456", "9876543210987654", "SPB pay or transfers between accounts"],
        "Сумма операции": [-100.0, -200.5, 300.0],
        "Кэшбэк": [1.0, 2.5, 0],
        "Дата операции": pd.to_datetime(["2023-12-01", "2023-12-15", "2023-12-20"]),
        "Категория": ["Еда", "Транспорт", "Перевод"],
        "Описание": ["Ресторан", "Такси", "Между счетами"],
        "Дата платежа": pd.to_datetime(["2023-12-02", "2023-12-16", "2023-12-21"]),
    }
    return pd.DataFrame(data)


@pytest.fixture
def test_period():
    """Фикстура с тестовым периодом"""
    return ["01.12.2023 00:00:00", "15.12.2023 23:59:59"]


@pytest.fixture
def mock_currency_api_response():
    """Фикстура для мокинга ответа currency API"""
    mock_response = Mock()
    mock_response.json.return_value = {"success": True, "rates": {"USD": 0.011, "EUR": 0.010}}
    mock_response.raise_for_status = Mock()
    return mock_response


@pytest.fixture
def mock_stock_api_response():
    """Фикстура для мокинга ответа stock API"""
    mock_response = Mock()
    mock_response.json.return_value = {"symbol": "AAPL", "ask": 150.0, "bid": 149.5}
    mock_response.raise_for_status = Mock()
    return mock_response


@pytest.fixture
def mock_datetime_now():
    """Фикстура для мокинга datetime.now()"""
    from unittest.mock import Mock

    # Создаем мок-объект для datetime
    mock_now = Mock()
    mock_now.hour = 10  # Значение по умолчанию

    # Возвращаем мок
    return mock_now


@pytest.fixture
def sample_date():
    return [
        (2025, 1, ["01.01.2025 00:00:00", "31.01.2025 23:59:59"]),
        (2024, 2, ["01.02.2024 00:00:00", "29.02.2024 23:59:59"]),
        (2023, 2, ["01.02.2023 00:00:00", "28.02.2023 23:59:59"]),
        (2022, 4, ["01.04.2022 00:00:00", "30.04.2022 23:59:59"]),
        (2021, 5, ["01.05.2021 00:00:00", "31.05.2021 23:59:59"]),
    ]


@pytest.fixture
def sample_dataframe_for_cashback():
    """Фикстура с тестовым DataFrame для тестирования кешбэка"""
    data = {
        "Номер карты": ["1234", "5678", "9012"],
        "Дата операции": pd.to_datetime(["2023-12-01", "2023-12-15", "2023-12-20"]),
        "Кэшбэк": [1.0, 2.5, 0],
        "Категория": ["Еда", "Транспорт", "Перевод"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def empty_dataframe():
    """Фикстура с пустым DataFrame"""
    return pd.DataFrame()
