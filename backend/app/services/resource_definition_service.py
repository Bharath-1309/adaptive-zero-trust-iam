import uuid

from app.models.resource_definition import ResourceDefinition
from app.repositories.resource_definition_repository import (
    ResourceDefinitionRepository,
)
from app.schemas.resource_definition import (
    ResourceDefinitionCreate,
    ResourceDefinitionUpdate,
)


class ResourceDefinitionService:

    def __init__(
        self,
        repository: ResourceDefinitionRepository,
    ):
        self.repository = repository

    def create_resource(
        self,
        data: ResourceDefinitionCreate,
    ) -> ResourceDefinition:

        name = data.name.strip()
        permission = data.required_permission.strip()

        if self.repository.get_by_name(name) is not None:
            raise ValueError(
                "A resource with this name already exists."
            )

        resource = ResourceDefinition(
            name=name,
            description=data.description,
            required_permission=permission,
            access_policy=data.access_policy,
            requires_office_location=(
                data.access_policy == "OFFICE_ONLY"
            ),
            is_active=True,
        )

        self.repository.add(resource)
        self.repository.flush()

        return resource

    def get_resource(
        self,
        resource_id: uuid.UUID,
    ) -> ResourceDefinition:

        resource = self.repository.get_by_id(resource_id)

        if resource is None:
            raise LookupError("Resource definition not found.")

        return resource

    def get_all_resources(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ResourceDefinition]:

        if offset < 0:
            raise ValueError("Offset cannot be negative.")

        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100.")

        return self.repository.get_all(offset, limit)

    def update_resource(
        self,
        resource_id: uuid.UUID,
        data: ResourceDefinitionUpdate,
    ) -> ResourceDefinition:

        resource = self.get_resource(resource_id)

        updates = data.model_dump(exclude_unset=True)

        if not updates:
            raise ValueError("At least one update is required.")

        if "name" in updates and updates["name"] is not None:
            existing = self.repository.get_by_name(updates["name"])

            if existing is not None and existing.id != resource.id:
                raise ValueError(
                    "A resource with this name already exists."
                )

        if "access_policy" in updates:
            resource.access_policy = updates["access_policy"]
            resource.requires_office_location = (
                updates["access_policy"] == "OFFICE_ONLY"
            )

            updates.pop("access_policy")

        for field, value in updates.items():
            setattr(resource, field, value)

        self.repository.flush()

        return resource