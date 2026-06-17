from datetime import datetime, timedelta
from jose import JWTError
from jose import jwt
from passlib.context import CryptContext

SECRET_KEY = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(
   schemes=["argon2"],
   deprecated="auto"
)


def hash_password(password: str):
   return pwd_context.hash(password)


def verify_password(
   plain_password,
   hashed_password
):
   return pwd_context.verify(
      plain_password,
      hashed_password
   )


def create_access_token(data: dict):
   to_encode = data.copy()

   expire = datetime.utcnow() + timedelta(
      minutes=ACCESS_TOKEN_EXPIRE_MINUTES
   )

   to_encode.update({
      "exp": expire
   })

   return jwt.encode(
      to_encode,
      SECRET_KEY,
      algorithm=ALGORITHM
   )
def decode_access_token(token: str):
   try:
      payload = jwt.decode(
         token,
         SECRET_KEY,
         algorithms=[ALGORITHM]
      )

      return payload

   except JWTError:
      return None