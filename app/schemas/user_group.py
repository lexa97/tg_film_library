from pydantic import BaseModel


class AddMemberResult(BaseModel):
    """Результат добавления участника в группу по контакту (для хендлера)."""

    success: bool
    group_name: str | None = None
    new_member_display_name: str | None = None
    error: str | None = None
