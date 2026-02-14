import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.reports import save_result_in_file, spending_by_category

sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))


# Тесты для spending_by_category
def test_spending_by_category_success(sample_dataframe):
    """Тест: успешное выполнение всех этапов"""
    # Используем sample_dataframe из фикстуры, не создаем новый
    df = sample_dataframe.copy()

    # Добавляем нужные колонки если их нет
    if "Дата операции" not in df.columns:
        df["Дата операции"] = pd.to_datetime(["2023-12-01", "2023-12-15", "2023-12-20"])
    if "Категория" not in df.columns:
        df["Категория"] = ["Еда", "Транспорт", "Еда"]
    if "Сумма операции" not in df.columns:
        df["Сумма операции"] = [-100, -50, -200]
    if "Описание" not in df.columns:
        df["Описание"] = ["Покупка", "Такси", "Покупка"]

    # Мокируем зависимости
    with (
        patch("src.reports.get_period_last_3_month") as mock_get_period,
        patch("src.reports.get_slice_df_full_month") as mock_get_slice,
        patch("src.reports.get_expenses_by_category") as mock_get_expenses,
    ):

        # Настраиваем моки
        mock_get_period.return_value = ["01.12.2023 00:00:00", "20.12.2023 23:59:59"]
        mock_get_slice.return_value = df
        mock_get_expenses.return_value = df[df["Категория"] == "Еда"]

        # Вызываем функцию
        result = spending_by_category(df, "Еда", "2023-12-20 23:59:59")

        # Проверяем
        assert not result.empty
        mock_get_period.assert_called_once_with("2023-12-20 23:59:59")
        mock_get_slice.assert_called_once()
        mock_get_expenses.assert_called_once()


def test_spending_by_category_error_in_get_period(sample_dataframe):
    """Тест: ошибка при получении периода"""
    with patch("src.reports.get_period_last_3_month") as mock_get_period:
        mock_get_period.side_effect = Exception("Ошибка периода")

        result = spending_by_category(sample_dataframe, "Еда")

        assert result.empty
        mock_get_period.assert_called_once()


def test_spending_by_category_error_in_get_slice(sample_dataframe):
    """Тест: ошибка при обрезке DataFrame"""
    with (
        patch("src.reports.get_period_last_3_month") as mock_get_period,
        patch("src.reports.get_slice_df_full_month") as mock_get_slice,
    ):
        mock_get_period.return_value = ["01.01.2024 00:00:00", "30.04.2024 23:59:59"]
        mock_get_slice.side_effect = Exception("Ошибка обрезки")

        result = spending_by_category(sample_dataframe, "Еда")

        assert result.empty
        mock_get_slice.assert_called_once()


def test_spending_by_category_error_in_get_expenses(sample_dataframe):
    """Тест: ошибка при получении расходов по категории"""
    with (
        patch("src.reports.get_period_last_3_month") as mock_get_period,
        patch("src.reports.get_slice_df_full_month") as mock_get_slice,
        patch("src.reports.get_expenses_by_category") as mock_get_expenses,
    ):
        mock_get_period.return_value = ["01.01.2024 00:00:00", "30.04.2024 23:59:59"]
        mock_get_slice.return_value = sample_dataframe
        mock_get_expenses.side_effect = Exception("Ошибка категории")

        result = spending_by_category(sample_dataframe, "Еда")

        assert result.empty
        mock_get_expenses.assert_called_once()


def test_spending_by_category_empty_result():
    """Тест: пустой результат (нет расходов по категории)"""
    # DataFrame без расходов по категории "Еда"
    data = {
        "Дата операции": pd.to_datetime(["2024-01-15", "2024-02-15"]),
        "Категория": ["Транспорт", "Транспорт"],
        "Сумма операции": [-100, -200],
        "Описание": ["Такси", "Метро"],
    }
    df = pd.DataFrame(data)

    with (
        patch("src.reports.get_period_last_3_month") as mock_get_period,
        patch("src.reports.get_slice_df_full_month") as mock_get_slice,
        patch("src.reports.get_expenses_by_category") as mock_get_expenses,
    ):
        mock_get_period.return_value = ["01.01.2024 00:00:00", "30.04.2024 23:59:59"]
        mock_get_slice.return_value = df
        mock_get_expenses.return_value = pd.DataFrame()  # Пустой результат

        result = spending_by_category(df, "Еда")

        assert result.empty


# Тесты для декоратора save_result_in_file
def test_decorator_success():
    """Тест: декоратор успешно записывает результат в файл"""
    # Создаем временную директорию для тестов
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Создаем папку log_result
        log_dir = temp_path / "log_result"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Мокаем BASE_DIR
        with patch("src.reports.BASE_DIR", temp_path):
            # Создаем тестовую функцию с декоратором
            @save_result_in_file()
            def test_function():
                json_str1 = '{"test": "data1", "value": 123}'
                json_str2 = '{"test": "data2", "value": 456}'
                df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
                return [json_str1, json_str2, df]

            # Вызываем декорированную функцию
            result = test_function()

            # Проверяем результат функции
            assert isinstance(result, list)
            assert len(result) == 3

            # Проверяем, что файл создался
            files = list(log_dir.glob("test_function*.txt"))
            assert len(files) == 1


def test_decorator_with_custom_filename():
    """Тест: декоратор с кастомным именем файла"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch("src.reports.BASE_DIR", Path(temp_dir)):

            @save_result_in_file("custom_name")
            def test_function():
                return ["{}", "{}", pd.DataFrame()]

            test_function()

            # Проверяем имя файла
            log_dir = Path(temp_dir) / "log_result"
            files = list(log_dir.glob("custom_name*.txt"))
            assert len(files) == 1
            assert files[0].name.startswith("custom_name")


def test_decorator_with_exception():
    """Тест: декоратор обрабатывает исключения"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch("src.reports.BASE_DIR", Path(temp_dir)):

            @save_result_in_file()
            def test_function():
                raise ValueError("Тестовая ошибка")

            result = test_function()

            # Функция должна вернуть None при ошибке
            assert result is None

            # Проверяем, что файл создался
            log_dir = Path(temp_dir) / "log_result"
            files = list(log_dir.glob("test_function*.txt"))
            assert len(files) == 1

            # Проверяем содержимое файла (должно быть пустым для formatted_content)
            file_path = files[0]
            with open(file_path, "r", encoding="UTF8") as f:
                content = f.read()

            # Проверяем наличие сообщения об ошибке в логе
            assert "Error" in content
            assert "Тестовая ошибка" in content


def test_decorator_with_empty_list():
    """Тест: декоратор с пустым списком"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch("src.reports.BASE_DIR", Path(temp_dir)):

            @save_result_in_file()
            def test_function():
                return []

            result = test_function()

            assert result == []

            # Проверяем, что файл создался (даже с пустым результатом)
            log_dir = Path(temp_dir) / "log_result"
            files = list(log_dir.glob("test_function*.txt"))
            assert len(files) == 1


def test_decorator_preserves_function_name():
    """Тест: декоратор сохраняет имя оригинальной функции"""

    @save_result_in_file()
    def original_function():
        return []

    assert original_function.__name__ == "original_function"


def test_decorator_with_partial_results():
    """Тест: декоратор с неполным списком результатов"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch("src.reports.BASE_DIR", Path(temp_dir)):

            @save_result_in_file()
            def test_function():
                # Только один элемент вместо трех
                return ['{"test": "data"}']

            result = test_function()

            assert len(result) == 1

            # Проверяем, что файл создался
            log_dir = Path(temp_dir) / "log_result"
            files = list(log_dir.glob("test_function*.txt"))
            assert len(files) == 1

            # Проверяем, что JSON записан корректно
            file_path = files[0]
            with open(file_path, "r", encoding="UTF8") as f:
                content = f.read()

            assert '"test": "data"' in content


def test_decorator_with_invalid_json():
    """Тест: декоратор с некорректным JSON"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch("src.reports.BASE_DIR", Path(temp_dir)):

            @save_result_in_file()
            def test_function():
                # Некорректный JSON
                return ["{invalid json}", "{}", pd.DataFrame()]

            result = test_function()

            # Должен вернуть None, так как произошло исключение при обработке JSON
            assert result is None

            # Проверяем, что файл создался
            log_dir = Path(temp_dir) / "log_result"
            files = list(log_dir.glob("test_function*.txt"))
            assert len(files) == 1

            # Проверяем содержимое файла (должно быть пустым для formatted_content, но с логом ошибки)
            file_path = files[0]
            with open(file_path, "r", encoding="UTF8") as f:
                content = f.read()

            # Проверяем наличие сообщения об ошибке в логе
            assert "Error" in content
            assert "test_function" in content
