from django.db import models
import cx_Oracle as ora
import modules.database as db

oracleDB = db.oracleDB

# Create your models here.
#---------장우석
#오라클 접속
def getConn():
    conn = ora.connect(oracleDB)
    cursor = conn.cursor()
    print("연결성공")
    return conn,cursor
def closeConn(conn,cursor):
    cursor.close()
    conn.close()
    print("연결종료")


#관리자 로그인
def getAdminNum(info):
    conn, cursor = getConn()
    sql = f"select m_division,m_name from member where m_id='{info[0]}' and m_pwd='{info[1]}'"
    try:
        cursor.execute(sql)
        adminNum=cursor.fetchone()
        # print(adminNum)
    except Exception as e:
        print(e)
    finally:
        closeConn(conn, cursor)
    return adminNum


#요청 종류별 수 가져오기
def getRequestLog():
    conn, cursor = getConn()
    try:
        cursor.execute("select request,count(*) from log group by request order by count(*) desc")
        reqList=cursor.fetchall()
        # print(reqList[0][0])
    except Exception as e:
        print(e)
    finally:
        closeConn(conn, cursor)
    return reqList

#날짜별 요청 수 가져오기
def getDateLog():
    conn, cursor = getConn()
    try:
        cursor.execute("select to_char(log_date,'yy-MM-dd'), count(*) from log group by to_char(log_date,'yy-MM-dd') order by to_char(log_date,'yy-MM-dd') asc")
        dateList=cursor.fetchall()
        # print(dateList[0][0])
    except Exception as e:
        result = 'c'
        print(e)
    finally:
        closeConn(conn, cursor)
    return dateList

# 회원 수
def getMemCount():
    conn, cursor = getConn()
    sql = "select count(*) from member"
    try:
        cursor.execute(sql)
        memCount=cursor.fetchone()
        # print(memCount)
    except Exception as e:
        print(e)
    finally:
        closeConn(conn, cursor)
    return memCount

# 게시물 수
def getBrdCount():
    conn, cursor = getConn()
    sql = "select count(*) from board"
    try:
        cursor.execute(sql)
        brdCount=cursor.fetchone()
        # print(brdCount)
    except Exception as e:
        print(e)
    finally:
        closeConn(conn, cursor)
    return brdCount

# 오늘 등록한 회원 수
def getToMemCount():
    conn, cursor = getConn()
    sql = "select count(*) from member where to_char(m_date,'yy/MM/dd') = to_char(sysdate,'yy/MM/dd')"
    try:
        cursor.execute(sql)
        toMemCount=cursor.fetchone()
        # print(toMemCount)
    except Exception as e:
        print(e)
    finally:
        closeConn(conn, cursor)
    return toMemCount

# 오늘 등록한 게시물 수
def getToBrdCount():
    conn, cursor = getConn()
    sql = "select count(*) from board where to_char(b_regdate,'yy/MM/dd') = to_char(sysdate,'yy/MM/dd')"
    try:
        cursor.execute(sql)
        toBrdCount=cursor.fetchone()
        # print(toBrdCount)
    except Exception as e:
        print(e)
    finally:
        closeConn(conn, cursor)
    return toBrdCount

# 회원 연령대별 분포
def getMemAgesCount():
    conn, cursor = getConn()
    sql = "select substr(to_char(to_number(to_char(sysdate,'yy'))+100 - to_number(substr(m_jumin,1,2))),-2,1), count(*) from member group by substr(to_char(to_number(to_char(sysdate,'yy'))+100 - to_number(substr(m_jumin,1,2))),-2,1)"
    try:
        cursor.execute(sql)
        memAgesCount=cursor.fetchall()
        # print(memAgesCount)
    except Exception as e:
        print(e)
    finally:
        closeConn(conn, cursor)
    return memAgesCount

# 회원 성별 분포
def getMemGenCount():
    conn, cursor = getConn()
    sql = "select SUBSTR(m_jumin,-1),count(*) from member group by SUBSTR(m_jumin,-1)"
    try:
        cursor.execute(sql)
        memGenCount=cursor.fetchall()
        # print(memGenCount)
    except Exception as e:
        print(e)
    finally:
        closeConn(conn, cursor)
    return memGenCount


# 회원 검색
def getMemInfom(m_id):
    conn, cursor = getConn()
    sql = f"select * from member where m_id='{m_id}' and m_division=1"
    try:
        cursor.execute(sql)
        memInform = cursor.fetchone()
        print(memInform)

    except Exception as e:
        print(e)
    finally:
        closeConn(conn, cursor)
    return memInform

#회원 삭제
def delMem(m_num):
    conn, cursor = getConn()
    sql = f"update member set m_division = 9 where m_num = '{m_num}'"
    print(sql)
    try:
        cursor.execute(sql)
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        closeConn(conn, cursor)











