from fastapi import APIRouter, WebSocket

router = APIRouter(prefix="/displays", tags=["displays_appearance"])
connected_clients = {}  # Przechowuje połączenia WebSocket do zmian wyglądu

# WebSocket do powiadamiania o zmianach wyświetlacza
@router.websocket("/appearance/{display_id}")
async def ws_display(websocket: WebSocket, display_id: int):
    await websocket.accept()
    print(f"Połączono WS z wyświetlaczem {display_id}")
    clients = connected_clients.setdefault(display_id, set())
    clients.add(websocket)

    try:
        while True:
            await websocket.receive_text()
    except:
        pass
    finally:
        clients.remove(websocket)
        if not clients:
            del connected_clients[display_id]