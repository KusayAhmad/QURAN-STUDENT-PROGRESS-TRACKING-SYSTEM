"""Static Quran surah metadata."""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QuranSurah(Base):
    """The 114 surahs of the Quran. Seeded once, read-only after.

    NOTE: `juz_no` and `hizb_no` here represent the *starting* juz/hizb of the surah.
    Surahs span multiple juz; a more granular ayah-level mapping is a future enhancement.
    """

    __tablename__ = "quran_surahs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    surah_order: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    surah_name_ar: Mapped[str] = mapped_column(String(80), nullable=False)
    surah_name_en: Mapped[str] = mapped_column(String(80), nullable=False)
    ayah_count: Mapped[int] = mapped_column(Integer, nullable=False)
    juz_no: Mapped[int] = mapped_column(Integer, nullable=False, comment="Starting juz")
    hizb_no: Mapped[int] = mapped_column(Integer, nullable=False, comment="Starting hizb")
