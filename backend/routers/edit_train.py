from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, contains_eager, joinedload
from datetime import date
from .. import models, schemas, database, listeners, collision_detection

router = APIRouter()

# Lista dostępnych torów do zmiany dla danego postoju
@router.get("/tracks/{stop_id}")
def get_tracks(stop_id: int, db: Session = Depends(database.get_db)):
    today = date.today()

    stop = (
        db.query(models.Stop)
        .options(
            joinedload(models.Stop.trip).joinedload(models.Trip.route),
            joinedload(models.Stop.statuses)
        )
        .filter(models.Stop.id == stop_id)
        .first()
    )
    
    if not stop:
        raise HTTPException(status_code=404, detail="Postój nie znaleziony.")

    # Pobranie station_id (poprzez strukturę peronów)
    platform = (
        db.query(models.Platform)
        .join(models.Track, models.Track.platform_id == models.Platform.id)
        .join(models.Stop, models.Stop.original_track_id == models.Track.id)
        .filter(models.Stop.id == stop_id)
        .first()
    )
    
    if not platform:
        raise HTTPException(status_code=404, detail="Stacja nie znaleziona.")
    
    station_id = platform.station_id

    # Wyznaczenie parametrów czasowych pociągu (w minutach)
    my_status = next((st for st in stop.statuses if st.date == today), None)
    my_arr_min = collision_detection.get_minutes(stop.arrival, my_status.arrival_delay if my_status else 0)
    my_dep_min = collision_detection.get_minutes(stop.departure, my_status.departure_delay if my_status else 0)

    # Pobranie wszystkich innych dzisiejszych pociągów na tej stacji
    other_station_stops = (
        db.query(models.Stop)
        .join(models.Trip)
        .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == today))
        .filter(models.Stop.id != stop_id)
        .join(models.Track, models.Stop.original_track_id == models.Track.id)
        .join(models.Platform, models.Track.platform_id == models.Platform.id)
        .filter(models.Platform.station_id == station_id)
        .options(
            contains_eager(models.Stop.statuses),
            joinedload(models.Stop.trip)
        )
        .all()
    )

    # Pobranie wszystkich torów na stacji
    all_tracks = (
        db.query(models.Track)
        .join(models.Platform)
        .filter(models.Platform.station_id == station_id)
        .options(joinedload(models.Track.platform))
        .all()
    )

    result = []
    for t in all_tracks:
        collision = False
        next_arrival_dt = None

        for os in other_station_stops:
            if not os.trip.calendar.runs_on_date(today):
                continue
            
            os_status = next((st for st in os.statuses if st.date == today), None)
            
            # Odwołane pociągi i autobusy nie zajmują torów kolejowych
            if os_status and (os_status.is_cancelled or os_status.bus):
                continue

            # Sprawdzenie na jakim torze znajduje się pociąg (plan vs status)
            actual_track_id = os_status.track_id if (os_status and os_status.track_id) else os.original_track_id
            if actual_track_id != t.id:
                continue

            # Pobranie czasów innego pociągu
            os_arr_min = collision_detection.get_minutes(os.arrival, os_status.arrival_delay if os_status else 0)
            os_dep_min = collision_detection.get_minutes(os.departure, os_status.departure_delay if os_status else 0)

            # Sprawdzenie kolizji czasowej
            if collision_detection.is_collision(my_arr_min, my_dep_min, os_arr_min, os_dep_min):
                collision = True
                break

            # Wyznaczenie dostępności (najbliższy pociąg po odjeździe)
            if os_arr_min is not None:
                if my_dep_min is not None and os_arr_min >= my_dep_min:
                    if next_arrival_dt is None or os_arr_min < next_arrival_dt:
                        next_arrival_dt = os_arr_min

        if not collision:
            # Formatowanie minut z powrotem na HH:MM
            available_time = None
            if next_arrival_dt is not None:
                h, m = divmod(next_arrival_dt, 60)
                available_time = f"{h:02d}:{m:02d}"

            result.append({
                "id": t.id,
                "number": t.number,
                "platform_number": t.platform.number if t.platform else None,
                "available_to": available_time,
            })

    return result

@router.get("/stop/{stop_id}")
def get_stop_details(stop_id: int, db: Session = Depends(database.get_db)):
    """
    Zwraca szczegóły postoju (dla danego stop_id)
    """
    stop = (
        db.query(models.Stop)
        .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == date.today()))
        .options(
            joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.type),
            joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.carrier),
            joinedload(models.Stop.original_track).joinedload(models.Track.platform).joinedload(models.Platform.station),
            contains_eager(models.Stop.statuses)
        )
        .filter(models.Stop.id == stop_id)
        .first()
    )

    status = next((st for st in stop.statuses if st.date == date.today()), None)
    if status and status.track:
        platform = db.query(models.Platform).filter(models.Platform.id == status.track.platform_id).first()
        track = db.query(models.Track).filter(models.Track.id == status.track_id).first()
    else:
        platform = db.query(models.Platform).filter(models.Platform.id == stop.original_track.platform_id).first()
        track = db.query(models.Track).filter(models.Track.id == stop.original_track_id).first()
    

    if not stop:
        raise HTTPException(status_code=404, detail="Postój nie znaleziony.")

    return {
        "id": stop.id,
        "train_number": stop.trip.route.train_number,
        "train_type": stop.trip.route.type.name if stop.trip.route.type else None,
        "carrier": stop.trip.route.carrier.name if stop.trip.route.carrier else None,
        "final_station": stop.trip.route.final_station.name if stop.trip.route.final_station else None,
        "station": stop.original_track.platform.station.name if stop.original_track.platform.station else None,
        "station_id": stop.original_track.platform.station.id if stop.original_track.platform.station else None,
        "arrival": stop.arrival.strftime("%H:%M") if stop.arrival else None,
        "departure": stop.departure.strftime("%H:%M") if stop.departure else None,
        "arrival_delay": status.arrival_delay if status else None,
        "departure_delay": status.departure_delay if status else None,
        "track_id": track.id if track else None,
        "platform_id": platform.id if platform else None,
        "is_cancelled": status.is_cancelled if status else False,
        "bus": status.bus if status else False,
    }


@router.put("/edit-stop/{id}")
async def edit_timetable(id: int, data: schemas.StopStatusUpdate, db: Session = Depends(database.get_db)):
    """
    Edytuje szczegóły postoju i wymusza odświeżenie ekranów.
    """
    stop = (
        db.query(models.Stop)
        .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == date.today()))
        .options(contains_eager(models.Stop.statuses))
        .filter(models.Stop.id == id)
        .first()
    )
    today = date.today()
    status = next((st for st in stop.statuses if st.date == today), None)

    if not stop:
        raise HTTPException(status_code=404, detail="Postój nie znaleziony.")

    if status:
        # Aktualizacja pól
        status.arrival_delay = data.arrival_delay
        status.departure_delay = data.departure_delay
        status.is_cancelled = data.is_cancelled 
        status.track_id = data.track_id
        status.bus = data.bus
    else:
        # Tworzenie nowego statusu
        new_status = models.StopStatus(
            stop_id=stop.id,
            date=date.today(),
            arrival_delay=data.arrival_delay or 0,
            departure_delay=data.departure_delay or 0,
            is_cancelled=data.is_cancelled or False,
            track_id=data.track_id or stop.original_track_id,
            bus=data.bus or False
        )
        db.add(new_status)

    db.commit()
    db.refresh(stop)

    # Powiadamianie WebSocketów
    try:
        station_id = status.track.platform.station_id if status and status.track and status.track.platform else stop.original_track.platform.station_id
        await listeners.notify_station_update(station_id)
        print(f"Wysłano sygnał odświeżenia dla stacji ID: {station_id}")
    except Exception as e:
        print(f"Błąd podczas powiadamiania WS: {e}")

    try:
        station_id = status.track.platform.station_id if status and status.track and status.track.platform else stop.original_track.platform.station_id
        await listeners.notify_voice_update(station_id, id)
        print(f"Wysłano sygnał komunikatu dla stacji ID: {station_id}")
    except Exception as e:
        print(f"Błąd podczas powiadamiania WS: {e}")

    return {"msg": "Postój zaktualizowany pomyślnie", "id": stop.id}