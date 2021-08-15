from django.db import models
import cx_Oracle as ora

# Create your models here.

def getConn():
    conn = ora.connect("flow79/kosmo7979@192.168.0.6/xe")
    cursor = conn.cursor()
    print("연결성공")
    return conn,cursor
def closeConn(conn,cursor):
    cursor.close()
    conn.close()
    print("연결종료")

def getLikeStock(m_id):
    conn, cursor = getConn()
    try:
        cursor.execute(f"select sl.slike_code, c.c_name from stock_like sl, company c where sl.slike_code = c.c_code and sl.m_id='{m_id}'")
        likeList=cursor.fetchall()
        print(likeList[0][0])
    except Exception as e:
        print(e)
    finally:
        closeConn(conn, cursor)
    return likeList