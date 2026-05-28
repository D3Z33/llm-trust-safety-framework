"""
Autenticação - Login, Logout, Refresh Token
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_password, create_access_token, create_refresh_token,
    get_current_user, decode_token
)
from app.core.config import settings
from app.models.db_models import User, AuditTrail
from app.models.schemas import UserLogin, Token, ChangePassword

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


async def _authenticate(username: str, password: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        user.failed_login_count = (user.failed_login_count or 0) + 1
        await db.commit()
        return None
    return user


@router.post("/login/json", response_model=Token, summary="Login (JSON)")
async def login_json(
    data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Login com username e senha (JSON)"""
    user = await _authenticate(data.username, data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    # Atualizar stats de login
    user.last_login = datetime.utcnow()
    user.login_count = (user.login_count or 0) + 1
    user.failed_login_count = 0

    # Registrar no audit trail
    db.add(AuditTrail(
        user_id=user.id,
        action="login",
        resource="auth",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:200],
    ))
    await db.commit()

    token_data = {
        "sub": user.username,
        "id": user.id,
        "role": user.role,
        "email": user.email,
        "full_name": user.full_name,
        "avatar_color": user.avatar_color,
        "department": user.department,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user.username, "id": user.id})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "avatar_color": user.avatar_color,
            "department": user.department,
        },
    )


@router.post("/login", response_model=Token, summary="Login (OAuth2 Form)")
async def login_form(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Login com formulário OAuth2 (compatível com /docs)"""
    user = await _authenticate(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    user.last_login = datetime.utcnow()
    user.login_count = (user.login_count or 0) + 1
    await db.commit()

    token_data = {
        "sub": user.username,
        "id": user.id,
        "role": user.role,
        "email": user.email,
        "full_name": user.full_name,
        "avatar_color": user.avatar_color,
        "department": user.department,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user.username, "id": user.id})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "avatar_color": user.avatar_color,
            "department": user.department,
        },
    )


@router.post("/refresh", summary="Renovar Token")
async def refresh_token(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Renova o access token usando o refresh token"""
    refresh_tok = data.get("refresh_token")
    if not refresh_tok:
        raise HTTPException(status_code=400, detail="refresh_token necessário")

    payload = decode_token(refresh_tok)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")

    result = await db.execute(select(User).where(User.username == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou inativo")

    token_data = {
        "sub": user.username,
        "id": user.id,
        "role": user.role,
        "email": user.email,
        "full_name": user.full_name,
        "avatar_color": user.avatar_color,
        "department": user.department,
    }
    new_access = create_access_token(token_data)

    return {
        "access_token": new_access,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/alterar-senha", summary="Alterar Senha")
async def alterar_senha(
    data: ChangePassword,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Altera a senha do usuário logado"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Autenticação necessária")

    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    from app.core.security import verify_password, get_password_hash
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")

    user.hashed_password = get_password_hash(data.new_password)
    user.updated_at = datetime.utcnow()
    await db.commit()

    return {"message": "Senha alterada com sucesso"}


@router.get("/eu", summary="Perfil do usuário logado")
async def eu(current_user: dict = Depends(get_current_user)):
    """Retorna dados do usuário logado a partir do token"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return current_user
