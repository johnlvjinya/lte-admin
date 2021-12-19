
import zipfile
import os



def zip_files(dir_path, zip_path):
    """
    :dir_path: 需要压缩的文件目录
    :zip_path: 压缩后的目录
    :return:
    """
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as f:
        for root, _, file_names in os.walk(dir_path):
            for filename in file_names:
                f.write(os.path.join(root, filename), os.path.join('lyric163',filename))
    f.close()

def zip_files_ver2(start_dir):
    start_dir = start_dir  # 要压缩的文件夹路径
    file_news = start_dir + '.zip'  # 压缩后文件夹的名字

    z = zipfile.ZipFile(file_news, 'w', zipfile.ZIP_DEFLATED)
    for dir_path, dir_names, file_names in os.walk(start_dir):
        f_path = dir_path.replace(start_dir, '')  # 这一句很重要，不replace的话，就从根目录开始复制
        f_path = f_path and f_path + os.sep or ''  # 实现当前文件夹以及包含的所有文件的压缩
        for filename in file_names:
            z.write(os.path.join(dir_path, filename), f_path + filename)
    z.close()
    return file_news


def unzip(file_path, unzip_path):
    # with zipfile.ZipFile(file_path,'r') as zzz:
    #     # for f_name in zzz.namelist():
    #     #     print(f_name.encode('cp437').decode('gbk'))

    extracting = zipfile.ZipFile(file_path)
    extracting.extractall(unzip_path)
    extracting.close()


if __name__=='__main__':
    # zip_files('zip_test', 'test.zip')
    zip_files_ver2('p_python_flask_python-plot-gallery')

