import json
from unittest.mock import MagicMock, patch

import pandas as pd

from src.services import get_full_df, get_increased_cashback


def test_get_full_df_success(sample_excel_file):
    """Тест на успешное чтение Excel файла"""

    with patch("src.services.get_xlsx_name") as mock_get_xlsx:
        mock_get_xlsx.return_value = sample_excel_file.name

        with patch("src.services.BASE_DIR") as mock_base_dir:

            mock_base_dir.joinpath.return_value = sample_excel_file

            result = get_full_df()

    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert "Дата операции" in result.columns
    assert "Номер карты" in result.columns


def test_get_full_df_file_not_found():
    """Тест на обработку отсутствующего файла"""

    with patch("src.services.get_xlsx_name") as mock_get_xlsx:
        mock_get_xlsx.return_value = "несуществующий_файл.xlsx"

        with patch("src.services.BASE_DIR") as mock_base_dir:

            mock_path = MagicMock()
            mock_base_dir.joinpath.return_value = mock_path

            with patch("pandas.read_excel") as mock_read_excel:
                mock_read_excel.side_effect = FileNotFoundError("Файл не найден")

                result = get_full_df()

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_get_increased_cashback_success(sample_dataframe_for_cashback):
    """Тест на корректный расчет кешбэка по категориям"""
    df = sample_dataframe_for_cashback.copy()

    year = 2023
    month = 12

    result = get_increased_cashback(df, year, month)

    assert isinstance(result, str)

    parsed_result = json.loads(result)

    assert isinstance(parsed_result, dict)


def test_get_increased_cashback_empty_dataframe():
    """Тест на обработку пустого датафрейма"""
    empty_df = pd.DataFrame()
    year = 2023
    month = 12

    result = get_increased_cashback(empty_df, year, month)

    assert result == "{}"


def test_get_increased_cashback_no_positive_cashback():
    """Тест на случай, когда нет положительного кешбэка"""
    data = {
        "Номер карты": ["1234", "5678"],
        "Дата операции": pd.to_datetime(["2023-12-01", "2023-12-15"]),
        "Кэшбэк": [0, 0],
        "Категория": ["Еда", "Транспорт"],
    }
    df = pd.DataFrame(data)
    year = 2023
    month = 12

    result = get_increased_cashback(df, year, month)

    assert isinstance(result, str)

    parsed_result = json.loads(result)

    assert parsed_result == {}
