from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from .. import models, schemas, database

router = APIRouter()

@router.get("/voice-settings/{station_id}")
def get_station_voice_settings(station_id: int, db: Session = Depends(database.get_db)):
    station = db.query(models.Station).join(models.VoiceModel, isouter=True).filter(models.Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Stacja nie znaleziona")

    return {
        "station_name": station.name,
        "model_id": station.voice_model_id,
        "model_name": station.voice_model.name if station.voice_model else None,
        "stability": station.voice_stability,
        "similarity": station.voice_similarity,
        "style": station.voice_style
    }

@router.get("/voice-models")
def get_voice_models(db: Session = Depends(database.get_db)):
    voices = db.query(models.VoiceModel).all()
    result = []
    for v in voices:
        result.append({
            "id": v.id,
            "name": v.name,
        })
    return result

@router.put("/edit-voice/{station_id}")
def edit_station_voice(station_id: int, data: schemas.VoiceSettingsEdit, db: Session = Depends(database.get_db)):
    station = db.query(models.Station).filter(models.Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Stacja nie znaleziona")

    station.voice_model_id = data.model_id
    station.voice_stability = data.stability
    station.voice_similarity = data.similarity
    station.voice_style = data.style

    db.commit()
    return {"message": "Ustawienia głosu zaktualizowane"}
