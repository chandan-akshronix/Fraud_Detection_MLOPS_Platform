"""
Authentication Dependencies
FastAPI dependencies for protected routes.
"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.auth import (
    get_auth,
    User,
    Role,
    Permission,
    AzureADB2CAuth,
)

# Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[User]:
    """
    Get current authenticated user from JWT token.
    
    Returns None if no token provided (for public endpoints).
    """
    if not credentials:
        return None
    
    auth = get_auth()
    user = await auth.validate_token(credentials.credentials)
    
    return user


async def require_auth(
    user: User = Depends(get_current_user),
) -> User:
    """
    Require authentication.
    
    Raises 401 if not authenticated.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_permission(permission: Permission):
    """
    Factory for permission-checking dependencies.
    
    Usage:
        @router.get("/admin", dependencies=[Depends(require_permission(Permission.USERS_MANAGE))])
    """
    async def check_permission(user: User = Depends(require_auth)) -> User:
        auth = get_auth()
        if not auth.has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}",
            )
        return user
    
    return check_permission


def require_role(role: Role):
    """
    Factory for role-checking dependencies.
    
    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(Role.ADMIN))])
    """
    async def check_role(user: User = Depends(require_auth)) -> User:
        auth = get_auth()
        if not auth.has_role(user, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role.value}",
            )
        return user
    
    return check_role


def require_any_role(roles: List[Role]):
    """
    Factory for checking if user has any of the specified roles.
    
    Usage:
        @router.get("/ml", dependencies=[Depends(require_any_role([Role.DATA_SCIENTIST, Role.ML_ENGINEER]))])
    """
    async def check_roles(user: User = Depends(require_auth)) -> User:
        auth = get_auth()
        if not any(auth.has_role(user, role) for role in roles):
            role_names = ", ".join(r.value for r in roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {role_names}",
            )
        return user
    
    return check_roles


# Convenience dependencies for common checks
require_admin = require_role(Role.ADMIN)
require_data_scientist = require_any_role([Role.ADMIN, Role.DATA_SCIENTIST])
require_ml_engineer = require_any_role([Role.ADMIN, Role.ML_ENGINEER])

# Permission-based dependencies
can_train_models = require_permission(Permission.MODEL_TRAIN)
can_deploy_models = require_permission(Permission.MODEL_DEPLOY)
can_manage_jobs = require_permission(Permission.JOBS_MANAGE)
can_configure_monitoring = require_permission(Permission.MONITORING_CONFIGURE)
