
from exts import db
from app import app
from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand

manager = Manager(app)      # 1. 要使用flask_migrate，必须绑定app和db
migrate = Migrate(app,db)   # 2. 把MigrateCommand命令添加到manager中
manager.add_command('db',MigrateCommand)

if __name__ == '__main__':
    manager.run()