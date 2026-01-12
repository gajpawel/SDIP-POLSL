from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database
from pwdlib import PasswordHash

router = APIRouter()
password_hash = PasswordHash.recommended()

@router.post("/login")
def login(data: schemas.LoginData, db: Session = Depends(database.get_db)):
    user = db.query(models.Administrator).filter(models.Administrator.login == data.login).first()
    if not user:
        raise HTTPException(status_code=400, detail="Niepoprawny login lub hasło")
    
    if not password_hash.verify(data.password, user.password):
        raise HTTPException(status_code=400, detail="Niepoprawny login lub hasło")

    return {"msg": "Zalogowano", "role_id": user.role_id, "admin_id": user.id}