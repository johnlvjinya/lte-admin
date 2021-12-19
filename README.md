


##### 运行

```
python app.py
```

增加config.py

```
host = '101.133.238.216'
user = 'root'
password = '####'
port = '3306'
db = 'flask_lte_cy'

app_name = 'flask_lte_cy'

import sys,platform
current_system = platform.system()

if current_system is 'Windows':
    python = "python"
else:
    python = "python3"


```





##### 文件说明

```
/migrations
数据库迁移文件

/myjson
配置文件

/myutils
自己造的轮子

/prj_m_code
排产算法代码

/static
flask静态文件，包括js,css,image等

/templates
后端代码和模板文件

app.py
主程序入口

app_scheduler.py
定时任务

config.py
数据库等配置信息

```



##### 页面关键代码

```
templates/base
flask的基本extends模板

dw_cy
创元的项目

echarts
echarts可视化模板

gantt_dist
甘特图打包的文件

ljy_tb
flask后台表格，包括CURD和表格导入导出

login_out
登录登出模板

ite
ite模板

prj
排产项目

```

