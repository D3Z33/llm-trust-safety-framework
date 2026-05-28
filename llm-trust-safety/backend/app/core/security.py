"""
Autenticação JWT e Controle de Acesso
LLM Trust & Safety Framework - Enterprise Edition
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pw = plain_password[:72] if len(plain_password.encode()) > 72 else plain_password
        return pwd_context.verify(pw, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    pw = password[:72] if len(password.encode()) > 72 else password
    return pwd_context.hash(pw)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[Dict]:
    """Retorna o usuário atual (None se não autenticado)"""
    if not token:
        return None
    payload = decode_token(token)
    return payload


async def require_auth(token: str = Depends(oauth2_scheme)) -> Dict:
    """Requer autenticação obrigatória"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação necessário",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
    return payload


def require_role(allowed_roles: List[str]):
    """Factory de dependência para controle de acesso por role"""
    async def _require_role(token: str = Depends(oauth2_scheme)) -> Dict:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticação necessária",
                headers={"WWW-Authenticate": "Bearer"},
            )
        payload = decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
            )
        user_role = payload.get("role", "viewer")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão insuficiente. Requer: {', '.join(allowed_roles)}. Seu perfil: {user_role}",
            )
        return payload
    return _require_role
