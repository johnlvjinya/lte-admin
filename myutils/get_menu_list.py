import re

def menu_dict(f_path):
    f_lines = [i.rstrip('\n') for i in open(f_path, encoding='utf-8').readlines()]
    active = 'pass'

    menu_dict = {}
    for i in f_lines:
        # if '<!--     家族分割符 -->':
        #     active = None
        if '{{ad.menu' in i:
            active = re.findall(r'{{ad.menu(.*)}}', i)[0]

        if '/file_path?' in i:
            k = re.findall(r'<a href="(.*).html"', i)[0].replace('/file_path?file_path=','')
            v = re.findall(r'{{ad.(.*)}}', i)[0]
            # print(k,'===>', v,'=====>',  active)
            menu_dict[k] = [v,active]

    return menu_dict



if __name__=="__main__":
    menu_dict = menu_dict('../templates/base/base03_nav.html')
    print(menu_dict)

