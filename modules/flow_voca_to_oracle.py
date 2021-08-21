import modules.database as db

oracleDB = db.oracleDB

class voca_to_oracle :
    import pandas as pd
    import cx_Oracle as ora
    
    def __init__ (self) :
        self.db = oracleDB # 각자의 윈도우 IP로 수정할 것
        self.conn = self.ora.connect(self.db)
        self.cursor = self.conn.cursor() 
        self.into_db()
        
    def get_info(self) : 
        header = [ 'v_num' ,'v_topic', 'v_voca', 'v_info' ]
        df = self.pd.read_excel('dataset/20210203_시사경제용어사전.xlsx' , names=header)
        return df
    
    def into_db(self) : 
        df = self.get_info()
        columns = ','.join(df.columns)  
        values =','.join([':{:d}'.format(i+1) for i in range(len(df.columns))])  
        sql = 'INSERT INTO voca({columns:}) VALUES ({values:})'
        self.cursor.executemany(sql.format(columns=columns, values=values), df.values.tolist())
        
        self.conn.commit()
        self.conn.close()
        print ('DB 에 입력완료')

voca_to_oracle().into_db()