from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PlaceSeasonProfile
from app.schemas import SeasonProfileCreate, SeasonRequest
from app.services.season import MONTHS, calculate_overall

router = APIRouter()


@router.post("/profiles", status_code=201)
def create_profile(data: SeasonProfileCreate, db: Session = Depends(get_db)):
    overall = calculate_overall(data.weather_score, data.crowd_score, data.festival_score, data.accessibility_score)
    row = db.query(PlaceSeasonProfile).filter_by(place_id=data.place_id, month=data.month).first()
    if row:
        row.weather_score = data.weather_score
        row.crowd_score = data.crowd_score
        row.festival_score = data.festival_score
        row.accessibility_score = data.accessibility_score
        row.overall_score = overall
        row.reason = data.reason
    else:
        row = PlaceSeasonProfile(
            place_id=data.place_id,
            month=data.month,
            weather_score=data.weather_score,
            crowd_score=data.crowd_score,
            festival_score=data.festival_score,
            accessibility_score=data.accessibility_score,
            overall_score=overall,
            reason=data.reason,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "place_id": row.place_id, "month": MONTHS[row.month], "overall_score": row.overall_score, "reason": row.reason}


@router.post("/recommend")
def recommend(data: SeasonRequest, db: Session = Depends(get_db)):
    rows = (
        db.query(PlaceSeasonProfile)
        .filter(PlaceSeasonProfile.place_id == data.place_id)
        .order_by(PlaceSeasonProfile.overall_score.desc())
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail={"code": "SEASON_DATA_NOT_FOUND", "message": "No seasonal profiles found for this place"})
    requested = next((row for row in rows if row.month == data.month), None)
    return {
        "place_id": data.place_id,
        "requested_month": {"month": MONTHS[data.month], "score": requested.overall_score, "reason": requested.reason} if requested else None,
        "best_month": {"month": MONTHS[rows[0].month], "score": rows[0].overall_score, "reason": rows[0].reason},
        "all_months": [{"month": MONTHS[x.month], "score": x.overall_score, "reason": x.reason} for x in sorted(rows, key=lambda r: r.month)],
    }
