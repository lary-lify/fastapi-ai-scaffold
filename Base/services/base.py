from sqlalchemy.ext.asyncio import AsyncSession


class BaseService:
    """Base class for service-layer objects bound to a DB session.

    Services orchestrate one or more repositories and hold the business logic
    that does not belong in routers or models. Subclasses typically build the
    repositories they need in ``__init__``::

        class UserService(BaseService):
            def __init__(self, session):
                super().__init__(session)
                self.repo = UserRepository(session)
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
