from pydantic import BaseModel

# Model Pydantic do odbioru JSON
class LoginData(BaseModel):
    login: str
    password: str

# Model do rejestracji nowego admina
class NewAdmin(BaseModel):
    login: str
    password: str
    password_repeat: str
    name: str | None = None
    surname: str | None = None
    role_id: int
    station_id: int | None = None

# Schemat danych wejściowych (edycja użytkownika)
class AdminUpdate(BaseModel):
    login: str
    name: str | None = None
    surname: str | None = None
    password: str | None = None
    password_repeat: str | None = None
    role_id: int | None = None
    station_id: int | None = None

class VoiceSettingsEdit(BaseModel):
    stability: int | None = None
    similarity: int | None = None
    style: int | None = None
    model_id: str | None = None

class NewDisplay(BaseModel):
    station_id: int
    alias: str | None = None
    platform_id: int | None = None
    track_id: int | None = None
    type_id: int
    font: str
    intermediates_number: int | None = None
    main_color: str | None = None
    background_color: str | None = None
    theme: bool | None = None

class DisplayUpdate(BaseModel):
    station_id: int | None = None
    alias: str | None = None
    platform_id: int | None = None
    track_id: int | None = None
    type_id: int | None = None
    font: str | None = None
    intermediates_number: int | None = None
    main_color: str | None = None
    background_color: str | None = None
    theme: bool | None = None

class StopStatusUpdate(BaseModel):
    track_id: int | None = None
    bus: bool | None = None
    is_cancelled: bool | None = None
    arrival_delay: int | None = None
    departure_delay: int | None = None