from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(p): return pwd.hash(p)
def verify_password(p, h): return pwd.verify(p, h)
def token_for(user_id):
    return jwt.encode({"sub": str(user_id), "exp": datetime.now(timezone.utc)+timedelta(days=7)}, settings.secret_key, algorithm="HS256")
def current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token: raise HTTPException(401, "Login required")
    try: uid = int(jwt.decode(token, settings.secret_key, algorithms=["HS256"])["sub"])
    except (JWTError, ValueError, KeyError): raise HTTPException(401, "Invalid session")
    user = db.get(User, uid)
    if not user: raise HTTPException(401, "User not found")
    return user

