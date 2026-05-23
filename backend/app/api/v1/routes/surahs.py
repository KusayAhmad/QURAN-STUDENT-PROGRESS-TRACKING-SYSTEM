"""Surah read-only routes."""
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.repositories import surah_repo
from app.schemas.surah import SurahRead

router = APIRouter(prefix="/surahs", tags=["surahs"])


@router.get("", response_model=list[SurahRead])
async def list_surahs(db: DbSession, _: CurrentUser) -> list[SurahRead]:
    surahs = await surah_repo.list_all(db)
    return [SurahRead.model_validate(s) for s in surahs]


@router.get("/{surah_id}", response_model=SurahRead)
async def get_surah(surah_id: int, db: DbSession, _: CurrentUser) -> SurahRead:
    surah = await surah_repo.get_by_id(db, surah_id)
    if surah is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Surah not found")
    return SurahRead.model_validate(surah)
