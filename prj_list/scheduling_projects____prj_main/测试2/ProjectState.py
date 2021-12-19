# coding: utf-8
import pymysql

# 更新项目状态
class ProjectState(object):
    def __init__(self, prj_name):
        self.prj_name = prj_name
        # # 连接数据库
        # try:
        #     self.con=pymysql.connect(host='127.0.0.1',user='root',passwd='root',db='dw_cy_scheduling')
        #     self.cur=self.con.cursor()
        # except:
        #     print('1.访问数据库出了点问题！')

    # 更新项目状态：数据解析完成
    def dataComplete(self):
        # try:
        #     self.cur.execute("update scheduling_projects set prj_process='40', prj_process_text='排产数据解析完成，开始求解', prj_error_text='请耐心等待，最长求解时间参见配置' where prj_name = '%s'" % self.prj_name)
        #     self.con.commit()
        # except:
        #     print('2.更新项目状态出了点问题！')
        pass

    # 更新项目状态：排产求解完成
    def solveComplete(self, status, delayTime, finishTime, wallTime):
        # try:
        #     if status == 'Optimal':
        #         self.cur.execute("update scheduling_projects set prj_process='90', prj_process_text='找到最优解', order_delay_hour='%s', order_finish_datetime='%s', run_cost_time_second='%s', prj_error_text=NULL where prj_name = '%s'" % (delayTime, finishTime, wallTime, self.prj_name))
        #     elif status == 'Feasible':
        #         self.cur.execute("update scheduling_projects set prj_process='90', prj_process_text='找到较优解', order_delay_hour='%s', order_finish_datetime='%s', run_cost_time_second='%s', prj_error_text=NULL where prj_name = '%s'" % (delayTime, finishTime, wallTime, self.prj_name))
        #     else:
        #         self.cur.execute("update scheduling_projects set prj_process='30', prj_process_text='没有找到可行解', prj_run_response_text='运行失败', run_cost_time_second='%s', prj_error_text='建议扩大搜索范围' where prj_name = '%s'" % (wallTime, self.prj_name))
        #     self.con.commit()
        # except:
        #     print('3.更新项目状态出了点问题！')
        pass
            
    # 更新项目状态：排产项目完成
    def projectComplete(self, status):
        # try:
        #     self.cur.execute("update scheduling_projects set prj_process='100', prj_process_text='排产全部完成', prj_run_response_text='运行%s' where prj_name = '%s'" % ('成功' if status else '失败', self.prj_name))
        #     self.con.commit()
        #     self.cur.close()
        #     self.con.close()
        # except:
        #     print('4.更新项目状态出了点问题！')
        pass