
from exts import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):### 用户名
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50),unique=True,nullable=False, comment='用户名')
    password = db.Column(db.String(50),nullable=False, comment='密码')
    email = db.Column(db.String(50), comment='邮箱')
    role = db.Column(db.String(50), comment='角色')
    def __init__(self, username, password):            # 使用name和password登录
        self.username = username
    def verify_password(self, password):
        return check_password_hash(generate_password_hash(self.password), password)

class AutoHtmlContainers(db.Model):### 自动生成echarts页面
    __tablename__ = 'autohtmlcontainers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    html_name = db.Column(db.String(255),nullable=False, comment='页面名称')
    container_name = db.Column(db.String(255), comment='图表名称')
    container_skip_url = db.Column(db.String(255), comment='图表跳转链接') 
    container_col_long = db.Column(db.Integer(), comment='图表宽度')
    container_chart_type = db.Column(db.String(255), comment='图表类型')
    container_data_url = db.Column(db.String(255),nullable=False, comment='图表数据地址')

class test1(db.Model):### 测试1
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    test11 = db.Column(db.String(50), comment='测试1')
    test22 = db.Column(db.String(50), comment='测试2')

class auto_sql_bi(db.Model):### 测试1
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    c01_name = db.Column(db.String(255),nullable=False, comment='名称')
    c02_cols_str = db.Column(db.String(255), comment='表头字段')
    c03_sql_str = db.Column(db.String(1255), comment='SQL语句')
    c04_bar = db.Column(db.String(50), comment='bar参数')
    c05_bar_group = db.Column(db.String(255), comment='bar_group参数')
    c06_pie = db.Column(db.String(255), comment='pie参数')
    c07_sankey = db.Column(db.String(255), comment='sankey参数')

class scheduling_projects____prj_main(db.Model):### 排产项目列表
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), unique=True,nullable=False, comment='项目名')
    prj_create_t = db.Column(db.DateTime, comment='创建时间')     # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 注意后面的创建时间都这样写创建时间
    prj_creator = db.Column(db.String(255), comment='创建人')
    last_refresh_t = db.Column(db.DateTime, comment='更新时间')          # 记录最近的运行时间，用来排序
    
    prj_process_text = db.Column(db.String(255), comment='项目进度说明')        # 项目进度，提示现在进行到了哪一步
    prj_process_int = db.Column(db.Integer(), comment='项目进度条')
    
    ## 未运行：浅绿色， 运行中：蓝色  运行成功：深绿色  运行失败：红色
    prj_run_state_text = db.Column(db.String(255), comment='运行状态')       # 未运行，正在运行，运行成功，运行失败
    prj_run_error_text = db.Column(db.String(255), comment='报错信息')              # 运行报错的提示
    prj_note = db.Column(db.String(255), comment='备注')              # 运行报错的提示
class scheduling_projects_input1_order(db.Model):### 客户订单
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_date = db.Column(db.Date, comment='接单日期')
    c02_customer = db.Column(db.String(50), comment='客户')
    c03_catagory = db.Column(db.String(50), comment='产品分类')
    c04_product_type = db.Column(db.String(50), comment='产品属性')
    c05_plan = db.Column(db.String(10), comment='是否纳入计划')
    c06_id_num = db.Column(db.String(50), comment='订单号')
    c07_fast_id = db.Column(db.String(50), comment='快捷编号')
    c08_product_id = db.Column(db.String(50), comment='产品编号')
    c09_num_need = db.Column(db.Integer(), comment='订单数量',nullable=False)
    c10_num_finish = db.Column(db.Integer(), comment='完工数量')
    c11_lishu = db.Column(db.String(50), comment='粒数')
    c12_delivery_date = db.Column(db.Date, comment='订单交期')
    c13_material_state = db.Column(db.String(50), comment='物料状态')
    c14lack_material_id = db.Column(db.String(50), comment='缺货料号')
    c15_lack_get_date = db.Column(db.Date, comment='预计到货时间')
    c16_priority1 = db.Column(db.String(10), comment='订单优先级')
    c17_catagory_1= db.Column(db.String(50), comment='订单分类')
    c18_plan_start_d = db.Column(db.String(255), comment='计划开始时间')
    c19_plan_end_d = db.Column(db.String(255), comment='计划结束时间')
    c20_state = db.Column(db.String(255), comment='订单状态')
    c21_actual_start_t = db.Column(db.String(255), comment='实际开始时间')
    c22_actual_end_t = db.Column(db.String(255), comment='实际结束时间')
    c23_note1 = db.Column(db.String(255), comment='备注')
class scheduling_projects_input2_process(db.Model):### 工艺路线
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_p_product_id = db.Column(db.String(50), comment='产品编号')
    c02_f_product_id = db.Column(db.String(50), comment='父料号')
    c03_son_product_id = db.Column(db.String(50), comment='子料号')
    c04_product_name = db.Column(db.String(50), comment='品名')
    c05_district = db.Column(db.String(50), comment='区域')
    c06_work_line = db.Column(db.String(50), comment='产线')
    c07_person_district = db.Column(db.String(50), comment='人员区域')
    c08_person_num = db.Column(db.String(50), comment='计划人数',nullable=False)
    c09_group_leader_num = db.Column(db.Integer(), comment='班组长人数',nullable=False)
    c10_machine_operator_num = db.Column(db.Integer(), comment='操机手人数',nullable=False)
    c11_device_type = db.Column(db.String(50), comment='设备类型')
    c12_device_num = db.Column(db.String(50), comment='设备数量')
    c13_device_standard_output = db.Column(db.String(50), comment='标准产能')
    # process_prepare_t = db.Column(db.String(50), comment='准备时间')
    c14_transfer_time_lower = db.Column(db.String(50), comment='转移时间下限')
    c15_transfer_time_upper= db.Column(db.String(50), comment='转移时间上限')
    c16_constraint_type = db.Column(db.String(10), comment='约束类型')
class scheduling_projects_input3_person(db.Model):### 人员
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255),nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_person_district = db.Column(db.String(50), comment='人员区域')
    c02_person_group = db.Column(db.String(50), comment='班组')
    c03_p_priority = db.Column(db.String(10), comment='优先级')
    c04_group_name = db.Column(db.String(50), comment='班次')
    
    c05_transfer_start_t = db.Column(db.Date, comment='切换起始时间')
    c06_transfer_period =db.Column(db.Integer(), comment='切换周期',nullable=False)
    c07_person_count = db.Column(db.Integer(), comment='合计人数',nullable=False)
    c08_group_leader_num =  db.Column(db.Integer(), comment='班组长人数',nullable=False)
    c09_leader_ability_type = db.Column(db.String(50), comment='能力标签')
    c10_machine_operator_num = db.Column(db.Integer(), comment='操机手人数',nullable=False)
class scheduling_projects_input4_person_holiday(db.Model):### 请假
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_person_name = db.Column(db.String(50), comment='员工')
    c02_person_district = db.Column(db.String(50), comment='人员区域')
    c03_group_name = db.Column(db.String(50), comment='班组')

    c04_is_leader = db.Column(db.String(10), comment='是否班组长')
    c05_leader_ability_type = db.Column(db.String(5), comment='能力标签')
    c06_is_operator = db.Column(db.String(10), comment='是否操机手')
    c07_holiday_start_t =db.Column(db.Date, comment='请假开始时间')
    c08_holiday_end_t = db.Column(db.Date, comment='请假结束时间')
class scheduling_projects_input5_device(db.Model):### 设备
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_device_type = db.Column(db.String(10), comment='设备类型')
    c02_device_id = db.Column(db.String(50), comment='设备编号')
    c03_device_name = db.Column(db.String(50), comment='设备名称')
    c04_device_state = db.Column(db.String(50), comment='设备状态')
    c05_device_ability = db.Column(db.String(50), comment='设备能力')
class scheduling_projects_input6_bom(db.Model):### 产品BOM
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_product_id = db.Column(db.String(50), comment='产品编号')
    c02_father_m = db.Column(db.String(50), comment='父料号')
    c03_son_m = db.Column(db.String(50), comment='子料号')
    c04_product_name = db.Column(db.String(50), comment='品名')
    c05_component = db.Column(db.String(50), comment='组成用量')
    c06_main_num = db.Column(db.String(50), comment='主件底数')
    c07_unit = db.Column(db.String(10), comment='单位')
    c08_cost_rate = db.Column(db.String(50), comment='损耗率')
    c09_main_type = db.Column(db.String(50), comment='料件属性')
    c10_bom_note = db.Column(db.String(255), comment='备注')
class scheduling_projects_input7_material(db.Model):### 物料
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_m_id = db.Column(db.String(50), comment='元件料号')
    c02_product_name = db.Column(db.String(50), comment='品名')
    c03_m_unit = db.Column(db.String(10), comment='发料单位')
    c04_m_num = db.Column(db.Float(), comment='库存可用量')

    r_t01 = db.Column(db.Date, comment='预计到货时间01')
    r_t01n01 = db.Column(db.Float(), comment='预计到货数量01')
    r_t02 = db.Column(db.Date, comment='预计到货时间02')
    r_t02n02 = db.Column(db.Float(), comment='预计到货数量02')    
    r_t03 = db.Column(db.Date, comment='预计到货时间03')
    r_t03n03 = db.Column(db.Float(), comment='预计到货数量03')
    r_t04 = db.Column(db.Date, comment='预计到货时间04')
    r_t04n04 = db.Column(db.Float(), comment='预计到货数量04')
    r_t05 = db.Column(db.Date, comment='预计到货时间05')
    r_t05n05 = db.Column(db.Float(), comment='预计到货数量05')
    r_t06 = db.Column(db.Date, comment='预计到货时间06')
    r_t06n06 = db.Column(db.Float(), comment='预计到货数量06')
    r_t07 = db.Column(db.Date, comment='预计到货时间07')
    r_t07n07 = db.Column(db.Float(), comment='预计到货数量07')
    r_t08 = db.Column(db.Date, comment='预计到货时间08')
    r_t08n08 = db.Column(db.Float(), comment='预计到货数量08')
    r_t09 = db.Column(db.Date, comment='预计到货时间09')
    r_t09n09 = db.Column(db.Float(), comment='预计到货数量09')
    r_t10 = db.Column(db.Date, comment='预计到货时间10')
    r_t10n10 = db.Column(db.Float(), comment='预计到货数量10')

    r_t11 = db.Column(db.Date, comment='预计到货时间11')
    r_t11n11 = db.Column(db.Float(), comment='预计到货数量11')
    r_t12 = db.Column(db.Date, comment='预计到货时间12')
    r_t12n12 = db.Column(db.Float(), comment='预计到货数量12')    
    r_t13 = db.Column(db.Date, comment='预计到货时间13')
    r_t13n13 = db.Column(db.Float(), comment='预计到货数量13')
    r_t14 = db.Column(db.Date, comment='预计到货时间14')
    r_t14n14 = db.Column(db.Float(), comment='预计到货数量14')
    r_t15 = db.Column(db.Date, comment='预计到货时间15')
    r_t15n15 = db.Column(db.Float(), comment='预计到货数量15')
    r_t16 = db.Column(db.Date, comment='预计到货时间16')
    r_t16n16 = db.Column(db.Float(), comment='预计到货数量16')
    r_t17 = db.Column(db.Date, comment='预计到货时间17')
    r_t17n17 = db.Column(db.Float(), comment='预计到货数量17')
    r_t18 = db.Column(db.Date, comment='预计到货时间18')
    r_t18n18 = db.Column(db.Float(), comment='预计到货数量18')
    r_t19 = db.Column(db.Date, comment='预计到货时间19')
    r_t19n19 = db.Column(db.Float(), comment='预计到货数量19')
    r_t20 = db.Column(db.Date, comment='预计到货时间20')
    r_t20n20 = db.Column(db.Float(), comment='预计到货数量20')

    r_t21 = db.Column(db.Date, comment='预计到货时间21')
    r_t21n21 = db.Column(db.Float(), comment='预计到货数量21')
    r_t22 = db.Column(db.Date, comment='预计到货时间22')
    r_t22n22 = db.Column(db.Float(), comment='预计到货数量22')    
    r_t23 = db.Column(db.Date, comment='预计到货时间23')
    r_t23n23 = db.Column(db.Float(), comment='预计到货数量23')
    r_t24 = db.Column(db.Date, comment='预计到货时间24')
    r_t24n24 = db.Column(db.Float(), comment='预计到货数量24')
    r_t25 = db.Column(db.Date, comment='预计到货时间25')
    r_t25n25 = db.Column(db.Float(), comment='预计到货数量25')
    r_t26 = db.Column(db.Date, comment='预计到货时间26')
    r_t26n26 = db.Column(db.Float(), comment='预计到货数量26')
    r_t27 = db.Column(db.Date, comment='预计到货时间27')
    r_t27n27 = db.Column(db.Float(), comment='预计到货数量27')
    r_t28 = db.Column(db.Date, comment='预计到货时间28')
    r_t28n28 = db.Column(db.Float(), comment='预计到货数量28')
    r_t29 = db.Column(db.Date, comment='预计到货时间29')
    r_t29n29 = db.Column(db.Float(), comment='预计到货数量29')
    r_t30 = db.Column(db.Date, comment='预计到货时间30')
    r_t30n30 = db.Column(db.Float(), comment='预计到货数量30')
class scheduling_projects_input8_calender(db.Model):### 生产日历
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c1_resource = db.Column(db.String(50), comment='资源')
    c2_work_day = db.Column(db.String(255), comment='出勤日期或星期')
    c3_work_mode = db.Column(db.String(255), comment='出勤模式或时间')
    c4_work_priority = db.Column(db.String(10), comment='优先级')
class scheduling_projects_input9_workmode(db.Model):### 出勤模式
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c1_work_mode1 = db.Column(db.String(50), comment='出勤模式')
    c2_work_day = db.Column(db.String(255), comment='工作时间')
class scheduling_projects_output_1_workno(db.Model):### 工单计划
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_work_no = db.Column(db.String(255), comment='工单编号')
    c02_district = db.Column(db.String(50), comment='区域')
    c03_workline = db.Column(db.String(50), comment='产线')
    c04_order_num_id = db.Column(db.String(50), comment='订单号')
    c05_order_fast_id = db.Column(db.String(50), comment='快捷编号')
    c06_product_id = db.Column(db.String(50), comment='产品编号')
    c07_order_num_need = db.Column(db.Integer(), comment='订单数量')
    c08_order_delivery_date = db.Column(db.Date, comment='订单交期')
    c09_material_lack_id = db.Column(db.String(255), comment='缺货料号')
    c10_material_lack_arrival_t = db.Column(db.Date, comment='预计到货时间')
    c11_order_priority = db.Column(db.String(20), comment='订单优先级')
    c12_father_m_id = db.Column(db.String(50), comment='父料号')
    c13_son_m_id = db.Column(db.String(50), comment='子料号')
    c14_product_name = db.Column(db.String(50), comment='品名')
    '''
    人员区域    
    计划人数    班组长人数   操机手人数   设备类型    
    设备数量    标准产能    准备时间    转移时间下限  
    转移时间上限  约束类型   
    '''
    c15_person_district_name = db.Column(db.String(50), comment='人员区域')
    c16_person_plan_num = db.Column(db.String(50), comment='计划人数')
    c17_group_leader_num = db.Column(db.String(50), comment='班组长人数')
    c18_operator_num = db.Column(db.String(50), comment='操机手人数')
    c19_device_type = db.Column(db.String(50), comment='设备类型')
    c20_device_num = db.Column(db.String(50), comment='设备数量')
    c21_device_standard_output = db.Column(db.String(50), comment='标准产能')
    # process_prepare_t = db.Column(db.String(50), comment='准备时间')
    c22_transfer_t_lower = db.Column(db.String(50), comment='转移时间下限')
    c23_transfer_t_upper = db.Column(db.String(50), comment='转移时间上限')
    c24_constraint_type = db.Column(db.String(255), comment='约束类型')
    '''
    是否固定    固定时间    
    计划开始时间  计划持续时长  计划结束时间  工单状态    
    分配人员    分配班组长   分配操机手   已完成数量   
    实际开始时间  实际结束时间
    '''
    c25_is_fixed = db.Column(db.String(10), comment='是否固定')
    c26_fixed_t = db.Column(db.String(50), comment='固定时间')
    c27_plan_start_t = db.Column(db.String(50), comment='计划开始时间')
    c28_plan_last_t = db.Column(db.Float(), comment='计划持续时长')
    c29_plan_end_t = db.Column(db.String(50), comment='计划结束时间')
    c30_actual_start_t = db.Column(db.String(50), comment='实际开始时间')
    c31_actual_end_t = db.Column(db.String(50), comment='实际结束时间')

    c32_work_no_state = db.Column(db.String(50), comment='工单状态')
    c33_allocate_p = db.Column(db.String(255), comment='分配人员')
    c34_allocate_leader = db.Column(db.String(255), comment='分配班组长')
    c35_allocate_operator = db.Column(db.String(255), comment='分配操机手')
    c36_finished_num = db.Column(db.String(50), comment='已完成数量')
class scheduling_projects_output_2_material_check(db.Model):### 物料核查
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    ###### 元件料号 品名  发料单位    订单号 产品编号    需求数量    需求时间    库存结余
    c1_material_num_id = db.Column(db.String(50), comment='元件料号')
    c2_product_name = db.Column(db.String(50), comment='品名')
    c3_m_unit = db.Column(db.String(50), comment='发料单位')
    c4_order_num_id = db.Column(db.String(50), comment='订单号')
    c5_product_num_id = db.Column(db.String(50), comment='产品编号')
    c6_product_need_num = db.Column(db.Float(), comment='需求数量',nullable=False)
    c7_product_need_t = db.Column(db.String(50), comment='需求时间')
    c8_p_reserve_num = db.Column(db.Float(), comment='库存结余',nullable=False)
class scheduling_projects_output_3_result_run_info(db.Model):### 运行结果
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    ###### 特殊字段
    c1_run_cost_time_second = db.Column(db.String(255), comment='运行耗时')        # 运行的耗时
    c2_order_delay_hour = db.Column(db.String(255), comment='延期时间')            # 订单延期时间
    c3_order_finish_datetime = db.Column(db.String(255), comment='完工时间')       # 订单完工时间
    c4_test1 = db.Column(db.Integer(), comment='整数测试',nullable=False)                         # 订单完工时间
    c5_test2 = db.Column(db.Float(), comment='小数测试',nullable=False)                           # 订单完工时间

class wc_father_t01_sku(db.Model):### wc本地料件库
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    c01_sku_id = db.Column(db.String(50), comment='料件编号')
    c01_sku_name = db.Column(db.String(50), comment='品名')
    c02_sku_history_sector = db.Column(db.String(255), comment='历史排产员字典')
class wc_father_t02_process(db.Model):### wc本地工艺库
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    c01_sku_id = db.Column(db.String(50), comment='料件编号')
    c02_father = db.Column(db.String(50), comment='父料号')
    c03_son = db.Column(db.String(50), comment='子料号')
    c04_root_style = db.Column(db.String(50), comment='节点类型')
    c05_son_name = db.Column(db.String(50), comment='品名')
    c06_standard_output = db.Column(db.String(50), comment='标准产能')
    c07_person_plan = db.Column(db.String(50), comment='计划人数')
    c08_group_leader_num = db.Column(db.String(50), comment='班组长人数')
    c09_device_type = db.Column(db.String(50), comment='设备类型')
    c10_production_type = db.Column(db.String(50), comment='生产方式')
    c11_near_match = db.Column(db.String(50), comment='近似匹配')

class workshop_cy____prj_main(db.Model):### 创元车间排产
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), unique=True,nullable=False, comment='项目名')
    prj_create_t = db.Column(db.DateTime, comment='创建时间')     # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 注意后面的创建时间都这样写创建时间
    prj_creator = db.Column(db.String(255), comment='创建人')
    last_refresh_t = db.Column(db.DateTime, comment='更新时间')          # 记录最近的运行时间，用来排序
    
    prj_process_text = db.Column(db.String(255), comment='项目进度说明')        # 项目进度，提示现在进行到了哪一步
    prj_process_int = db.Column(db.Integer(), comment='项目进度条')
    
    ## 未运行：浅绿色， 运行中：蓝色  运行成功：深绿色  运行失败：红色
    prj_run_state_text = db.Column(db.String(255), comment='运行状态')       # 未运行，正在运行，运行成功，运行失败
    prj_run_error_text = db.Column(db.String(255), comment='报错信息')              # 运行报错的提示
    prj_note = db.Column(db.String(255), comment='备注')              # 运行报错的提示
class workshop_cy_input01_ws_info(db.Model):### 车间信息
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='车间')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_name = db.Column(db.String(50), comment='名称')
    c02_value = db.Column(db.String(255), comment='值')
class workshop_cy_input02_planer_history(db.Model):### 排产员
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='车间')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_staff_name = db.Column(db.String(50), comment='姓名')
    c02_staff_id = db.Column(db.String(50), comment='工号')
    c02_staff_time = db.Column(db.String(50), default='*', comment='负责时间')
class workshop_cy_input03_sku(db.Model):### 料件
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='车间')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_sku_id = db.Column(db.String(50), comment='料件编号')
    c02_sku_name = db.Column(db.String(50), comment='料件名称')
    c03_sku_relate_staff = db.Column(db.String(50), comment='料件关联排产员工号')
class workshop_cy_input04_worker(db.Model):### 工人
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='车间')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_worker_name = db.Column(db.String(50), comment='姓名')
    c02_worker_id = db.Column(db.String(50), comment='工号')
    c03_worker_type = db.Column(db.String(50), comment='工种')
    c04_is_formal = db.Column(db.String(50), comment='是否是正式工')
    c04_sku_maintenance_state = db.Column(db.String(10), comment='是否手工维护')  # 0:自动匹配， 1，手工维护
class workshop_cy_input05_machine(db.Model):### 机器
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='车间')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_worker_name = db.Column(db.String(50), comment='姓名')
    c02_worker_id = db.Column(db.String(50), comment='工号')
    c03_worker_type = db.Column(db.String(50), comment='工种')
    c04_is_formal = db.Column(db.String(50), comment='是否是正式工')
    c04_sku_maintenance_state = db.Column(db.String(10), comment='是否手工维护')  # 0:自动匹配， 1，手工维护
class workshop_cy_input06_material(db.Model):### 材料
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='车间')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_m_name = db.Column(db.String(50), comment='物料名称')
    c02_m_arrival_t = db.Column(db.String(50), comment='到货时间') # 今天之前就表示有效库存
    c03_m_num = db.Column(db.String(50), comment='数量')
class workshop_cy_input07_process(db.Model):### 工艺
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='车间')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c01_m_id = db.Column(db.String(50), comment='料件编号')
    c02_f_m_id = db.Column(db.String(50), comment='父料号')
    c03_s_m_id = db.Column(db.String(50), comment='子料号')
    c04_s_m_id = db.Column(db.String(50), comment='节点类型')
    c05_m_name = db.Column(db.String(50), comment='品名')
    c06_standard_output = db.Column(db.String(50), comment='标准产能')
    c07_person_need = db.Column(db.String(50), comment='计划人数')
    c08_group_leader_num = db.Column(db.String(50), comment='班组长人数')
    c09_device_type = db.Column(db.String(50), comment='设备类型')
    c10_production_type = db.Column(db.String(50), comment='生产方式')
    c11_match = db.Column(db.String(50), comment='近似匹配')

class sjtu_pmedian____prj_main(db.Model):### pmedian项目列表
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), unique=True,nullable=False, comment='项目名')
    prj_create_t = db.Column(db.DateTime, comment='创建时间')     # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 注意后面的创建时间都这样写创建时间
    prj_creator = db.Column(db.String(255), comment='创建人')
    last_refresh_t = db.Column(db.DateTime, comment='更新时间')          # 记录最近的运行时间，用来排序
    
    prj_process_text = db.Column(db.String(255), comment='项目进度说明')        # 项目进度，提示现在进行到了哪一步
    prj_process_int = db.Column(db.Integer(), comment='项目进度条')
    
    ## 未运行：浅绿色， 运行中：蓝色  运行成功：深绿色  运行失败：红色
    prj_run_state_text = db.Column(db.String(255), comment='运行状态')       # 未运行，正在运行，运行成功，运行失败
    prj_run_error_text = db.Column(db.String(255), comment='报错信息')              # 运行报错的提示
    prj_note = db.Column(db.String(255), comment='备注')              # 运行报错的提示
class sjtu_pmedian_input1_basic(db.Model):### 基本参数
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    name = db.Column(db.String(255), comment='参数名称')
    value = db.Column(db.Float(), comment='参数值')
    unit = db.Column(db.String(255), comment='单位')
    note = db.Column(db.String(255), comment='备注')
class sjtu_pmedian_input2_transferstation(db.Model):### 中转站
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    sub_names = db.Column(db.String(255), comment='名称')
    weight_percentage = db.Column(db.Float(), comment='重量占比因子')
    lng = db.Column(db.Float(), comment='经度')
    lat = db.Column(db.Float(), comment='纬度')
    district = db.Column(db.String(255), comment='所属区')
class sjtu_pmedian_input3_recyclingcenter(db.Model):### 备选集散场
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    district = db.Column(db.String(255), comment='区')
    sub_district = db.Column(db.String(255), comment='街镇')
    location = db.Column(db.String(255), comment='位置')
    lng = db.Column(db.Float(), comment='经度')
    lat = db.Column(db.Float(), comment='纬度')
    max_load = db.Column(db.Integer(), comment='最大容量')
    max_load_unit = db.Column(db.String(255), comment='最大容量单位')
    has_selected = db.Column(db.Integer(), comment='是否选择')  
class sjtu_pmedian_input4_costmatrix(db.Model):### cost矩阵
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    ts_name = db.Column(db.String(255), comment='中转站')
    rrc_name = db.Column(db.String(255), comment='集散场')
    cost = db.Column(db.String(255), comment='费用')
    cost_unit = db.Column(db.String(255), comment='单位')
class sjtu_pmedian_output_1_allocationmatrix(db.Model):### 分配矩阵
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    ts = db.Column(db.String(255), comment='中转站')
    rrc = db.Column(db.String(255), comment='集散场')
    p_value = db.Column(db.Integer(), comment='p值')
class sjtu_pmedian_output_2_buildscale(db.Model):### 建设规模
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    p_value = db.Column(db.Integer(), comment='p值')
    rrc = db.Column(db.String(255), comment='集散场')
    rrc_scale = db.Column(db.Integer(), comment='规模')
    scale_unit = db.Column(db.String(255), comment='规模单位')
class sjtu_pmedian_output_3_costmatrix(db.Model):### 成本矩阵
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    p = db.Column(db.Integer(), comment='p值')
    transport_cost = db.Column(db.Float(), comment='运输成本')
    scale_cost = db.Column(db.Float(), comment='规模成本')
    total_cost = db.Column(db.Float(), comment='总成本')

class sjtu_carbon_emission____prj_main(db.Model):### 碳排放项目列表
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), unique=True,nullable=False, comment='项目名')
    prj_create_t = db.Column(db.DateTime, comment='创建时间')     # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 注意后面的创建时间都这样写创建时间
    prj_creator = db.Column(db.String(255), comment='创建人')
    last_refresh_t = db.Column(db.DateTime, comment='更新时间')          # 记录最近的运行时间，用来排序
    
    prj_process_text = db.Column(db.String(255), comment='项目进度说明')        # 项目进度，提示现在进行到了哪一步
    prj_process_int = db.Column(db.Integer(), comment='项目进度条')
    
    ## 未运行：浅绿色， 运行中：蓝色  运行成功：深绿色  运行失败：红色
    prj_run_state_text = db.Column(db.String(255), comment='运行状态')       # 未运行，正在运行，运行成功，运行失败
    prj_run_error_text = db.Column(db.String(255), comment='报错信息')              # 运行报错的提示
    prj_note = db.Column(db.String(255), comment='备注')              # 运行报错的提示
class sjtu_carbon_emission_input1_region_msw_generation(db.Model):### 区域MSW产量
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c1_sjtu_name = db.Column(db.String(50), comment='名称')
    c2_sjtu_year = db.Column(db.String(50), comment='年份')
    c3_sjtu_ssp = db.Column(db.String(50), comment='ssp类别')
    c4_sjtu_msw = db.Column(db.Float(), comment='垃圾产量')
    c5_sjtu_landfill = db.Column(db.Float(), comment='填埋处理')
    c6_sjtu_incineration = db.Column(db.Float(), comment='焚烧处理')
    c7_sjtu_compost = db.Column(db.Float(), comment='生物处理')
    c8_3sjtu_recycling = db.Column(db.Float(), comment='回收处理')
class sjtu_carbon_emission_input2_region_info(db.Model):### 区域对应
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c1_sjtu_region_name = db.Column(db.String(50), comment='地区')
    c2_sjtu_region_en = db.Column(db.String(50), comment='对应')
class sjtu_carbon_emission_input3_regionfactor(db.Model):### 区域因子
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c1_sjtu_region_name = db.Column(db.String(50), comment='地区')
    c2_sjtu_region_level = db.Column(db.String(50), comment='地区级别')
    c3_sjtu_ssp = db.Column(db.String(50), comment='ssp类别')

    c4_incineration_ch4 = db.Column(db.Float(), comment='填埋CH4')
    c5_incineration_co2 = db.Column(db.Float(), comment='焚烧CO2')
    c6_incineration_n2o = db.Column(db.Float(), comment='焚烧N2O')

    c7_incineration_fuel_co2 = db.Column(db.Float(), comment='焚烧燃料CO2')
    c8_incineration_fuel_ch4 = db.Column(db.Float(), comment='焚烧燃料CH4')
    c9_incineration_fuel_n2o = db.Column(db.Float(), comment='焚烧燃料N2O')

    c10_incineration_electricity_co2 = db.Column(db.Float(), comment='焚烧发电CO2')

    c11_bio_compost_ch4 = db.Column(db.Float(), comment='堆肥CH4')
    c12_bio_compost_n2o = db.Column(db.Float(), comment='堆肥N2O')
    c13_bio_digest_ch4 = db.Column(db.Float(), comment='厌氧消化CH4') 

    c14_electricity_c2o = db.Column(db.Float(), comment='发电CO2')
    c15_ferterlizer_c2o = db.Column(db.Float(), comment='制肥CO2') 
    c16_recycle_c2o = db.Column(db.Float(), comment='回收CO2')  
class sjtu_carbon_emission_input4_region_detail(db.Model):### 区域详细信息
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    c1_sjtu_district = db.Column(db.String(50), comment='地区')
    c2_sjtu_en_name = db.Column(db.String(50), comment='英文')
    c3_short_written = db.Column(db.String(50), comment='简写')
    c4_belong_place = db.Column(db.String(50), comment='所属区域')
class sjtu_carbon_emission_output1_carbon_emission_result(db.Model):### 碳排放结果
    ####### 一般性字段
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prj_name = db.Column(db.String(255), nullable=False, comment='项目名')
    d_insert_t = db.Column(db.String(50), comment='导入时间')   # 数据导入时间

    a1_sjtu_name = db.Column(db.String(50), comment='名称')
    a2_sjtu_year = db.Column(db.String(50), comment='年份')
    a3_sjtu_ssp = db.Column(db.String(50), comment='ssp类别')
    a4_sjtu_msw = db.Column(db.Float(), comment='垃圾产量')

    '''
    填埋处理    焚烧处理    生物处理    回收处理    填埋排放    焚烧排放   
     焚烧净排    生物排放    生物净排    总排放   总净排放    填埋CH4   焚烧CO2   
     焚烧N2O   焚烧燃料CO2 焚烧发电CO2 堆肥CH4   堆肥N2O   
     厌氧消化CH4 发电CO2   制肥CO2   回收CO2
    '''
    e0 = db.Column(db.Float(), comment='填埋处理')
    e1 = db.Column(db.Float(), comment='焚烧处理')
    e2 = db.Column(db.Float(), comment='生物处理')
    e3 = db.Column(db.Float(), comment='回收处理')
    e4 = db.Column(db.Float(), comment='填埋排放')
    e5 = db.Column(db.Float(), comment='焚烧排放')

    e6 = db.Column(db.Float(), comment='焚烧净排')
    e7 = db.Column(db.Float(), comment='生物排放')
    e8 = db.Column(db.Float(), comment='生物净排')
    e9 = db.Column(db.Float(), comment='总排放')
    e10 = db.Column(db.Float(), comment='总净排放')
    e11 = db.Column(db.Float(), comment='填埋CH4')
    e12 = db.Column(db.Float(), comment='焚烧CO2')

    e13 = db.Column(db.Float(), comment='焚烧N2O')
    e14 = db.Column(db.Float(), comment='焚烧燃料CO2')
    e15 = db.Column(db.Float(), comment='焚烧发电CO2')
    e16 = db.Column(db.Float(), comment='堆肥CH4')
    e17 = db.Column(db.Float(), comment='堆肥N2O')

    e18 = db.Column(db.Float(), comment='厌氧消化CH4')
    e19 = db.Column(db.Float(), comment='发电CO2')
    e20 = db.Column(db.Float(), comment='制肥CO2')
    e21 = db.Column(db.Float(), comment='回收CO2')


