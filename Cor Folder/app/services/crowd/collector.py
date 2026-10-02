def normalize_crowd_level(value: str) -> str:
    value = value.strip().upper().replace(" ", "_")
    allowed = {"VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH"}
    if value not in allowed:
        raise ValueError(f"crowd_level must be one of {sorted(allowed)}")
    return value
