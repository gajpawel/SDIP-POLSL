from datetime import date

def runs_on_date(start_date, end_date, days_mask, target_date: date):
        if not (start_date <= target_date <= end_date):
            return False
        weekday = target_date.weekday()
        return bool(days_mask & (1 << weekday))