"""Seed Quran surahs + a demo school/admin/teacher.

Usage:
    python -m seeds.seed              # idempotent
    python -m seeds.seed --demo-users # also create demo admin + teacher
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.school import School
from app.models.surah import QuranSurah
from app.models.user import User, UserRole

SEEDS_DIR = Path(__file__).parent


async def seed_surahs(db: AsyncSession) -> int:
    data = json.loads((SEEDS_DIR / "surahs.json").read_text(encoding="utf-8"))
    existing = (await db.execute(select(QuranSurah.id))).scalars().all()
    existing_ids = set(existing)
    inserted = 0
    for row in data:
        if row["id"] in existing_ids:
            continue
        db.add(QuranSurah(**row))
        inserted += 1
    await db.commit()
    return inserted


async def seed_demo_users(db: AsyncSession) -> None:
    school = (
        await db.execute(select(School).where(School.name == "Demo School"))
    ).scalar_one_or_none()
    if school is None:
        school = School(name="Demo School", timezone="UTC")
        db.add(school)
        await db.flush()

    admin = (
        await db.execute(select(User).where(User.email == "admin@example.com"))
    ).scalar_one_or_none()
    if admin is None:
        db.add(
            User(
                name="Demo Admin",
                email="admin@example.com",
                password_hash=hash_password("admin123!"),
                role=UserRole.ADMIN,
                school_id=school.id,
            )
        )

    teacher = (
        await db.execute(select(User).where(User.email == "teacher@example.com"))
    ).scalar_one_or_none()
    if teacher is None:
        db.add(
            User(
                name="Demo Teacher",
                email="teacher@example.com",
                password_hash=hash_password("teacher123!"),
                role=UserRole.TEACHER,
                school_id=school.id,
            )
        )
    await db.commit()


async def main(demo_users: bool) -> None:
    async with AsyncSessionLocal() as db:
        inserted = await seed_surahs(db)
        print(f"Surahs inserted: {inserted} (114 total expected)")
        if demo_users:
            await seed_demo_users(db)
            print("Demo users ensured: admin@example.com / teacher@example.com")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-users", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.demo_users))
