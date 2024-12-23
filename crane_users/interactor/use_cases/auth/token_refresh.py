from dataclasses import dataclass
from datetime import datetime, UTC
from typing import cast

from crane_users.domain.entities.tokens import generate_user_access_token
from crane_users.domain.exceptions import (
    RefreshSessionNotFoundException,
    RefreshSessionIsExpiredException,
)
from crane_users.interactor.ports.repositories.refresh_session import (
    RefreshSessionRepository,
)
from crane_users.interactor.dto.auth import TokenRefreshInputDTO, TokenRefreshOutputDTO
from crane_users.interactor.ports.repositories.user import UserRepository
from crane_users.domain.entities.user import User


@dataclass
class TokenRefreshUseCase:
    user_repository: UserRepository
    refresh_session_repository: RefreshSessionRepository

    async def execute(self, input_dto: TokenRefreshInputDTO) -> TokenRefreshOutputDTO:
        refresh_session = await self.refresh_session_repository.get_session(
            input_dto.refresh_token
        )
        if not refresh_session:
            raise RefreshSessionNotFoundException
        now = datetime.now(UTC)
        if not refresh_session.is_fresh(now):
            raise RefreshSessionIsExpiredException

        user = await self.user_repository.get_user(refresh_session.user_id)
        access_token = generate_user_access_token(cast(User, user), now)
        return TokenRefreshOutputDTO(access_token=access_token)
