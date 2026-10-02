"""
Developer 2 — Visit Service.

Orchestrates visit creation, GPS verification, anti-cheat, and reward granting.
"""
from __future__ import annotations

import hashlib
import io
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.gamification.anti_cheat import AntiCheatService
from app.gamification.gps_verification import verify_gps
from app.gamification.models import (
    TransactionType,
    Visit,
    VisitProof,
    VisitStatus,
    ProofStatus,
)
from app.gamification.place_provider import PlaceProvider
from app.gamification.storage_provider import StorageProvider
from app.gamification.wallet_service import WalletService

_ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
_MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB

_anti_cheat = AntiCheatService()
_wallet_svc = WalletService()


class VisitService:

    def __init__(
        self,
        place_provider: PlaceProvider,
        storage_provider: StorageProvider,
    ) -> None:
        self._places = place_provider
        self._storage = storage_provider

    # ------------------------------------------------------------------
    # Create and verify a visit
    # ------------------------------------------------------------------

    async def create_visit(
        self,
        db: Session,
        user_id: str,
        place_id: str,
        user_lat: float,
        user_lon: float,
        visit_timestamp: datetime,
    ) -> Visit:
        """
        1. Fetch place from Developer 1's provider.
        2. Calculate GPS distance.
        3. Run anti-cheat checks.
        4. Persist visit with VERIFIED / FLAGGED / REJECTED status.
        5. Award visit points if VERIFIED (idempotent).
        """
        # Normalise timestamp timezone
        if visit_timestamp.tzinfo is None:
            visit_timestamp = visit_timestamp.replace(tzinfo=timezone.utc)

        # --- Fetch place ---
        place = await self._places.get_place(place_id)

        # --- GPS verification ---
        gps_result = verify_gps(
            user_lat, user_lon,
            place.latitude, place.longitude,
            place.verification_radius,
        )

        # --- Gather context for anti-cheat ---
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        recent_visits = (
            db.query(Visit)
            .filter(
                Visit.user_id == user_id,
                Visit.created_at >= today_start,
            )
            .order_by(Visit.created_at.desc())
            .all()
        )
        previous_verified = (
            db.query(Visit)
            .filter(
                Visit.user_id == user_id,
                Visit.status == VisitStatus.VERIFIED,
            )
            .order_by(Visit.created_at.desc())
            .limit(5)
            .all()
        )

        # --- Anti-cheat evaluation ---
        ac_decision = _anti_cheat.evaluate_visit(
            distance_metres=gps_result.distance_metres,
            verification_radius=place.verification_radius,
            visit_lat=user_lat,
            visit_lon=user_lon,
            visit_timestamp=visit_timestamp,
            request_time=datetime.now(timezone.utc),
            user_id=user_id,
            place_id=place_id,
            recent_visits=recent_visits,
            previous_verified_visits=previous_verified,
            today_visit_count=len(recent_visits),
        )

        # --- Persist visit ---
        rejection_reason: Optional[str] = None
        if ac_decision.decision in (VisitStatus.REJECTED, VisitStatus.FLAGGED):
            rejection_reason = ", ".join(ac_decision.reasons)

        visit = Visit(
            user_id=user_id,
            place_id=place_id,
            latitude=user_lat,
            longitude=user_lon,
            timestamp=visit_timestamp,
            status=ac_decision.decision,
            verification_method="GPS",
            verification_radius=place.verification_radius,
            distance_from_place=gps_result.distance_metres,
            rejection_reason=rejection_reason,
        )
        db.add(visit)
        db.flush()  # get visit.id without committing

        # --- Award visit points (VERIFIED only, idempotent) ---
        if ac_decision.decision == VisitStatus.VERIFIED and not visit.visit_reward_granted:
            pts = settings.VISIT_REWARD_POINTS
            _wallet_svc.credit(
                db=db,
                user_id=user_id,
                amount=pts,
                transaction_type=TransactionType.VISIT_REWARD,
                reference_id=str(visit.id),
                description=f"Visit reward: {place.name}",
            )
            visit.visit_reward_granted = True
            db.flush()

        db.commit()
        db.refresh(visit)
        return visit

    # ------------------------------------------------------------------
    # Upload photo proof for an existing visit
    # ------------------------------------------------------------------

    async def upload_proof(
        self,
        db: Session,
        user_id: str,
        visit_id: int,
        file: UploadFile,
        proof_lat: Optional[float] = None,
        proof_lon: Optional[float] = None,
    ) -> VisitProof:
        """
        1. Validate ownership of the visit.
        2. Validate image.
        3. Check for duplicate hashes.
        4. Store image.
        5. Award photo points if visit is VERIFIED (once per visit).
        """
        visit = db.get(Visit, visit_id)
        if visit is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "VISIT_NOT_FOUND", "message": "Visit not found"},
            )
        if visit.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN", "message": "You do not own this visit"},
            )

        # --- Validate image ---
        content_type = file.content_type or ""
        if content_type not in _ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INVALID_IMAGE_TYPE",
                    "message": f"Unsupported image type '{content_type}'. Allowed: {sorted(_ALLOWED_MIME_TYPES)}",
                },
            )

        data = await file.read()

        if len(data) > _MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "FILE_TOO_LARGE",
                    "message": f"Image exceeds maximum size of {_MAX_FILE_SIZE_BYTES // (1024*1024)} MB",
                },
            )

        if len(data) < 100:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_IMAGE", "message": "File is too small to be a valid image"},
            )

        # --- Compute SHA-256 ---
        file_hash = hashlib.sha256(data).hexdigest()

        # --- Duplicate hash check ---
        existing_hashes = [
            p.file_hash
            for p in db.query(VisitProof).filter(VisitProof.file_hash == file_hash).all()
        ]
        if existing_hashes:
            ac = AntiCheatService()
            decision_obj = __import__(
                "app.gamification.anti_cheat", fromlist=["AntiCheatDecision"]
            ).AntiCheatDecision(decision="VERIFIED")
            ac.check_duplicate_proof(file_hash, existing_hashes, decision_obj)
            if decision_obj.decision == "REJECTED":
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "DUPLICATE_PROOF",
                        "message": "This image has already been uploaded as proof",
                    },
                )

        # --- Store image ---
        image_url = await self._storage.store_image(
            data,
            file.filename or "upload.jpg",
            file_hash,
        )

        # --- Persist proof ---
        proof = VisitProof(
            visit_id=visit.id,
            image_url=image_url,
            latitude=proof_lat,
            longitude=proof_lon,
            timestamp=datetime.now(timezone.utc),
            verification_status=ProofStatus.ACCEPTED,
            file_hash=file_hash,
            metadata_={"content_type": content_type, "size_bytes": len(data)},
        )
        db.add(proof)
        db.flush()

        # --- Award photo points (VERIFIED visit, once per visit) ---
        if visit.status == VisitStatus.VERIFIED and not visit.photo_reward_granted:
            pts = settings.PHOTO_REWARD_POINTS
            _wallet_svc.credit(
                db=db,
                user_id=user_id,
                amount=pts,
                transaction_type=TransactionType.PHOTO_REWARD,
                reference_id=str(visit.id),
                description=f"Photo proof reward for visit {visit.id}",
            )
            visit.photo_reward_granted = True
            db.flush()

        db.commit()
        db.refresh(proof)
        return proof

    # ------------------------------------------------------------------
    # Get a visit (ownership enforced)
    # ------------------------------------------------------------------

    def get_visit(self, db: Session, user_id: str, visit_id: int) -> Visit:
        visit = db.get(Visit, visit_id)
        if visit is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "VISIT_NOT_FOUND", "message": "Visit not found"},
            )
        if visit.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN", "message": "You do not own this visit"},
            )
        return visit

    # ------------------------------------------------------------------
    # List visits for a user
    # ------------------------------------------------------------------

    def list_visits(
        self,
        db: Session,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Visit], int]:
        base_q = db.query(Visit).filter(Visit.user_id == user_id)
        total = base_q.count()
        items = (
            base_q
            .order_by(Visit.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total
