from fastapi import APIRouter, WebSocket, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, contains_eager
from datetime import datetime, timedelta, date
from ... import models, database
import json
import asyncio
from ...listeners import station_update_listeners # Słownik kolejek zdarzeń dla wyświetlaczy stacyjnych

router = APIRouter(prefix="/displays", tags=["displays_views"])

# Wyświetlacz zbiorczy peronowy
@router.websocket("/platform-display-data/{platform_id}")
async def ws_platform_display_data(websocket: WebSocket, platform_id: int, db: Session = Depends(database.get_db)):
    await websocket.accept()
    print(f"Połączono z wyświetlaczem peronowym {platform_id}")

    station_id = (
        db.query(models.Platform)
        .filter(models.Platform.id == platform_id)
        .first()
        .station_id
    )
    # Tworzenie kolejki zdarzeń dla tego konkretnego połączenia
    update_queue = asyncio.Queue()
    # Rejestracja kolejki w globalnym słowniku
    station_update_listeners[station_id].append(update_queue)

    try:
        while True:
            db.commit()
            current_datetime = datetime.now()
            
            today = current_datetime.date()

            stop_data = (
                db.query(models.Stop)
                .join(models.Track)
                .join(models.Platform)
                .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == today))
                .filter(
                    models.Platform.station_id == station_id,
                    models.Stop.departure.isnot(None)
                )
                .options(
                    joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.type),
                    joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.final_station),
                    joinedload(models.Stop.original_track)
                    .joinedload(models.Track.platform)
                    .joinedload(models.Platform.station),
                    contains_eager(models.Stop.statuses)
                )
                .order_by(models.Stop.departure.asc())
                .all()
            )

            filtered_stops = []

            for s in stop_data:
                # Pominięcie pociągów, które nie odjadą z tego toru, odwołanych, zastąpionych autobusem lub niekursujących dziś
                if not s.trip.calendar.runs_on_date(today):
                    continue
                status = next((st for st in s.statuses if st.date == today), None)
                if not status and s.original_track.platform_id != platform_id:
                    continue
                elif status and status.track and status.track.platform_id != platform_id:
                    continue
                elif status and status.track is None and s.original_track.platform_id != platform_id:
                    continue
                scheduled_departure = datetime.combine(current_datetime.date(), s.departure)
                
                delay_minutes = status.departure_delay if status and status.departure_delay is not None else 0
                estimated_departure = scheduled_departure + timedelta(minutes=delay_minutes)
                
                if estimated_departure >= current_datetime:
                    s.estimated_departure_dt = estimated_departure
                    filtered_stops.append(s)
                
                if len(filtered_stops) >= 3:
                    break

            if not filtered_stops:
                await websocket.send_text(json.dumps([])) # Pusta lista zamiast błędu, żeby wyczyścić ekran
                sleep_time = 30 # Jeśli brak pociągów, sprawdź za 30 sekund
            else:
                display_data = []
                for s in filtered_stops:
                    intermediate_data = (
                        db.query(models.Stop)
                        .join(models.Track)
                        .join(models.Platform)
                        .filter(
                            models.Stop.trip_id == s.trip_id,
                            models.Stop.sequence > s.sequence,
                        )
                        .options(
                            joinedload(models.Stop.original_track)
                            .joinedload(models.Track.platform)
                            .joinedload(models.Platform.station)
                        )
                        .order_by(models.Stop.departure.asc())
                        .all()
                    )

                    intermediate = [
                        i.original_track.platform.station.name
                        for i in intermediate_data
                        if i.original_track and i.original_track.platform and i.original_track.platform.station and i.original_track.platform.station.id != i.trip.route.final_station.id
                    ]

                    status = next((st for st in s.statuses if st.date == today), None)
                    if status and status.track:
                        track = db.query(models.Track).filter(models.Track.id == status.track_id).first()
                    else:
                        track = db.query(models.Track).filter(models.Track.id == s.original_track_id).first()
                    d = {
                        "station": s.trip.route.final_station.name if s.trip.route.final_station else None,
                        "departure_time": s.departure.strftime("%H:%M") if s.departure else None,
                        "departure_delay": status.departure_delay if status and status.departure_delay else 0,
                        "track": track.number if track else None,
                        "train_type": s.trip.route.type.code if s.trip.route.type else None,
                        "intermediate": intermediate,
                        "train_number": s.trip.route.train_number,
                        "is_cancelled": status.is_cancelled if status else False,
                        "bus": status.bus if status else False
                    }
                    display_data.append(d)
                await websocket.send_text(json.dumps(display_data))
                # Obliczanie czasu do następnego odświeżenia - gdy pierwszy pociąg na liście "odjedzie" (jego czas minie)
                first_train_departure = filtered_stops[0].estimated_departure_dt
                seconds_until_departure = (first_train_departure - datetime.now()).total_seconds()
                
                # Bufor (1 sekunda), żeby na pewno zniknął przy następnym pobraniu
                # Oczekiwanie nie dłużej niż 60 sekund (health check) i nie krócej niż 5 sekund (żeby nie mrugało przy błędnych zegarach)
                sleep_time = max(60, min(seconds_until_departure + 1, 60))

            # Inteligentne oczekiwanie
            try:
                # Oczekiwanie na sygnał z kolejki (od edit_timetable) PRZEZ określony czas (sleep_time)
                await asyncio.wait_for(update_queue.get(), timeout=sleep_time)
                # Jeśli kod tutaj dotrze, to znaczy, że update_queue.get() zwróciło wynik (nastąpiła edycja rozkladu)
                print(f"Wykryto edycję dla stacji {station_id}! Natychmiastowe odświeżanie.")
            except asyncio.TimeoutError:
                # Jeśli minął czas timeout=sleep_time, rzucany jest wyjątek - nie wystąpiła edycja, ale czas minął
                pass
    
    except Exception as e:
        print(f"Rozłączono ({platform_id}): {e}")
    finally:
        # Usuwanie kolejki z listy listenerów po rozłączeniu
        if station_id in station_update_listeners:
            if update_queue in station_update_listeners[station_id]:
                station_update_listeners[station_id].remove(update_queue)

# Wyświetlacz wejściowy peronowy
@router.websocket("/entrance-platform-display-data/{platform_id}")
async def ws_entrance_platform_display_data(
    websocket: WebSocket,
    platform_id: int,
    db: Session = Depends(database.get_db)
):
    await websocket.accept()
    print(f"Połączono z wejściowym wyświetlaczem peronowym {platform_id}")

    station_id = (
        db.query(models.Platform)
        .filter(models.Platform.id == platform_id)
        .first()
        .station_id
    )

    #  Tworzenie kolejki zdarzeń dla tego konkretnego połączenia
    update_queue = asyncio.Queue()
    # Rejestracja kolejki w globalnym słowniku
    station_update_listeners[station_id].append(update_queue)
    today = date.today()
    try:
        while True:
            db.commit()
            limit = (datetime.now() + timedelta(minutes=20))

            tracks = (
                db.query(models.Track)
                .filter(models.Track.platform_id == platform_id)
                .all()
            )

            stops = []
            for t in tracks:
                stop_data = (
                    db.query(models.Stop)
                    .join(models.Track)
                    .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == today))
                    .filter(models.Stop.departure.isnot(None))
                    .options(
                        joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.type),
                        joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.final_station),
                        contains_eager(models.Stop.statuses)

                    )
                    .order_by(models.Stop.departure.asc())
                    .all()
                )

                current_datetime = datetime.now()
                filtered_stop = []

                for s in stop_data:
                    status = next((st for st in s.statuses if st.date == today), None)
                    # Pominięcie pociągów, które nie odjadą z tego toru, odwołanych, zastąpionych autobusem lub niekursujących dziś
                    if status and status.is_cancelled:
                        continue
                    if status and status.bus:
                        continue
                    if not s.trip.calendar.runs_on_date(today):
                        continue
                    if not status and s.original_track_id != t.id:
                        continue
                    if status and status.track is None and s.original_track_id != t.id:
                        continue
                    elif status and status.track_id != t.id:
                        continue
            
                    scheduled_departure = datetime.combine(current_datetime.date(), s.departure)
                    
                    delay_minutes = status.departure_delay if status and status.departure_delay else 0
                    estimated_departure = scheduled_departure + timedelta(minutes=delay_minutes)
                    
                    if estimated_departure >= current_datetime and estimated_departure <= limit:
                        s.estimated_departure_dt = estimated_departure 
                        filtered_stop = s
                        break

                # jeśli brak odjazdu — NIE dodawaj None
                if filtered_stop:
                    stops.append(filtered_stop)

             # Wysłanie danych do klienta
            if not stops:
                await websocket.send_text(json.dumps([])) # Pusta lista zamiast błędu, żeby wyczyścić ekran
                sleep_time = 30 # Jeśli brak pociągów, sprawdź za 30 sekund
            else:
                display_data = []
                for s in stops:
                    status = next((st for st in s.statuses if st.date == today), None)
                
                    d = {
                        "station": (
                            s.trip.route.final_station.name
                            if s.trip and s.trip.route and s.trip.route.final_station
                            else None
                        ),
                        "departure_time": (
                            s.departure.strftime("%H:%M") if s.departure else None
                        ),
                        "departure_delay": status.departure_delay if status and status.departure_delay else 0,
                        "track": status.track.number if status and status.track else s.original_track.number,
                        "train_type": s.trip.route.type.code if s.trip and s.trip.route and s.trip.route.type else None,
                        "train_number": s.trip.route.train_number if s.trip and s.trip.route else None,
                        "intermediate": [],  # Zwracane w razie potrzeby
                    }
                    display_data.append(d)

                await websocket.send_text(json.dumps(display_data))
                # Obliczanie czasu do następnego odświeżenia - gdy pierwszy pociąg na liście "odjedzie" (jego czas minie)
                first_train_departure = min(stops[0].estimated_departure_dt, stops[1].estimated_departure_dt) if len(stops) > 1 else stops[0].estimated_departure_dt
                seconds_until_departure = (first_train_departure - datetime.now()).total_seconds()
                
                # Dodajno bufor (1 sekunda), żeby na pewno zniknął przy następnym pobraniu
                # Oczekiwanie nie dłużej niż 60 sekund (health check) i nie krócej niż 5 sekund (żeby nie mrugało przy błędnych zegarach)
                sleep_time = max(60, min(seconds_until_departure + 1, 60))

            # Inteligentne oczekiwanie
            try:
                # Oczekiwanie na sygnał z kolejki (od edit_timetable) PRZEZ określony czas (sleep_time)
                await asyncio.wait_for(update_queue.get(), timeout=sleep_time)
                # Jeśli kod tutaj dotrze, to znaczy, że update_queue.get() zwróciło wynik (nastąpiła edycja rozkladu)
                print(f"Wykryto edycję dla stacji {station_id}! Natychmiastowe odświeżanie.")
            except asyncio.TimeoutError:
                # Jeśli minął czas timeout=sleep_time, rzucany jest wyjątek - nie wystąpiła edycja, ale czas minął
                pass

    except Exception as e:
        print(f"Rozłączono ({platform_id}): {e}")
    finally:
        # Usuwanie kolejki z listy listenerów po rozłączeniu
        if station_id in station_update_listeners:
            if update_queue in station_update_listeners[station_id]:
                station_update_listeners[station_id].remove(update_queue)


# Wyświetlacz stacyjny lub tablica informacyjna - odjazdy
@router.websocket("/station-display-departures-data/{station_id}")
async def ws_station_display_departures_data(websocket: WebSocket, station_id: int, db: Session = Depends(database.get_db)):
    await websocket.accept()
    print(f"Połączono z wyświetlaczem stacyjnym {station_id}")

    # Tworzenie kolejki zdarzeń dla tego konkretnego połączenia
    update_queue = asyncio.Queue()
    # Rejestracja kolejki w globalnym słowniku
    station_update_listeners[station_id].append(update_queue)

    try:
        while True:
            # Pobieranie i przetwarzanie danych
            db.commit() # Ważne: nowa transakcja przy każdym obiegu
            current_datetime = datetime.now()
            today = date.today()

            stop_candidates = (
                db.query(models.Stop)
                .join(models.Track)
                .join(models.Platform)
                .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == today))
                .filter(
                    models.Platform.station_id == station_id,
                    models.Stop.departure.isnot(None),
                )
                .options(
                    joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.carrier),
                    joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.type),
                    joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.final_station),
                    joinedload(models.Stop.original_track).joinedload(models.Track.platform).joinedload(models.Platform.station),
                    contains_eager(models.Stop.statuses)
                )
                .order_by(models.Stop.departure.asc())
                .all()
            )

            filtered_stops = []
            # Filtracja w Pythonie
            for s in stop_candidates:
                # Pominięcie pociągów, które nie odjadą dziś
                if not s.trip.calendar.runs_on_date(today):
                    continue
                status = next((st for st in s.statuses if st.date == today), None)
                scheduled_departure = datetime.combine(current_datetime.date(), s.departure)
                delay_minutes = status.departure_delay if status and status.departure_delay is not None else 0
                estimated_departure = scheduled_departure + timedelta(minutes=delay_minutes)
                if estimated_departure >= current_datetime:
                    s.estimated_departure_dt = estimated_departure 
                    filtered_stops.append(s)
                
                if len(filtered_stops) >= 10:
                    break
            
            # Wysłanie danych do klienta
            if not filtered_stops:
                await websocket.send_text(json.dumps([]))
                sleep_time = 30 # Jeśli brak pociągów, sprawdź za 30 sekund
            else:
                # Budowanie JSON
                display_data = []
                for s in filtered_stops:
                    intermediate_data = (
                        db.query(models.Stop)
                        .join(models.Track)
                        .join(models.Platform)
                        .filter(
                            models.Stop.trip_id == s.trip_id,
                            models.Stop.sequence > s.sequence,
                        )
                        .options(
                            joinedload(models.Stop.original_track)
                            .joinedload(models.Track.platform)
                            .joinedload(models.Platform.station)
                        )
                        .order_by(models.Stop.departure.asc())
                        .all()
                    )

                    intermediate = [
                        i.original_track.platform.station.name
                        for i in intermediate_data
                        if i.original_track and i.original_track.platform and i.original_track.platform.station and i.original_track.platform.station.id != i.trip.route.final_station.id
                    ]
                    status = next((st for st in s.statuses if st.date == today), None)
                    if status and status.track:
                        platform = status.track.platform.number if status.track.platform else None
                        track = status.track.number
                    else:
                        platform = s.original_track.platform.number if s.original_track and s.original_track.platform else None
                        track = s.original_track.number if s.original_track else None
                    d = {
                        "station": s.trip.route.final_station.name if s.trip.route.final_station else None,
                        "time": s.departure.strftime("%H:%M") if s.departure else None,
                        "delay": status.departure_delay if status and status.departure_delay else 0,
                        "platform/track": platform + "/" + str(track),
                        "train_type": s.trip.route.type.code if s.trip.route.type else None,
                        "intermediate": intermediate,
                        "train_number": s.trip.route.train_number,
                        "carrier": s.trip.route.carrier.code if s.trip.route.carrier else None,
                        "is_cancelled": status.is_cancelled if status else False,
                        "bus": status.bus if status else False
                    }
                    display_data.append(d)
                
                await websocket.send_text(json.dumps(display_data))

                # Obliczanie czasu do następnego odświeżenia - gdy pierwszy pociąg na liście "odjedzie" (jego czas minie)
                first_train_departure = filtered_stops[0].estimated_departure_dt
                seconds_until_departure = (first_train_departure - datetime.now()).total_seconds()
                
                # Dodajno bufor (1 sekunda), żeby na pewno zniknął przy następnym pobraniu
                # Oczekiwanie nie dłużej niż 60 sekund (health check) i nie krócej niż 5 sekund (żeby nie mrugało przy błędnych zegarach)
                sleep_time = max(60, min(seconds_until_departure + 1, 60))

            # Inteligentne oczekiwanie
            try:
                # Oczekiwanie na sygnał z kolejki (od edit_timetable) PRZEZ określony czas (sleep_time)
                await asyncio.wait_for(update_queue.get(), timeout=sleep_time)
                # Jeśli kod tutaj dotrze, to znaczy, że update_queue.get() zwróciło wynik (nastąpiła edycja rozkladu)
                print(f"Wykryto edycję dla stacji {station_id}! Natychmiastowe odświeżanie.")
            except asyncio.TimeoutError:
                # Jeśli minął czas timeout=sleep_time, rzucany jest wyjątek - nie wystąpiła edycja, ale czas minął
                pass
            
    except Exception as e:
        print(f"Rozłączono ({station_id}): {e}")
    finally:
        # Usuwanie kolejki z listy listenerów po rozłączeniu
        if station_id in station_update_listeners:
            if update_queue in station_update_listeners[station_id]:
                station_update_listeners[station_id].remove(update_queue)


# Wyświetlacz stacyjny lub tablica informacyjna - przyjazdy
@router.websocket("/station-display-arrivals-data/{station_id}")
async def ws_station_display_arrivals_data(websocket: WebSocket, station_id: int, db: Session = Depends(database.get_db)):
    await websocket.accept()
    print(f"Połączono z wyświetlaczem stacyjnym {station_id}")

    # Tworzenie kolejki zdarzeń dla tego konkretnego połączenia
    update_queue = asyncio.Queue()
    # Rejestracja kolejki w globalnym słowniku
    station_update_listeners[station_id].append(update_queue)

    try:
        while True:
            db.commit()

            current_datetime = datetime.now()
            today = date.today()
            filtered_stops = []

            stop_data = (
                db.query(models.Stop)
                .join(models.Track)
                .join(models.Platform)
                .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == today))
                .filter(
                    models.Platform.station_id == station_id,
                    models.Stop.arrival.isnot(None),
                )
                .options(
                    joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.carrier),
                    joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.type),
                    joinedload(models.Stop.original_track)
                    .joinedload(models.Track.platform)
                    .joinedload(models.Platform.station),
                    contains_eager(models.Stop.statuses)
                )
                .order_by(models.Stop.arrival.asc())
                .all()
            )

            filtered_stops = []

            for s in stop_data:
                # Pominięcie pociągów, które nie kursują dziś
                if not s.trip.calendar.runs_on_date(today):
                    continue
                status = next((st for st in s.statuses if st.date == today), None)
                scheduled_arrival = datetime.combine(current_datetime.date(), s.arrival)
                
                delay_minutes = status.arrival_delay if status and status.arrival_delay is not None else 0
                estimated_arrival = scheduled_arrival + timedelta(minutes=delay_minutes)
                
                if estimated_arrival >= current_datetime:
                    s.estimated_arrival_dt = estimated_arrival
                    filtered_stops.append(s)

                if len(filtered_stops) >= 10:
                    break

            # Wysłanie danych do klienta
            if not filtered_stops:
                await websocket.send_text(json.dumps([]))
                sleep_time = 30 # Jeśli brak pociągów, sprawdź za 30 sekund
            else:
                display_data = []
                for s in filtered_stops:
                    intermediate_data = (
                        db.query(models.Stop)
                        .join(models.Track)
                        .join(models.Platform)
                        .filter(
                            models.Stop.trip_id == s.trip_id,
                            models.Stop.sequence < s.sequence,
                        )
                        .options(
                            joinedload(models.Stop.original_track)
                            .joinedload(models.Track.platform)
                            .joinedload(models.Platform.station)
                        )
                        .order_by(models.Stop.sequence.asc())
                        .all()
                    )
                    intermediate_data.pop(0)  # Usuwamy stację początkową
                    intermediate = [
                        i.original_track.platform.station.name
                        for i in intermediate_data
                        if i.original_track and i.original_track.platform and i.original_track.platform.station
                    ]
                    station = (
                        db.query(models.Stop)
                        .join(models.Track)
                        .join(models.Platform)
                        .join(models.Station)
                        .filter(models.Stop.trip_id == s.trip_id)
                        .order_by(models.Stop.sequence.asc())
                        .first()
                    ).original_track.platform.station.name if s.original_track and s.original_track.platform and s.original_track.platform.station else None

                    status = next((st for st in s.statuses if st.date == today), None)
                    if status and status.track:
                        platform = status.track.platform.number if status.track.platform else None
                        track = status.track.number
                    else:
                        platform = s.original_track.platform.number if s.original_track and s.original_track.platform else None
                        track = s.original_track.number if s.original_track else None
                    
                    d = {
                        "station": station,
                        "time": s.arrival.strftime("%H:%M") if s.arrival else None,
                        "delay": status.arrival_delay if status and status.arrival_delay else 0,
                        "platform/track": platform + "/" + str(track),
                        "train_type": s.trip.route.type.code if s.trip.route.type else None,
                        "intermediate": intermediate,
                        "train_number": s.trip.route.train_number,
                        "carrier": s.trip.route.carrier.code if s.trip.route.carrier else None,
                        "is_cancelled": status.is_cancelled if status else False,
                        "bus": status.bus if status else False
                    }
                    display_data.append(d)
                await websocket.send_text(json.dumps(display_data))
                # Obliczanie czasu do następnego odświeżenia - gdy pierwszy pociąg na liście "odjedzie" (jego czas minie)
                first_train_arrival = filtered_stops[0].estimated_arrival_dt
                seconds_until_arrival = (first_train_arrival - datetime.now()).total_seconds()
                
                # Dodajno bufor (1 sekunda), żeby na pewno zniknął przy następnym pobraniu
                # Oczekiwanie nie dłużej niż 60 sekund (health check) i nie krócej niż 5 sekund (żeby nie mrugało przy błędnych zegarach)
                sleep_time = max(60, min(seconds_until_arrival + 1, 60))

            # Inteligentne oczekiwanie
            try:
                # Oczekiwanie na sygnał z kolejki (od edit_timetable) PRZEZ określony czas (sleep_time)
                await asyncio.wait_for(update_queue.get(), timeout=sleep_time)
                # Jeśli kod tutaj dotrze, to znaczy, że update_queue.get() zwróciło wynik (nastąpiła edycja rozkladu)
                print(f"Wykryto edycję dla stacji {station_id}! Natychmiastowe odświeżanie.")
            except asyncio.TimeoutError:
                # Jeśli minął czas timeout=sleep_time, rzucany jest wyjątek - nie wystąpiła edycja, ale czas minął
                pass
    except Exception as e:
        print(f"Rozłączono ({station_id}): {e}")
    finally:
        # Usuwanie kolejki z listy listenerów po rozłączeniu
        if station_id in station_update_listeners:
            if update_queue in station_update_listeners[station_id]:
                station_update_listeners[station_id].remove(update_queue)

# Infokiosk - przyjazdy
@router.get("/infokiosk-arrivals-data/{station_id}")
def infokiosk_arrivals_data(station_id: int, db: Session = Depends(database.get_db)):
    print(f"Połączono z infokioskiem {station_id}")
    try:
        today = date.today()
        stop = (
            db.query(models.Stop)
            .join(models.Track)
            .join(models.Platform)
            .filter(
                models.Platform.station_id == station_id,
                models.Stop.arrival.isnot(None),
            )
            .options(
                joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.carrier),
                joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.type),
                joinedload(models.Stop.original_track)
                .joinedload(models.Track.platform)
                .joinedload(models.Platform.station),
            )
            .order_by(models.Stop.arrival.asc())
            .all()
        )

        if not stop:
            raise HTTPException(status_code=404, detail="Brak przyjazdów.")

        display_data = []
        for s in stop:
            if not s.trip.calendar.runs_on_date(today):
                continue
            intermediate_data = (
                db.query(models.Stop)
                .join(models.Track)
                .join(models.Platform)
                .filter(
                    models.Stop.trip_id == s.trip_id,
                    models.Stop.sequence < s.sequence,
                )
                .options(
                    joinedload(models.Stop.original_track)
                    .joinedload(models.Track.platform)
                    .joinedload(models.Platform.station)
                )
                .order_by(models.Stop.sequence.asc())
                .all()
            )

            intermediate = [
                {"station": i.original_track.platform.station.name, "time": i.arrival.strftime("%H:%M")}
                for i in intermediate_data
                if i.original_track and i.original_track.platform and i.original_track.platform.station and i.arrival
            ]

            station = (
                db.query(models.Stop)
                .join(models.Track)
                .join(models.Platform)
                .join(models.Station)
                .filter(models.Stop.trip_id == s.trip_id)
                .order_by(models.Stop.sequence.asc())
                .first()
            ).original_track.platform.station.name if s.original_track and s.original_track.platform and s.original_track.platform.station else None

            d = {
                "station": station,
                "time": s.arrival.strftime("%H:%M") if s.arrival else None,
                "platform/track": s.original_track.platform.number + "/" + str(s.original_track.number) if s.original_track else None,
                "intermediate": intermediate,
                "train_type": s.trip.route.type.code if s.trip.route.type else None,
                "train_number": s.trip.route.train_number,
                "carrier": s.trip.route.carrier.code if s.trip.route.carrier else None,
            }
            display_data.append(d)
        return display_data
    except Exception as e:
        print(f"Błąd ({station_id}): {e}")

# Infokiosk - odjazdy
@router.get("/infokiosk-departures-data/{station_id}")
def infokiosk_departures_data(station_id: int, db: Session = Depends(database.get_db)):
    print(f"Połączono z infokioskiem {station_id}")
    try:
            stop = (
                db.query(models.Stop)
                .join(models.Track)
                .join(models.Platform)
                .filter(
                    models.Platform.station_id == station_id,
                    models.Stop.departure.isnot(None),
                )
                .options(
                    joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.carrier),
                    joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.type),
                    joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.final_station),
                    joinedload(models.Stop.original_track)
                    .joinedload(models.Track.platform)
                    .joinedload(models.Platform.station),
                )
                .order_by(models.Stop.departure.asc())
                .all()
            )

            if not stop:
                raise HTTPException(status_code=404, detail="Brak odjazdów.")

            display_data = []
            for s in stop:
                today = date.today()
                if not s.trip.calendar.runs_on_date(today):
                    continue
                intermediate_data = (
                    db.query(models.Stop)
                    .join(models.Track)
                    .join(models.Platform)
                    .filter(
                        models.Stop.trip_id == s.trip_id,
                        models.Stop.sequence > s.sequence,
                    )
                    .options(
                        joinedload(models.Stop.original_track)
                        .joinedload(models.Track.platform)
                        .joinedload(models.Platform.station)
                    )
                    .order_by(models.Stop.sequence.asc())
                    .all()
                )

                intermediate = [
                    {"station": i.original_track.platform.station.name, "time": i.departure.strftime("%H:%M")}
                    for i in intermediate_data
                    if i.original_track and i.original_track.platform and i.original_track.platform.station and i.departure
                ]
                d = {
                    "station": s.trip.route.final_station.name if s.trip.route.final_station else None,
                    "time": s.departure.strftime("%H:%M") if s.departure else None,
                    "platform/track": s.original_track.platform.number + "/" + str(s.original_track.number) if s.original_track else None,
                    "intermediate": intermediate,
                    "train_type": s.trip.route.type.code if s.trip.route.type else None,
                    "train_number": s.trip.route.train_number,
                    "carrier": s.trip.route.carrier.code if s.trip.route.carrier else None,
                }
                display_data.append(d)
            return display_data
    except Exception as e:
        print(f"Błąd ({station_id}): {e}")

# Wyświetlacz krawędziowy
@router.websocket("/edge-display-data/{track_id}")
async def ws_edge_display_data(websocket: WebSocket, track_id: int, db: Session = Depends(database.get_db)):
    await websocket.accept()
    print(f"Połączono z wyświetlaczem {track_id}")
    
    station_id = (
        db.query(models.Track)
        .filter(models.Track.id == track_id)
        .join(models.Platform)
        .first()
        .platform.station_id
    )

    # Tworzenie kolejki zdarzeń dla tego konkretnego połączenia
    update_queue = asyncio.Queue()
    # Rejestracja kolejki w globalnym słowniku
    station_update_listeners[station_id].append(update_queue)
    today = date.today()

    try:
        while True:
            db.commit()
            limit = (datetime.now() + timedelta(minutes=20))

            stop_data = (
                db.query(models.Stop)
                .filter(models.Stop.departure.isnot(None))
                .order_by(models.Stop.departure.asc())
                .all()
            )

            current_datetime = datetime.now()
            filtered_stops = []

            for s in stop_data:
                status = next((st for st in s.statuses if st.date == today), None)
                # Pominięcie pociągów, które nie odjadą z tego toru, odwołanych, zastąpionych autobusem lub niekursujących dziś
                if not status and s.original_track_id != track_id:
                    continue
                if status and status.is_cancelled:
                    continue
                if status and status.bus:
                    continue
                if not s.trip.calendar.runs_on_date(today):
                    continue
                if status and status.track is None and s.original_track_id != track_id:
                    continue
                if status and status.track_id != track_id:
                    continue
                
                scheduled_departure = datetime.combine(current_datetime.date(), s.departure)
                
                delay_minutes = status.departure_delay if status and status.departure_delay is not None else 0
                estimated_departure = scheduled_departure + timedelta(minutes=delay_minutes)
                
                if estimated_departure >= current_datetime and estimated_departure <= limit:
                    s.estimated_departure_dt = estimated_departure
                    filtered_stops = s
                    break

            stop = filtered_stops if filtered_stops else None

            if not stop:
                await websocket.send_text(json.dumps([]))
                sleep_time = 30 # Jeśli brak pociągów, sprawdź za 30 sekund
            else:
                display_data = (
                    db.query(models.Stop)
                    .options(
                        joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.carrier),
                        joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.type),
                        joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.final_station),
                    )
                    .filter(models.Stop.id == stop.id)
                    .first()
                )
                # Pobieramy stacje pośrednie (po bieżącym przystanku)
                intermediate_data = (
                    db.query(models.Stop)
                    .join(models.Track)
                    .join(models.Platform)
                    .filter(
                        models.Stop.trip_id == display_data.trip_id,
                        models.Stop.sequence > display_data.sequence,
                    )
                    .options(
                        joinedload(models.Stop.original_track)
                        .joinedload(models.Track.platform)
                        .joinedload(models.Platform.station)
                    )
                    .order_by(models.Stop.departure.asc())
                    .all()
                )

                intermediate = [
                    i.original_track.platform.station.name
                    for i in intermediate_data
                    if i.original_track and i.original_track.platform and i.original_track.platform.station and i.original_track.platform.station.id != i.trip.route.final_station.id
                ]
                if intermediate:
                    intermediate.pop()  # Usuwamy stację docelową
                status = next((st for st in display_data.statuses if st.date == today), None)
                data = {
                    "station": display_data.trip.route.final_station.name if display_data.trip.route.final_station else "",
                    "departure_time": display_data.departure.strftime("%H:%M") if display_data.departure else "",
                    "departure_delay": status.departure_delay if status and status.departure_delay else 0,
                    "train_type": display_data.trip.route.type.name if display_data.trip.route.type else "",
                    "train_number": display_data.trip.route.train_number,
                    "carrier": display_data.trip.route.carrier.name if display_data.trip.route.carrier else "",
                    "intermediate": intermediate,
                }

                await websocket.send_text(json.dumps(data))
                # Obliczanie czasu do następnego odświeżenia - gdy pierwszy pociąg na liście "odjedzie" (jego czas minie)
                first_train_departure = stop.estimated_departure_dt
                seconds_until_departure = (first_train_departure - datetime.now()).total_seconds()
                
                # Dodajno bufor (1 sekunda), żeby na pewno zniknął przy następnym pobraniu
                # Oczekiwanie nie dłużej niż 60 sekund (health check) i nie krócej niż 5 sekund (żeby nie mrugało przy błędnych zegarach)
                sleep_time = max(60, min(seconds_until_departure + 1, 60))

            # Inteligentne oczekiwanie
            try:
                # Oczekiwanie na sygnał z kolejki (od edit_timetable) PRZEZ określony czas (sleep_time)
                await asyncio.wait_for(update_queue.get(), timeout=sleep_time)
                # Jeśli kod tutaj dotrze, to znaczy, że update_queue.get() zwróciło wynik (nastąpiła edycja rozkladu)
                print(f"Wykryto edycję dla stacji {station_id}! Natychmiastowe odświeżanie.")
            except asyncio.TimeoutError:
                # Jeśli minął czas timeout=sleep_time, rzucany jest wyjątek - nie wystąpiła edycja, ale czas minął
                pass

    except Exception as e:
        print(f"Rozłączono ({track_id}): {e}")
    finally:
        # Usuwanie kolejki z listy listenerów po rozłączeniu
        if station_id in station_update_listeners:
            if update_queue in station_update_listeners[station_id]:
                station_update_listeners[station_id].remove(update_queue)
