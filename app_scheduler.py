

import datetime
import pandas as pd

import myutils.dict_json_saver as mdjs
from colour import Color
import cx_Oracle as cx

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

con = cx.connect('fmdsreader/Fmds@2cSz3#@10.1.254.145:10021/topprd')     # 连接数据库
cur = con.cursor()                                                    # 获得游标

def quantile_5_95_df_col(df, col):      # 将某一列的极大极小值去除
    quantile_5 = df[col].quantile(0.025)
    quantile_95 = df[col].quantile(0.975)
    df_clear = df.drop(df[(df[col]<quantile_5) | (df[col]>quantile_95)].index).reset_index(drop=True) #删除x小于0.01或大于10的行
    return df_clear


class TastkList():
    def __init__(self):
        pass

    def unique_sfaacrtid_list(self):  # 资料录入者名单，以及曾经录入的工单数
        print('查询订单概要时间：', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        sql = '''
        SELECT count(distinct(xmdcdocno)),count(distinct(xmdcsite)),count(distinct(xmdc001)),count(distinct(xmdcud003)) from xmdc_t
        '''
        cur.execute(sql)
        rows = cur.fetchone()
        cn_list = '订单数,据点数,SKU数,结案人'.split(',')
        en_list = 'order_nums,stand_points,sku_nums,deal_person'.split(',')
        res = dict(zip(en_list, rows))

        mdjs.save_dict_to_json(res, file_path='mytemp/t100-订单.json')
        
    def tb_col_classify_sort(self,tb_name,col_name,sort_v=None,current_year=None):      # 营运据点
        if not sort_v:
            sort_v = 5

        sql = '''
        SELECT %s,count(*) as num from %s
        group by %s order by num
        '''%(col_name, tb_name, col_name)

        cur.execute(sql)
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns='name,v'.split(',')).fillna(0)
        df = df[df['v']>sort_v].reset_index(drop=True)

        mydict = {}

        mydict['k_list'] = df['name'].tolist()
        mydict['v_list'] = df['v'].tolist()
        # print(mydict['v_list'])

        red = Color("red")
        colors = list(red.range_to(Color("lightgreen"),df.shape[0]))  
        mydict['c_list'] = []
        for i in range(df.shape[0]): 
            mydict['c_list'].append(str(colors[i]))

        mdjs.save_dict_to_json(mydict, file_path='mytemp/%s-%s.json'%(tb_name, col_name))

    def get_sale_info(self):
        print('查询订单开始1：', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        sql = '''
        SELECT xmdc001,xmdc007,xmdc012,xmdc015 from xmdc_t  t where t.xmdc012 
        between to_date('2021-01-01 00:00:00','yyyy-mm-dd hh24:mi:ss') 
        and to_date('2021-12-30 23:59:59','yyyy-mm-dd hh24:mi:ss')
        '''
        cols_list = '料件编号,销售数量,约定交货日,单价'.split(',')

        cur.execute(sql)
        rows = cur.fetchall()        
        df = pd.DataFrame(rows, columns=cols_list).fillna(0)
        # df.to_csv('mytemp/res.txt',sep='\t', index=False)
        # df = pd.read_csv('mytemp/res.txt',sep='\t')
        df['总价'] = df['销售数量']*df['单价']
        df = df[df['总价']>0].reset_index(drop=True)
        df = quantile_5_95_df_col(df, '总价')
        print(df)

        hist, bin_edges = np.histogram(df['总价'].values, bins=100)
        mydict = {}
        mydict['k_list'] = [str(i) for i in bin_edges]
        mydict['v_list'] = [float(i) for i in hist]
        mydict['c_list'] = ['blue' for i in range(len(hist))]
        mdjs.save_dict_to_json(mydict, file_path='mytemp/订单-总价分布.json')

        hist, bin_edges = np.histogram(df['销售数量'].values, bins=100)
        mydict = {}
        mydict['k_list'] = [str(i) for i in bin_edges]
        mydict['v_list'] = [float(i) for i in hist]
        mydict['c_list'] = ['green' for i in range(len(hist))]
        mdjs.save_dict_to_json(mydict, file_path='mytemp/订单-销售数量分布.json')

        hist, bin_edges = np.histogram(df['单价'].values, bins=100)
        mydict = {}
        mydict['k_list'] = [str(i) for i in bin_edges]
        mydict['v_list'] = [float(i) for i in hist]
        mydict['c_list'] = ['limegreen' for i in range(len(hist))]
        mdjs.save_dict_to_json(mydict, file_path='mytemp/订单-单价分布.json')

        print('查询订单结束1：', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


def run():
    TLLT = TastkList()
    # TLLT.unique_sfaacrtid_list()
    # TLLT.tb_col_classify_sort(tb_name='xmdc_t',col_name='xmdcsite') # 据点柱状图
    # TLLT.tb_col_classify_sort(tb_name='xmda_t',col_name='xmdastus') # 订单单头-状态码
    # TLLT.tb_col_classify_sort(tb_name='xmda_t',col_name='xmda004',sort_v=100) # 订单单头-客户编号
    TLLT.get_sale_info()
  


if __name__=="__main__":
    run()



