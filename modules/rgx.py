import re
import random
import string
from modules.db import cursor, cnx
from fastapi import HTTPException

InvalidTokenException = HTTPException(status_code=401, detail="Invalid token")

emailRegex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
usernameRegex = r"\w{0,45}"  # Samo a-z, A-Z, 0-9 i underscore
tokenRegex = r"\w{64}"  # 64 charactera samo slova i brojeva
fullNameRegex = r"[a-zA-Z\ čćšđžČĆŠĐŽ\.]{1,45}"
passwRegex = r"(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[\W_])\S{8,64}"

def generateRandom(length):
    """
    Generira pseudorandom token koji se koristi za email verification, user authentication i imena fotografija storeanih na serveru
    """
    choices = string.ascii_letters + string.digits
    return "".join(random.choice(choices) for _ in range(length))


def lenCheck(text: str, len: int, allowNewlines: bool = True):
    """
    regex koji matcha bilo koji ASCII character, hrvatske znakove i tabove/newlineove do određene duljine
    """
    if allowNewlines:
        reg = r"[ -~ćĆčČšŠđĐžŽ„”€\n\t\r]{0," + str(len) + r"}"
    else:
        reg = r"[ -~ćĆčČšŠđĐžŽ„”€]{0," + str(len) + r"}"
    return re.fullmatch(reg, text)


def checkToken(token: str):
    """
    Funkcija za provjeru valjanosti tokena
    """
    if not re.fullmatch(tokenRegex, token):
        return False
    cursor.execute("SELECT id FROM Users WHERE token = %s", (token,))

    if cursor.fetchone() is not None:
        return True
    else:
        return False