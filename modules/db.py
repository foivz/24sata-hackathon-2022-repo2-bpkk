import mysql.connector

cnx = mysql.connector.connect(
    user="root", password="AdminPass123", host="localhost", database="sys")
cursor = cnx.cursor()


def checkCnx():
    cnx.ping(reconnect=True, attempts=3)