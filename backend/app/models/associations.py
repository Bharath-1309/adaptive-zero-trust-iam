from sqlalchemy import Column, ForeignKey, Index, Table, Uuid

from app.db.base import Base

user_roles = Table(
"user_roles",
Base.metadata,
Column(
"user_id",
Uuid(as_uuid=True),
ForeignKey("users.id", ondelete="RESTRICT"),
primary_key=True,
),
Column(
"role_id",
Uuid(as_uuid=True),
ForeignKey("roles.id", ondelete="RESTRICT"),
primary_key=True,
),
Index(
"ix_user_roles_role_id",
"role_id",
),
)

role_permissions = Table(
"role_permissions",
Base.metadata,
Column(
"role_id",
Uuid(as_uuid=True),
ForeignKey("roles.id", ondelete="RESTRICT"),
primary_key=True,
),
Column(
"permission_id",
Uuid(as_uuid=True),
ForeignKey("permissions.id", ondelete="RESTRICT"),
primary_key=True,
),
Index(
"ix_role_permissions_permission_id",
"permission_id",
),
)
