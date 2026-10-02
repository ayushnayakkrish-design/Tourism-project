from datetime import datetime, timezone
from app.database import SessionLocal
from app.models import CrowdObservation, PlaceSeasonProfile
from app.services.season import calculate_overall

db = SessionLocal()

# Replace these IDs with real Google Place IDs after searching.
DEMO_PLACE = "demo_konark"

crowd = [
    ("VERY_LOW", 8), ("LOW", 9), ("MODERATE", 10),
    ("HIGH", 11), ("HIGH", 12), ("MODERATE", 13),
    ("HIGH", 16), ("VERY_HIGH", 17),
]
for level, hour in crowd:
    db.add(CrowdObservation(
        place_id=DEMO_PLACE,
        timestamp=datetime(2026, 10, 2, hour, tzinfo=timezone.utc),
        crowd_level=level,
        source="demo",
        confidence=0.8,
    ))

for month in range(1, 13):
    weather = 90 if month in [10, 11, 12, 1, 2] else 65
    crowd_score = 85 if month in [6, 7, 8] else 70
    festival = 75
    access = 90
    overall = calculate_overall(weather, crowd_score, festival, access)
    db.add(PlaceSeasonProfile(
        place_id=DEMO_PLACE,
        month=month,
        weather_score=weather,
        crowd_score=crowd_score,
        festival_score=festival,
        accessibility_score=access,
        overall_score=overall,
        reason="Demo data; replace with researched/local tourism data.",
    ))

db.commit()
db.close()
print("Demo data inserted.")
