from fastapi import APIRouter, HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from datetime import datetime, timedelta
import warnings

# Try to import PyJWT (jwt) or python-jose as a fallback. If neither is available,
# leave `jwt` as None and warn; token creation/verification will raise helpful errors.
_JWT_IMPL = None
try:
    import jwt  # PyJWT
    _JWT_IMPL = 'pyjwt'
except Exception:
    try:
        from jose import jwt  # python-jose
        _JWT_IMPL = 'jose'
    except Exception:
        jwt = None
        _JWT_IMPL = None
        warnings.warn("No JWT library found. Install PyJWT (`pip install PyJWT`) or python-jose (`pip install python-jose`) to enable token creation/verification.")

from database import Database

# -----------------------------
# CONFIG
# -----------------------------
SECRET_KEY = "your-secret-key"  # change this!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter()
db = Database()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# -----------------------------
# PASSWORD HELPERS
# -----------------------------
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)


# -----------------------------
# JWT HELPERS
# -----------------------------
def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    if jwt is None:
        raise HTTPException(status_code=500, detail="JWT library is not installed. Install PyJWT (`pip install PyJWT`) or python-jose (`pip install python-jose`).")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    if jwt is None:
        raise HTTPException(status_code=500, detail="JWT library is not installed. Install PyJWT (`pip install PyJWT`) or python-jose (`pip install python-jose`).")
    try:
        # Both PyJWT and python-jose support this call signature
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception as e:
        emsg = str(e).lower()
        if 'expired' in emsg:
            raise HTTPException(status_code=401, detail="Token expired")
        raise HTTPException(status_code=401, detail="Invalid token")


# -----------------------------
# AUTH ENDPOINTS
# -----------------------------
from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

@router.post("/register")
def register(payload: RegisterRequest):
    hashed = hash_password(payload.password)

    # Save user (store password hash in users.password_hash)
    try:
        user_id = db.add_user(username=payload.username, email=payload.email, password_hash=hashed)
    except Exception:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    return {"message": "User registered", "user_id": user_id}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password

    # Get user with password hash
    user = db.get_user_by_username(username)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    user_id = user[0]
    try:
        stored_hash = user['password_hash']
    except Exception:
        # fallback: assume the last column is password_hash in older schemas
        try:
            stored_hash = user[-1]
        except Exception:
            stored_hash = None

    if not stored_hash or not verify_password(password, stored_hash):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # Create token
    token = create_access_token({"sub": username, "user_id": user_id})

    return {"access_token": token, "token_type": "bearer"}


# -----------------------------
# PROTECTED ROUTE EXAMPLE
# -----------------------------
@router.get("/me")
def get_me(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    return {"user": payload}
