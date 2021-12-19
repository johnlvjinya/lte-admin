#!/usr/bin/env python
# coding: utf-8

# In[1]:


# 导入模块
import math
import xlsxwriter
import collections
import numpy as np
import pandas as pd
from ProjectState import ProjectState
from ortools.linear_solver import pywraplp
from datetime import datetime, date, time, timedelta
from pandas._libs.tslibs.timestamps import Timestamp
from docplex.cp.model import CpoModel, CpoStepFunction, INTERVAL_MAX


# In[2]:


# # 获取命令行参数
# ####################################################################################flask后端-注释开始
import sys
import command as tc
cmd_arg = tc.Argument(sys.argv)

prj_name = "泡罩专属-勿删"
start_run_time = cmd_arg.get_value("start_run_time")
start_run_period = cmd_arg.get_value("start_run_period")
solve_max_time = int(cmd_arg.get_value("solve_max_time"))
dataFile = 'templates/dw_cy/paozhao_schedule/algorithm/泡罩专属-勿删-算法数据导出.xlsx'# 排产数据文件
resultFile = 'templates/dw_cy/paozhao_schedule/algorithm/智能排产结果.xlsx' # 排产结果文件


startTime = datetime.strptime(start_run_time, '%Y-%m-%dT%H:%M') # 临时测试
period = 1/60
maxDays = int(start_run_period)                # 排产最大时长(单位天），次选100
maxValue = int(maxDays*24/period)              # 变量最大值
# ####################################################################################本地调试-注释结束


##################################################################################本地调试-注释开始
# prj_name = "泡罩专属-勿删"                         # 排产项目名称
# dataFile = '泡罩专属-勿删-算法数据导出.xlsx'   # 排产数据文件
# resultFile = '智能排产结果.xlsx'               # 排产结果文件
# startTime = datetime.strptime('2021/10/27 8:00', '%Y/%m/%d %H:%M') # 指定排产开始时间
# maxDays = 100                           # 排产最大时长(单位天）
# period = 1/60                           # 时间最小粒度(单位小时)
# maxValue = int(maxDays*24/period)       # 变量最大值，整型变量加范围，是否速度更快
# solve_max_time = 600                    # 最大运行时长(单位秒）
###################################################################################本地调试-注释结束


# In[3]:


# 全局变量定义
WorkType = collections.namedtuple('WorkType', 'workNo parentWorkNo fromSheet area resources orderNo productShort productNo quantity deliveryDate shortPart availableTime priority parentNo childNo partName capacity groupName groupNumber managerNumber qualifyNumber deviceTypes deviceNums duration minMoveTime maxMoveTime constraintType isFixed fixTime workState beginTime endTime') # 定义工作类型
allWorks = {}                                 # 记录所有工作
allPersons = {}                               # 记录所有人员
allTasks = {}                                 # 记录所有Interval变量
choiceTasks = {}                              # 记录产线可选Interval变量
resourceTasks = collections.defaultdict(list) # 记录产线Interval变量
personTasks = collections.defaultdict(list)   # 记录总人数Interval变量
managerTasks = collections.defaultdict(list)  # 记录班组长Interval变量
qualifyTasks = collections.defaultdict(list)  # 记录操机手Interval变量
deviceTasks = collections.defaultdict(list)   # 记录设备类型Interval变量
resourcePersonTasks = collections.defaultdict(list) # 记录产线Interval变量和人数
mdl = CpoModel()                              # 定义求解器
projectState = ProjectState(prj_name)         # 更新项目状态对象


# In[4]:


# 日期变量定义
weekday = {'星期一':0, '星期二':1, '星期三':2, '星期四':3, '星期五':4, '星期六':5, '星期日':6}
nighthours = [0, 1, 2, 3, 4, 5, 6, 7]  # 放在前一天晚上的小时，而不是第二天开始
priorities = ['紧急', '重要', '普通', '']   # 订单优先级

# 读取订单信息
orderTable = pd.read_excel(dataFile, '客户订单', keep_default_na=False)
orderTable = orderTable.sort_values(['订单交期'])

# 读取工单信息
sheetTable = pd.read_excel(dataFile, '客户工单', keep_default_na=False)
sheetTable = sheetTable.sort_values(['预计完工日'])

# 读取工艺路线
processTable = pd.read_excel(dataFile, '工艺路线', keep_default_na=False)

# 读取人员
personTable = pd.read_excel(dataFile, '人员', keep_default_na=False)
personTable = personTable.sort_values(['优先级'], ascending=False)
absentTable = pd.read_excel(dataFile, '请假', keep_default_na=False)

# 读取设备
deviceTable = pd.read_excel(dataFile, '设备', keep_default_na=False)

# 读取产品BOM和物料信息
bomTable = pd.read_excel(dataFile, '产品BOM', keep_default_na=False)
materialTable = pd.read_excel(dataFile, '物料', keep_default_na=False)

# 读取生产日历
calendarTable = pd.read_excel(dataFile, '生产日历', keep_default_na=False)
calendarTable = calendarTable.sort_values(['优先级'])

# 读取出勤模式
timeMode = {}
timeTable = pd.read_excel(dataFile, '出勤模式', keep_default_na=False)
for row, mode in timeTable.iterrows():
    timeMode[mode['出勤模式']] = mode['工作时间']


# In[5]:


# 获取日期
def getDate(anyDate):
    if isinstance(anyDate, Timestamp):
        return anyDate.to_pydatetime().date()
    elif isinstance(anyDate, datetime):
        return anyDate.date()
    elif isinstance(anyDate, str):
        anyDate = anyDate.strip()
        if ' ' in anyDate:
            anyDate = anyDate[:anyDate.find(' ')]
        if '-' in anyDate:
            return date(*map(int, anyDate.split('-')))
        else:
            return date(*map(int, anyDate.split('/')))

# 获取考勤时间范围
def getWorkTime(workMode):
    result = ''
    for mode in workMode.split(';'):
        # 获取出勤模式
        if mode in timeMode.keys():
            mode = timeMode[mode]
        elif mode == '休假':
            mode = ''
        # 记录结果
        if result == '':
            result += mode
        else:
            result += ';' + mode
    return result

# 获取资源的生产日历：resource资源名称
def getResourceCalendar(resource):
    results = {}
    startDay = startTime.date()
    if startTime.hour in nighthours: # 凌晨排在前一天晚上
        startDay -= timedelta(days=1)

    for i in range(maxDays):
        # 获取每一天
        everyday = startDay + timedelta(days=i)
        week = everyday.weekday()
        results[everyday] = ''
        # 遍历生产日历
        for row, calendar in calendarTable.iterrows():
            if calendar['资源'] == '*' or resource in calendar['资源'].split(';'):
                daysScope = calendar['出勤日期或星期']
                workMode = calendar['出勤模式或时间']
                if isinstance(daysScope, Timestamp) and everyday == daysScope.to_pydatetime().date():
                    results[everyday] = workMode
                elif isinstance(daysScope, datetime) and everyday == daysScope.date():
                    results[everyday] = workMode
                elif isinstance(daysScope, str):
                    daysScope = daysScope.split(';')
                    for scope in daysScope:
                        try:
                            span = scope.split('-')
                            if len(span) == 1:
                                if  '星期' in span[0] and week == weekday[span[0]]:
                                    results[everyday] = workMode
                                elif '星期' not in span[0] and everyday == getDate(span[0]):
                                    results[everyday] = workMode
                            elif len(span) > 1:
                                if '星期' in span[0] and week >= weekday[span[0]] and week <= weekday[span[1]]:
                                    results[everyday] = workMode
                                elif '星期' not in span[0] and everyday >= getDate(span[0]) and everyday <= getDate(span[1]):
                                    results[everyday] = workMode
                        except:
                            pass
        # 获取该日期的时间范围
        results[everyday] = getWorkTime(results[everyday])
    return results


# In[6]:


# 定义人员类
class Person:
    # 构造函数，groupName人员区域
    def __init__(self, groupName):
        self.groupName = groupName
        self.teamPersonSeris = {}
        self.teamManagerSeris = {}
        self.teamQualifySeris = {}
        self.personSeris = np.zeros(round(maxDays*24/period), dtype=int)
        self.managerSeris = np.zeros(round(maxDays*24/period), dtype=int)
        self.qualifySeris = np.zeros(round(maxDays*24/period), dtype=int)
        if startTime.hour in nighthours: # 凌晨排在前一天晚上
            startDay = -1
        else:
            startDay = 0

        # 获取每个班组的时间序列，班组然后相加
        for row, team in personTable.iterrows():
            if team['人员区域'] == groupName:
                # 切换周期
                switchDate = getDate(team['切换起始时间'])
                switchCycle = team['切换周期']
                self.teamPersonSeris[team['班组']] = np.zeros(round(maxDays*24/period), dtype=int)
                self.teamManagerSeris[team['班组']] = np.zeros(round(maxDays*24/period), dtype=int)
                self.teamQualifySeris[team['班组']] = np.zeros(round(maxDays*24/period), dtype=int)
                for day in range(startDay, startDay+maxDays):
                    # 白班夜班自动切换
                    if team['班次'] == '夜班':
                        if switchDate is not None and switchCycle > 0:
                            if (((startTime.date() - switchDate).days + day) // switchCycle) % 2 == 0:
                                beginTime = datetime.combine(startTime+timedelta(days=day), time(20, 0))
                                endTime = datetime.combine(startTime+timedelta(days=day+1), time(8, 0))
                            else:
                                beginTime = datetime.combine(startTime+timedelta(days=day), time(8, 0))
                                endTime = datetime.combine(startTime+timedelta(days=day), time(20, 0))
                        else:
                            beginTime = datetime.combine(startTime+timedelta(days=day), time(20, 0))
                            endTime = datetime.combine(startTime+timedelta(days=day+1), time(8, 0))
                    else:
                        if switchDate is not None and switchCycle > 0:
                            if (((startTime.date() - switchDate).days + day) // switchCycle) % 2 == 0:
                                beginTime = datetime.combine(startTime+timedelta(days=day), time(8, 0))
                                endTime = datetime.combine(startTime+timedelta(days=day), time(20, 0))
                            else:
                                beginTime = datetime.combine(startTime+timedelta(days=day), time(20, 0))
                                endTime = datetime.combine(startTime+timedelta(days=day+1), time(8, 0))
                        else:
                            beginTime = datetime.combine(startTime+timedelta(days=day), time(8, 0))
                            endTime = datetime.combine(startTime+timedelta(days=day), time(20, 0))
                    # 设置时间序列
                    beginIndex = 0
                    if beginTime > startTime:
                        beginIndex = round((beginTime - startTime).total_seconds()/(3600*period))
                    endIndex = 0
                    if endTime > startTime:
                        if  endTime < startTime+timedelta(days=maxDays):
                            endIndex = round((endTime - startTime).total_seconds()/(3600*period))
                        else:
                            endIndex = round(maxDays*24/period)
                    self.teamPersonSeris[team['班组']][beginIndex:endIndex] = team['合计人数']
                    numbers = {'超强':3, '较强':2, '普通':1, '':1}
                    self.teamManagerSeris[team['班组']][beginIndex:endIndex] = team['班组长人数']*numbers[team['能力标签']]
                    self.teamQualifySeris[team['班组']][beginIndex:endIndex] = team['操机手人数']
                self.personSeris += self.teamPersonSeris[team['班组']]
                self.managerSeris += self.teamManagerSeris[team['班组']]
                self.qualifySeris += self.teamQualifySeris[team['班组']]

        # 针对缺勤人员减1
        for row, absent in absentTable.iterrows():
            if absent['人员区域'] == groupName:
                # 获取缺勤起始范围
                beginTime = datetime.strptime(absent['请假开始时间'], '%Y/%m/%d %H:%M')
                endTime = datetime.strptime(absent['请假结束时间'], '%Y/%m/%d %H:%M')
                beginIndex = 0
                if beginTime > startTime:
                    beginIndex = round((beginTime - startTime).total_seconds()/(3600*period))
                endIndex = 0
                if endTime > startTime:
                    if  endTime < startTime+timedelta(days=maxDays):
                        endIndex = round((endTime - startTime).total_seconds()/(3600*period))
                    else:
                        endIndex = round(maxDays*24/period)
                # 缺勤人数减1
                if '是' in absent['是否班组长']:
                    numbers = {'超强':3, '较强':2, '普通':1, '':1}
                    managerNum = numbers[absent['能力标签']]
                    if absent['班组'] in self.teamManagerSeris:
                        self.teamManagerSeris[absent['班组']][beginIndex:endIndex] -= managerNum
                    self.managerSeris[beginIndex:endIndex] -= managerNum
                else:
                    if absent['班组'] in self.teamPersonSeris:
                        self.teamPersonSeris[absent['班组']][beginIndex:endIndex] -= 1
                    self.personSeris[beginIndex:endIndex] -= 1
                    if '是' in absent['是否操机手']:
                        if absent['班组'] in self.teamQualifySeris:
                            self.teamQualifySeris[absent['班组']][beginIndex:endIndex] -= 1
                        self.qualifySeris[beginIndex:endIndex] -= 1


# In[7]:


# 定义设备类
class Device:
    # 构造函数，name设备类型
    def __init__(self, deviceType):
        self.deviceType = deviceType
        self.timeSeris = np.zeros(round(maxDays*24/period), dtype=int)
        
        # 获取每个设备的时间序列，然后相加
        for row, device in deviceTable.iterrows():
            if device['设备类型'] == deviceType and device['设备状态'] != '报废':
                deviceCalendar = getResourceCalendar(device['设备名称'])
                deviceSeris = np.zeros(round(maxDays*24/period), dtype=int)
                for day in deviceCalendar:
                    workMode = deviceCalendar[day]
                    if workMode != '':
                        for timeRange in workMode.split(';'):
                            # 提取时间范围
                            timeRange = timeRange.split('-')
                            # 起始时间
                            beginHour, beginMinute = map(int, timeRange[0].split(':'))
                            if beginHour == 24: beginHour = 0
                            if beginHour in nighthours: # 凌晨排在前一天晚上
                                beginTime = datetime.combine(day+timedelta(days=1), time(beginHour, beginMinute))
                            else:
                                beginTime = datetime.combine(day, time(beginHour, beginMinute))
                            beginIndex = 0
                            if beginTime > startTime:
                                beginIndex = round((beginTime - startTime).total_seconds()/(3600*period))
                            # 结束时间
                            endHour, endMinute = map(int, timeRange[1].split(':'))
                            if endHour == 24: endHour = 0
                            if endHour in nighthours: # 凌晨排在前一天晚上
                                endTime = datetime.combine(day+timedelta(days=1), time(endHour, endMinute))
                            else:
                                endTime = datetime.combine(day, time(endHour, endMinute))
                            endIndex = 0
                            if endTime > startTime:
                                if  endTime < startTime+timedelta(days=maxDays):
                                    endIndex = round((endTime - startTime).total_seconds()/(3600*period))
                                else:
                                    endIndex = round(maxDays*24/period)
                            # 设置时间序列
                            deviceSeris[beginIndex:endIndex] = 1
                self.timeSeris += deviceSeris


# In[8]:


# 工单工作
for row1, work in sheetTable.iterrows():
    # 针对每个订单读取工单信息
    for row2, process in processTable[processTable['子料号']==work['生产料号']].iterrows():
        workNo = work['单号']
        parentWorkNo = work['母工单单号']
        area = process['区域']
        resources = str(process['产线'])
        orderNo = work['参考原始单号']
        productShort = process['产品编号'][1:6]
        productNo = process['产品编号']
        quantity = work['生产数量']
        priority = ''
        parentNo = process['父料号']
        childNo = process['子料号']
        partName = process['品名']
        groupName = process['人员区域']
        deviceTypes = process['设备类型']
        deviceNums = process['设备数量']
        constraintType = process['约束类型']

        # 寻找父工单
        if parentWorkNo == '' and orderNo != '':
            for row, tmpWork in sheetTable.iterrows():
                if tmpWork['参考原始单号'] == orderNo and tmpWork['生产料号'] == parentNo:
                    parentWorkNo = tmpWork['单号']
                    break
        
        # 订单交期
        try:
            deliveryDate = datetime.combine(getDate(work['预计完工日']), time(17))
            deliveryDate = round((deliveryDate-startTime).total_seconds()/(3600*period))
        except:
            deliveryDate = maxValue

        # 标准产能
        capacity = str(process['标准产能']).lower()
        if '||' in capacity:
            duration = []
            for everyone in capacity.split('||'): 
                if 'pcs/h' in everyone:
                    duration.append(round(quantity/float(everyone[:everyone.find('pcs/h')])/period))
                elif 'h' in everyone:
                    duration.append(round(float(everyone[:everyone.find('h')])/period))
        elif 'pcs/h' in capacity:
            duration = round(quantity/float(capacity[:capacity.find('pcs/h')])/period)
        elif 'h' in capacity:
            duration = round(float(capacity[:capacity.find('h')])/period)
        else:
            continue

        # 计划人数
        planNumber = process['计划人数']
        if isinstance(planNumber, str) and '||' in planNumber:
            groupNumber = []
            for everyone in planNumber.split('||'):
                groupNumber.append(int(everyone))
        else:
            groupNumber = int(planNumber)
        
        # 班组长人数
        try:
            managerNumber = int(process['班组长人数'])
        except:
            managerNumber = 0

        # 操机手人数
        try:
            qualifyNumber = int(process['操机手人数'])
        except:
            qualifyNumber = 0

        # 最小排队时间，含非工作时间
        minMoveTime = process['转移时间下限']
        if isinstance(minMoveTime, str) and 'h' in minMoveTime:
            minMoveTime = round(float(minMoveTime[:minMoveTime.find('h')])/period)
        elif isinstance(minMoveTime, str) and 'm' in minMoveTime:
            minMoveTime = round(float(minMoveTime[:minMoveTime.find('m')])/(60*period))
        else:
            minMoveTime = 0

        # 最大排队时间，含非工作时间
        maxMoveTime = process['转移时间上限']
        if isinstance(maxMoveTime, str) and 'h' in maxMoveTime:
            maxMoveTime = round(float(maxMoveTime[:maxMoveTime.find('h')])/period)
        elif isinstance(maxMoveTime, str) and 'm' in maxMoveTime:
            maxMoveTime = round(float(maxMoveTime[:maxMoveTime.find('m')])/(60*period))
        else:
            maxMoveTime = 0

        allWorks[workNo] = WorkType(workNo, parentWorkNo, True, area, resources, orderNo, productShort, productNo, quantity, deliveryDate, '', 0, priority, parentNo, childNo, partName, capacity, groupName, groupNumber, managerNumber, qualifyNumber, deviceTypes, deviceNums, duration, minMoveTime, maxMoveTime, constraintType, False, '', '未开工', 0, 0)


# In[9]:


# 订单工作
for row1, order in orderTable.iterrows():
    # 过滤掉不纳入和已完成订单
    if order['是否纳入计划'] == '否':
        continue

    # 针对每个订单读取工单信息
    for row2, process in processTable[processTable['产品编号']==order['产品编号']].iterrows():
        workNo = '%s_%s_%s_%s' % (order['订单号'], process['子料号'], order['订单数量'], order['订单交期'])
        parentWorkNo = '%s_%s_%s_%s' % (order['订单号'], process['父料号'], order['订单数量'], order['订单交期'])
        area = process['区域']
        resources = str(process['产线'])
        orderNo = order['订单号']
        productShort = order['快捷编号']
        productNo = order['产品编号']
        quantity = order['订单数量']
        priority = order['订单优先级']
        parentNo = process['父料号']
        childNo = process['子料号']
        partName = process['品名']
        groupName = process['人员区域']
        deviceTypes = process['设备类型']
        deviceNums = process['设备数量']
        constraintType = process['约束类型']

        # 订单交期
        try:
            deliveryDate = datetime.combine(getDate(order['订单交期']), time(17))
            deliveryDate = round((deliveryDate-startTime).total_seconds()/(3600*period))
        except:
            deliveryDate = maxValue

        # 预计到货时间
        shortPart = ''
        availableTime = 0
        shortParts = order['缺货料号']
        if isinstance(shortParts, str) and shortParts != '':
            for i, eachPart in enumerate(shortParts.split('&&')):
                for row3, hasPart in bomTable[bomTable['父料号']==childNo].iterrows():
                    if hasPart['子料号'] == eachPart:
                        # 记录缺货料号
                        if shortPart == '':
                            shortPart += eachPart
                        else:
                            shortPart += ';' + eachPart

                        # 记录最晚到货时间
                        availableTimes = order['预计到货时间']
                        if isinstance(availableTimes, str) and availableTimes != '':
                            availableTimes = availableTimes.split('&&')
                            if len(availableTimes) > i:
                                try:
                                    tmpAvailableTime = datetime.strptime(availableTimes[i]+' 8:00', '%Y/%m/%d %H:%M')
                                    tmpAvailableTime = round((tmpAvailableTime-startTime).total_seconds()/(3600*period))
                                    if tmpAvailableTime > availableTime:
                                        availableTime = tmpAvailableTime
                                except:
                                    pass
                        elif isinstance(availableTimes, Timestamp) and i == 0:
                            availableTime = round((availableTimes.to_pydatetime()+timedelta(hours=8)-startTime).total_seconds()/(3600*period))
                        elif isinstance(availableTimes, datetime) and i == 0:
                            availableTime = round((availableTimes+timedelta(hours=8)-startTime).total_seconds()/(3600*period))
                            
        # 标准产能
        capacity = str(process['标准产能']).lower()
        if '||' in capacity:
            duration = []
            for everyone in capacity.split('||'): 
                if 'pcs/h' in everyone:
                    duration.append(round(quantity/float(everyone[:everyone.find('pcs/h')])/period))
                elif 'h' in everyone:
                    duration.append(round(float(everyone[:everyone.find('h')])/period))
        elif 'pcs/h' in capacity:
            duration = round(quantity/float(capacity[:capacity.find('pcs/h')])/period)
        elif 'h' in capacity:
            duration = round(float(capacity[:capacity.find('h')])/period)
        else:
            continue

        # 计划人数
        planNumber = process['计划人数']
        if isinstance(planNumber, str) and '||' in planNumber:
            groupNumber = []
            for everyone in planNumber.split('||'):
                groupNumber.append(int(everyone))
        else:
            groupNumber = int(planNumber)
        
        # 班组长人数
        try:
            managerNumber = int(process['班组长人数'])
        except:
            managerNumber = 0

        # 操机手人数
        try:
            qualifyNumber = int(process['操机手人数'])
        except:
            qualifyNumber = 0

        # 最小排队时间，含非工作时间
        minMoveTime = process['转移时间下限']
        if isinstance(minMoveTime, str) and 'h' in minMoveTime:
            minMoveTime = round(float(minMoveTime[:minMoveTime.find('h')])/period)
        elif isinstance(minMoveTime, str) and 'm' in minMoveTime:
            minMoveTime = round(float(minMoveTime[:minMoveTime.find('m')])/(60*period))
        else:
            minMoveTime = 0

        # 最大排队时间，含非工作时间
        maxMoveTime = process['转移时间上限']
        if isinstance(maxMoveTime, str) and 'h' in maxMoveTime:
            maxMoveTime = round(float(maxMoveTime[:maxMoveTime.find('h')])/period)
        elif isinstance(maxMoveTime, str) and 'm' in maxMoveTime:
            maxMoveTime = round(float(maxMoveTime[:maxMoveTime.find('m')])/(60*period))
        else:
            maxMoveTime = 0

        allWorks[workNo] = WorkType(workNo, parentWorkNo, False, area, resources, orderNo, productShort, productNo, quantity, deliveryDate, shortPart, availableTime, priority, parentNo, childNo, partName, capacity, groupName, groupNumber, managerNumber, qualifyNumber, deviceTypes, deviceNums, duration, minMoveTime, maxMoveTime, constraintType, False, '', '未开工', 0, 0)


# In[10]:


# 定义求解器区间变量
for key in allWorks:
    work = allWorks[key]
    if '||' in work.resources:
        choice_vars = []
        for resource in work.resources.split('||'):
            if isinstance(work.duration, list):
                for i, item in enumerate(work.duration):
                    if work.isFixed:
                        interval = mdl.interval_var(size=item, start=work.fixedTime, optional=True)
                    elif work.availableTime > 0:
                        interval = mdl.interval_var(size=item, start=(work.availableTime, INTERVAL_MAX), optional=True)
                    else:
                        interval = mdl.interval_var(size=item, optional=True)
                    choice_vars.append(interval)
                    resourceTasks[resource].append((work, interval))
                    if work.groupNumber[i] > 0:
                        personTasks[work.groupName].append((interval, work.groupNumber[i]))
                        resourcePersonTasks[resource].append((interval, work.groupNumber[i]))
            else:
                if work.isFixed:
                    interval = mdl.interval_var(size=work.duration, start=work.fixedTime, optional=True)
                elif work.availableTime > 0:
                    interval = mdl.interval_var(size=work.duration, start=(work.availableTime, INTERVAL_MAX), optional=True)
                else:
                    interval = mdl.interval_var(size=work.duration, optional=True)
                choice_vars.append(interval)
                resourceTasks[resource].append((work, interval))
                if work.groupNumber > 0:
                    resourcePersonTasks[resource].append((interval, work.groupNumber))
        job = mdl.interval_var()
        mdl.add(mdl.alternative(job, choice_vars))
        allTasks[key] = job
        choiceTasks[key] = choice_vars
        if not isinstance(work.duration, list) and work.groupNumber > 0:
            personTasks[work.groupName].append((job, work.groupNumber))
        if work.managerNumber > 0:
            managerTasks[work.groupName].append((job, work.managerNumber))
        if work.qualifyNumber > 0:
            qualifyTasks[work.groupName].append((job, work.qualifyNumber))
        if len(work.deviceTypes) > 0:
            deviceNums = work.deviceNums.split('&&')
            for i, deviceType in enumerate(work.deviceTypes.split('&&')):
                try:
                    deviceTasks[deviceType].append((job, int(deviceNums[i])))
                except:
                    pass             
    else:
        if isinstance(work.duration, list):
            choice_vars = []
            for i, item in enumerate(work.duration):
                if work.isFixed:
                    interval = mdl.interval_var(size=item, start=work.fixedTime, optional=True)
                elif work.availableTime > 0:
                    interval = mdl.interval_var(size=item, start=(work.availableTime, INTERVAL_MAX), optional=True)
                else:
                    interval = mdl.interval_var(size=item, optional=True)
                choice_vars.append(interval)
                resourceTasks[work.resources].append((work, interval))
                if work.groupNumber[i] > 0:
                    personTasks[work.groupName].append((interval, work.groupNumber[i]))
                    resourcePersonTasks[work.resources].append((interval, work.groupNumber[i]))
            job = mdl.interval_var()
            mdl.add(mdl.alternative(job, choice_vars))
            allTasks[key] = job
            choiceTasks[key] = choice_vars
            if work.managerNumber > 0:
                managerTasks[work.groupName].append((job, work.managerNumber))
            if work.qualifyNumber > 0:
                qualifyTasks[work.groupName].append((job, work.qualifyNumber))
            if len(work.deviceTypes) > 0:
                deviceNums = work.deviceNums.split('&&')
                for i, deviceType in enumerate(work.deviceTypes.split('&&')):
                    try:
                        deviceTasks[deviceType].append((job, int(deviceNums[i])))
                    except:
                        pass
        else:
            if work.isFixed:
                interval = mdl.interval_var(size=work.duration, start=work.fixedTime)
            elif work.availableTime > 0:
                interval = mdl.interval_var(size=work.duration, start=(work.availableTime, INTERVAL_MAX))
            else:
                interval = mdl.interval_var(size=work.duration)
            resourceTasks[work.resources].append((work, interval))
            allTasks[key] = interval
            choiceTasks[key] = interval
            if work.groupNumber > 0:
                personTasks[work.groupName].append((interval, work.groupNumber))
                resourcePersonTasks[work.resources].append((interval, work.groupNumber))
            if work.managerNumber > 0:
                managerTasks[work.groupName].append((interval, work.managerNumber))
            if work.qualifyNumber > 0:
                qualifyTasks[work.groupName].append((interval, work.qualifyNumber))
            if len(work.deviceTypes) > 0:
                deviceNums = work.deviceNums.split('&&')
                for i, deviceType in enumerate(work.deviceTypes.split('&&')):
                    try:
                        deviceTasks[deviceType].append((interval, int(deviceNums[i])))
                    except:
                        pass


# In[11]:


# 构建生产日历约束
for resource in resourceTasks:
    # 获取生产日历
    resource_calendar = CpoStepFunction()
    resource_calendar.set_value(0, maxValue, 0)
    calendar = getResourceCalendar(resource)
    for day in calendar:
        workMode = calendar[day]
        if workMode != '':
            for timeRange in workMode.split(';'):
                # 提取时间范围
                timeRange = timeRange.split('-')
                # 起始时间
                beginHour, beginMinute = map(int, timeRange[0].split(':'))
                if beginHour == 24: beginHour = 0
                if beginHour in nighthours: # 凌晨排在前一天晚上
                    beginTime = datetime.combine(day+timedelta(days=1), time(beginHour, beginMinute))
                else:
                    beginTime = datetime.combine(day, time(beginHour, beginMinute))
                beginIndex = 0
                if beginTime > startTime:
                    beginIndex = round((beginTime - startTime).total_seconds()/(3600*period))
                # 结束时间
                endHour, endMinute = map(int, timeRange[1].split(':'))
                if endHour == 24: endHour = 0
                if endHour in nighthours: # 凌晨排在前一天晚上
                    endTime = datetime.combine(day+timedelta(days=1), time(endHour, endMinute))
                else:
                    endTime = datetime.combine(day, time(endHour, endMinute))
                endIndex = 0
                if endTime > startTime:
                    if  endTime < startTime+timedelta(days=maxDays):
                        endIndex = round((endTime - startTime).total_seconds()/(3600*period))
                    else:
                        endIndex = maxValue
                # 设置时间序列
                resource_calendar.set_value(beginIndex, endIndex, 100)

    # 设置每条产线的生产日历
    for work, interval in resourceTasks[resource]:
        interval.set_intensity(resource_calendar)
        mdl.add(mdl.forbid_start(interval, resource_calendar))
        mdl.add(mdl.forbid_end(interval, resource_calendar))


# In[12]:


# 构建顺序约束
for key in allWorks:
    work = allWorks[key]
    parentKey = work.parentWorkNo
    if work.parentNo != work.childNo and parentKey in allTasks.keys():
        childJob = allTasks[key]
        parentJob = allTasks[parentKey]
        if work.constraintType == '串行':
            mdl.add(mdl.end_before_start(childJob, parentJob, work.minMoveTime))
            if work.maxMoveTime > work.minMoveTime:
                mdl.add(mdl.start_before_end(parentJob, childJob, -work.maxMoveTime))
        else:
            mdl.add(mdl.start_before_start(childJob, parentJob, work.minMoveTime))
            mdl.add(mdl.end_before_end(childJob, parentJob, work.minMoveTime))
            if work.maxMoveTime > work.minMoveTime:
                mdl.add(mdl.start_before_start(parentJob, childJob, -work.maxMoveTime))


# In[13]:


# 构建排他约束
for resource in resourceTasks:
    intervals = [interval for work, interval in resourceTasks[resource]]
    sequence = mdl.sequence_var(intervals, list(range(len(intervals))))
    metrix = mdl.transition_matrix(len(intervals))
    for i,(work1, interval1) in enumerate(resourceTasks[resource]):
        for j,(work2, interval2) in enumerate(resourceTasks[resource]):
            if work1.productShort != work2.productShort:
                if '灌装' in resource:
                    metrix.set_value(i, j, int(8/period))
                else:
                    metrix.set_value(i, j, int(0.5/period))
            elif work1.productNo != work2.productNo:
                if '灌装' in resource:
                    metrix.set_value(i, j, int(4/period))
                else:
                    metrix.set_value(i, j, int(0.25/period))
    mdl.add(mdl.no_overlap(sequence, metrix, is_direct=True))


# In[14]:


# 构建总人数约束
for groupName in personTasks:
    if groupName in allPersons:
        person = allPersons[groupName]
    else:
        person = Person(groupName)
        allPersons[groupName] = person
    preNum = 0
    personLimit = mdl.step_at(0, 0)
    for i, number in enumerate(person.personSeris):
        if preNum > number:
            personLimit -= mdl.step_at(i, preNum - number)
        elif preNum < number:
            personLimit += mdl.step_at(i, number - preNum)
        preNum = number
    for task, need in personTasks[groupName]:
        personLimit -= mdl.pulse(task, need)
    mdl.add(personLimit >= 0)
        
# 构建班组长人数约束
for groupName in managerTasks:
    if groupName in allPersons:
        person = allPersons[groupName]
    else:
        person = Person(groupName)
        allPersons[groupName] = person
    preNum = 0
    managerLimit = mdl.step_at(0, 0)
    for i, number in enumerate(person.managerSeris):
        if preNum > number:
            managerLimit -= mdl.step_at(i, preNum - number)
        elif preNum < number:
            managerLimit += mdl.step_at(i, number - preNum)
        preNum = number
    for task, need in managerTasks[groupName]:
        managerLimit -= mdl.pulse(task, need)
    mdl.add(managerLimit >= 0)

# 构建操机手人数约束
for groupName in qualifyTasks:
    if groupName in allPersons:
        person = allPersons[groupName]
    else:
        person = Person(groupName)
        allPersons[groupName] = person
    preNum = 0
    qualifyLimit = mdl.step_at(0, 0)
    for i, number in enumerate(person.qualifySeris):
        if preNum > number:
            qualifyLimit -= mdl.step_at(i, preNum - number)
        elif preNum < number:
            qualifyLimit += mdl.step_at(i, number - preNum)
        preNum = number
    for task, need in qualifyTasks[groupName]:
        qualifyLimit -= mdl.pulse(task, need)
    mdl.add(qualifyLimit >= 0)


# In[15]:


# 构建设备并行约束
for device in deviceTasks:
    equipment = Device(device)
    preNum = 0
    deviceLimit = mdl.step_at(0, 0)
    for i, number in enumerate(equipment.timeSeris):
        if preNum > number:
            deviceLimit -= mdl.step_at(i, preNum - number)
        elif preNum < number:
            deviceLimit += mdl.step_at(i, number - preNum)
        preNum = number
    for task, need in deviceTasks[device]:
        deviceLimit -= mdl.pulse(task, need)
    mdl.add(deviceLimit >= 0)


# In[16]:


# 定义目标函数：超期时间最小
objectVars = []
for key in allWorks:
    work = allWorks[key]
    if work.fromSheet or work.parentNo == work.childNo:
        delayVar = mdl.integer_var(0, maxValue)
        endTime = mdl.end_of(allTasks[key])
        mdl.add(delayVar==mdl.conditional(endTime+work.minMoveTime>work.deliveryDate, endTime+work.minMoveTime-work.deliveryDate, 0))
#         mdl.add(mdl.if_then(endTime+work.minMoveTime>work.deliveryDate, delayVar==endTime+work.minMoveTime-work.deliveryDate))
#         mdl.add(mdl.if_then(endTime+work.minMoveTime<=work.deliveryDate, delayVar==0))
        objectVars.append(delayVar)

# 定义目标函数：最后完成时间最小
objectVars.extend([mdl.end_of(allTasks[key])*0.01 for key in allWorks if allWorks[key].parentNo == allWorks[key].childNo])
makespanVar = mdl.max([mdl.end_of(allTasks[key]) for key in allWorks if allWorks[key].parentNo == allWorks[key].childNo])
objectVars.append(makespanVar)

# 定义目标函数：同一产线的人数变动最小
for resource in resourcePersonTasks:
    needList = [mdl.presence_of(task)*need for task, need in resourcePersonTasks[resource]]
    objectVars.append(mdl.max(needList) - mdl.min(needList))
mdl.add(mdl.minimize(mdl.sum(objectVars)))


# In[17]:


# 求解并打印结果
projectState.dataComplete()
print('求解进行中，请耐心等待......最多15分钟，取决于订单数量和模型复杂度......')
msol = mdl.solve(TimeLimit=solve_max_time)
msol.print_solution()
status = msol.get_solve_status()
# 求解并打印结果
if status == 'Optimal' or status == 'Feasible':
    if status == 'Optimal':
        print('找到最优解，求解时间(秒):', msol.get_solve_time())
    else:
        print('找到可行解，求解时间(秒):', msol.get_solve_time())
    # 总延期时间和全部完工时间
    totalDelay = 0
    maxEnd = 0
    for key in allWorks:
        work = allWorks[key]
        if work.fromSheet or work.parentNo == work.childNo:
            beginIndex, endIndex, size = msol.get_value(allTasks[key])
            if endIndex+work.minMoveTime>work.deliveryDate:
                totalDelay += endIndex+work.minMoveTime-work.deliveryDate
            if endIndex > maxEnd:
                maxEnd = endIndex
    print('总延期时间: %.2f小时，全部完工时间：%s' % (totalDelay*period, startTime+timedelta(hours=maxEnd*period)))
    projectState.solveComplete(status, totalDelay*period, startTime+timedelta(hours=maxEnd*period), msol.get_solve_time())   
else:
    print('很遗憾，没找到可行解，建议扩大变量范围！')
    projectState.solveComplete(status, 0, startTime, msol.get_solve_time())


# In[18]:


# 记录排产结果
resultWorks = []
resourceWorks = collections.defaultdict(list)
if status == 'Optimal' or status == 'Feasible': 
    for row, key in enumerate(allWorks):
        # 开始和结束时间
        work = allWorks[key]
        beginIndex, endIndex, size = msol.get_value(allTasks[key])

        # 对应产线、人数和标准产能
        resources = work.resources            
        capacity = work.capacity
        groupNumber = work.groupNumber
        if key in choiceTasks.keys():
            if '||' in work.resources:
                for i, resource in enumerate(work.resources.split('||')):
                    if '||' in work.capacity:
                        myCapacities = work.capacity.split('||')
                        for j, item in enumerate(myCapacities):
                            if msol.get_var_solution(choiceTasks[key][i*len(myCapacities)+j]).is_present():
                                resources = resource            
                                capacity = item
                                groupNumber = work.groupNumber[j]
                                break
                    elif msol.get_var_solution(choiceTasks[key][i]).is_present():
                        resources = resource            
                        break
            elif '||' in work.capacity:
                for j, item in enumerate(work.capacity.split('||')):
                    if msol.get_var_solution(choiceTasks[key][j]).is_present():
                        capacity = item
                        groupNumber = work.groupNumber[j]
                        break

        # 记录数据
        result = WorkType(work.workNo, work.parentWorkNo, work.fromSheet, work.area, resources, work.orderNo, work.productShort, work.productNo, work.quantity, work.deliveryDate, work.shortPart, work.availableTime, work.priority, work.parentNo, work.childNo, work.partName, capacity, work.groupName, groupNumber, work.managerNumber, work.qualifyNumber, work.deviceTypes, work.deviceNums, work.duration, work.minMoveTime, work.maxMoveTime, work.constraintType, work.isFixed, work.fixTime, work.workState, beginIndex, endIndex)
        resultWorks.append(result)
        resourceWorks[resources].append(result)


# In[19]:


# 进行人员分配
workAssigns = collections.defaultdict(list)
teamAssigns = collections.defaultdict(list)
resourceAssigns = collections.defaultdict(list)
allPersons = {}
staffResults = {}
managerResults = {}
qualifyResults = {}
maxAssign = 7*24*60             # 最多安排几天，如1天、3天、7天、14天，建议7天
maxNumber = 0                   # 最大人数范围
if status == 'Optimal' or status == 'Feasible': 
    solver = pywraplp.Solver.CreateSolver('SCIP') # 定义SCIP求解器
    for work in resultWorks:
        if work.beginTime >= maxAssign:   
            continue
        if work.groupName in allPersons:
            person = allPersons[work.groupName]
        else:
            person = Person(work.groupName)
            allPersons[work.groupName] = person
        # 定义人数分配变量
        for team in person.teamPersonSeris:
            assign = []
            for i in range(maxAssign):
                maxPerson = min(int(person.teamPersonSeris[team][i]), work.groupNumber)
                maxNumber = max(maxPerson, maxNumber)
                if maxPerson > 0 and i >= work.beginTime and i < work.endTime:
                    assign.append(solver.IntVar(0, maxPerson, ''))
                else:
                    assign.append(0)
            workAssigns[work].append(assign)
            teamAssigns[work.groupName, team].append(assign)
            resourceAssigns[work.resources, team].append((work.beginTime, work.endTime, assign))
        # 添加工单人数分配约束
        for i in range(work.beginTime, min(maxAssign, work.endTime)):
            solver.Add(sum([assign[i] for assign in workAssigns[work]]) == work.groupNumber)
        # 添加工单人数不变约束
        for assign in workAssigns[work]:
            for i in range(work.beginTime+1, min(maxAssign, work.endTime)):
                if not isinstance(assign[i-1], int) and not isinstance(assign[i], int):
                        solver.Add(assign[i-1] == assign[i])
        # 添加工单人数换班后也不变约束
#         for assign in workAssigns[work]:
#             previous = None
#             for i in range(work.beginTime, min(maxAssign, work.endTime)):
#                 if not isinstance(assign[i], int):
#                     if previous is not None:
#                         solver.Add(previous == assign[i])
#                     previous = assign[i]
    # 添加每个班组的人数约束
    for groupName, team in teamAssigns:
        if groupName in allPersons:
            person = allPersons[groupName]
        else:
            person = Person(groupName)
            allPersons[groupName] = person
        for i in range(maxAssign):
            if person.teamPersonSeris[team][i] > 0:
                solver.Add(sum([assign[i] for assign in teamAssigns[groupName, team]]) <= int(person.teamPersonSeris[team][i]))
    # 定义目标函数，尽量少拆分
    objectVars = []
    for work in workAssigns:
        for assign in workAssigns[work]:
            for i in range(work.beginTime, min(maxAssign, work.endTime)):
                if not isinstance(assign[i], int):
                    boolAssign = solver.IntVar(0, 1, '')
                    solver.Add(boolAssign <= assign[i])
                    solver.Add(boolAssign*solver.infinity() >= assign[i])
                    objectVars.append(boolAssign)
#     # 定义目标函数，相同工单的白班和夜班尽量稳定
#     for work in workAssigns:
#         for assign in workAssigns[work]:
#             preEnd = None
#             need = False
#             for i in range(work.beginTime, min(maxAssign, work.endTime)):
#                 if not isinstance(assign[i], int):
#                     if need and preEnd is not None:
#                         absAssign = solver.IntVar(0, maxNumber, '')
#                         solver.Add(absAssign >= assign[i] - preEnd)
#                         solver.Add(absAssign >= preEnd - assign[i])
#                         objectVars.append(absAssign)
#                     preEnd = assign[i]
#                     need = False
#                 elif preEnd is not None:
#                     need = True
    # 定义目标函数，相同产线同一班次尽量稳定
    for resource,team in resourceAssigns:
        resourceAssigns[resource,team].sort(key=lambda item:item[0])
        preAssign = None
        preEndIndex = 0
        for beginIndex,endIndex,assign in resourceAssigns[resource,team]:
            if preAssign is not None and not isinstance(preAssign[preEndIndex-1], int) and not isinstance(assign[beginIndex], int):
                absAssign = solver.IntVar(0, maxNumber, '')
                solver.Add(absAssign >= assign[beginIndex] - preAssign[preEndIndex-1])
                solver.Add(absAssign >= preAssign[preEndIndex-1] - assign[beginIndex])
                objectVars.append(absAssign)
            preAssign = assign
            preEndIndex = min(maxAssign, endIndex)
    solver.Minimize(sum(objectVars))
    # 求解并打印结果
    print('人员分配求解进行中，请耐心等待......最多15分钟，取决于订单数量和模型复杂度......')
    solver.SetTimeLimit(solve_max_time*1000)
    staffStatus = solver.Solve()
    if staffStatus == pywraplp.Solver.OPTIMAL:
        print('人员分配找到最优解，求解时间(秒):', solver.wall_time()/1000)
    elif staffStatus == pywraplp.Solver.FEASIBLE:
        print('人员分配找到可行解，求解时间(秒):', solver.wall_time()/1000)
    else:
        print('很遗憾，没找到可行解，建议扩大搜索范围和时长！')
    # 记录人员分配结果
    if staffStatus == pywraplp.Solver.OPTIMAL or staffStatus == pywraplp.Solver.FEASIBLE:
        for work in resultWorks:
            if work.beginTime >= maxAssign:   
                continue
            if work.groupName in allPersons:
                person = allPersons[work.groupName]
            else:
                person = Person(work.groupName)
                allPersons[work.groupName] = person
            shift = {}
            begin = work.beginTime
            for i in range(work.beginTime, min(maxAssign, work.endTime)):
                isShift = False
                for team,assign in zip(person.teamPersonSeris.keys(), workAssigns[work]):
                    if not isinstance(assign[i], int):
                        number = assign[i].solution_value()
                        if number > 0:
                            if team in shift:
                                shift[team] = max(shift[team], number)
                            else:
                                shift[team] = number
                            if i == min(maxAssign, work.endTime)-1 or isinstance(assign[i+1], int):
                                isShift = True
                if isShift and len(shift) > 0:
                    shift = sorted(shift.items(), key=lambda item:item[1], reverse=True)
                    strShift = ','.join(['%s:%d人'%(key, value) for key,value in shift])
                    if work in staffResults:
                        staffResults[work] += '//' + strShift
                    else:
                        staffResults[work] = strShift
                        
                    # 进行班组长分配
                    assignManager = []
                    remainManager = work.managerNumber
                    for team,_ in shift:
                        if remainManager <= 0:
                            break
                        available = min(person.teamManagerSeris[team][begin:i+1])
                        if available >= remainManager:
                            assignManager.append('%s班组长'%team)
                            person.teamManagerSeris[team][begin:i+1] -= remainManager
                            remainManager = 0
                            break
                        elif available > 0:
                            assignManager.append('%s班组长'%team)
                            person.teamManagerSeris[team][begin:i+1] -= available
                            remainManager -= available
                    if work in managerResults:
                        managerResults[work] += '//' + ','.join(assignManager)
                    else:
                        managerResults[work] = ','.join(assignManager)
                        
                    # 进行操机手分配
                    assignQualify = []
                    remainQualify = work.qualifyNumber
                    for team,_ in shift:
                        if remainQualify <= 0:
                            break
                        available = min(person.teamQualifySeris[team][begin:i+1])
                        if available >= remainQualify:
                            assignQualify.append('%s操机手'%team)
                            person.teamQualifySeris[team][begin:i+1] -= remainQualify
                            remainQualify = 0
                            break
                        elif available > 0:
                            assignQualify.append('%s操机手'%team)
                            person.teamQualifySeris[team][begin:i+1] -= available
                            remainQualify -= available
                    if work in qualifyResults:
                        qualifyResults[work] += '//' + ','.join(assignQualify)
                    else:
                        qualifyResults[work] = ','.join(assignQualify)
                        
                    # 进入下一班次
                    shift = {}
                    begin = i+1


# In[20]:


# 递归获取每个物料的需求数量：quantity订单数量, productNo产品编号, parentNo父料号, childNo子料号, partRequire组成用量, partBase主件底数
def getBomRequire(quantity, productNo, parentNo, childNo, partRequire=1, partBase=1):
    if parentNo == None:
        for row, bom in bomTable[bomTable['子料号']==childNo].iterrows():
            parentNo = bom['父料号']
            partRequire = float(bom['组成用量'])
            partBase = float(bom['主件底数'])
            if parentNo == productNo:
                return quantity * partRequire / partBase
            else:
                return getBomRequire(quantity, productNo, None, parentNo) * partRequire / partBase
    else:
        if parentNo == productNo:
            return quantity * partRequire / partBase
        else:
            return getBomRequire(quantity, productNo, None, parentNo) * partRequire / partBase


# In[21]:


# 保存排产结果到Excel
if status == 'Optimal' or status == 'Feasible': 
    # 创建表格
    excel = xlsxwriter.Workbook(resultFile, {'nan_inf_to_errors': True})
    style_blue = excel.add_format({'font_size':9, 'bold':False, 'border':1, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#E8F6F6', 'text_wrap': True})
    style_green = excel.add_format({'font_size':9, 'bold':False, 'border':1, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#7FFF7F', 'text_wrap': True})
    style_red = excel.add_format({'font_size':9, 'bold':False, 'border':1, 'align': 'center', 'valign': 'vcenter', 'fg_color': '#FFC0C0', 'text_wrap': True})

    # 写入工单计划标题
    sheet = excel.add_worksheet('工单计划')
    sheet.write_row(0, 0, ['工单编号', '区域', '产线', '订单号', '快捷编号', '产品编号', '订单数量', '订单交期', '缺货料号', '预计到货时间', '订单优先级', '父料号', '子料号', '品名', '人员区域', '计划人数', '班组长人数', '操机手人数', '设备类型', '设备数量', '标准产能', '转移时间下限', '转移时间上限', '约束类型', '是否固定', '固定时间', '计划开始时间', '计划结束时间', '工单状态', '分配人员', '分配班组长', '分配操机手', '已完成数量', '实际开始时间', '实际结束时间'])
    # 写入工单计划数据
    for row, work in enumerate(resultWorks):
        # 开始和结束时间
        begin = startTime+timedelta(hours=work.beginTime*period)
        end = startTime+timedelta(hours=work.endTime*period)
        deliveryDate = (startTime+timedelta(hours=work.deliveryDate*period)).strftime('%Y/%m/%d')
        if work.availableTime > 0:
            availableTime = (startTime+timedelta(hours=work.availableTime*period)).strftime('%Y/%m/%d')
        else:
            availableTime = ''
        # 人员分配
        assignPerson, assignManager, assignQualify = '', '', ''
        if work in staffResults.keys():
            assignPerson = staffResults[work]
        if work in managerResults.keys():
            assignManager = managerResults[work]
        if work in qualifyResults.keys():
            assignQualify = qualifyResults[work]
        # Excel颜色变化
        if (work.fromSheet or work.parentNo == work.childNo) and work.endTime + work.minMoveTime > work.deliveryDate:
            style = style_red
        elif work.workState == '已完成':
            style = style_green
        else:
            style = style_blue
        sheet.write_row(row+1, 0, [work.workNo, work.area, work.resources, work.orderNo, work.productShort, work.productNo, work.quantity, deliveryDate, work.shortPart, availableTime, work.priority, work.parentNo, work.childNo, work.partName, work.groupName, work.groupNumber, work.managerNumber, work.qualifyNumber, work.deviceTypes, work.deviceNums, work.capacity, work.minMoveTime, work.maxMoveTime, work.constraintType, '是' if work.isFixed else '否', work.fixTime, begin.strftime('%Y/%m/%d %H:%M'), end.strftime('%Y/%m/%d %H:%M'), work.workState, assignPerson, assignManager, assignQualify, '', '', ''], style)

    # 插入物料核查标题
    sheet = excel.add_worksheet('物料核查')
    sheet.write_row(0, 0, ['元件料号', '品名', '发料单位'])
    for row, material in materialTable.iterrows():
        sheet.write_row(row+1, 0, [material['元件料号'], material['品名'], material['发料单位']])
    # 写入物料核查数据
    orderCount = {}     # 记录每个元件有多少张订单
    requireCount = {}   # 记录每个元件的累计需求
    resultWorks.sort(key=lambda work:work.beginTime)
    for work in resultWorks:
        begin = startTime+timedelta(hours=work.beginTime*period)
        # 根据BOM核查物料
        for row2, bom in bomTable[bomTable['父料号']==work.childNo].iterrows():
            part = bom['子料号']
            for row3, material in materialTable[materialTable['元件料号']==part].iterrows():
                # 计算需求数量
                require = getBomRequire(work.quantity, work.productNo, work.childNo, part, float(bom['组成用量']), float(bom['主件底数']))
                if str(bom['单位']).lower() == 'pcs':
                    require = math.ceil(require)
                # 计算库存可用量
                available = material['库存可用量']
                i=0
                while material.iloc[4+i*2] != '' and material.iloc[5+i*2] != '':
                    if begin >= datetime.combine(getDate(material.iloc[4+i*2]), time(hour=8)):
                        available += material.iloc[5+i*2]
                    i += 1
                # 统计每个元件有多少张订单
                if part in orderCount.keys():
                    orderCount[part] += 1
                else:
                    orderCount[part] = 1
                # 统计每个元件的累计需求量
                if part in requireCount.keys():
                    requireCount[part] += require
                else:
                    requireCount[part] = require
                remain = available - requireCount[part]
                if str(bom['单位']).lower() == 'pcs':
                    remain = int(remain)
                if remain < 0:
                    style = style_red
                else:
                    style = style_blue
                sheet.write_row(row3+1, orderCount[part]*5-2, [work.orderNo, work.productNo, require, begin.strftime('%Y/%m/%d %H:%M'), remain], style)
    # 插入物料核查标题
    if len(orderCount) == 0:
        sheet.write_row(0, 3,  ['订单号', '产品编号', '需求数量', '需求时间', '库存结余'])
    else:
        sheet.write_row(0, 3,  ['订单号', '产品编号', '需求数量', '需求时间', '库存结余'] * max(orderCount.values()))

    # 保存Excel文件，更新项目状态
    try:
        excel.close()      # 保存智能排产结果
        projectState.projectComplete(True)
    except:
        projectState.projectComplete(False)
else:
    print('很遗憾，没找到可行解，建议扩大变量范围！') 


# In[ ]:




