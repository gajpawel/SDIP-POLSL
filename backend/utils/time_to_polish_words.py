def time_to_polish_words(time_str: str) -> str:
    if not time_str:
        return ""

    try:
        hours, minutes = map(int, time_str.split(':'))
    except (ValueError, AttributeError):
        return ""

    hours_ordinal = [
        "zerowej", "pierwszej", "drugiej", "trzeciej", "czwartej", "piątej",
        "szóstej", "siódmej", "ósmej", "dziewiątej", "dziesiątej", "jedenastej",
        "dwunastej", "trzynastej", "czternastej", "piętnastej", "szesnastej", "siedemnastej",
        "osiemnastej", "dziewiętnastej", "dwudziestej", "dwudziestej pierwszej",
        "dwudziestej drugiej", "dwudziestej trzeciej"
    ]

    ones = ["", "jeden", "dwa", "trzy", "cztery", "pięć", "sześć", "siedem", "osiem", "dziewięć"]
    teens = ["dziesięć", "jedenaście", "dwanaście", "trzynaście", "czternaście", "piętnaście", "szesnaście", "siedemnaście", "osiemnaście", "dziewiętnaście"]
    tens = ["", "", "dwadzieścia", "trzydzieści", "czterdzieści", "pięćdziesiąt"]

    def convert_minutes(m: int) -> str:
        if m == 0:
            return "zero zero"
        if m < 10:
            return f"zero {ones[m]}"
        if m < 20:
            return teens[m - 10]
        
        ten_part = tens[m // 10]
        one_part = ones[m % 10]
        return f"{ten_part} {one_part}".strip()

    if hours < 0 or hours > 23:
        return ""
    if minutes < 0 or minutes > 59:
        return ""

    return f"{hours_ordinal[hours]} {convert_minutes(minutes)}".strip()

