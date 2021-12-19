
import os

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

def get_file_list(path):
    res_list = []
    lsfiles = os.listdir(path)
    dirs = [i for i in lsfiles if os.path.isdir(os.path.join(path, i))]
    if dirs:
        for i in dirs:
            res_list +=get_file_list(path+'/'+i)
    files = [i for i in lsfiles if os.path.isfile(os.path.join(path, i))]
    for f in files:
        # print(os.path.join(path, f))
        res_list.append(path+'/'+f)
    return res_list


if __name__ == '__main__':
    res_list = get_file_list('templates')
    res_list = [i.replace(r'templates/', '') for i in res_list]
    for i in res_list:
        print(i)