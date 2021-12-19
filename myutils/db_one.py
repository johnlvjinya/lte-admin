
import pymysql

class MysqlOneDatabase(object):

    def __init__(self, host, port, user, password, db):
        self.conn = pymysql.connect(
            host=host,
            port=port,
            user= user,
            password=password,
            db=db,
            autocommit=True
            )
        self.cur = self.conn.cursor()

    def conn_ping(self):
        self.conn.ping(reconnect=True)

    def sql_select_one(self, sql):
        self.conn.ping(reconnect=True)
        self.cur.execute(sql)
        res = self.cur.fetchone()
        return res

    def sql_select_all(self, sql):
        self.conn.ping(reconnect=True)
        self.cur.execute(sql)
        res = self.cur.fetchall()
        res = list(res)
        return res
   
    def sql_insert_excutemany(self, sql, values):
        self.conn.ping(reconnect=True)
        self.cur.executemany(sql, values)
        self.conn.commit()

    def sql_excute(self, sql):
        self.conn.ping(reconnect=True)
        self.cur.execute(sql)
        self.conn.commit()

    def sql_excute_no_commit(self, sql):
        self.conn.ping(reconnect=True)
        self.cur.execute(sql)

    def sql_excute_values(self, sql, values):
        self.conn.ping(reconnect=True)
        self.cur.execute(sql, values)
        self.conn.commit()

if __name__=='__main__':
    MOD = MysqlOneDatabase(
        host='127.0.0.1', 
        port=int('3306'), 
        user='root', 
        password='123456', 
        db='dw_cy_scheduling')

    sql = '''
    SELECT * FROM scheduling_projects WHERE prj_name='curd2';
    '''
    res = MOD.sql_select_one(sql)
    print(res)






