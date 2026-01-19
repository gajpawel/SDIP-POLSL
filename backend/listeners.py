import asyncio
from typing import List, Dict
from collections import defaultdict

# Słowniki przechowujące kolejki zdarzeń dla każdej stacji
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