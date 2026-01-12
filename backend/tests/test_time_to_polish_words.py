from utils.time_to_polish_words import time_to_polish_words

def test_full_hours():
    assert time_to_polish_words("00:00") == "zerowej zero zero"
    assert time_to_polish_words("12:00") == "dwunastej zero zero"
    assert time_to_polish_words("23:00") == "dwudziestej trzeciej zero zero"

def test_single_digit_minutes():
    assert time_to_polish_words("01:05") == "pierwszej zero pięć"
    assert time_to_polish_words("09:09") == "dziewiątej zero dziewięć"
    assert time_to_polish_words("20:01") == "dwudziestej zero jeden"

def test_teens_minutes():
    assert time_to_polish_words("10:10") == "dziesiątej dziesięć"
    assert time_to_polish_words("15:11") == "piętnastej jedenaście"
    assert time_to_polish_words("22:19") == "dwudziestej drugiej dziewiętnaście"

def test_regular_minutes():
    assert time_to_polish_words("08:20") == "ósmej dwadzieścia"
    assert time_to_polish_words("14:35") == "czternastej trzydzieści pięć"
    assert time_to_polish_words("18:59") == "osiemnastej pięćdziesiąt dziewięć"

def test_invalid_inputs():
    assert time_to_polish_words("") == ""
    assert time_to_polish_words(None) == ""
    assert time_to_polish_words("25:00") == ""
    assert time_to_polish_words("10:65") == ""

    