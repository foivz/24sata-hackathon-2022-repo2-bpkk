from pydoc import describe
from typing import Optional
from unicodedata import category
from xml.dom import InvalidAccessErr
from fastapi import HTTPException, Request, APIRouter, Header, Body, UploadFile
from pydantic import BaseModel
from sklearn.metrics import r2_score

from modules.db import cursor, cnx
from modules.rgx import checkToken, InvalidTokenException
import modules.tesseract as tesseract

import cv2 as cv
import numpy as np

import datetime

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

cardRouter = APIRouter(prefix="")

class newCard(BaseModel):
    cvv:    str
    number:  str
    valid:    str

@cardRouter.post("/addCard/")
async def newReceipt(post: newCard, request: Request, x_token: str = Header(None, convert_underscores=True)):
    token = x_token
    cvv = post.cvv
    number = post.number
    valid = post.valid

    if not checkToken(token):
        raise InvalidTokenException

    cursor.execute("SELECT id FROM users WHERE token = %s", (token,))
    userID = cursor.fetchone()
    print(userID)
    userID = userID[0]

    cursor.execute("INSERT INTO cards (cvv, number, valid, uid) VALUES (%s, %s, %s, %s)",
                   (cvv, number, valid, userID))
    cnx.commit()

    cursor.execute(
        "SELECT id FROM cards WHERE uid = %s ORDER BY id DESC LIMIT 1", (userID,))
    card = cursor.fetchone()

    return {"detail": "Card added", "id": card[0]}


def parser(card):
    r = dict(zip(["id", "uid", "cvv", "number", "valid"], card))
    return r

@cardRouter.post("/getCard/")
async def newReceipt(request: Request, x_token: str = Header(None, convert_underscores=True)):
    token = x_token

    if not checkToken(token):
        raise InvalidTokenException

    cursor.execute("SELECT id FROM users WHERE token = %s", (token,))
    userID = cursor.fetchone()
    print(userID)
    userID = userID[0]

    cursor.execute(
        "SELECT * FROM cards WHERE uid = %s", (userID,))
    cards = cursor.fetchall()

    return (parser(c) for c in cards)