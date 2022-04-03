from fastapi import FastAPI

from modules.profile import profileRouter
from modules.receipts import postRouter
from modules.cards import cardRouter
from modules.db import checkCnx, cursor, cnx


from datetime import datetime

import __main__
import requests
app = FastAPI(title="App Backend")
# za production: app = FastAPI(title = "App Backend", openapi_url = None) disablea docs i list endpointova

app.include_router(profileRouter)
app.include_router(postRouter)
app.include_router(cardRouter)