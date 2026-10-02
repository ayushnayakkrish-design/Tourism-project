LEVEL_SCORE = {
    "VERY_LOW": 100,
    "LOW": 80,
    "MODERATE": 60,
    "HIGH": 30,
    "VERY_HIGH": 10,
}

def crowd_score(level: str) -> int:
    return LEVEL_SCORE.get(level.upper(), 50)
