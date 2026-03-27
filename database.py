import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="archu",
    database="furspeak"
)

cursor = db.cursor(dictionary=True)