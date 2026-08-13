from fastapi import APIRouter, Depends, Query

from Base.common.response import error_response, success_response
from Base.db.base import get_db
from Base.schemas.base import PageSchema
from Base.schemas.user import UserCreate, UserOut, UserUpdate
from Base.security.jwt import get_current_user
from Base.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
async def list_users(_: dict = Depends(get_current_user), db=Depends(get_db)):
    svc = UserService(db)
    users = await svc.list()
    return success_response(
        data=[UserOut.model_validate(u).model_dump() for u in users]
    )


@router.get("/page")
async def page_users(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    _: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Paginated user list wrapped in :class:`PageSchema`."""
    svc = UserService(db)
    items, total = await svc.paginate(page=page, page_size=page_size)
    payload = PageSchema[UserOut](
        total=total,
        page=page,
        page_size=page_size,
        items=[UserOut.model_validate(u) for u in items],
    )
    return success_response(data=payload.model_dump())


@router.get("/{user_id}")
async def get_user(
    user_id: int, _: dict = Depends(get_current_user), db=Depends(get_db)
):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if user is None:
        return error_response("用户不存在", code=404)
    return success_response(data=UserOut.model_validate(user).model_dump())


@router.post("")
async def create_user(
    body: UserCreate, _: dict = Depends(get_current_user), db=Depends(get_db)
):
    svc = UserService(db)
    user = await svc.create(
        username=body.username, email=body.email, password=body.password
    )
    if user is None:
        return error_response("用户名或邮箱已存在", code=409)
    return success_response(
        data=UserOut.model_validate(user).model_dump(), message="创建成功"
    )


@router.put("/{user_id}")
async def update_user(
    user_id: int, body: UserUpdate, _: dict = Depends(get_current_user), db=Depends(get_db)
):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if user is None:
        return error_response("用户不存在", code=404)
    data = body.model_dump(exclude_unset=True)
    user = await svc.update(user, **data)
    return success_response(
        data=UserOut.model_validate(user).model_dump(), message="更新成功"
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int, _: dict = Depends(get_current_user), db=Depends(get_db)
):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    if user is None:
        return error_response("用户不存在", code=404)
    await svc.delete(user)
    return success_response(message="删除成功")
