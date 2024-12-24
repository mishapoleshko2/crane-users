from dataclasses import dataclass
from typing import cast
from datetime import datetime, UTC

from crane_auth.domain.entities.tokens import (
    RefreshSession,
    generate_user_access_token,
)
from crane_auth.domain.exceptions import (
    UserIsNotRegisteredException,
    IncorrectPasswordError,
)
from crane_auth.interactor.dto.auth import UserLoginInputDTO, UserLoginOutputDTO
from crane_auth.interactor.ports.repositories.refresh_session import (
    RefreshSessionRepository,
)
from crane_auth.interactor.ports.repositories.user import UserRepository
from crane_auth.interactor.validations.user_login import UserLoginDataValidator


@dataclass
class UserLoginUseCase:
    user_repository: UserRepository
    refresh_session_repository: RefreshSessionRepository

    async def execute(self, input_dto: UserLoginInputDTO) -> UserLoginOutputDTO:
        validator = UserLoginDataValidator()
        validator.validate(input_dto.as_dict())

        if input_dto.email:
            user = await self.user_repository.find_user_by_email(input_dto.email)
        else:
            user = await self.user_repository.find_user_by_login(
                cast(str, input_dto.login)
            )

        if not user:
            raise UserIsNotRegisteredException

        if not user.is_me(input_dto.password):
            raise IncorrectPasswordError("not correnct login/email or password")

        await self.refresh_session_repository.delete_user_session(user.id)

        now = datetime.now(UTC)
        refresh_session = RefreshSession(user_id=user.id, created_dt=now)
        await self.refresh_session_repository.create_session(refresh_session)

        access_token = generate_user_access_token(user, now)

        return UserLoginOutputDTO(
            access_token=access_token,
            refresh_token=refresh_session.token,
            refresh_token_ttl=refresh_session.ttl,
            refresh_token_expires=refresh_session.expire_time,
        )