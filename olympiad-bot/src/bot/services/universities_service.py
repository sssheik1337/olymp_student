"""Сервис подбора ВУЗов по избранным олимпиадам."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repository.db import AsyncSessionLocal
from bot.repository.models import Olympiad, User, UserOlympiad


@dataclass(frozen=True, slots=True)
class FacultyInfo:
    """Описание факультета в демо-данных."""

    title: str
    description: str
    benefits: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class UniversityData:
    """Демо-информация о ВУЗе и связанных олимпиадах."""

    id: int
    name: str
    description: str
    olympiad_ids: tuple[int, ...]
    benefits: tuple[str, ...]
    faculties: tuple[FacultyInfo, ...]


@dataclass(frozen=True, slots=True)
class UniversityRecommendation:
    """Подборка ВУЗа с учётом избранных олимпиад пользователя."""

    id: int
    name: str
    description: str
    benefits: tuple[str, ...]
    matched_olympiads: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class UniversityDetail:
    """Расширенная информация о ВУЗе для экранов детализации."""

    id: int
    name: str
    description: str
    benefits: tuple[str, ...]
    matched_olympiads: tuple[str, ...]
    faculties: tuple[FacultyInfo, ...]


DEMO_UNIVERSITIES: tuple[UniversityData, ...] = (
    UniversityData(
        id=1,
        name="НИУ ВШЭ",
        description="БВИ и дополнительные баллы за профильные олимпиады.",
        olympiad_ids=(1, 3, 4),
        benefits=(
            "БВИ на ИПМиМ и ФКН по олимпиадам ВШЭ и ВсОШ",
            "100 баллов ЕГЭ по профильному предмету",
        ),
        faculties=(
            FacultyInfo(
                title="Факультет компьютерных наук",
                description="Направления программной инженерии, анализа данных и ИИ.",
                benefits=(
                    "БВИ для призёров НТИ и ВсОШ по информатике",
                    "Именные стипендии первокурсникам-олимпиадникам",
                ),
            ),
            FacultyInfo(
                title="Факультет математики",
                description="Совместные программы с РЭШ и зарубежными вузами.",
                benefits=(
                    "Высший приоритет при поступлении по олимпиадам НИУ ВШЭ",
                    "Льготное заселение в кампус",
                ),
            ),
        ),
    ),
    UniversityData(
        id=2,
        name="МФТИ",
        description="Физтех поддерживает призёров инженерных олимпиад.",
        olympiad_ids=(3, 5),
        benefits=(
            "БВИ на ФИВТ и ФАКИ за призовые места",
            "Усиленная стипендия и наставничество",
        ),
        faculties=(
            FacultyInfo(
                title="ФИВТ",
                description="Программирование, алгоритмы и суперкомпьютеры.",
                benefits=(
                    "БВИ по олимпиадам НТИ и Физтех",
                    "Участие в проектных командах с 1 курса",
                ),
            ),
            FacultyInfo(
                title="ФАКИ",
                description="Физика, квантовые технологии и исследования.",
                benefits=(
                    "100 баллов за физику при призе Физтех",
                    "Повышенная стипендия «Физтех»",
                ),
            ),
        ),
    ),
    UniversityData(
        id=3,
        name="МГУ имени М. В. Ломоносова",
        description="Классические программы и расширенные квоты для олимпиадников.",
        olympiad_ids=(2, 6),
        benefits=(
            "БВИ на мехмат и ВМК по олимпиадам «Ломоносов» и ВсОШ",
            "Дополнительные баллы к конкурсу аттестатов",
        ),
        faculties=(
            FacultyInfo(
                title="Механико-математический факультет",
                description="Фундаментальная математика и исследовательские школы.",
                benefits=(
                    "БВИ за призы ВсОШ по математике",
                    "Участие в научных лабораториях с первого курса",
                ),
            ),
            FacultyInfo(
                title="Факультет вычислительной математики и кибернетики",
                description="Разработка алгоритмов, ИИ и суперкомпьютерные технологии.",
                benefits=(
                    "БВИ за олимпиаду «Ломоносов» по информатике",
                    "Персональные гранты для лучших абитуриентов",
                ),
            ),
        ),
    ),
)


class UniversitiesService:
    """Подбор ВУЗов на основе избранных олимпиад пользователя."""

    def __init__(self, session_factory: type[AsyncSession] | None = None) -> None:
        self._session_factory = session_factory or AsyncSessionLocal
        self._universities: Mapping[int, UniversityData] = {
            item.id: item for item in DEMO_UNIVERSITIES
        }

    async def list_recommendations(self, *, tg_user_id: int) -> Sequence[UniversityRecommendation]:
        """Вернуть демо-подборку ВУЗов для пользователя."""

        async with self._session_factory() as session:
            favorites = await self._load_favorites(session, tg_user_id)

        if not favorites:
            return ()

        recommendations: list[UniversityRecommendation] = []
        for university in self._universities.values():
            matched_titles = [
                favorites[olymp_id]
                for olymp_id in university.olympiad_ids
                if olymp_id in favorites
            ]
            if not matched_titles:
                continue
            recommendations.append(
                UniversityRecommendation(
                    id=university.id,
                    name=university.name,
                    description=university.description,
                    benefits=university.benefits,
                    matched_olympiads=tuple(matched_titles),
                )
            )

        recommendations.sort(
            key=lambda item: (-len(item.matched_olympiads), item.name.lower())
        )
        return tuple(recommendations)

    async def get_details(
        self, *, tg_user_id: int, university_id: int
    ) -> UniversityDetail | None:
        """Получить детальную информацию по выбранному ВУЗу."""

        university = self._universities.get(university_id)
        if university is None:
            return None

        async with self._session_factory() as session:
            favorites = await self._load_favorites(session, tg_user_id)

        matched_titles = tuple(
            favorites[olymp_id]
            for olymp_id in university.olympiad_ids
            if olymp_id in favorites
        )
        if not matched_titles:
            return None

        return UniversityDetail(
            id=university.id,
            name=university.name,
            description=university.description,
            benefits=university.benefits,
            matched_olympiads=matched_titles,
            faculties=university.faculties,
        )

    async def _load_favorites(
        self, session: AsyncSession, tg_user_id: int
    ) -> Mapping[int, str]:
        """Получить избранные олимпиады пользователя."""

        stmt = (
            select(Olympiad.id, Olympiad.title)
            .join(UserOlympiad, UserOlympiad.olympiad_id == Olympiad.id)
            .join(User, User.id == UserOlympiad.user_id)
            .where(User.tg_id == tg_user_id)
        )
        result = await session.execute(stmt)
        return {olymp_id: title for olymp_id, title in result.all()}


@lru_cache
def get_universities_service() -> UniversitiesService:
    """Получить singleton-сервис подбора ВУЗов."""

    return UniversitiesService()


__all__ = [
    "FacultyInfo",
    "UniversityDetail",
    "UniversityRecommendation",
    "UniversitiesService",
    "get_universities_service",
]
