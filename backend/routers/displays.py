from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, database, schemas
import json
from .HTML.displays_appearance import connected_clients

router = APIRouter(prefix="/displays", tags=["displays"])

# Typy wyświetlaczy
@router.get("/types")
def get_display_types(db: Session = Depends(database.get_db)):
    types = db.query(models.DisplayType).all()
    return [{"id": t.id, "name": t.name, "picture_path": t.picture_path} for t in types]

# Konkretny wyświetlacz do edycji
@router.get("/display/{display_id}")
def get_display(display_id: int, db: Session = Depends(database.get_db)):
    display = db.query(models.Display).filter(models.Display.id == display_id).first()
    if not display:
        raise HTTPException(status_code=404, detail="Display not found")
    return {
        "id": display.id,
        "alias": display.alias,
        "type_id": display.type_id,
        "station_id": display.station_id,
        "platform_id": display.platform_id,
        "track_id": display.track_id,
        "main_color": display.main_color,
        "background_color": display.background_color,
        "theme": display.theme,
        "font": display.font,
        "intermediates_number": display.intermediates_number,
    }

# Wszystkie wyświetlacze na stacji
@router.get("/{station_id}")
def get_displays(station_id: int, db: Session = Depends(database.get_db)):
    displays = (
        db.query(models.Display)
        .join(models.DisplayType)
        .outerjoin(models.Platform)
        .outerjoin(models.Track)
        .filter(models.Display.station_id == station_id)
        .all()
    )
    result = []
    for d in displays:
        if d.type_id == 1:
            result.append({
                "id": d.id,
                "alias": d.alias,
                "type_id": d.type_id,
                "name": d.type.name if d.type else None,
                "location": "Tor " + str(d.track.number) if d.track else None,
                "location_id": d.track_id,
                "image_url": d.type.picture_path if d.type else None,
                "font": d.font,
                "main_color": d.main_color,
                "background_color": d.background_color,
                "theme": d.theme,
                "intermediates_number": d.intermediates_number,
            })
        elif d.type_id == 2 or d.type_id == 3:
            result.append({
                "id": d.id,
                "alias": d.alias,
                "type_id": d.type_id,
                "name": d.type.name if d.type else None,
                "location": "Peron " + d.platform.number if d.platform else None,\
                "location_id": d.platform_id,
                "image_url": d.type.picture_path if d.type else None,
                "font": d.font,
                "main_color": d.main_color,
                "background_color": d.background_color,
                "theme": d.theme,
                "intermediates_number": d.intermediates_number,
            })
        else:
            result.append({
                "id": d.id,
                "alias": d.alias,
                "type_id": d.type_id,
                "name": d.type.name if d.type else None,
                "location": "Stacja",
                "location_id": d.station_id,
                "image_url": d.type.picture_path if d.type else None,
                "font": d.font,
                "main_color": d.main_color,
                "background_color": d.background_color,
                "theme": d.theme,
                "intermediates_number": d.intermediates_number,
            })

    return result

@router.get("/platforms/{station_id}")
def get_platforms(station_id: int, db: Session = Depends(database.get_db)):
    platforms = db.query(models.Platform).filter(models.Platform.station_id == station_id).all()
    return [{"id": p.id, "number": p.number} for p in platforms]

@router.get("/tracks/{station_id}")
def get_tracks(station_id: int, db: Session = Depends(database.get_db)):
    tracks = db.query(models.Track).join(models.Platform).filter(models.Platform.station_id == station_id).all()
    return [{"id": t.id, "number": t.number} for t in tracks]

@router.post("/add")
def add_display(data: schemas.NewDisplay, db: Session = Depends(database.get_db)):
    # Walidacja wymaganych pól
    if not data.station_id:
        raise HTTPException(status_code=400, detail="station_id jest wymagane")
    
    new_display = models.Display(
        alias=data.alias or None,
        type_id=data.type_id,
        station_id=int(data.station_id),  # konwersja na int
        platform_id=data.platform_id or None,
        track_id=data.track_id or None,
        main_color=data.main_color,
        background_color=data.background_color,
        font=data.font,
        theme=data.theme,
        intermediates_number = int(data.intermediates_number) if data.intermediates_number else None
    )
    db.add(new_display)
    db.commit()
    db.refresh(new_display)
    return {"msg": "Wyświetlacz dodany pomyślnie", "id": new_display.id}

@router.put("/edit/{display_id}")
async def edit_display(display_id: int, data: schemas.DisplayUpdate, db: Session = Depends(database.get_db)):
    display = db.query(models.Display).filter(models.Display.id == display_id).first()
    if not display:
        raise HTTPException(status_code=404, detail="Display not found")

    display.alias = data.alias or None
    display.type_id = data.type_id
    display.station_id = int(data.station_id)
    display.platform_id = data.platform_id or None
    display.track_id = data.track_id or None
    display.main_color = data.main_color
    display.background_color = data.background_color
    display.font = data.font
    display.theme = data.theme
    display.intermediates_number = int(data.intermediates_number) if data.intermediates_number else None

    db.commit()

    # powiadom WebSockety
    if display_id in connected_clients:
        for ws in list(connected_clients[display_id]):
            try:
                await ws.send_text(json.dumps({"updated": True}))
            except:
                pass
    return {"msg": "Wyświetlacz zaktualizowany pomyślnie"}

@router.delete("/delete/{display_id}")
def delete_display(display_id: int, db: Session = Depends(database.get_db)):
    display = db.query(models.Display).filter(models.Display.id == display_id).first()
    if not display:
        raise HTTPException(status_code=404, detail="Display not found")

    db.delete(display)
    db.commit()
    return {"msg": "Wyświetlacz usunięty pomyślnie"}