
### sublime text3 安装pretty json
### 使用ctrl+alt+j格式化json数据


import json

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)

def save_dict_to_json(data_input, file_path='parameter.json'):
        with open(file_path,'w',encoding='utf-8') as f2:
            json.dump(data_input, f2,ensure_ascii=False, cls=NpEncoder)


if __name__ == '__main__':
    a = []
    b = {'a':1}
    c = {'b':2}
    a.append(b)
    a.append(c)
    save_dict_to_json(a, file_path='parameter.json')

    ########## json文件的加载，变成dict数据格式
    path = 'parameter.json'
    file = open(path, "rb")
    parameter_dict = json.load(file) # 剩下的就是解析了，都是列表和字典的操作
    print(type(parameter_dict))
    print(parameter_dict)
