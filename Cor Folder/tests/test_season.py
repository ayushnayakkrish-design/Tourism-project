from app.services.season import calculate_overall


def test_overall_score():
    assert calculate_overall(100, 100, 100, 100) == 100
    assert calculate_overall(0, 0, 0, 0) == 0


def test_weighted_score_is_bounded():
    value = calculate_overall(80, 70, 60, 90)
    assert 0 <= value <= 100
