from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database
from pwdlib import PasswordHash

# Hashowanie haseł
password_hash = PasswordHash.recommended()

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/add")
def add_admin(data: schemas.NewAdmin, db: Session = Depends(database.get_db)):
    existing = db.query(models.Administrator).filter(models.Administrator.login == data.login).first()
    if existing:
        raise HTTPException(status_code=400, detail="Login już istnieje")

    new_admin = models.Administrator(
        login=data.login,
        password=password_hash.hash(data.password),
        name=data.name,
        surname=data.surname,
        role_id=data.role_id,
        station_id=data.station_id
    )
    db.add(new_admin)
    db.commit()
    return {"msg": "Użytkownik dodany pomyślnie"}

@router.put("/edit/{admin_id}")
def edit_admin(admin_id: int, data: schemas.AdminUpdate, db: Session = Depends(database.get_db)):
    # Znajdź użytkownika
    admin = db.query(models.Administrator).filter(models.Administrator.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Nie znaleziono użytkownika")

    # Sprawdź unikalność loginu (jeśli zmieniany)
    if data.login != admin.login:
        existing = db.query(models.Administrator).filter(models.Administrator.login == data.login).first()
        if existing:
            raise HTTPException(status_code=400, detail="Login już istnieje")

    # Jeśli podano hasło, sprawdź czy się zgadza z powtórzeniem
    if data.password or data.password_repeat:
        if data.password != data.password_repeat:
            raise HTTPException(status_code=400, detail="Hasła nie są identyczne")
        # Hasło (na razie bez haszowania, jak chciałeś)
        admin.password = password_hash.hash(data.password)

    # Aktualizacja pozostałych pól
    admin.login = data.login
    admin.name = data.name
    admin.surname = data.surname
    admin.role_id = data.role_id
    admin.station_id = data.station_id

    db.commit()
    db.refresh(admin)
    return {"msg": "Użytkownik zaktualizowany pomyślnie", "id": admin.id}

@router.get("/roles")
def get_roles(db: Session = Depends(database.get_db)):
    roles = db.query(models.Role).all()
    return [{"id": r.id, "name": r.name} for r in roles]

@router.get("/stations")
def get_stations(db: Session = Depends(database.get_db)):
    stations = db.query(models.Station).order_by(models.Station.name).all()
    return [{"id": s.id, "name": s.name} for s in stations]

@router.get("/admins")
def get_admins(db: Session = Depends(database.get_db)):
    admins = db.query(models.Administrator).all()
    result = []
    for admin in admins:
        role = db.query(models.Role).filter(models.Role.id == admin.role_id).first()
        station = db.query(models.Station).filter(models.Station.id == admin.station_id).first()
        result.append({
            "id": admin.id,
            "login": admin.login,
            "name": admin.name,
            "surname": admin.surname,
            "role": role.name if role else None,
            "station": station.name if station else None
        })
    return result

@router.get("/admin/{admin_id}")
def get_admin(admin_id: int, db: Session = Depends(database.get_db)):
    admin = db.query(models.Administrator).join(models.Station).filter(models.Administrator.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Administrator nie znaleziony")
    return {
        "id": admin.id,
        "login": admin.login,
        "name": admin.name,
        "surname": admin.surname,
        "role_id": admin.role_id,
        "station_id": admin.station_id,
        "station": admin.station.name if admin.station else None
    }

@router.delete("/delete/{admin_id}")
def delete_admin(admin_id: int, db: Session = Depends(database.get_db)):
    admin = db.query(models.Administrator).filter(models.Administrator.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Administrator nie znaleziony")

    db.delete(admin)
    db.commit()
    return {"msg": "Administrator usunięty pomyślnie"}