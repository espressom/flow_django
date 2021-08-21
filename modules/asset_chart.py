class asset_chart:
    def category_cash(m_id):
        print(' >>> category_cash 진입 >>>')
        import pandas as pd
        import cx_Oracle as ora
        import plotly.graph_objects as go
        from modules import database as db
        db = db.oracleDB
        conn = ora.connect(db)
        cursor = conn.cursor()
        sql_category = "select c_category, sum(c_price) from cashflow where m_id='" + m_id + "' and c_flow='유출' and to_number(to_char(c_date,'yymmdd')) > to_number(to_char(sysdate,'yymmdd'))-to_number(to_char(sysdate,'dd')) group by c_category"
        cursor.execute(sql_category)
        out_category = cursor.fetchall()
        # 연결닫기
        conn.commit()
        cursor.close()
        conn.close()

        category_name = [out_category[i][0] for i in range(0, len(out_category))]
        category_sum = [out_category[i][1] for i in range(0, len(out_category))]
        df = pd.DataFrame({"카테고리": category_name,
                           "금액": category_sum})
        fig = go.Figure(data=[go.Pie(labels=df['카테고리'], values=df['금액'], textinfo='label+percent',
                                     insidetextorientation='radial'
                                     )])
        fig.update(layout_showlegend=False)
        fig.show()
        return fig
        
    def month_cash(m_id):
        import pandas as pd
        import cx_Oracle as ora
        import numpy as np
        import plotly.express as pt
        from modules import database as db
        db = db.oracleDB
        conn = ora.connect(db)
        cursor = conn.cursor()
        # 유출
        sql_out = "select to_char(c_date,'yymm') x1, sum(c_price) y1 from cashflow where m_id='" + m_id + "' and c_flow='유출' and to_number(to_char(c_date,'yymm')) > to_number(to_char(sysdate,'yymm'))-100 group by to_char(c_date,'yymm') order by x1 asc"
        cursor.execute(sql_out)
        cash_out = cursor.fetchall()
        # 유입
        sql_in = "select to_char(c_date,'yymm') x2, sum(c_price) y2 from cashflow where m_id='" + m_id + "' and c_flow='유입' and to_number(to_char(c_date,'yymm')) > to_number(to_char(sysdate,'yymm'))-100 group by to_char(c_date,'yymm') order by x2 asc"
        cursor.execute(sql_in)
        cash_in = cursor.fetchall()
        # 연결닫기
        conn.commit()
        cursor.close()
        conn.close()
        # 유출
        x1 = [cash_out[i][0] for i in range(0, len(cash_out))]
        y1 = [cash_out[i][1] for i in range(0, len(cash_out))]
        # 유입
        x2 = [cash_in[i][0] for i in range(0, len(cash_in))]
        y2 = [cash_in[i][1] for i in range(0, len(cash_in))]
        # 그래프
        df = pd.DataFrame({"월": x1,"지출": y1,"유입": y2})
        df['월'] = df['월'].str.slice(start=2)
        mon = df['월'].values
        monli = [(mon == '01'), (mon == '02'), (mon == '03'), (mon == '04'), (mon == '05'), (mon == '06'), (mon == '07'),
                 (mon == '08'), (mon == '09'), (mon == '10'), (mon == '11'), (mon == '12')]
        meng = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        res = np.select(monli, meng)
        df['월'] = res
        fig = pt.line(df, x="월", y=["지출", "유입"], width=900, height=500)
        fig.update_layout(
            #title="월별 유입 지출",
            xaxis_title="",
            yaxis_title="",
            yaxis_tickformat=',',
            legend_title="",
            font=dict(
                family="Courier New, monospace",
                size=18,
                color="RebeccaPurple"
            )
        )
        fig.show()
        return fig





