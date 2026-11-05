import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.resource_definition import ResourceDefinition


class ResourceDefinitionRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        resource_id: uuid.UUID,
    ) -> ResourceDefinition | None:
        statement = select(ResourceDefinition).where(
            ResourceDefinition.id == resource_id
        )
        return self.db.scalar(statement)

    def get_by_name(
        self,
        name: str,
    ) -> ResourceDefinition | None:
        statement = select(ResourceDefinition).where(
            ResourceDefinition.name == name
        )
        return self.db.scalar(statement)

    def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ResourceDefinition]:
        statement = (
            select(ResourceDefinition)
            .order_by(ResourceDefinition.name.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def get_active_resources(self) -> list[ResourceDefinition]:
        statement = (
            select(ResourceDefinition)
            .where(ResourceDefinition.is_active.is_(True))
            .order_by(ResourceDefinition.name.asc())
        )
        return list(self.db.scalars(statement).all())

    def add(
        self,
        resource: ResourceDefinition,
    ) -> ResourceDefinition:
        self.db.add(resource)
        return resource

    def flush(self) -> None:
        self.db.flush()