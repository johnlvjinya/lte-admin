
import pandas as pd


# df = pd.read_excel("sjtu_msw_predict_input_history.xlsx")

# rows = []
# sub_name_list = df['sub_names'].unique().tolist()
# for sb in sub_name_list:
#     row_i = [sb, sb+'省']
#     rows.append(row_i)

# df2 = pd.DataFrame(rows, columns='wrong,right'.split(','))
# df2.to_excel('draft01.xlsx', index=False)


df1 = pd.read_excel('sjtu_msw_predict_input_history.xlsx')
df2 = pd.read_excel('province_map.xlsx')


df = df1.merge(df2, left_on = "sub_names",right_on = "sub_names")
df.to_excel('res.xlsx', index=False)


