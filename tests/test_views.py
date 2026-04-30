import json
from unittest.mock import MagicMock, patch

import pandas as pd

from src.views import main_response


def test_main_response_success_simple():
    """Упрощенный тест успешного выполнения"""

    mock_df = MagicMock(spec=pd.DataFrame)

    with (
        patch("src.views.get_xlsx_name", return_value="test.xlsx"),
        patch("src.views.BASE_DIR") as mock_base_dir,
        patch("src.views.time_for_greeting", return_value="Добрый день"),
        patch("src.views.get_time_period", return_value=["01.01.2024 00:00:00", "20.01.2024 16:20:00"]),
        patch("src.views.slice_period_and_sort_df", return_value=mock_df),
        patch(
            "src.views.spending_on_the_card",
            return_value=[{"last_digits": "1234", "total_spent": 1000.0, "cashback": 50.0}],
        ),
        patch(
            "src.views.get_top_transactions",
            return_value=[{"date": "20.01.2024", "amount": 5000.0, "category": "Еда", "description": "Ресторан"}],
        ),
        patch(
            "src.views.open_json", return_value={"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "TSLA"]}
        ),
        patch("src.views.currency_api", return_value=([{"currency": "USD", "rate": 90.5}], 90.5)),
        patch("src.views.current_stock_prise", return_value=[{"stock": "AAPL", "price": 18000.0}]),
    ):

        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_base_dir.joinpath.return_value = mock_file

        result = main_response("2024-01-20 16:20:00")

        assert isinstance(result, str)

        data = json.loads(result)

        assert "greeting" in data
        assert data["greeting"] == "Добрый день"

        assert "cards" in data
        assert isinstance(data["cards"], list)
        assert len(data["cards"]) == 1

        assert "top_transactions" in data
        assert isinstance(data["top_transactions"], list)

        assert "currency_rates" in data
        assert isinstance(data["currency_rates"], list)

        assert "stock_prices" in data
        assert isinstance(data["stock_prices"], list)


def test_main_response_empty_dict_on_error():
    """Тест, что при ошибке json.dumps возвращается пустой словарь"""

    mock_df = MagicMock(spec=pd.DataFrame)

    with (
        patch("src.views.get_xlsx_name", return_value="test.xlsx"),
        patch("src.views.BASE_DIR") as mock_base_dir,
        patch("src.views.time_for_greeting", return_value="Добрый день"),
        patch("src.views.get_time_period", return_value=["01.01.2024 00:00:00", "20.01.2024 16:20:00"]),
        patch("src.views.slice_period_and_sort_df", return_value=mock_df),
        patch("src.views.spending_on_the_card", return_value=[{"last_digits": "1234", "total_spent": 1000.0}]),
        patch("src.views.get_top_transactions", return_value=[{"date": "20.01.2024", "amount": 5000.0}]),
        patch("src.views.open_json", return_value={"user_currencies": ["USD"]}),
        patch("src.views.currency_api", return_value=([{"currency": "USD", "rate": 90.5}], 90.5)),
        patch("src.views.current_stock_prise", return_value=[{"stock": "AAPL", "price": 18000.0}]),
        patch("json.dumps", side_effect=Exception("Test error")),
    ):

        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_base_dir.joinpath.return_value = mock_file

        result = main_response("2024-01-20 16:20:00")

        assert result == {}
