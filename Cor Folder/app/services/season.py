MONTHS = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

def calculate_overall(weather, crowd, festival, accessibility):
    # Transparent weighted rule. Scores are 0-100.
    return round(
        weather * 0.35 +
        crowd * 0.30 +
        festival * 0.15 +
        accessibility * 0.20,
        2,
    )

def season_reason(row):
    return (
        f"Weather {row.weather_score:.0f}/100, "
        f"crowd {row.crowd_score:.0f}/100, "
        f"festival {row.festival_score:.0f}/100, "
        f"accessibility {row.accessibility_score:.0f}/100."
    )
