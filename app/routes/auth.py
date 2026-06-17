from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

router = APIRouter()

@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=user.username,
        email=user.email,
        phone=user.phone,
        password_hash=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({
        "user_id": new_user.id,
        "username": new_user.username,
        "role": new_user.role
    })

    return {
        "message": "Signup successful",
        "access_token": token,
        "token_type": "bearer",
        "username": new_user.username,
        "balance": new_user.balance,
        "role": new_user.role
    }

@router.post("/login")
def login(
user: UserLogin,
db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(
        User.username == user.username
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=400,
            detail="Invalid username or password"
        )

    if not verify_password(
        user.password,
        db_user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid username or password"
        )

    token = create_access_token(
        {
            "user_id": db_user.id,
            "username": db_user.username,
            "role": db_user.role
        }
    )

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "username": db_user.username,
        "balance": db_user.balance,
        "role": db_user.role
    }
@router.get("/me")
def get_me(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):

    token = authorization.replace(
        "Bearer ",
        ""
    )

    payload = decode_access_token(
        token
    )

    user = db.query(User).filter(
        User.id == payload["user_id"]
    ).first()

    return {
        "username": user.username,
        "balance": user.balance,
        "role": user.role
    }