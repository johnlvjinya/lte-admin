

import os
import sys
import time
import pymysql
import subprocess
import numpy as np
import pandas as pd

import config
import cplex_data as cdt
import s02_data_transformer as s02
from jinja2 import Environment, FileSystemLoader

# f_handler=open('algorithm_log/p_median.txt', 'w') 
# sys.stdout=f_handler
# sys.path.append("..")
# print('current_time:', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) )


class RunPmedianProject():
    def __init__(self, project_id='p001', clear_output=True):
        try:
            self.db = pymysql.connect(host=config.host, port=int(config.port), user=config.user, passwd=config.password, db=config.db)    # 数据库Ip, 用户，密码，选择数据库
            self.cur = self.db.cursor()   
            self.project_id = project_id     

            ###### 删除结果表
            for tb in config.output_list:
                sql = "DELETE FROM {0} WHERE project_id='{1}';".format(tb, project_id)
                self.cur.execute(sql)
            self.db.commit()

            if os.path.exists('output') is False:  # 结果缓存路径
                os.mkdir('output')

            PPTF = s02.PmedianProjectTransformer(project_id)
            self.basic = PPTF.basic
            self.cost_matrix = PPTF.cost_matrix
            self.rrc = PPTF.rrc
            self.ts = PPTF.ts

            self.clear_output = clear_output
            self.res_dict = PPTF.res_data_json()             # 得到需要的数据
            for key,value in self.res_dict.items():
                print(key, type(value))
        except Exception as e:
            raise Exception(str(e)) 

    def calculation(self):
        res_dict = self.res_dict

        basic_params = res_dict.get('basic_params')  # 'ts_numbers,rrc_numbers,min_p,trans_cost,total_msw,recyclable_percent,recyling_rate,scale_cost,factor_m_cost'.split(',')
        ts_numbers = basic_params.get('ts_numbers')
        rrc_numbers = basic_params.get('rrc_numbers')
        min_p = basic_params.get('min_p')
        scale_cost = basic_params.get('scale_cost')
        factor_m_cost = basic_params.get('factor_m_cost')
        total_msw = basic_params.get('total_msw')
        recyclable_percent = basic_params.get('recyclable_percent')
        recyling_rate = basic_params.get('recyling_rate')

        print('ts_numbers...', ts_numbers)
        print('rrc_numbers...', rrc_numbers)
        weight_ts_list = res_dict.get('weight_ts_list')
        has_selected_list = res_dict.get('has_selected_list')
        max_load_list = res_dict.get('max_load_list')
        cost_df = res_dict.get('cost_df')
        cost_df_cols = list(cost_df.columns.values)         # 集散场的名称

        # print('weight_ts_list..........................', weight_ts_list)
        print('has_selected_list..........................', has_selected_list)
        print('max_load_list..........................', max_load_list)


        # 循环p求解p中值的结果
        cost_rows = []
        rrc_built_rows = []

        # for p in range(min_p, rrc_numbers+1):  # rrc_numbers+1
        for p in range(min_p, min_p+2):                   # 测试用
            print('.........................', p)
            if os.path.exists('output/p='+str(p)) is False:
                os.mkdir('output/p='+str(p))

            current_path = os.path.abspath(__file__)
            father_path = os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".")
            env = Environment(loader = FileSystemLoader(father_path))

            template = env.get_template('pmedian_template.mod')
            context = {
                'rrc_numbers': rrc_numbers,
                'ts_numbers': ts_numbers,
                'p': p,
                'has_selected':has_selected_list,
                'rrc_index_list': list(range(1, rrc_numbers+1)),
                'left_brace':'{',
                'right_brace':'}',
            }

            content = template.render(context)
            with open('output/p='+str(p)+'/model.mod','w', encoding='utf-8') as fp:
                fp.write(content)

            with open('output/p='+str(p)+'/data.dat', 'w') as f11:
                b = cdt.CplexData(f11)                                  # 将needs写入dat文件
                b.data_1d_list('weight_ts', weight_ts_list)
                b.data_1d_list('rrc_max_load', max_load_list)

                min_load = [i*0.6 for i in max_load_list]
                rrc_selected_min_load = [int(i+0.499) for i in min_load]
                b.data_1d_list('rrc_selected_min_load', rrc_selected_min_load)
                b.data_1d_list('has_selected', has_selected_list)

                b.data_2d_array('cost_df', np.array(cost_df))

            process = subprocess.Popen('oplrun output/p='+str(p)+'/model.mod' + ' output/p='+str(p)+'/data.dat', stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            result = process.wait()

            

            if os.path.exists('output/p='+str(p)+'/r_Xj.csv') is True:
                
                xj = pd.read_csv('output/p='+str(p)+'/r_Xj.csv')
                df = pd.read_csv('output/p='+str(p)+'/r_Yij.csv')
                df = df[df['decision Varibles']==1].reset_index(drop=True)

                ## 构造allcoation 导入数据库

                # id = models.AutoField(verbose_name='序号',primary_key=True)
                # project_id = models.CharField(verbose_name='项目编号',null=True,max_length=50)
                # p_value = models.IntegerField(verbose_name='p值',null=True)
                # ts = models.CharField(verbose_name='集散场',null=True,max_length=50)
                # rrc = models.CharField(verbose_name='中转站',null=True,max_length=50)

                rrc = self.rrc
                ts = self.ts
                rrc_list = list(rrc['sub_district'])        # 集散场列表
                ts_list = list(ts['sub_names'])            # 中转站列表

                insert_rows = []
                trans_cost_p = 0
                for i in range(df.shape[0]):
                    rrc_index = df['rrc'][i]-1
                    rrc_name = cost_df_cols[rrc_index]
                    ts_index = df['ts'][i]-1
                    trans_cost_p += cost_df[rrc_name][ts_index]     # 交通成本


                    ts_name = ts_list[ts_index]
                    row_i = (self.project_id, p, ts_name, rrc_name)
                    insert_rows.append(row_i)

                # allocation matrix
                tb_name = config.out_allocation
                sql = "insert into {0}(project_id, p_value, ts, rrc)values(%s,%s,%s,%s)".format(tb_name)
                self.cur.executemany(sql,insert_rows)
                self.db.commit()


                print('find solution......最小化交通成本', round(trans_cost_p,1), '万元')
                # df = df.sort_values('ts')
                rrc_weight_list = [0]*rrc_numbers

                for i in range(df.shape[0]):
                    rrc_index = df['rrc'][i]-1
                    ts_index = df['ts'][i]-1
                    rrc_weight_list[rrc_index] = rrc_weight_list[rrc_index]+weight_ts_list[ts_index]  # 单位是吨

                print(rrc_weight_list, '单位是吨')
                rrc_built_rows.append(rrc_weight_list)

                scale_cost_list = []
                for wi in rrc_weight_list:
                    cost_percent = (wi/(1000*total_msw*recyclable_percent*recyling_rate))**factor_m_cost
                    cost_wanyuan = scale_cost*cost_percent/10000          # 单位是万元
                    cost_i = round(cost_wanyuan, 1)                 # 保留1位小数
                    scale_cost_list.append(cost_i)

                scale_cost_rrcs = round(sum(scale_cost_list),1)
                print('...............最小化规模成本', scale_cost_rrcs, '万元')

                cost_rows.append([p, trans_cost_p, scale_cost_rrcs])

            else:
                print('not find------')


        cost_rows = pd.DataFrame(cost_rows, columns='p, 交通成本, 规模成本'.split(', '))
        cost_rows['总成本'] = cost_rows['交通成本'] + cost_rows['规模成本']
        cost_rows.to_csv('output/total_cost_output.csv', index=False, encoding='gbk')

        rrc_built_rows = pd.DataFrame(rrc_built_rows, columns=cost_df_cols)
        rrc_built_rows['p_value'] = cost_rows['p']
        rrc_built_rows.to_csv('output/rrc_built_rows.csv', index=False, encoding='gbk')


        ## 导入结果数据
        rrc_list = list(rrc['sub_district'])        # 集散场列表
        ts_list = list(ts['sub_names'])         # 中转站列表


        # id = models.AutoField(verbose_name='序号',primary_key=True)
        # project_id = models.CharField(verbose_name='项目编号',null=True,max_length=50)
        # p_value = models.IntegerField(verbose_name='p值',null=True)
        # rrc = models.CharField(verbose_name='集散场',null=True,max_length=50)
        # rrc_scale = models.FloatField(verbose_name='集散场规模',null=True)
        # scale_unit = models.CharField(verbose_name='规模单位',null=True,max_length=50)
        insert_rows = []
        for rrc_name in rrc_list:
            for i in range(rrc_built_rows.shape[0]):
                row_i = [self.project_id, int(rrc_built_rows['p_value'][i]), rrc_name, float(rrc_built_rows[rrc_name][i]), '吨']
                insert_rows.append(row_i)

        # allocation matrix
        tb_name = config.out_scale
        sql = "insert into {0}(project_id, p_value, rrc, rrc_scale, scale_unit)values(%s,%s,%s,%s,%s)".format(tb_name)
        self.cur.executemany(sql,insert_rows)
        self.db.commit()


        # id = models.AutoField(verbose_name='序号',primary_key=True)
        # project_id = models.CharField(verbose_name='项目编号',null=True,max_length=50)
        # p = models.IntegerField(verbose_name='p值',null=True)
        # transport_cost = models.FloatField(verbose_name='交通成本',null=True)
        # scale_cost = models.FloatField(verbose_name='规模成本',null=True)
        # total_cost = models.FloatField(verbose_name='总成本',null=True)
        insert_rows = []
        for i in range(cost_rows.shape[0]):
            row_i = [self.project_id, int(cost_rows['p'][i]), float(cost_rows['交通成本'][i]), float(cost_rows['规模成本'][i]), float(cost_rows['总成本'][i])]
            insert_rows.append(row_i)

        # allocation matrix
        tb_name = config.out_cost
        sql = "insert into {0}(project_id, p, transport_cost, scale_cost, total_cost)values(%s,%s,%s,%s,%s)".format(tb_name)
        self.cur.executemany(sql,insert_rows)
        self.db.commit()

    def clear_local_output(self):
        if self.clear_output:
            import shutil
            shutil.rmtree('output')
            shutil.rmtree('data')

    def run(self):
        try:
            self.calculation()
            self.clear_local_output()
        except Exception as e:
            raise Exception(str(e)) 


if __name__=='__main__':

    try:
        import command as tc
        cmd_arg = tc.Argument(sys.argv)
        project_id = cmd_arg.get_value("project_id")      # 命令行传递参数
        if project_id:  ####### 如果从命令行传过来，说明是调用子进程的
            RPP = RunPmedianProject(project_id=project_id, clear_output=True)
        else:           ####### 否则本地直接运行测试
            RPP = RunPmedianProject(clear_output=True)
        RPP.run()
        with open('algorithm_log/p_median.txt', 'w') as f2:
            print('成功', file=f2)

    except Exception as e:
        with open('algorithm_log/p_median.txt', 'w') as f2:
            print(e, file=f2)





