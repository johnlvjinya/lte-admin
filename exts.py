
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()  # 此时先不传入app， 防止app.py与model.py循环引用