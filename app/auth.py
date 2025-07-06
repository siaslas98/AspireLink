import bcrypt
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Reads `user_id` from an HTTP-only cookie, fetches the User from the DB,
    and raises 401 if missing/invalid.
    """
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).get(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user
