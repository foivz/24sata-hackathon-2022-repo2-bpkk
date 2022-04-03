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

postRouter = APIRouter(prefix="")

class newReceipt(BaseModel):
    category:    str
    description:  str
    price:    int
    items: list
    time: Optional[str]

@postRouter.post("/add/")
async def newReceipt(post: newReceipt, request: Request, x_token: str = Header(None, convert_underscores=True)):
    token = x_token
    category = post.category
    description = post.description
    price = post.price
    items = map(str, post.items)

    if not checkToken(token):
        raise InvalidTokenException

    _items = ""
    for item in items:
        _items += f"{addGetProduct(item)} "

    cursor.execute("SELECT id FROM users WHERE token = %s", (token,))
    userID = cursor.fetchone()[0]
    if post.time == None:
        date = datetime.datetime.now()
    else:
        date = datetime.datetime.strptime(post.time, r"%Y-%m-%dT%H:%M:%S")

    cursor.execute("INSERT INTO receipt (uid, category, description, price, date, items) VALUES (%s, %s, %s, %s, %s, %s)",
                   (userID, category, description, price, date, _items))
    cnx.commit()

    cursor.execute(
        "SELECT id FROM receipt WHERE uid = %s ORDER BY id DESC LIMIT 1", (userID,))
    post = cursor.fetchone()

    return {"detail": "Receipt uploaded", "id": post[0]}

def parser(receipt):
    r = dict(zip(["id", "uid", "category", "description", "price", "date"], receipt))
    items = receipt[-1]
    items = items[:-1] if items[-1] == " " else items
    r["items"] = list(map(int, items.split(" ")))
    return r

class getReceipts(BaseModel):
    fid: Optional[int]

@postRouter.post("/getReceipts/")
async def getReceipts(post: getReceipts, request: Request, x_token: str = Header(None, convert_underscores=True)):
    token = x_token
    print(token)
    if not checkToken(token):
        return InvalidTokenException    
    
    if post.fid != None:
        cursor.execute("SELECT id FROM users WHERE familyid = %s;", (post.fid,))
        ret = cursor.fetchone()
        if ret == None: return HTTPException(status_code=402, detail="Invalid Family ID")

        id = ret[0]
    else:
        cursor.execute("SELECT id FROM users WHERE token = %s;", (token,))
        ret = cursor.fetchone()
        if ret == None: return InvalidTokenException

        id = ret[0]

    cursor.execute("SELECT * FROM receipt WHERE uid = %s", (id,))
    receipts = cursor.fetchall()

    return (parser(r) for r in receipts)

@postRouter.post("/getProducts/")
async def getReceipts(request: Request, x_token: str = Header(None, convert_underscores=True)):
    token = x_token
    if not checkToken(token):
        return InvalidTokenException    

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    
    return [{int(p[0]):p[1]} for p in products]

def addGetProduct(name):
    cursor.execute("SELECT id FROM products WHERE name = %s;", (name,))
    ret = cursor.fetchone()
    
    if ret == None:
        cursor.execute("INSERT INTO products (name) VALUES (%s)",
                    (name,))
        cnx.commit()
        cursor.execute("SELECT id FROM products WHERE name = %s;", (name,))
        ret = cursor.fetchone()

    return ret[0]


class getDataClass(BaseModel):
    category: str
    description: str

@postRouter.post("/getData/")
async def getData(file: UploadFile, request: Request,  x_token: str = Header(None, convert_underscores=True), category: str = Header(None, convert_underscores=True), description: str = Header(None, convert_underscores=True), time: str = Header(None, convert_underscores=True)):
    token = x_token

    print(token)

    contents = await file.read()
    nparr = np.fromstring(contents, np.uint8)
    img = cv.imdecode(nparr, cv.IMREAD_COLOR)
    ukupno, items = tesseract.processTheImage(img)
    _items = ""
    for item in items:
        _items += f"{addGetProduct(item)} "

    cursor.execute("SELECT id FROM users WHERE token = %s", (token,))
    userID = cursor.fetchone()
    print(userID)
    userID = userID[0]


    if time == None:
        date = datetime.datetime.now()
    else:
        date = datetime.datetime.strptime(time, r"%Y-%m-%dT%H:%M:%S")


    cursor.execute("INSERT INTO receipt (uid, category, description, price, date, items) VALUES (%s, %s, %s, %s, %s, %s)",
                   (userID, category, description, ukupno, date, _items[:-1]))
    cnx.commit()

    cursor.execute(
        "SELECT id FROM receipt WHERE uid = %s ORDER BY id DESC LIMIT 1", (userID,))
    post = cursor.fetchone()

    return {"detail": "Receipt uploaded", "id": post[0]}


@postRouter.post("/getGraph/")
async def getGraph(request: Request,  x_token: str = Header(None, convert_underscores=True)):
    token = x_token
    if not checkToken(token):
        return InvalidTokenException 
    cursor.execute("SELECT id FROM users WHERE token = %s", (token,))
    userID = cursor.fetchone()
    print(userID)
    userID = userID[0]

    cursor.execute(
        "SELECT price, date FROM receipt WHERE uid = %s ORDER BY date ASC", (userID,))
    receipts = cursor.fetchall()

    datay = []

    for i in receipts:
        datay.append(i[0])

    return datay

@postRouter.post("/predict/")
async def predict(request: Request,  x_token: str = Header(None, convert_underscores=True)):
    token = x_token
    if not checkToken(token):
        return InvalidTokenException   

    cursor.execute("SELECT id FROM users WHERE token = %s", (token,))
    userID = cursor.fetchone()
    print(userID)
    userID = userID[0]

    cursor.execute(
        "SELECT price, date FROM receipt WHERE uid = %s ORDER BY date ASC", (userID,))
    receipts = cursor.fetchall()

    datay = []
    datax = []

    for i in receipts:
        datay.append(i[0])
        datax.append(i[1])

    dif = datax[0]
    data2x = []
    for ele in datax:
        data2x.append((ele-dif).days)
    
    x = np.array(data2x).reshape((-1, 1))
    y = np.array(datay)

    model = LinearRegression().fit(x, y)

    a = model.coef_
    s = model.intercept_

    modelOut = datay[-7:]
    for n in range(1, 8):
        vri = ((datax[-1]-dif).days+n)*a+s
        modelOut.append(round(vri[0]))

    return modelOut
