from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.common.response import success_response
from app.db.base import get_db
from app.db.models.user import User
from app.schemas.user import LoginIn, TokenOut, UserOut
from app.security.jwt import create_access_token, get_current_user
from app.security.password import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db=Depends(get_db)):
    """Exchange username + password for a JWT access token."""
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
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
