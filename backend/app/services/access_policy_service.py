from app.models.access_policy import AccessPolicy
from app.repositories.access_policy_repository import (
    AccessPolicyRepository,
)
from app.schemas.access_policy import (
    AccessPolicyCreate,
    AccessPolicyUpdate,
)


class AccessPolicyService:

    def __init__(
        self,
        repository: AccessPolicyRepository,
    ):
        self.repository = repository

    def create_policy(
        self,
        data: AccessPolicyCreate,
    ) -> AccessPolicy:

        if self.repository.get_by_name(data.name):
            raise ValueError("A policy with this name already exists.")

        policy = AccessPolicy(
            name=data.name,
            description=data.description,
            effect=data.effect,
            priority=data.priority,
            conditions=data.conditions,
            is_active=True,
        )

        self.repository.add(policy)
        self.repository.flush()

        return policy

    def get_policy(self, policy_id):
        policy = self.repository.get_by_id(policy_id)

        if policy is None:
            raise LookupError("Policy not found.")

        return policy

    def get_all_policies(
        self,
        offset: int = 0,
        limit: int = 100,
    ):
        if offset < 0:
            raise ValueError("Offset cannot be negative.")

        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100.")

        return self.repository.get_all(offset, limit)

    def update_policy(
        self,
        policy_id,
        data: AccessPolicyUpdate,
    ):

        policy = self.get_policy(policy_id)

        updates = data.model_dump(exclude_unset=True)

        if "name" in updates:
            existing = self.repository.get_by_name(updates["name"])

            if existing is not None and existing.id != policy.id:
                raise ValueError("A policy with this name already exists.")

        for field, value in updates.items():
            setattr(policy, field, value)

        self.repository.flush()

        return policy

    def deactivate_policy(self, policy_id):

        policy = self.get_policy(policy_id)

        policy.is_active = False

        self.repository.flush()

        return policy