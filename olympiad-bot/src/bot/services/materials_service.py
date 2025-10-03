"""Сервис подбора материалов для подготовки."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repository.db import AsyncSessionLocal
from bot.repository.models import Material


@dataclass(frozen=True, slots=True)
class MaterialLink:
    """Ссылка на материал для подготовки."""

    title: str
    url: str


@dataclass(frozen=True, slots=True)
class MaterialsBundle:
    """Набор материалов по категориям."""

    past_problems: tuple[MaterialLink, ...]
    theory: tuple[MaterialLink, ...]
    articles: tuple[MaterialLink, ...]
    additional: tuple[MaterialLink, ...] = ()


@dataclass(frozen=True, slots=True)
class AdminMaterial:
    """Запись материала для административной панели."""

    id: int
    olympiad_id: int
    title: str
    url: str
    added_by_admin_id: int | None
    created_at: datetime


class MaterialsService:
    """Бизнес-логика формирования подборок материалов."""

    def __init__(
        self,
        demo_data: Mapping[int, MaterialsBundle] | None = None,
        session_factory: type[AsyncSession] | None = None,
    ) -> None:
        self._session_factory = session_factory or AsyncSessionLocal
        self._demo_data = demo_data or _DEFAULT_DEMO_MATERIALS

    async def get_materials(self, olympiad_id: int) -> MaterialsBundle:
        """Вернуть материалы по олимпиаде с учётом демо-заглушек и БД."""

        bundle = self._demo_data.get(olympiad_id, _DEFAULT_DEMO_MATERIALS[0])

        async with self._session_factory() as session:
            stmt = (
                select(Material)
                .where(Material.olympiad_id == olympiad_id)
                .order_by(Material.created_at.desc())
            )
            result = await session.execute(stmt)
            db_links = tuple(
                MaterialLink(title=item.title, url=item.url)
                for item in result.scalars()
            )

        if not db_links:
            return bundle

        return MaterialsBundle(
            past_problems=bundle.past_problems,
            theory=bundle.theory,
            articles=bundle.articles,
            additional=db_links,
        )

    async def list_admin_materials(self) -> Sequence[AdminMaterial]:
        """Вернуть все материалы для административного интерфейса."""

        async with self._session_factory() as session:
            stmt = select(Material).order_by(Material.created_at.desc())
            result = await session.execute(stmt)
            materials = tuple(
                self._map_admin_material(material) for material in result.scalars()
            )
        return materials

    async def get_material(self, material_id: int) -> AdminMaterial | None:
        """Получить материал по идентификатору."""

        async with self._session_factory() as session:
            material = await session.get(Material, material_id)
            if material is None:
                return None
            return self._map_admin_material(material)

    async def create_material(
        self,
        *,
        olympiad_id: int,
        title: str,
        url: str,
        admin_tg_id: int,
    ) -> AdminMaterial:
        """Создать новый материал и вернуть его представление."""

        async with self._session_factory() as session:
            async with session.begin():
                material = Material(
                    olympiad_id=olympiad_id,
                    title=title,
                    url=url,
                    added_by_admin_id=admin_tg_id,
                )
                session.add(material)
                await session.flush()
                await session.refresh(material)
                return self._map_admin_material(material)

    async def update_material(
        self,
        *,
        material_id: int,
        olympiad_id: int,
        title: str,
        url: str,
        admin_tg_id: int,
    ) -> bool:
        """Обновить существующий материал."""

        async with self._session_factory() as session:
            async with session.begin():
                material = await session.get(Material, material_id)
                if material is None:
                    return False
                material.olympiad_id = olympiad_id
                material.title = title
                material.url = url
                material.added_by_admin_id = admin_tg_id
            return True

    async def delete_material(self, material_id: int) -> bool:
        """Удалить материал по идентификатору."""

        async with self._session_factory() as session:
            async with session.begin():
                material = await session.get(Material, material_id)
                if material is None:
                    return False
                await session.delete(material)
            return True

    def _map_admin_material(self, material: Material) -> AdminMaterial:
        """Собрать dataclass с деталями материала."""

        return AdminMaterial(
            id=material.id,
            olympiad_id=material.olympiad_id,
            title=material.title,
            url=material.url,
            added_by_admin_id=material.added_by_admin_id,
            created_at=material.created_at,
        )


_DEFAULT_DEMO_MATERIALS: dict[int, MaterialsBundle] = {
    0: MaterialsBundle(
        past_problems=(
            MaterialLink(
                title="Задачи прошлых лет (PDF)",
                url="https://example.org/past-papers.pdf",
            ),
        ),
        theory=(
            MaterialLink(
                title="Теория и видеоразборы на YouTube",
                url="https://www.youtube.com/playlist?list=DEMO_OLYMPIAD",
            ),
        ),
        articles=(
            MaterialLink(
                title="Подборка статей и методичек",
                url="https://example.org/articles",
            ),
        ),
    ),
    1: MaterialsBundle(
        past_problems=(
            MaterialLink(
                title="НИУ ВШЭ: комплект задач прошлых лет",
                url="https://example.org/hse/problems",
            ),
        ),
        theory=(
            MaterialLink(
                title="НИУ ВШЭ: теория и видеоразборы",
                url="https://example.org/hse/theory",
            ),
        ),
        articles=(
            MaterialLink(
                title="НИУ ВШЭ: методички и полезные статьи",
                url="https://example.org/hse/articles",
            ),
        ),
    ),
    2: MaterialsBundle(
        past_problems=(
            MaterialLink(
                title="ВсОШ по математике: задачи за 2023 год",
                url="https://example.org/vsosh/problems",
            ),
        ),
        theory=(
            MaterialLink(
                title="ВсОШ: теория и вебинары",
                url="https://example.org/vsosh/theory",
            ),
        ),
        articles=(
            MaterialLink(
                title="ВсОШ: рекомендации и методические материалы",
                url="https://example.org/vsosh/articles",
            ),
        ),
    ),
    3: MaterialsBundle(
        past_problems=(
            MaterialLink(
                title="НТИ: задачи отборочного и финала",
                url="https://example.org/nti/problems",
            ),
        ),
        theory=(
            MaterialLink(
                title="НТИ: теория и тренировки",
                url="https://example.org/nti/theory",
            ),
        ),
        articles=(
            MaterialLink(
                title="НТИ: статьи и гайды",
                url="https://example.org/nti/articles",
            ),
        ),
    ),
    4: MaterialsBundle(
        past_problems=(
            MaterialLink(
                title="ВсОШ по информатике: задания прошлых лет",
                url="https://example.org/informatics/problems",
            ),
        ),
        theory=(
            MaterialLink(
                title="ВсОШ по информатике: теория и разборы",
                url="https://example.org/informatics/theory",
            ),
        ),
        articles=(
            MaterialLink(
                title="ВсОШ по информатике: полезные материалы",
                url="https://example.org/informatics/articles",
            ),
        ),
    ),
    5: MaterialsBundle(
        past_problems=(
            MaterialLink(
                title="Физтех: комплект прошлых туров",
                url="https://example.org/mipt/problems",
            ),
        ),
        theory=(
            MaterialLink(
                title="Физтех: лекции и видеоразборы",
                url="https://example.org/mipt/theory",
            ),
        ),
        articles=(
            MaterialLink(
                title="Физтех: статьи и памятки",
                url="https://example.org/mipt/articles",
            ),
        ),
    ),
    6: MaterialsBundle(
        past_problems=(
            MaterialLink(
                title="Ломоносов: задачи прошлых лет",
                url="https://example.org/lomonosov/problems",
            ),
        ),
        theory=(
            MaterialLink(
                title="Ломоносов: теория и видео",
                url="https://example.org/lomonosov/theory",
            ),
        ),
        articles=(
            MaterialLink(
                title="Ломоносов: методические рекомендации",
                url="https://example.org/lomonosov/articles",
            ),
        ),
    ),
}


@lru_cache
def get_materials_service() -> MaterialsService:
    """Получить singleton-сервис материалов."""

    return MaterialsService()


__all__ = [
    "AdminMaterial",
    "MaterialLink",
    "MaterialsBundle",
    "MaterialsService",
    "get_materials_service",
]
