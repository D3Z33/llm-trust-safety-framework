"""
Rotas de Usuários - Gerenciamento de usuários (Admin)
"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.core.security import get_current_user, get_password_hash, require_role
from app.models.db_models import User, APIKey, AuditTrail
from app.models.schemas import UserCreate, UserUpdate, UserResponse, APIKeyCreate, APIKeyResponse
import secrets
import hashlib

router = APIRouter(prefix="/api/usuarios", tags=["Usuários"])


def _hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


@router.get("", response_model=list[UserResponse])
async def listar_usuarios(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"])),
):
    """Lista todos os usuários (somente admin)"""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"])),
):
    """Criar novo usuário"""
    # Verificar duplicatas
    existing = await db.execute(
        select(User).where(
            (User.username == data.username) | (User.email == data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username ou e-mail já cadastrado"
        )

    CORES = ["#3b82f6", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#ec4899"]
    user = User(
        username=data.username,
        email=data.email,
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        department=data.department,
        phone=data.phone,
        avatar_color=secrets.choice(CORES),
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Audit trail
    db.add(AuditTrail(
        user_id=current_user.get("id"),
        action="criar_usuario",
        resource="users",
        resource_id=str(user.id),
        new_value={"username": user.username, "role": user.role},
        ip_address=request.client.host if request.client else None,
    ))
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/eu", response_model=UserResponse)
async def meu_perfil(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retorna perfil do usuário atual"""
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


@router.put("/eu", response_model=UserResponse)
async def atualizar_perfil(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Atualiza perfil do usuário atual"""
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.email is not None:
        user.email = data.email
    if data.department is not None:
        user.department = data.department
    if data.phone is not None:
        user.phone = data.phone

    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def atualizar_usuario(
    user_id: int,
    data: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"])),
):
    """Atualiza um usuário (admin)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    old_values = {"role": user.role, "is_active": user.is_active}

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.email is not None:
        user.email = data.email
    if data.department is not None:
        user.department = data.department
    if data.phone is not None:
        user.phone = data.phone
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.role is not None:
        user.role = data.role

    user.updated_at = datetime.utcnow()

    db.add(AuditTrail(
        user_id=current_user.get("id"),
        action="atualizar_usuario",
        resource="users",
        resource_id=str(user_id),
        old_value=old_values,
        new_value={"role": user.role, "is_active": user.is_active},
        ip_address=request.client.host if request.client else None,
    ))
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}")
async def desativar_usuario(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"])),
):
    """Desativa um usuário"""
    if user_id == current_user.get("id"):
        raise HTTPException(
            status_code=400,
            detail="Você não pode desativar sua própria conta"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_active = False
    user.updated_at = datetime.utcnow()

    db.add(AuditTrail(
        user_id=current_user.get("id"),
        action="desativar_usuario",
        resource="users",
        resource_id=str(user_id),
        ip_address=request.client.host if request.client else None,
    ))
    await db.commit()
    return {"message": f"Usuário {user.username} desativado"}


# ──────────────────────────── API Keys ────────────────────────────
@router.get("/apikeys/minhas", response_model=list[APIKeyResponse])
async def minhas_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Lista API Keys do usuário atual"""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user["id"])
        .order_by(APIKey.created_at.desc())
    )
    return result.scalars().all()


@router.post("/apikeys", response_model=APIKeyResponse, status_code=201)
async def criar_api_key(
    data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Cria uma nova API Key"""
    from datetime import timedelta

    raw_key = f"ltf_{secrets.token_urlsafe(32)}"
    key_hash = _hash_api_key(raw_key)
    prefix = raw_key[:12]

    expires_at = None
    if data.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=data.expires_days)

    api_key = APIKey(
        user_id=current_user["id"],
        name=data.name,
        key_hash=key_hash,
        key_prefix=prefix,
        scopes=data.scopes,
        expires_at=expires_at,
        rate_limit_per_min=data.rate_limit_per_min,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    response = APIKeyResponse.model_validate(api_key)
    response.key = raw_key  # retorna só na criação
    return response


@router.delete("/apikeys/{key_id}")
async def revogar_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Revoga uma API Key"""
    result = await db.execute(
        select(APIKey).where(
            (APIKey.id == key_id) & (APIKey.user_id == current_user["id"])
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API Key não encontrada")

    key.is_active = False
    await db.commit()
    return {"message": "API Key revogada com sucesso"}
