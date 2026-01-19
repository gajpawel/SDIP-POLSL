from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.responses import Response
from ... import models, database, schemas
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from dotenv import load_dotenv
import os

# Załaduj zmienne z pliku .env
load_dotenv() 

# Konfiguracja klienta
# Klucz jest pobierany ze zmiennych środowiskowych
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY") 

if not ELEVEN_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY nie został ustawiony w zmiennych środowiskowych lub pliku .env!")

router = APIRouter()

client = ElevenLabs(api_key=ELEVEN_API_KEY)

@router.post("/speak/{station_id}")
async def speak_text(request: schemas.SpeakRequest, station_id: int, db: Session = Depends(database.get_db)):
    # Pobieramy ustawienia głosu dla danej stacji
    station = db.query(models.Station).filter(models.Station.id == station_id).first()
    if station:
        voice_id = station.voice_model_id if station.voice_model_id is not None else "JBFqnCBsd6RMkjVDRZzb"
        voice_stability = station.voice_stability if station.voice_stability is not None else 90
        voice_similarity = station.voice_similarity if station.voice_similarity is not None else 80
        voice_style = station.voice_style if station.voice_style is not None else 0
    
    station_voice_settings = VoiceSettings(
        # Przekształcenie na skalę 0.0 - 1.0
        stability=voice_stability*0.01,
        similarity_boost=voice_similarity*0.01,
        style=voice_style*0.01,
    )
    request.voice_id = voice_id
    try:
        print(f"Generowanie mowy ...")
        audio_generator = client.text_to_speech.convert(
            voice_id=request.voice_id,
            model_id="eleven_multilingual_v2",
            text=request.text,
            output_format="mp3_44100_128",
            voice_settings=station_voice_settings
        )
        # Generator zwraca fragmenty pliku, musimy je złączyć
        audio_bytes = b"".join(audio_generator)

        # Zwracamy plik audio bezpośrednio do przeglądarki
        return Response(content=audio_bytes, media_type="audio/mpeg")

    except Exception as e:
        print(f"Błąd ElevenLabs: {e}")
        # Wypisujemy szczegóły błędu, co ułatwi debugowanie (np. zły klucz API)
        raise HTTPException(status_code=500, detail=str(e))