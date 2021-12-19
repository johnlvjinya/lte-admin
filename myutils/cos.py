

import sys
sys.path.append('..')       # 相当于cd .. 返回上一级目录，也就可以调用那边的文件了

import os
import time
import tarfile
import zipfile
import config
import shutil
import logging
import csv
import config
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client


logging.basicConfig(level=logging.INFO, stream=sys.stdout)
if os.path.exists('temp') is False:
    os.mkdir('temp')
'''
mysqldump
Usage: mysqldump [OPTIONS] database [tables]
OR     mysqldump [OPTIONS] --databases [OPTIONS] DB1 [DB2 DB3...]
OR     mysqldump [OPTIONS] --all-databases [OPTIONS]
For more options, use mysqldump --help
'''



# print(f_path)

class MyTencentCos():
    def __init__(self):
        config_cos = CosConfig(Region=config.region, SecretId=config.secret_id, SecretKey=config.secret_key, Token=None, Scheme=config.scheme)
        self.client = CosS3Client(config_cos)               # 获取客户端对象

    def upload_bucket_file(self, file_path, key):
        with open(file_path, 'rb') as fp:
            response = self.client.put_object(
                Bucket=config.bucket_name+config.secret_string,  # 存储桶的名称
                Body=fp,
                Key=key,  # 文件名
                # Key=file_path,                # 出现在存储桶中的是个文件夹
                StorageClass='STANDARD',
                EnableMD5=False
            )


def copy_db():
    db_host=config.host
    db_user=config.user
    db_passwd=config.password
    db_name=config.db
    db_charset="utf8"

    if os.path.exists('temp/copy_db') is False:
        os.mkdir('temp/copy_db')
    
    time_now = time.strftime("%Y-%m-%dT%H-%M-%S")

    db_backup_name="temp/copy_db/{0}_{1}.sql".format(config.db, time_now)
    key_name = "{0}/{1}_{2}.sql".format(config.db, config.db, time_now)
    os.system("mysqldump -h%s -u%s -p%s %s --default_character-set=%s > %s" %(db_host, db_user, db_passwd, db_name, db_charset, db_backup_name))
    MTC = MyTencentCos()
    MTC.upload_bucket_file(db_backup_name, key_name)

    try:
        shutil.rmtree('temp/copy_db')
    except:
        pass

# if __name__ == "__main__":
#     # print("begin to dump mysql database crm...");
#     # print("mysqldump -h%s -u%s -p%s %s --default_character-set=%s > %s" %(db_host, db_user, db_passwd, db_name, db_charset, db_backup_name))
#     # os.system("mysqldump -h%s -u%s -p%s %s --default_character-set=%s > %s" %(db_host, db_user, db_passwd, db_name, db_charset, db_backup_name))
#     # os.system("mysqldump -h%s -u%s -p%s %s --default_character-set=%s > %s" %(db_host, db_user, db_passwd, db_name, db_charset, db_backup_name))
#     copy_db()
#     # print("begin zip files...")
#     # zip_files()
#     # print("done, pyhon is great!")