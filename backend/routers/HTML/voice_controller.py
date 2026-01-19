from fastapi import APIRouter, WebSocket, Depends
from sqlalchemy.orm import Session, joinedload, contains_eager
from datetime import datetime, timedelta, date
import asyncio
import json
from ... import models, database
from sqlalchemy import or_, func
from sqlalchemy.dialects import postgresql
from ...listeners import voice_update_listeners # Słownik kolejek zdarzeń dla komunikatów głosowych

router = APIRouter()

def roman_to_arabic(roman):
    roman_numerals = {
        'I': 1,
        'V': 5,
        'X': 10,
        'L': 50,
        'C': 100,
        'D': 500,
        'M': 1000
    }
    total = 0
    prev_value = 0
    for char in reversed(roman):
        value = roman_numerals.get(char, 0)
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value
    return total

@router.websocket("/voice-timetable-edit/{station_id}")
async def ws_voice_timetable_edit(websocket: WebSocket, station_id: int, db: Session = Depends(database.get_db)):
    await websocket.accept()
    print(f"Podłączono kontroler głosowy dla stacji {station_id}")
    
    # Tworzenie kolejki zdarzeń dla tego konkretnego połączenia
    update_queue = asyncio.Queue()
    # Rejestracja kolejki w globalnym słowniku
    voice_update_listeners[station_id].append(update_queue)
    today = date.today()

    try:
        while True:
            try:
                # Inteligentne oczekiwanie na sygnał z kolejki
                stop_id = await asyncio.wait_for(update_queue.get(), timeout=60)
                
                print(f"Wykryto edycję dla stacji {station_id} i postoju {stop_id}!")
                
                # Pobieramy szczegóły zmienionego postoju
                stop = (
                    db.query(models.Stop)
                    .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == today))
                    .filter(models.Stop.id == stop_id)
                    .options(
                        joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.type),
                        joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.final_station),
                        contains_eager(models.Stop.statuses),
                    )
                    .first()
                )
                
                if not stop or not stop.trip.calendar.runs_on_date(today):
                    continue

                status = next((st for st in stop.statuses if st.date == today), None)
                
                # Wyznaczanie stacji początkowej (pierwszy stop w trasie)
                origin_stop = (
                    db.query(models.Stop)
                    .join(models.Track)
                    .join(models.Platform)
                    .join(models.Station)
                    .filter(models.Stop.trip_id == stop.trip_id)
                    .order_by(models.Stop.sequence.asc()) 
                    .first()
                )

                # Parsowanie nazwy pociągu
                train_name = ""
                if stop.trip.route.train_number:
                    parts = stop.trip.route.train_number.split()
                    train_name = " ".join(parts[1:]) if len(parts) > 1 else parts[0]

                # Przygotowanie danych dla frontendu
                print("Wysyłam dane")
                data_payload = {
                    "id": stop.id,
                    "train_type": stop.trip.route.type.name if stop.trip.route.type else "",
                    "train_number": train_name,
                    "origin_station": origin_stop.original_track.platform.station.name if origin_stop else "Nieznana",
                    "final_station": stop.trip.route.final_station.name if stop.trip.route.final_station else "",
                    "arrival_time": stop.arrival.strftime("%H:%M") if stop.arrival else None,
                    "arrival_delay": status.arrival_delay if status else 0,
                    "departure_time": stop.departure.strftime("%H:%M") if stop.departure else None,
                    "is_cancelled": status.is_cancelled if status else False,
                    "bus": status.bus if status else False
                }
                
                await websocket.send_text(json.dumps(data_payload))

            except asyncio.TimeoutError:
                # Brak edycji w ciągu 60s, pętla kręci się dalej (keep-alive)
                pass

    except Exception as e:
        print(f"Błąd WS ({station_id}): {e}")
    finally:
        print("Rozłączono głos")
        # Sprzątanie po rozłączeniu
        if station_id in voice_update_listeners:
            if update_queue in voice_update_listeners[station_id]:
                voice_update_listeners[station_id].remove(update_queue)


@router.websocket("/voice-data/{station_id}")
async def ws_voice_data(websocket: WebSocket, station_id: int, db: Session = Depends(database.get_db)):
    await websocket.accept()
    print(f"Podłączono kontroler głosowy dla stacji {station_id}")

    try:
        while True:
            # Commit, aby odświeżyć stan bazy danych (pobranie zmian z innych sesji)
            db.commit()
            
            today = date.today()
            current_datetime = datetime.now()
            # Patrzymy 15 minut wstecz
            lookback = (current_datetime - timedelta(minutes=15)).time()

            # Definicja czasu rzeczywistego bezpośrednio w SQL (wykorzystujemy StopStatus)
            # Używamy postgresql.INTERVAL do dodawania minut opóźnienia do czasu planowego
            real_arrival = models.Stop.arrival + func.cast(
                func.concat(func.coalesce(models.StopStatus.arrival_delay, 0), ' minutes'), 
                postgresql.INTERVAL
            )
            
            real_departure = models.Stop.departure + func.cast(
                func.concat(func.coalesce(models.StopStatus.departure_delay, 0), ' minutes'), 
                postgresql.INTERVAL
            )

            actual_op_time = func.coalesce(real_arrival, real_departure)

            # Pobieramy pociągi na stacji
            stops = (
                db.query(models.Stop)
                .join(models.Track, models.Stop.original_track_id == models.Track.id)
                .join(models.Platform, models.Track.platform_id == models.Platform.id)
                .outerjoin(models.StopStatus, (models.StopStatus.stop_id == models.Stop.id) & (models.StopStatus.date == today))
                .filter(
                    models.Platform.station_id == station_id,
                    or_(
                        real_arrival >= lookback,
                        real_departure >= lookback
                    )
                )
                .options(
                    joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.type),
                    joinedload(models.Stop.trip).joinedload(models.Trip.route).joinedload(models.Route.final_station),
                    contains_eager(models.Stop.statuses),
                    joinedload(models.Stop.original_track).joinedload(models.Track.platform)
                )
                .order_by(actual_op_time.asc())
                .limit(20)
                .all()
            )

            data_list = []
            for s in stops:
                # Sprawdzenie kalendarza (czy pociąg kursuje dzisiaj)
                if not s.trip.calendar.runs_on_date(today):
                    continue

                status = next((st for st in s.statuses if st.date == today), None)
                
                # Obliczanie czasu postoju (uwzględniając ewentualną północ)
                stop_duration = 0
                if s.arrival and s.departure:
                    dt_arr = datetime.combine(today, s.arrival)
                    dt_dep = datetime.combine(today, s.departure)
                    if dt_dep < dt_arr:
                        dt_dep += timedelta(days=1)
                    stop_duration = (dt_dep - dt_arr).total_seconds() / 60

                # Wyznaczanie stacji początkowej (pierwszy stop w trasie)
                origin_stop = (
                    db.query(models.Stop)
                    .join(models.Track)
                    .join(models.Platform)
                    .join(models.Station)
                    .filter(models.Stop.trip_id == s.trip_id)
                    .order_by(models.Stop.sequence.asc())
                    .first()
                )

                # Parsowanie nazwy pociągu - usunięcie numeru, pozostawienie imienia
                if(s.trip.route.train_number):
                    train_number_to_edit = (s.trip.route.train_number).split()
                    # Łączy słowa od drugiego do końca, rozdzielając je spacją
                    train_name = " ".join(train_number_to_edit[1:])
                else:
                    train_name = ""

                # Wyznaczanie toru i peronu (uwzględniając dynamiczną zmianę w StopStatus)
                actual_track_id = status.track_id if (status and status.track_id) else s.original_track_id
                
                # Pobieramy dane o aktualnym torze (z cache sesji lub bazy)
                current_track_obj = db.query(models.Track).options(joinedload(models.Track.platform)).filter(models.Track.id == actual_track_id).first()
                
                platform_num = current_track_obj.platform.number if current_track_obj and current_track_obj.platform else ""
                track_num = current_track_obj.number if current_track_obj else ""
                
                # Sprawdzamy czy tor został zmieniony względem planu (original_track_id)
                changed_track = False
                if status and status.track_id and status.track_id != s.original_track_id:
                    changed_track = True

                data_list.append({
                    "id": s.id,
                    "train_type": s.trip.route.type.name if s.trip.route.type else "",
                    "train_number": train_name,
                    "origin_station": origin_stop.original_track.platform.station.name if origin_stop else "",
                    "final_station": s.trip.route.final_station.name if s.trip.route.final_station else "",
                    "arrival_time": s.arrival.strftime("%H:%M") if s.arrival else None,
                    "departure_time": s.departure.strftime("%H:%M") if s.departure else None,
                    "arrival_delay": status.arrival_delay if status and status.arrival_delay else 0,
                    "departure_delay": status.departure_delay if status else 0,
                    "platform": roman_to_arabic(platform_num) if platform_num else "",
                    "track": track_num,
                    "stop_duration": int(stop_duration),
                    "changed_track": changed_track,
                    "is_cancelled": status.is_cancelled if status else False,
                    "bus": status.bus if status else False
                })

            await websocket.send_text(json.dumps(data_list))
            await asyncio.sleep(5)

    except Exception as e:
        print(f"Rozłączono głos ({station_id}): {e}")