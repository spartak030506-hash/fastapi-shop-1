from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    """Схема ответа с сообщением"""

    message: str

    model_config = ConfigDict(
        frozen=True,
    )
