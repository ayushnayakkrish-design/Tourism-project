from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CrowdObservation
from app.schemas import CrowdObservationCreate
from app.services.crowd.collector import normalize_crowd_level
from app.services.crowd.predictor import best_time_slots, predict_from_observations

router = APIRouter()


@router.post("/observations", status_code=201)
def create_observation(data: CrowdObservationCreate, db: Session = Depends(get_db)):
    try:
        level = normalize_crowd_level(data.crowd_level)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "INVALID_CROWD_LEVEL", "message": str(exc)}) from exc
    obs = CrowdObservation(
        place_id=data.place_id,
        timestamp=data.timestamp or datetime.now(timezone.utc),
        crowd_level=level,
        source=data.source,
        confidence=data.confidence,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return {
        "id": obs.id,
        "place_id": obs.place_id,
        "timestamp": obs.timestamp,
        "crowd_level": obs.crowd_level,
        "source": obs.source,
        "confidence": obs.confidence,
    }


@router.get("/{place_id}")
def crowd(place_id: str, db: Session = Depends(get_db)):
    observations = (
        db.query(CrowdObservation)
        .filter(CrowdObservation.place_id == place_id)
        .order_by(CrowdObservation.timestamp.desc())
        .limit(200)
        .all()
    )
    prediction = predict_from_observations(observations, datetime.now().hour)
    return {
        "place_id": place_id,
        "prediction": prediction,
        "observations": [
            {"timestamp": x.timestamp, "crowd_level": x.crowd_level, "source": x.source, "confidence": x.confidence}
            for x in observations
        ],
    }


@router.get("/{place_id}/best-time")
def best_time(place_id: str, db: Session = Depends(get_db)):
    observations = (
        db.query(CrowdObservation)
        .filter(CrowdObservation.place_id == place_id)
        .all()
    )
    slots = best_time_slots(observations)
    return {"place_id": place_id, "recommended_slots": slots[:5]}
