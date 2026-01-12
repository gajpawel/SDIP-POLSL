from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, contains_eager
from sqlalchemy import or_
from datetime import datetime, time, timedelta, date
from .. import models, database, schemas
import asyncio
from typing import List, Dict
from collections import defaultdict
from typing import Optional, List, Tuple

router = APIRouter(prefix="/timetable", tags=["timetable"])

# Słownik przechowujący kolejki zdarzeń dla każdej stacji
# Klucz: station_id (int), Wartość: Lista kolejek asyncio.Queue
station_update_listeners: Dict[int, List[asyncio.Queue]] = defaultdict(list)
voice_update_listeners: Dict[int, List[asyncio.Queue]] = defaultdict(list)

async def notify_station_update(station_id: int):
    """
    Funkcja pomocnicza do wysyłania sygnału odświeżenia 
    do wszystkich WebSocketów nasłuchujących na danej stacji.
    """
    if station_id in station_update_listeners:
        for queue in station_update_listeners[station_id]:
            # Wrzucamy cokolwiek do kolejki, aby przerwać oczekiwanie (await)
            await queue.put(True)

async def notify_voice_update(station_id: int, stop_id: int):
    """
    Funkcja pomocnicza do wysyłania sygnału odświeżenia 
    do WebSocketów dla komunikatów głosowych nasłuchujących na danej stacji.
    """
    if station_id in voice_update_listeners:
        for queue in voice_update_listeners[station_id]:
            # Wrzucamy id zmienionego postoju do kolejki, aby przerwać oczekiwanie (await)
            await queue.put(stop_id)


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
            .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == target_date))
            .filter(
                models.Platform.station_id == station_id,
                models.Stop.departure.isnot(None),
                models.Route.final_station_id != station_id
            )
            .options(
                #joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.type),
                #joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.carrier),
                #joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.final_station),
                #joinedload(models.Stop.trip).joinedload(models.Trip.calendar),
                #joinedload(models.Stop.original_track).joinedload(models.Track.platform),
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
def get_timetable(station_id: int, db: Session = Depends(database.get_db)):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    current_datetime = datetime.now()

    def get_stops_for_date(target_date: date):
        return (
            db.query(models.Stop)
            .join(models.Trip)
            .join(models.Track, models.Stop.original_track_id == models.Track.id)
            .join(models.Platform, models.Track.platform_id == models.Platform.id)
            .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == target_date))
            .filter(
                models.Platform.station_id == station_id,
                models.Stop.arrival.isnot(None),
                models.Stop.sequence != 0
            )
            .options(
                #joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.type),
                #joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.carrier),
                #joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.final_station),
                #joinedload(models.Stop.original_track).joinedload(models.Track.platform),
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


@router.get("/stop/{stop_id}")
def get_stop_details(stop_id: int, db: Session = Depends(database.get_db)):
    """
    Zwraca szczegóły postoju (dla danego stop_id)
    """
    today = date.today()
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
    if status:
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

@router.get("/train/{train_id}")
def get_train_details(train_id: int, db: Session = Depends(database.get_db)):
    """
    Zwraca szczegóły trasy pociągu (dla danego train_id)
    """
    trip_id = db.query(models.Stop.trip_id).filter(models.Stop.id == train_id).scalar()
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

# Lista dostępnych torów do zmiany dla danego postoju
@router.get("/tracks/{stop_id}")
def get_tracks(stop_id: int, db: Session = Depends(database.get_db)):
    today = date.today()

    def is_collision(
        a_arrival: Optional[int],
        a_departure: Optional[int],
        b_arrival: Optional[int],
        b_departure: Optional[int]
    ) -> bool:

        def get_segments(arr: Optional[int], dep: Optional[int]) -> List[Tuple[int, int]]:
            if arr is None and dep is None:
                return []
            
            start, end = 0, 0
            if arr is None:
                start, end = dep, dep + 5
            elif dep is None:
                start, end = arr, arr + 5
            else:
                start, end = arr, dep

            if end < start:
                return [(start, 1440), (0, end)]
            
            return [(start, end)]

        def segments_collide(s1: Tuple[int, int], s2: Tuple[int, int]) -> bool:
            return not (s1[1] <= s2[0] or s2[1] <= s1[0])

        segments_a = get_segments(a_arrival, a_departure)
        segments_b = get_segments(b_arrival, b_departure)

        if not segments_a or not segments_b:
            return False

        for seg_a in segments_a:
            for seg_b in segments_b:
                if segments_collide(seg_a, seg_b):
                    return True

        return False

    def get_minutes(t, delay=0):
        """Pomocnicza funkcja konwertująca Time na minuty od północy."""
        if t is None: return None
        return (t.hour * 60 + t.minute + (delay or 0)) % 1440

    # 1. Pobieramy szczegóły wybranego postoju
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

    # 2. Pobieramy station_id (poprzez strukturę peronów)
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

    # 3. Wyznaczamy parametry czasowe naszego pociągu (w minutach)
    my_status = next((st for st in stop.statuses if st.date == today), None)
    my_arr_min = get_minutes(stop.arrival, my_status.arrival_delay if my_status else 0)
    my_dep_min = get_minutes(stop.departure, my_status.departure_delay if my_status else 0)

    # 4. OPTYMALIZACJA: Pobieramy WSZYSTKIE inne dzisiejsze pociągi na tej stacji naraz
    # Pozwala to uniknąć zapytań SQL wewnątrz pętli po torach.
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

    # 5. Pobieramy listę wszystkich dostępnych torów na stacji
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
            # Sprawdzamy kalendarz (czy kursuje dzisiaj)
            if not os.trip.calendar.runs_on_date(today):
                continue
            
            os_status = next((st for st in os.statuses if st.date == today), None)
            
            # Odwołane pociągi i autobusy nie zajmują torów kolejowych
            if os_status and (os_status.is_cancelled or os_status.bus):
                continue

            # Sprawdzamy na jakim torze znajduje się pociąg (plan vs status)
            actual_track_id = os_status.track_id if (os_status and os_status.track_id) else os.original_track_id
            if actual_track_id != t.id:
                continue

            # Pobieramy czasy innego pociągu
            os_arr_min = get_minutes(os.arrival, os_status.arrival_delay if os_status else 0)
            os_dep_min = get_minutes(os.departure, os_status.departure_delay if os_status else 0)

            # 6. SPRAWDZANIE KOLIZJI (wykorzystuje Twoją nową logikę z track_collision.py)
            if is_collision(my_arr_min, my_dep_min, os_arr_min, os_dep_min):
                collision = True
                break

            # 7. Wyznaczanie dostępności (najbliższy pociąg po naszym odjeździe)
            # Logika pomocnicza dla frontendu
            if os_arr_min is not None:
                # Uproszczone wyznaczanie pociągu przyjeżdżającego "później"
                # (W systemach czasu rzeczywistego zwykle porównuje się to w skali liniowej dnia)
                if my_dep_min is not None and os_arr_min >= my_dep_min:
                    if next_arrival_dt is None or os_arr_min < next_arrival_dt:
                        next_arrival_dt = os_arr_min

        if not collision:
            # Formatuje minuty z powrotem na HH:MM
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


@router.put("/edit/{id}")
async def edit_timetable(id: int, data: schemas.StopStatusUpdate, db: Session = Depends(database.get_db)): # Zmieniono na async def
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

    # --- NOWOŚĆ: Powiadamianie WebSocketów ---
    # Musimy znaleźć station_id, do którego należy ten postój.
    # Ścieżka: Stop -> Track -> Platform -> Station
    try:
        # Pobieramy obiekt z relacjami, żeby dostać się do ID stacji
        station_id = status.track.platform.station_id if status and status.track and status.track.platform else stop.original_track.platform.station_id
        await notify_station_update(station_id)
        print(f"Wysłano sygnał odświeżenia dla stacji ID: {station_id}")
    except Exception as e:
        print(f"Błąd podczas powiadamiania WS: {e}")

    try:
        station_id = status.track.platform.station_id if status and status.track and status.track.platform else stop.original_track.platform.station_id
        await notify_voice_update(station_id, id)
        print(f"Wysłano sygnał komunikatu dla stacji ID: {station_id}")
    except Exception as e:
        print(f"Błąd podczas powiadamiania WS: {e}")

    return {"msg": "Postój zaktualizowany pomyślnie", "id": stop.id}
