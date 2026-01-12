from fastapi import FastAPI
from backend.routers import admin, auth
from backend.database import engine
from backend import models
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import admin, auth, timetable, displays, voice

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
app.include_router(displays.router)
app.include_router(voice.router)