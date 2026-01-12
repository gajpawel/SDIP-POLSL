from utils.runs_on_date import runs_on_date
from datetime import date

start_date = date(2023, 1, 1)
end_date = date(2023, 12, 31)
days_mask = 0b0011111  # Kursuje w dni powszednie (Pn-Pt)

def test_runs_on_date_within_range_and_day():
    target_date = date(2023, 3, 15)  # Sroda
    assert runs_on_date(start_date, end_date, days_mask, target_date) == True

def test_runs_on_date_out_of_range():
    target_date = date(2024, 1, 1)  # Poza zakresem
    assert runs_on_date(start_date, end_date, days_mask, target_date) == False

def test_runs_on_date_not_scheduled_day():
    target_date = date(2023, 3, 18)  # Sobota
    assert runs_on_date(start_date, end_date, days_mask, target_date) == False

def test_runs_on_date_edge_case_start_date():
    target_date = date(2023, 1, 1)  # Niedziela (nie kursuje)
    assert runs_on_date(start_date, end_date, days_mask, target_date) == False