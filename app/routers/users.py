from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.common.response import error_response, success_response
from app.db.base import get_db
from app.db.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.security.jwt import get_current_user
from app.security.password import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
async def list_users(_: dict = Depends(get_current_user), db=Depends(get_db)):
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    return success_response(data=[UserOut.model_validate(u).model_dump() for u in users])


@router.get("/{user_id}")
async def get_user(user_id: int, _: dict = Depends(get_current_user), db=Depends(get_db)):
    user = await db.get(User, user_id)
    if user is None:
        return error_response("用户不存在", code=404)
    return success_response(data=UserOut.model_validate(user).model_dump())


@router.post("")
async def create_user(
    body: UserCreate, _: dict = Depends(get_current_user), db=Depends(get_db)
):
    existing = await db.execute(
        select(User).where(
            (User.username == body.username) | (User.email == body.email)
        )
    )
    if existing.scalars().first():
        return error_response("用户名或邮箱已存在", code=409)

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return success_response(data=UserOut.model_validate(user).model_dump(), message="创建成功")


@router.put("/{user_id}")
async def update_user(
    user_id: int, body: UserUpdate, _: dict = Depends(get_current_user), db=Depends(get_db)
):
    user = await db.get(User, user_id)
    if user is None:
        return error_response("用户不存在", code=404)

    data = body.model_dump(exclude_unset=True)
    if data.get("password"):
        user.hashed_password = hash_password(data["password"])
    data.pop("password", None)
    for key, value in data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return success_response(data=UserOut.model_validate(user).model_dump(), message="更新成功")


@router.delete("/{user_id}")
async def delete_user(
    user_id: int, _: dict = Depends(get_current_user), db=Depends(get_db)
):
    user = await db.get(User, user_id)
    if user is None:
        return error_response("用户不存在", code=404)
    await db.delete(user)
    await db.commit()
    return success_response(message="删除成功")
