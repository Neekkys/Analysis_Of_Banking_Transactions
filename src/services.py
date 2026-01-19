from pandas import DataFrame
from typing import Dict
from src.utils import

def get_increased_cashback(data: DataFrame, year: str, month: str) -> Dict:

    time_period = get_time_month_period()