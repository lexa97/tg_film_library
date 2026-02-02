from pydantic import BaseModel


class FilmCreate(BaseModel):
    """Данные для создания/сохранения фильма в БД (из TMDB или другого источника)."""

    external_id: str
    source: str
    title: str
    title_original: str | None = None
    year: int | None = None
    description: str | None = None
    poster_url: str | None = None
    media_type: str = "movie"


class FilmSearchResult(BaseModel):
    """Один результат поиска фильма для отображения пользователю (карточка + кнопка «Подтвердить»)."""

    external_id: str
    source: str
    title: str
    year: int | None = None
    description: str | None = None
    poster_url: str | None = None
    media_type: str = "movie"


class AddFilmResult(BaseModel):
    """Результат добавления фильма в группу (для хендлера)."""

    success: bool
    film_title: str | None = None
    film_year: int | None = None
    group_name: str | None = None
    error: str | None = None


class MarkWatchedResult(BaseModel):
    """Результат отметки «просмотрен» (для хендлера)."""

    success: bool
    group_name: str | None = None
    film_title: str | None = None
    error: str | None = None
