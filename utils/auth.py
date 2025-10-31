from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import os, dotenv

# configuration
dotenv.load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

def create_access_token(data : dict):
    to_encode = data.copy() # copy so we don't modify the origina dictionary
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp" : expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token : str):
    try:
        payload=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Could not validate credentials"
        )
    


# -----------------------------------------------------------------------------------------
# JWT DEPENDENCIES ------------------------------------------------------------------------

security = HTTPBearer() # <- tells the app to look for Authorization: bearer <token> header

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """
    Extracts and verifies the JWT token from the Authorization header.
    Returns the user_id if valid.
    Raises 401 if invalid.
    """
    token = credentials.credentials # Extract the actual token string
    payload = verify_access_token(token) # Verify it (raises 401 if invalid)
    user_id = payload.get("user_id") # grab the user id

    # in case someone creates a jwt with no user id in it (avoiding bugs)
    if user_id is None: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return user_id

# USAGE - PUT THIS BEFORE PROTECTED ROUTES
# user_id: int = Depends(get_current_user_id)