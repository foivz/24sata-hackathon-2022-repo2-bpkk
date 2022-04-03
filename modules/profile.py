from tokenize import Token
import bcrypt

from fastapi import HTTPException, Request, APIRouter, Header
from typing import Optional
from pydantic import BaseModel
import re
import requests
from modules.rgx import *
from modules.db import cursor, cnx


profileRouter = APIRouter()

class userLogin(BaseModel):
    username: str
    passw:    str


@profileRouter.post("/login/")
async def login(user: userLogin, request: Request):
    username = user.username
    passw = user.passw

    BadCredentialsException = HTTPException(
        status_code=400, detail="Wrong username or password")
    if not re.fullmatch(usernameRegex, username):
        raise BadCredentialsException
    if not re.fullmatch(passwRegex, passw):
        raise BadCredentialsException

    cursor.execute("SELECT password FROM Users WHERE username = %s", (username,))

    hash = list(cursor)
    if not len(hash):
        raise BadCredentialsException

    if bcrypt.checkpw(bytes(passw, "utf-8"), bytes(hash[0][0], "utf-8")):

        unique = False
        while not unique:
            token = generateRandom(64)
            unique = not checkToken(token)

        cursor.execute(
            "UPDATE Users SET token = %s WHERE username = %s", (token, username))
        cnx.commit()

        return {"token": token}
    else:
        raise BadCredentialsException


class userRegister(BaseModel):
    username: str
    email:    str
    familyid: int
    passw:    str


@profileRouter.post("/register/")
async def register(user: userRegister, request: Request):
    username = user.username
    email = user.email
    passw = user.passw
    familyid = user.familyid

    # Check if all the things are valid
    if not re.fullmatch(usernameRegex, username):
        raise HTTPException(status_code=400, detail="Username too long or uses invalid characters. Max allowed length is 45 chars, and the allowed characters are a-z, A-Z, 0-9 and _")
    if not re.fullmatch(emailRegex, email):
        raise HTTPException(status_code=400, detail="Invalid email")
    if not re.fullmatch(passwRegex, passw):
        raise HTTPException(status_code=400, detail="Invalid password (>=8 chars, 1 upper, 1 lower, 1 number, 1 special)")

    # Test if username is used
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    if len(list(cursor)):
        raise HTTPException(status_code=400, detail="Username taken")

    # Test if email is used
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    if len(list(cursor)):
        raise HTTPException(status_code=400, detail="Email in use")

    # Generate unique token
    unique = False
    while not unique:
        token = generateRandom(64)
        unique = not checkToken(token)

    # Generate hash
    hashed = bcrypt.hashpw(bytes(passw, "utf-8"), bcrypt.gensalt())

    # Save in the database
    cursor.execute("INSERT INTO users (username, email, familyid, password, token) VALUES (%s, %s, %s, %s, %s)",
                   (username, email, familyid, hashed, token))
    cnx.commit()

    cursor.execute("SELECT id FROM users WHERE token = %s", (token,))

    return {"token": token}


class userInfo(BaseModel):
    username: Optional[str]
    id:       Optional[str]

@profileRouter.post("/logout/")
async def logout(request: Request, x_token: str = Header(None, convert_underscores=True)):
    token = x_token
    if not checkToken(token):
        raise InvalidTokenException

    cursor.execute(
        "UPDATE Users SET token = null WHERE token = %s LIMIT 1", (token,))

    cnx.commit()
    return {"detail": "Success"}


class setFid(BaseModel):
    fid: int

@profileRouter.post("/setfid/")
async def setFid(post: setFid, request: Request, x_token: str = Header(None, convert_underscores=True)):
    token = x_token
    if not checkToken(token):
        raise HTTPException(status_code=401, detail="Token invalid")

    cursor.execute(
        "UPDATE users SET familyid = %s WHERE token = %s LIMIT 1", (post.fid, token,))
    cnx.commit()
    return {"detail": "Success"}


@profileRouter.post("/checkToken/")
async def checkTokenEndpoint(request: Request, x_token: str = Header(None, convert_underscores=True)):
    """
    Endpoint za provjeru valjanosti tokena
    """
    token = x_token
    if checkToken(token):
        return {"detail": "Token valid"}
    else:
        raise HTTPException(status_code=401, detail="Token invalid")