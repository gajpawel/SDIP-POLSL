from utils.roman_to_arabic import roman_to_arabic

def test_roman_to_arabic_basic():
    assert roman_to_arabic("III") == 3
    assert roman_to_arabic("IV") == 4
    assert roman_to_arabic("IX") == 9
    assert roman_to_arabic("LVIII") == 58
    assert roman_to_arabic("MCMXCIV") == 1994

def test_roman_to_arabic_edge_cases():
    assert roman_to_arabic("") == 0
    assert roman_to_arabic("MMMCMXCIX") == 3999
    assert roman_to_arabic("XLII") == 42
    assert roman_to_arabic("CDXLIV") == 444

def test_roman_to_arabic_invalid():
    assert roman_to_arabic("A") == 0
    assert roman_to_arabic("IIII") == 4 
    assert roman_to_arabic("VV") == 10