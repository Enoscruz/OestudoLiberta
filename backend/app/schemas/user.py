"""Contratos Pydantic relacionados a usuários e papéis."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import RoleName, UserStatus


class RoleRead(BaseModel):
    """Papel de acesso do usuário."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: RoleName


class UserRead(BaseModel):
    """Perfil do usuário exposto pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    status: UserStatus
    email_verified: bool
    role: RoleRead
    created_at: datetime
