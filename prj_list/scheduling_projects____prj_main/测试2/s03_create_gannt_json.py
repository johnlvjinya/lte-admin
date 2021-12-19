
import time
import pandas as pd

import json
from datetime import datetime


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)

def save_dict_to_json(data_input, file_path='parameter.json'):
        with open(file_path,'w',encoding='utf-8') as f2:
            json.dump(data_input, f2,ensure_ascii=False, cls=NpEncoder)


class GetGanntJson():
    def __init__(self):


        import sys
        import command as tc
        cmd_arg = tc.Argument(sys.argv)
        prj_name = cmd_arg.get_value("prj_name")
        self.input_excel = 'prj_list/scheduling_projects____prj_main/%s/output/智能排产结果.xlsx'%prj_name
        self.save_path = 'prj_list/scheduling_projects____prj_main/%s/d_json/智能排产结果.json'%prj_name
        self.save_path_order = 'prj_list/scheduling_projects____prj_main/%s/d_json/智能排产结果_order.json'%prj_name
        self.save_path_delivery = 'prj_list/scheduling_projects____prj_main/%s/d_json/delivery_compare.json'%prj_name


        ######################################本地测试
        # prj_name = '创元权限测试'
        # self.input_excel = 'output/智能排产结果.xlsx'%prj_name
        # self.save_path = 'd_json/智能排产结果.json'
        # self.save_path_order = 'd_json/智能排产结果_order.json'
        # self.save_path_delivery = 'd_json/delivery_compare.json'


        self.df = pd.read_excel(self.input_excel, sheet_name='工单计划', keep_default_na=False)
        self.df = self.df.sort_values(['产线']).reset_index(drop=True)
        self.w_line_list = self.df['产线'].unique().tolist()
        
        self.df = self.df.sort_values(['订单交期']).reset_index(drop=True)
        self.order_list = self.df['订单号'].unique().tolist()
        self.mydict = {}

        self.my_order_dict = {}
        self.delivery_dict = {}

    def cal_parkingApron(self):
        self.mydict['parkingApron'] = {}
        self.mydict['parkingApron']['dimensions'] = ["Name","Type","Near Bridge"]

        data_list = []
        for w_line_i in self.w_line_list:
            df_i = self.df[self.df['产线']==w_line_i].reset_index(drop=True)
            data_i = [df_i['产线'][0], df_i['区域'][0], True]
            data_list.append(data_i)
        self.mydict['parkingApron']['data'] = data_list
        # print(data_list)

        #################### order的字典
        self.my_order_dict['parkingApron'] = {}
        self.my_order_dict['parkingApron']['dimensions'] = ["Name","Type","Near Bridge"]

        data_list = []
        for order_i in self.order_list:
            df_i = self.df[self.df['订单号']==order_i].reset_index(drop=True)
            data_i = [str(df_i['订单号'][0]), str(df_i['订单交期'][0]), True]
            data_list.append(data_i)
        self.my_order_dict['parkingApron']['data'] = data_list
        # print(data_list)
        pass

    def cal_flight(self):
        self.mydict['flight'] = {}
        self.mydict['flight']['dimensions'] = [
            "车间名称",
            "开工时间",
            "完工时间",
            "工单编号", # "Flight Number"
            "VIP",

            "订单号",
            "子料号",
            "订单数量",
            "分配人员",
            "分配班组长"
            ]

        data_list = []
        for i in range(self.df.shape[0]):
            index_i = self.w_line_list.index(self.df['产线'][i])  # +1
            
            tss1 = self.df['计划开始时间'][i]+':00'
            timeArray = time.strptime(tss1, "%Y/%m/%d %H:%M:%S")
            timeStamp = int(time.mktime(timeArray))*1000
            t_start_i = timeStamp
            # print(timeArray, timeStamp)

            tss1 = self.df['计划结束时间'][i]+':00'
            timeArray = time.strptime(tss1, "%Y/%m/%d %H:%M:%S")
            timeStamp = int(time.mktime(timeArray))*1000
            t_end_i = timeStamp

            flight_number = str(self.df['工单编号'][i])

            order_d1 = time.strptime(str(self.df['订单交期'][i])+' 00:00:00', "%Y/%m/%d %H:%M:%S")
            order_t1 = int(time.mktime(order_d1))*1000
            # print(t_end_i, order_t1)
            if t_end_i>order_t1:  # 延期  
                v5 = False
            else:
                v5 = True

            v6 = str(self.df['订单号'][i])
            v7 = str(self.df['子料号'][i])
            v8 = str(int(self.df['订单数量'][i]))
            v9 = str(self.df['分配人员'][i])
            v10 = str(self.df['分配班组长'][i])

            data_i = [index_i, t_start_i, t_end_i, flight_number, v5, v6, v7, v8, v9, v10]
            data_list.append(data_i)
            # print(data_i)
        self.mydict['flight']['data'] = data_list

    def cal_flight2(self):
        self.my_order_dict['flight'] = {}
        self.my_order_dict['flight']['dimensions'] = [
            "订单号",
            "开工时间",
            "完工时间",
            "工单编号", # "Flight Number"
            "VIP",

            "产线",
            "订单交期",
            "订单数量",
            "分配人员",
            "分配班组长"
            ]

        data_list = []
        
        for i in range(self.df.shape[0]):
            index_i = self.order_list.index(self.df['订单号'][i])  # +1
            
            tss1 = self.df['计划开始时间'][i]+':00'
            timeArray = time.strptime(tss1, "%Y/%m/%d %H:%M:%S")
            timeStamp = int(time.mktime(timeArray))*1000
            t_start_i = timeStamp
            # print(timeArray, timeStamp)

            tss1 = self.df['计划结束时间'][i]+':00'
            timeArray = time.strptime(tss1, "%Y/%m/%d %H:%M:%S")
            timeStamp = int(time.mktime(timeArray))*1000
            t_end_i = timeStamp

            flight_number = str(self.df['工单编号'][i])

            order_d1 = time.strptime(str(self.df['订单交期'][i])+' 00:00:00', "%Y/%m/%d %H:%M:%S")
            order_t1 = int(time.mktime(order_d1))*1000
            # print(t_end_i, order_t1)
            if t_end_i>order_t1:  # 延期  
                v5 = False
            else:
                v5 = True

            v6 = str(self.df['产线'][i])
            v7 = str(self.df['订单交期'][i])
            v8 = str(int(self.df['订单数量'][i]))
            v9 = str(self.df['分配人员'][i])
            v10 = str(self.df['分配班组长'][i])

            data_i = [index_i, t_start_i, t_end_i, flight_number, v5, v6, v7, v8, v9, v10]
            data_list.append(data_i)
        # for ddi in data_i:
        #     print(ddi, type(ddi))
            # print(data_i)
        self.my_order_dict['flight']['data'] = data_list
        
    def cal_delivery_date(self):
        df = self.df.sort_values('订单交期').reset_index(drop=True)
        # t1 = self.df['订单交期'][0]
        # t2 = self.df['计划结束时间'][0]

        self.delivery_dict['name_list'] = df['工单编号'].tolist()
        date_list_c1 = []
        date_list_c2 = []
        for i,row_i in df.iterrows():
            t1 = time.strptime(row_i['订单交期'], "%Y/%m/%d")
            t2 = time.strptime(row_i['计划结束时间'], "%Y/%m/%d %H:%M")
            # print(t1,t2, type(t1), type(t2))
            ttt1 = int(time.mktime(t1)/3600)
            ttt2 = int(time.mktime(t2)/3600)
            date_list_c1.append(ttt1)
            date_list_c2.append(ttt2)

        df['order_deliver'] = date_list_c1
        df['order_finish'] = date_list_c2

        df['order_deliver'] = df['order_deliver']-min(date_list_c1)
        df['order_finish'] = df['order_finish']-min(date_list_c1)

        self.delivery_dict['data_list_c1'] = df['order_deliver'].tolist()
        self.delivery_dict['data_list_c2'] = df['order_finish'].tolist()



        pass

    def save_json(self):
        # print(self.save_path)
        save_dict_to_json(self.mydict, self.save_path)
        save_dict_to_json(self.my_order_dict, self.save_path_order)
        save_dict_to_json(self.delivery_dict, self.save_path_delivery)

        pass

    def run(self):
        self.cal_parkingApron()
        self.cal_flight()
        self.cal_flight2()
        self.cal_delivery_date()
        self.save_json()
        pass



if __name__=='__main__':
    # save_path='static/wan_right_result_01.json'
    # input_excel_path='data/智能排产结果.xlsx'

    # input_excel="原始LV"
    a = GetGanntJson()
    a.run()


