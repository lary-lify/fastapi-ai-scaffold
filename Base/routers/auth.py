from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from Base.common.response import error_response, success_response
from Base.config.setting import settings
from Base.db.base import get_db
from Base.db.models.user import User
from Base.schemas.user import LoginIn, TokenOut, UserOut, UserRegister
from Base.security.jwt import create_access_token, get_current_user
from Base.security.password import verify_password
from Base.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(body: UserRegister, db=Depends(get_db)):
    """Public self-registration.

    Field validation (username pattern, email format, password length, password
    != username) is enforced by :class:`UserRegister`; uniqueness of username /
    email is checked in the service layer. Returns ``409`` when the account
    already exists.
    """
    svc = UserService(db)
    user = await svc.register(
        username=body.username, email=body.email, password=body.password
    )
    if user is None:
        return error_response("用户名或邮箱已存在", code=409)
    return success_response(
        data=UserOut.model_validate(user).model_dump(), message="注册成功，验证邮件已发送"
    )


@router.get("/verify-email")
async def verify_email(
    token: str = Query(..., min_length=1, description="邮箱验证令牌"),
    db=Depends(get_db),
):
    """Activate an account from the link emailed after registration."""
    svc = UserService(db)
    user = await svc.verify_email(token)
    if user is None:
        return error_response("验证码无效或已过期", code=400)
    return success_response(
        data=UserOut.model_validate(user).model_dump(), message="邮箱验证成功"
    )


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db=Depends(get_db)):
    """Exchange username + password for a JWT access token."""
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )
    if settings.auth.require_email_verification and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="邮箱未验证，请先完成邮箱验证"
        )
    token = create_access_token(subject=str(user.id), extra={"username": user.username})
    return TokenOut(access_token=token)


@router.get("/me")
async def me(current: dict = Depends(get_current_user), db=Depends(get_db)):
    """Return the currently authenticated user (resolved from the JWT)."""
    user_id = int(current["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return success_response(data=UserOut.model_validate(user).model_dump())
