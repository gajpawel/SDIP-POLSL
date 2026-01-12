from utils.track_collision import is_collision

def test_no_collision_simple():
    assert not is_collision(60, 70, 80, 90)

def test_collision_overlap():
    assert is_collision(60, 80, 70, 90)

def test_collision_single_minute():
    assert is_collision(None, 120, 120, None)

def test_no_collision_midnight_wrap():
    assert is_collision(1380, 15, 10, 20)