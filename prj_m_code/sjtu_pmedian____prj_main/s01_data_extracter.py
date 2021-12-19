
import os
import config
import pymysql
import pandas as pd


class MysqlPandas():
	def __init__(self):
		self.db = pymysql.connect(host=config.host, port=int(config.port), user=config.user, passwd=config.password, db=config.db)
		self.cur = self.db.cursor() 
	def get_all_table(self):
		self.cur.execute('SHOW TABLES')                                     # 获取mysql中所有表
		results = self.cur.fetchall()
		ri_list = []
		for ri in results:
			ri_list.append(ri[0].strip(' '))
			# print(ri[0].strip(' '), type(ri[0]))
		return ri_list

	def get_tb_column(self, tb):                                        # 查看数据库中
		self.cur.execute("select * from {0}".format(tb))                # 查看这个表的列名
		column_name_list = []
		for column in self.cur.description:	
			column_name_list.append(column[0])
		return column_name_list

	def select_tb_by_cols_value_to_df(self, tb, cols, value):
		sql = '''
		select * from {0}
		where {1}='{2}'
		'''.format(tb, cols, value)
		self.cur.execute(sql)
		results = self.cur.fetchall()
		rows = []
		for row in results:
			rows.append(list(row))
		df = pd.DataFrame(rows, columns=self.get_tb_column(tb))
		return df


class PmedianProject():
	def __init__(self, project_id, save_csv=False):
		self.project_id = project_id
		self.save_csv = save_csv
		self.mp = MysqlPandas()

	def data_extracter(self):
		
		basic = config.basic
		costmatrix = config.costmatrix
		ts = config.ts
		rrc = config.rrc

		tb_list = [basic, costmatrix, ts, rrc]  ############ 将需要的表保存到字典中
		mydict = {}
		for tb in tb_list:
			df = self.mp.select_tb_by_cols_value_to_df(tb, 'project_id', self.project_id)
			if self.save_csv:  # 保存数据用来测试
				if os.path.exists('data') is False:
					os.mkdir('data')
				df.to_csv('data/%s.csv'%tb, index=False, encoding='gbk')
				
			if tb in [basic, ts, rrc] and df.shape[0]==0:
				raise Exception(tb+"表没有数据") 
			mydict[tb] = df
			print('success getting %s'%tb)
		return mydict
		

if __name__ == '__main__':
	PP = PmedianProject('p001', save_csv=True)
	DICT1 = PP.data_extracter()
	# print(DICT1)





