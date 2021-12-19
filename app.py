
import os
import json
import config
import datetime
import pandas as pd
import myutils.db_one as mmp
import myutils.get_menu_list as mgml
from exts import db
from models import User
from urllib.parse import urlparse
from shutil import copytree
from werkzeug.utils import secure_filename          # 使用这个是为了确保filename是安全的
from flask import send_file, send_from_directory, json, jsonify, make_response,flash
from flask import Flask, render_template, request, redirect, Response, abort, session,url_for
from flask_login import UserMixin, login_user, logout_user, login_required, LoginManager, current_user



MOD = mmp.MysqlOneDatabase(host=config.host, port=int(config.port), user=config.user, password=config.password, db=config.db)

app = Flask(__name__)
app.config['SECRET_KEY'] = "dfdfdffdad"
app.jinja_env.auto_reload = True                    # 动态加载页面
app.config['TEMPLATE_AUTO_RELOAD'] =True  
app.config.update(
    SECRET_KEY='SeriouslydevelopedbyJailman11',
    SQLALCHEMY_DATABASE_URI="mysql+pymysql://{0}:{1}@{2}:{3}/{4}".format(config.user,config.password,config.host,int(config.port),config.db),
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    SQLALCHEMY_RECORD_QUERIES = True,
    SQLALCHEMY_POOL_SIZE = 1024,
    SQLALCHEMY_POOL_TIMEOUT = 90,
    SQLALCHEMY_POOL_RECYCLE = 3,
    SQLALCHEMY_MAX_OVERFLOW = 1024,
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(minutes=60*24),
)
db.init_app(app)
login_manager = LoginManager(app)
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'

from templates.ljy_tb.ljy_tb import ljy_tb
app.register_blueprint(ljy_tb, url_prefix='/ljy_tb')

from templates.prj.scheduling_projects.scheduling_projects import scheduling_projects
app.register_blueprint(scheduling_projects, url_prefix='/scheduling_projects')

from templates.prj.sjtu_carbon_emission.sjtu_carbon_emission import sjtu_carbon_emission
app.register_blueprint(sjtu_carbon_emission, url_prefix='/sjtu_carbon_emission')

# from templates.dw_cy.t100_echarts.t100_echarts import t100_echarts
# app.register_blueprint(t100_echarts, url_prefix='/t100_echarts')
# from templates.dw_cy.paozhao_schedule.paozhao_schedule import paozhao_schedule
# app.register_blueprint(paozhao_schedule, url_prefix='/paozhao_schedule')
# from templates.dw_cy.sql_note_list.sql_note_list import sql_note_list
# app.register_blueprint(sql_note_list, url_prefix='/sql_note_list')

from templates.echarts.demo_echarts.demo_echarts import demo_echarts
app.register_blueprint(demo_echarts, url_prefix='/demo_echarts')

from templates.auto_tb_bi.tb_sql.tb_sql import tb_sql
app.register_blueprint(tb_sql, url_prefix='/tb_sql')

@login_manager.user_loader
def load_user(userid):return User.query.get(int(userid))

@app.route("/")
def hello_world():
    return redirect('/file_path?file_path=lte/index.html')       # 'hello world'   # redirect('gannt_list')

@app.route("/index")
@login_required
def index():
    return redirect('/')       # 'hello world'   # redirect('gannt_list')

@app.route("/file_path") ## http://127.0.0.1:5001/gannt_render?file_name=schedule
@login_required
def file_path():
    print(current_user.__dict__)
    file_path = request.args.get('file_path')
    f_url = file_path.replace('.html', '')
    menu_dict = mgml.menu_dict('templates/base/base03_nav.html')
    print(f_url)
    if f_url in menu_dict.keys():
        ad = {
        'user_role':current_user.__dict__.get('role'),
        'menu'+menu_dict[f_url][1]:"menu-open",
        menu_dict[f_url][1]:"active",
        menu_dict[f_url][0]:"active",
        }
    else:
        ad = {}    
    return render_template(file_path, ad=ad)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is not None and user.verify_password(password):
            session.permanent = True
            login_user(user)
            return redirect('/')
        else:
            return render_template('login_out/login.html', reback='账号或密码错误！', app_name=config.app_name)
    else:
        return render_template('login_out/login.html', reback='', app_name=config.app_name)

@app.route("/logout", methods=["GET", "POST"])
def logout(): 
    logout_user()
    return render_template('login_out/logout.html', reback='')

@app.route("/copy_folder", methods=["GET", "POST"])
def copy_folder(): 
    source_folder = request.args.get('source_folder')                         # 获得contents
    target_folder = request.args.get('target_folder')                         # 获得contents
    if source_folder and target_folder:
        print('existing folder............source_folder.....', source_folder)
        print('existing folder............target_folder.....', target_folder)
        try:
            copytree(source_folder, target_folder)
        except Exception as e:
            flash(str(e))
    else:
        print('dont existing folder..........')
    return redirect(request.referrer)   # 执行完函数后，返回原来的位置 

@app.route('/json_file')
def json_file():
    j_file_path = request.args.get('j_file_path')
    try:
        with open(j_file_path,'r', encoding='utf8')as fp:
            mydict = json.load(fp)
        fp.close()
    except:
        mydict = {}
    return jsonify(mydict)


################################################################### 以下是定时任务
# import app_scheduler
# from flask_apscheduler import APScheduler # 引入APScheduler

# class SchedulerConfig(object):
#     JOBS = [
#         {
#             'id': 'app_scheduler.run', # 任务id
#             'func': '__main__:app_scheduler.run', # 任务执行程序
#             'args': None, # 执行程序参数
#             'trigger': 'interval',
#             'seconds': 3600
#         }
#     ]

########################################## 在调试模式下，Flask的重新加载器将加应用程序两次
if __name__ == '__main__':
    # app.config.from_object(SchedulerConfig())
    # scheduler = APScheduler()  # 实例化APScheduler
    # scheduler.init_app(app)  # 把任务列表载入实例flask
    # scheduler.start()  # 启动任务计划
    
    app.run(host="0.0.0.0", port=5002, debug=True)  # , debug=True
