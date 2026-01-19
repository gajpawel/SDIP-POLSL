from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, contains_eager
from datetime import datetime, time, timedelta, date
from .. import models, database

router = APIRouter(prefix="/timetable", tags=["timetable"])

@router.get("/station/{station_id}")
def get_station_name(station_id: int, db: Session = Depends(database.get_db)):
    station = db.query(models.Station).filter(models.Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Stacja nie znaleziona.")
    return {"id": station.id, "name": station.name}

@router.get("/departures/{station_id}")
def get_departures(station_id: int, db: Session = Depends(database.get_db)):
    """
    Zwraca listę odjazdów ze stacji (dla danego station_id) uwzględniając kalendarz i statusy rzeczywiste.
    """
    today = date.today()
    tomorrow = today + timedelta(days=1)
    current_datetime = datetime.now()

    def get_stops_for_date(target_date: date):
        return (
            db.query(models.Stop)
            .join(models.Trip)
            .join(models.Track, models.Stop.original_track_id == models.Track.id)
            .join(models.Platform, models.Track.platform_id == models.Platform.id)
            .join(models.Route, models.Trip.route_id == models.Route.id)
            .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == target_date))
            .filter(
                models.Platform.station_id == station_id,
                models.Stop.departure.isnot(None),
                models.Route.final_station_id != station_id
            )
            .options(
                contains_eager(models.Stop.statuses)
            )
            .all()
        )

    stops_today_raw = get_stops_for_date(today)
    stops_tomorrow_raw = get_stops_for_date(tomorrow)

    processed_stops = []

    # Przetwarzanie dzisiejszych odjazdów
    for s in stops_today_raw:
        if not s.trip.calendar.runs_on_date(today):
            continue
            
        status = next((st for st in s.statuses if st.date == today), None)
        
        # Obliczanie czasu rzeczywistego do filtrowania i sortowania
        delay = status.departure_delay if status and status.departure_delay else 0
        planned_dt = datetime.combine(today, s.departure)
        estimated_dt = planned_dt + timedelta(minutes=delay)

        if estimated_dt >= current_datetime:
            processed_stops.append({
                "stop": s,
                "status": status,
                "estimated": estimated_dt,
                "date": today
            })

    processed_stops.sort(key=lambda x: x['estimated'])
    first_departure_time = processed_stops[0]['stop'].departure if processed_stops else time(23, 59, 59)

    # Przetwarzanie jutrzejszych odjazdów (do czasu pierwszego dzisiejszego)
    for s in stops_tomorrow_raw:
        if not s.trip.calendar.runs_on_date(tomorrow):
            continue
            
        if s.departure >= first_departure_time:
            continue

        status = next((st for st in s.statuses if st.date == tomorrow), None)
        delay = status.departure_delay if status else 0
        estimated_dt = datetime.combine(tomorrow, s.departure) + timedelta(minutes=delay)

        processed_stops.append({
            "stop": s,
            "status": status,
            "estimated": estimated_dt,
            "date": tomorrow
        })

    if not processed_stops:
        raise HTTPException(status_code=404, detail="Brak odjazdów dla tej stacji.")

    processed_stops.sort(key=lambda x: x['estimated'])

    result = []
    for item in processed_stops:
        s = item['stop']
        status = item['status']
        
        # Wyznaczanie aktualnego toru i peronu
        # Jeśli w statusie jest track_id, musimy pobrać dane o tym torze
        actual_track_id = status.track_id if (status and status.track_id) else s.original_track_id
        
        # Pobieramy obiekt toru (z cache SQLAlchemy dzięki joinedload/identity map)
        actual_track = db.query(models.Track).options(joinedload(models.Track.platform)).filter(models.Track.id == actual_track_id).first()
        
        bus = False
        # Obsługa pola delay: liczba lub "Odwołany"
        display_delay = status.departure_delay if status else 0
        if status and status.is_cancelled:
            display_delay = "Odwołany"
        elif status and status.bus:
            bus = True

        result.append({
            "id": s.id,
            "station": s.trip.route.final_station.name if s.trip.route.final_station else None,
            "train_number": s.trip.route.train_number,
            "train_type": s.trip.route.type.code if s.trip.route.type else None,
            "train_code": s.trip.route.type.code if s.trip.route.type else None,
            "carrier": s.trip.route.carrier.name if s.trip.route.carrier else None,
            "platform": actual_track.platform.number if actual_track and actual_track.platform else None,
            "track": actual_track.number if actual_track else None,
            "original": True if actual_track_id == s.original_track_id else False,
            "departure_time": s.departure.strftime("%H:%M") if s.departure else None,
            "delay": display_delay,
            "bus": bus,
        })

    return result

@router.get("/arrivals/{station_id}")
def get_arrivals(station_id: int, db: Session = Depends(database.get_db)):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    current_datetime = datetime.now()

    def get_stops_for_date(target_date: date):
        return (
            db.query(models.Stop)
            .join(models.Trip)
            .join(models.Track, models.Stop.original_track_id == models.Track.id)
            .join(models.Platform, models.Track.platform_id == models.Platform.id)
            .join(models.Route, models.Trip.route_id == models.Route.id)
            .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == target_date))
            .filter(
                models.Platform.station_id == station_id,
                models.Stop.arrival.isnot(None),
                models.Stop.sequence != 0
            )
            .options(
                contains_eager(models.Stop.statuses)
            )
            .all()
        )

    stops_today_raw = get_stops_for_date(today)
    stops_tomorrow_raw = get_stops_for_date(tomorrow)

    processed_stops = []

    # Przetwarzanie dzisiejszych odjazdów
    for s in stops_today_raw:
        if not s.trip.calendar.runs_on_date(today):
            continue
            
        status = next((st for st in s.statuses if st.date == today), None)
        
        # Obliczanie czasu rzeczywistego do filtrowania i sortowania
        delay = status.arrival_delay if status and status.arrival_delay else 0
        planned_dt = datetime.combine(today, s.arrival)
        estimated_dt = planned_dt + timedelta(minutes=delay)

        if estimated_dt >= current_datetime:
            processed_stops.append({
                "stop": s,
                "status": status,
                "estimated": estimated_dt,
                "date": today
            })

    processed_stops.sort(key=lambda x: x['estimated'])
    first_arrival_time = processed_stops[0]['stop'].arrival if processed_stops else time(23, 59, 59)

    # Przetwarzanie jutrzejszych odjazdów (do czasu pierwszego dzisiejszego)
    for s in stops_tomorrow_raw:
        if not s.trip.calendar.runs_on_date(tomorrow):
            continue
            
        if s.arrival >= first_arrival_time:
            continue

        status = next((st for st in s.statuses if st.date == tomorrow), None)
        delay = status.arrival_delay if status else 0
        estimated_dt = datetime.combine(tomorrow, s.arrival) + timedelta(minutes=delay)

        processed_stops.append({
            "stop": s,
            "status": status,
            "estimated": estimated_dt,
            "date": tomorrow
        })

    if not processed_stops:
        raise HTTPException(status_code=404, detail="Brak przyjazdów dla tej stacji.")

    processed_stops.sort(key=lambda x: x['estimated'])

    result = []
    for item in processed_stops:
        s = item['stop']
        status = item['status']
        
        # Wyznaczanie aktualnego toru i peronu
        # Jeśli w statusie jest track_id, musimy pobrać dane o tym torze
        actual_track_id = status.track_id if (status and status.track_id) else s.original_track_id
        
        # Pobieramy obiekt toru (z cache SQLAlchemy dzięki joinedload/identity map)
        actual_track = db.query(models.Track).options(joinedload(models.Track.platform)).filter(models.Track.id == actual_track_id).first()
        bus = False
        # Obsługa pola delay: liczba lub "Odwołany"
        display_delay = status.arrival_delay if status else 0
        if status and status.is_cancelled:
            display_delay = "Odwołany"
        elif status and status.bus:
             bus = True
        
        # stacja początkowa
        station = (
                    db.query(models.Stop)
                    .join(models.Track)
                    .join(models.Platform)
                    .join(models.Station)
                    .filter(models.Stop.trip_id == s.trip_id)
                    .order_by(models.Stop.sequence.asc())
                    .first()
                ).original_track.platform.station.name if s.original_track and s.original_track.platform and s.original_track.platform.station else None

        result.append({
            "id": s.id,
            "station": station,
            "train_number": s.trip.route.train_number,
            "train_type": s.trip.route.type.code if s.trip.route.type else None,
            "train_code": s.trip.route.type.code if s.trip.route.type else None,
            "carrier": s.trip.route.carrier.name if s.trip.route.carrier else None,
            "platform": actual_track.platform.number if actual_track and actual_track.platform else None,
            "track": actual_track.number if actual_track else None,
            "original": True if actual_track_id == s.original_track_id else False,
            "arrival_time": s.arrival.strftime("%H:%M") if s.arrival else None,
            "delay": display_delay,
            "bus": bus,
        })

    return result

@router.get("/train/{stop_id}")
def get_train_details(stop_id: int, db: Session = Depends(database.get_db)):
    """
    Zwraca szczegóły trasy pociągu (dla danego train_id)
    """
    trip_id = db.query(models.Stop.trip_id).filter(models.Stop.id == stop_id).scalar()
    trip = (
        db.query(models.Trip)
        .options(
            joinedload(models.Trip.route).joinedload(models.Route.type),
            joinedload(models.Trip.route).joinedload(models.Route.carrier),
        )
        .filter(models.Trip.trip_id == trip_id)
        .first()
    )

    if not trip:
        raise HTTPException(status_code=404, detail="Pociąg nie znaleziony.")

    stops = (
        db.query(models.Stop)
        .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == date.today()))
        .options(
            joinedload(models.Stop.original_track).joinedload(models.Track.platform),
            contains_eager(models.Stop.statuses)
        )
        .filter(models.Stop.trip_id == trip_id)
        .order_by(models.Stop.sequence)
        .all()
    )
    
    stops_details = []
    for stop in stops:
        status = next((st for st in stop.statuses if st.date == date.today()), None)
        if status:
            platform = db.query(models.Platform).filter(models.Platform.id == status.track.platform_id).first()
            track = db.query(models.Track).filter(models.Track.id == status.track_id).first()
        else:
            platform = db.query(models.Platform).filter(models.Platform.id == stop.original_track.platform_id).first()
            track = db.query(models.Track).filter(models.Track.id == stop.original_track_id).first()
        stops_details.append({
            "id": stop.id,
            "station": platform.station.name if platform and platform.station else None,
            "arrival_time": stop.arrival.strftime("%H:%M") if stop.arrival else None,
            "departure_time": stop.departure.strftime("%H:%M") if stop.departure else None,
            "platform": platform.number if platform else None,
            "track": track.number if track else None,
            "original": False if status and stop.original_track_id!=status.track_id else True,
            "arrival_delay": status.arrival_delay if status else None,
            "departure_delay": status.departure_delay if status else None,
            "is_cancelled": status.is_cancelled if status else False,
            "bus": status.bus if status else False,
        })

    return {
        "train_number": trip.route.train_number,
        "train_type": trip.route.type.name if trip.route.type else None,
        "carrier": trip.route.carrier.name if trip.route.carrier else None,
        "final_station": trip.route.final_station.name if trip.route.final_station else None,
        "stops": stops_details,
    }