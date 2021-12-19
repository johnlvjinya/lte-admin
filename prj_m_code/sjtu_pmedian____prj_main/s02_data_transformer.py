
import config
import pandas as pd
from math import radians, cos, sin, asin, sqrt

import s01_data_extracter as s01

def get_df_col_value(df, col, value):			# 得到值
	try:
		res = df[df[col]==value].reset_index(drop=True)['value'][0]
		return res
	except:
		raise Exception(value+"基本参数不完整") 


class PmedianProjectTransformer():

	def __init__(self, project_id, local_csv=False):
		basic = config.basic
		costmatrix = config.costmatrix
		ts = config.ts
		rrc = config.rrc

		if local_csv:
			self.data_path = 'data/'
			self.basic = pd.read_csv(self.data_path+'%s.csv'%basic, encoding='gbk')
			self.cost_matrix =  pd.read_csv(self.data_path+'%s.csv'%costmatrix, encoding='gbk')
			self.rrc = pd.read_csv(self.data_path+'%s.csv'%rrc, encoding='gbk')
			self.ts = pd.read_csv(self.data_path+'%s.csv'%ts, encoding='gbk')
		else:  # 调用s01得到相关数据
			PP = s01.PmedianProject(project_id, save_csv=True)
			mydict = PP.data_extracter()
			self.basic = mydict.get(basic)
			self.cost_matrix = mydict.get(costmatrix)
			self.rrc = mydict.get(rrc)
			self.ts = mydict.get(ts)

		self.ts_numbers = self.ts.shape[0]                # 提取参数
		self.rrc_numbers = self.rrc.shape[0]
		self.min_p = self.rrc[self.rrc['has_selected']==1].reset_index(drop=True).shape[0]
		
		self.trans_cost = get_df_col_value(self.basic, 'name', 'trans_cost')
		self.total_msw = get_df_col_value(self.basic, 'name',  'MSW')
		self.recyclable_percent = get_df_col_value(self.basic, 'name',  'recyclable_percent')
		self.recyling_rate = get_df_col_value(self.basic, 'name',  'recyling_rate')
		self.scale_cost = get_df_col_value(self.basic, 'name',  'scale_cost')
		self.factor_m_cost = get_df_col_value(self.basic, 'name',  'factor_m_cost')




	def get_weight_ts(self):		# 每个ts的回收量
		weight_ts = []
		# print('wi, self.total_msw, self.recyclable_percent, self.recyling_rate')
		for pi in self.ts['weight_percentage']:
			wi = int(1000*self.total_msw*pi*self.recyclable_percent*self.recyling_rate+0.499) 	# 吨
			# print(wi, self.total_msw, self.recyclable_percent, self.recyling_rate)
			weight_ts.append(wi)
		return weight_ts


	def get_max_load(self):				# rrc最大的处理量	
		list1 = list(self.rrc['max_load'])		# (千吨/年)
		res = [int(i) for i in list1]				# 千吨
		return res


	def get_has_selected(self):				# 找到已经选择的
		res = list(self.rrc['has_selected'])
		return res

	def get_weight_distance_df(self):		# 欧几里得距离
		weight_ts = self.get_weight_ts()
		rows = []
		for i in range(self.ts.shape[0]):
			row_i = []
			for j in range(self.rrc.shape[0]):
				lon1, lat1, lon2, lat2 = map(radians, [self.ts['lng'][i], self.ts['lat'][i], self.rrc['lng'][j], self.rrc['lat'][j]])
				dlon = lon2 - lon1 
				dlat = lat2 - lat1 
				a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
				c = 2 * asin(sqrt(a)) 
				r = 6371 																	# 地球平均半径，单位为公里
				dij = c * r
				weight_dij = int(dij*weight_ts[i]*self.trans_cost+0.499)
				row_i.append(weight_dij)

			rows.append(row_i)
		df = pd.DataFrame(rows, columns = self.rrc['sub_district'])
		df = df/10000  # 变成万元
		# df.to_csv('distance.csv', encoding='gbk')
		return df

	def get_cost_df(self):
		# 构造cost_matrix
		if self.cost_matrix.shape[0]<self.ts_numbers*self.rrc_numbers:     	# 如果cost_matrix为空，则构造欧几里得距离（也可以先计算好输入--根据路网距离/时间等等参数）
		    cost_matrix_r = self.get_weight_distance_df()
		if self.cost_matrix.shape[0]==self.ts_numbers*self.rrc_numbers:     	# 如果cost_matrix不为空，则构造欧几里得距离（也可以先计算好输入--根据路网距离/时间等等参数）
		    cost_matrix_r = cost_matrix
		return cost_matrix_r

	def res_data_json(self):
		values = [self.ts_numbers, self.rrc_numbers, self.min_p, self.trans_cost, self.total_msw, self.recyclable_percent, self.recyling_rate, self.scale_cost, self.factor_m_cost]
		keys = 'ts_numbers,rrc_numbers,min_p,trans_cost,total_msw,recyclable_percent,recyling_rate,scale_cost,factor_m_cost'.split(',')
		basic_params = dict(zip(keys, values))

		weight_ts_list = self.get_weight_ts()
		has_selected_list = self.get_has_selected()
		max_load_list = self.get_max_load()
		cost_df = self.get_cost_df()

		values = [basic_params, weight_ts_list, has_selected_list, max_load_list, cost_df]
		keys = 'basic_params, weight_ts_list, has_selected_list, max_load_list, cost_df'.split(', ')
		res_dict = dict(zip(keys, values))
		# print(res_dict)
		return res_dict



if __name__ == '__main__':
	a = PmedianProjectTransformer('p001', local_csv=True)
	res = a.res_data_json()
	for key,value in res.items():
		print(key, type(value))

	



