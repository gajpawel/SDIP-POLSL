from fastapi import FastAPI
from backend.database import engine
from backend import models
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import admin, auth, timetable, displays, voice, edit_train # Routery części administracyjnej
from backend.routers.HTML import displays_views, displays_appearance, voice_controller, speak # Routery części użytkowej
# Tworzymy tabele w DB
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(timetable.router)
app.include_router(edit_train.router)
app.include_router(displays.router)
app.include_router(voice.router)

app.include_router(speak.router)
app.include_router(voice_controller.router)
app.include_router(displays_views.router)
app.include_router(displays_appearance.router)