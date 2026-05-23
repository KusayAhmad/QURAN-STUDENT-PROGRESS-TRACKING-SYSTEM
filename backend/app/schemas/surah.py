"""Surah schemas (read-only metadata)."""
from pydantic import BaseModel, ConfigDict


class SurahRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    surah_order: int
    surah_name_ar: str
    surah_name_en: str
    ayah_count: int
    juz_no: int
    hizb_no: int
