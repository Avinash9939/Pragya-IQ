import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bcrypt
orig_hashpw = bcrypt.hashpw
def patched_hashpw(password, salt):
    if len(password) > 72:
        password = password[:72]
    return orig_hashpw(password, salt)
bcrypt.hashpw = patched_hashpw

from sqlalchemy import create_engine, text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def update_user():
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/bi_platform")
    hashed = pwd_context.hash("password123")
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id FROM users WHERE email='avinash1@gmail.com'")).fetchone()
        if res:
            conn.execute(text("UPDATE users SET hashed_password = :hp WHERE id = :uid"), {"hp": hashed, "uid": res[0]})
            print("Updated avinash1@gmail.com password to password123")
        conn.commit()

if __name__ == '__main__':
    update_user()
