import os,sys,json,glob,time
import random
from collections import Counter
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import yaml
import datetime

with open('./config.yaml', 'r', encoding='utf-8') as f:
    result = yaml.load(f.read(), Loader=yaml.FullLoader)
FILE_CHANGED_FLAG = False
MAA_config_path = result['MAA_config_path']
upper_replace_dict = result['upper_replace']# {"涓村厜:*":"榛?1:0"}
replace_dict = result['normal_replace']# {"闂伒:*":"娴佹槑:3:1", "绾儸鑹鹃泤娉曟媺:*":"娴佹槑:3:1", "婢勯棯:*":"閫诲悇鏂?1:0", "鑳藉ぉ浣?*":"鑹炬媺:3:1"}
extra_opers = result['extra_opers']
powerful_opers = result['powerful_opers']
target_json = {}
class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global FILE_CHANGED_FLAG
        print(event)
        FILE_CHANGED_FLAG = True
        if not event.is_directory:
            print(f"文件 {event.src_path} 已发生变化")




def monitor_file(file_path):
    global FILE_CHANGED_FLAG
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(file_path), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
            print(f'\r{datetime.datetime.now()} waiting', end='')
            if FILE_CHANGED_FLAG:
                print('\n')
                jsons = get_json_files(MAA_config_path)
                for i in jsons:
                    replace_json(i)
                time.sleep(1)
                FILE_CHANGED_FLAG = False
    except KeyboardInterrupt:
        observer.stop()
    observer.join()



def replace_json(file_path:str):
    global target_json
    with open(file_path, 'r', encoding='utf+8') as f:
        target_json = json.load(f)




    print(target_json)
    def get_all_names():
        all_names = []
        if 'groups' in target_json:
            for i in target_json['groups']:
                for j in i['opers']:
                    all_names.append(j['name'])
        if 'opers' in target_json:
            for i in target_json['opers']:
                all_names.append(i['name'])
        return all_names

    def get_opers_num():
        return len(target_json['opers']) + len(target_json['groups'])

    def super_replace_oper(ori_oper, ori_skill, target_oper, target_skill, target_skill_usage):
        global target_json
        if 'groups' in target_json:
            for i in range(len(target_json['groups'])):
                for j in range(len(target_json['groups'][i]['opers'])):
                    if target_json['groups'][i]['opers'][j]['name'] == ori_oper:
                        if target_json['groups'][i]['opers'][j]['skill'] in ori_skill:
                            target_json['groups'][i]['opers'][j]['skill'] = target_skill
                            target_json['groups'][i]['opers'][j]['skill_usage'] = target_skill_usage
                            target_json = eval(str(target_json).replace(ori_oper, target_oper))
                            print(f'super replace: {ori_oper} -> {target_oper}')
                            return True
        return False

    def replace_oper(ori_oper, ori_skill, target_oper, target_skill, target_skill_usage):
        global target_json
        if 'groups' in target_json:
            for i in range(len(target_json['groups'])):
                for j in range(len(target_json['groups'][i]['opers'])):
                    if target_json['groups'][i]['opers'][j]['name'] == ori_oper:
                        if target_json['groups'][i]['opers'][j]['skill'] in ori_skill:
                            target_json['groups'][i]['opers'].append({'name':target_oper, 'skill':target_skill, 'skill_usage':target_skill_usage})
                            print(f'{ori_oper} -> {target_oper}')
                            return True
        if 'opers' in target_json:
            for i in range(len(target_json['opers'])):
                if target_json['opers'][i]['name'] == ori_oper:
                    if target_json['opers'][i]['skill'] in ori_skill:
                        target_json['opers'][i]['skill'] = target_skill
                        target_json['opers'][i]['skill_usage'] = target_skill_usage
                        target_json = eval(str(target_json).replace(ori_oper, target_oper))
                        print(f'{ori_oper} -> {target_oper}')
                        return True
        return False



    def add_WSDE(name,skill,skill_usage):
        global target_json

        target_json['opers'].append({
      "name": name,
      "skill": skill,
      "skill_usage": skill_usage
    })

        all_direction = []
        average_position = [0,0]
        cnt = 0



        for i in target_json['actions']:
            if i['type'] in ['Deploy', '部署']:
                cnt += 1
                if i['direction'] not in ['None', '无']:
                    all_direction.append(i['direction'])
                average_position[0] += i['location'][0]
                average_position[1] += i['location'][1]

        counter = Counter(all_direction)
        max_dire = counter.most_common(1)[0][0]
        average_position[0] = int(average_position[0]/cnt)
        average_position[1] = int(average_position[1] / cnt)

        isDaemon = False
        if target_json['actions'][-1]['type'] == 'SkillDaemon':
            target_json['actions'].pop(-1)
            isDaemon = True

        for i in range(13):
            target_json['actions'].append({
                "type": "Deploy",
                "name": name,
                "location": [average_position[0]+random.randint(-2,2), average_position[1]+random.randint(-2,2)],
                "direction": max_dire
            })
        if isDaemon:
            target_json['actions'].append({
      "type": "SkillDaemon"
    })

    def add_extra_opers(name, skill=1, skill_usage=0):
        target_json['opers'].append({
            "name": name,
            "skill": skill,
            "skill_usage": skill_usage
        },)

    combined_dict = {}
    combined_dict.update(replace_dict)
    combined_dict.update(upper_replace_dict)

    for k in list(combined_dict.keys()):
        alln = get_all_names()
        ori_oper, ori_skill = k.split(':')
        if ori_skill == '*':
            ori_skill = [0,1,2,3,4,5,6]
        else:
            ori_skill = [int(ori_skill)]
        target_oper, target_skill, target_skill_usage = combined_dict[k].split(':')
        target_skill = int(target_skill)
        target_skill_usage = int(target_skill_usage)
        if ori_oper in alln and target_oper not in alln:
            if k in list(upper_replace_dict.keys()):
                super_replace_oper(ori_oper, ori_skill, target_oper, target_skill, target_skill_usage)
            else:
                replace_oper(ori_oper, ori_skill, target_oper, target_skill, target_skill_usage)

    for k in powerful_opers:
        if get_opers_num() >= 12: break
        alln = get_all_names()
        oper, oper_skill, oper_usage = k.split(':')
        oper_skill = int(oper_skill); oper_usage=int(oper_usage)
        if oper not in alln:
            add_WSDE(oper, oper_skill, oper_usage)

    for oper in extra_opers:
        if get_opers_num() >= 12: break
        alln = get_all_names()
        if oper not in alln:
            add_extra_opers(oper)

    json.dump(target_json, open(file_path, 'w', encoding='utf+8'), ensure_ascii=False)

def get_json_files(directory):
    pattern = os.path.join(directory, '**/*.json')
    json_files = glob.glob(pattern, recursive=True)
    json_files.append(os.path.join(directory, "../_temp_copilot.json"))
    return [os.path.abspath(file) for file in json_files]

monitor_file(MAA_config_path)


