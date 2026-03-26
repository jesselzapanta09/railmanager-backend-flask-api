# app/utils/db.py
from app.extensions import mysql
import MySQLdb.cursors

def get_cursor():
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)