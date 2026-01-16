import json
from unittest.mock import MagicMock, patch

import pandas as pd

from src.views import main_response


def test_main_response_success_simple():
    """Упрощенный тест успешного выполнения"""

    mock_dependencies = {
        "get_xlsx_path": "test.xlsx",
        "time_for_greeting": "Добрый день",
        "get_time_period": ["01.01.2024 00:00:00", "20.01.2024 16:20:00"],
        "slice_period_and_sort_df": MagicMock(spec=pd.DataFrame),
        "spending_on_the_card": [{"last_digits": "1234", "total_spent": 1000.0, "cashback": 50.0}],
        "get_top_transactions": [
            {"date": "20.01.2024", "amount": 5000.0, "category": "Еда", "description": "Ресторан"}
        ],
        "open_json": {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "TSLA"]},
        "currency_api": ([{"currency": "USD", "rate": 90.5}], 90.5),
        "current_stock_prise": [{"stock": "AAPL", "price": 18000.0}],
    }

    patches = []
    for func_name, return_value in mock_dependencies.items():
        if func_name == "slice_period_and_sort_df":
            patch_obj = patch(f"src.views.{func_name}", return_value=MagicMock(spec=pd.DataFrame))
        else:
            patch_obj = patch(f"src.views.{func_name}", return_value=return_value)
        patches.append(patch_obj)

    mocks = []
    for patch_obj in patches:
        mocks.append(patch_obj.__enter__())

    mock_base_dir = mocks[-1]
    mock_base_dir.joinpath.return_value = MagicMock()

    try:

        result = main_response("2024-01-20 16:20:00")

        assert isinstance(result, str)

        data = json.loads(result)

        assert "greeting" in data
        assert "cards" in data
        assert "top_transactions" in data
        assert "currency_rates" in data
        assert "stock_prices" in data

    finally:

        for patch_obj in patches:
            patch_obj.__exit__(None, None, None)


def test_main_response_empty_dict_on_error():
    """Тест, что при ошибке json.dumps возвращается пустой словарь"""

    with (
        patch("src.views.get_xlsx_path", return_value="test.xlsx"),
        patch("src.views.BASE_DIR") as mock_base_dir,
        patch("src.views.time_for_greeting", return_value="Добрый день"),
        patch("src.views.get_time_period", return_value=["01.01.2024 00:00:00", "20.01.2024 16:20:00"]),
        patch("src.views.slice_period_and_sort_df", return_value=MagicMock(spec=pd.DataFrame)),
        patch("src.views.spending_on_the_card", return_value=[{"last_digits": "1234", "total_spent": 1000.0}]),
        patch("src.views.get_top_transactions", return_value=[{"date": "20.01.2024", "amount": 5000.0}]),
        patch("src.views.open_json", return_value={"user_currencies": ["USD"]}),
        patch("src.views.currency_api", return_value=([{"currency": "USD", "rate": 90.5}], 90.5)),
        patch("src.views.current_stock_prise", return_value=[{"stock": "AAPL", "price": 18000.0}]),
        patch("json.dumps", side_effect=Exception("Test error")),
    ):
        mock_base_dir.joinpath.return_value = MagicMock()

        result = main_response("2024-01-20 16:20:00")

        assert result == {}
