import html,json
import urllib
from os import makedirs
from os.path import join,exists
from .textfilter.filter import DFAFilter
import random
import os,re
from hoshino import logger
FILE_PATH = os.path.dirname(__file__)

def beautiful(msg: str) -> str:
    beautiful_message = DFAFilter()
    beautiful_message.parse(os.path.join(os.path.dirname(__file__), 'textfilter','sensitive_words.txt'))
    msg = beautiful_message.filter(msg)
    return msg

async def doing_img(bot, img: str, is_ans: bool = False, save: bool = False) -> str:
    img_path = os.path.join(FILE_PATH, 'img/')
    if not exists(img_path):
        makedirs(img_path)
    if save:
        try:
            img_url = await bot.get_image(file=img)
            file = os.path.join(img_path, img)
            if not os.path.isfile(img_path + img):
                urllib.request.urlretrieve(url=img_url['url'], filename=file)
                logger.critical(f'XQA: 已下载图片{img}')
        except:
            if not os.path.isfile(img_path + img):
                logger.critical(f'XQA: 图片{img}已经过期，请重新设置问答')
            pass
    if is_ans:  # 保证保存图片的完整性，方便迁移和后续做操作
        return 'file:///' + os.path.abspath(img_path + img)
    return img

# 进行图片处理
async def adjust_img(bot, str_raw: str, is_ans: bool = False, save: bool = False) -> str:
    flit_msg = beautiful(str_raw) # 整个消息匹配敏感词
    cq_list = re.findall(r'(\[CQ:(\S+?),(\S+?)=(\S+?)])', str_raw) # 找出其中所有的CQ码
    # 对每个CQ码元组进行操作
    for cqcode in cq_list:
        flit_cq = beautiful(cqcode[0]) # 对当前的CQ码匹配敏感词
        raw_body = cqcode[3].split(',')[0].split('.image')[0].split('/')[-1].split('\\')[-1] # 获取等号后面的东西，并排除目录
        if cqcode[1] == 'image':
            # 对图片单独保存图片，并修改图片路径为真实路径
            raw_body = raw_body if '.' in raw_body else raw_body + '.image'
            raw_body = await doing_img(bot, raw_body, is_ans, save)
        if is_ans:
            # 如果是回答的时候，就将 匹配过的消息 中的 匹配过的CQ码 替换成未匹配的
            flit_msg = flit_msg.replace(flit_cq, f'[CQ:{cqcode[1]},{cqcode[2]}={raw_body}]')
        else:
            # 如果是保存问答的时候，就只替换图片的路径，其他CQ码的替换相当于没变
            str_raw = str_raw.replace(cqcode[0], f'[CQ:{cqcode[1]},{cqcode[2]}={raw_body}]')
    # 解决回答中不用于随机回答的\#
    flit_msg = flit_msg.replace('\#', '#')
    return str_raw if not is_ans else flit_msg

async def msg_save(bot,uid,gid,msg):
    try:
        if not exists(join(FILE_PATH,f'bottle')):#创建bottle文件夹
            makedirs(join(FILE_PATH,f'bottle'))
        msg = html.unescape(msg)
        msg = await adjust_img(bot,msg,False,True)
        if not exists(join(FILE_PATH,f'bottle/data.json')):
            data = [{
                'msg' : msg,
                'uid' : uid,
                'gid' : gid,
                'id'  : 1,
                'time' : 0,
                'comment' : []     
            }]
            with open(join(FILE_PATH,f'bottle/data.json'),'w',encoding='utf-8') as f:
                json.dump(data,f,indent=4, ensure_ascii=False)
            return 1
        else: 
            with open(join(FILE_PATH,f'bottle/data.json'),'r',encoding='utf-8') as f:
                data_list = json.load(f)
            id = data_list[-1]['id']+1
            data = {
                'msg' : msg,
                'uid' : uid,
                'gid' : gid,
                'id'  : id,
                'time' : 0,
                'comment' : []
            }
            data_list.append(data)
            with open(join(FILE_PATH,f'bottle/data.json'),'w',encoding='utf-8') as f:
                json.dump(data_list,f,indent=4, ensure_ascii=False)
            return id
    except:
        return None
    
async def check_member(bot,uid,gid):
    memberlist = await bot.get_group_member_list(gid)
    for i in memberlist:
        if i['user_id'] == uid:
            return True
    return False 

async def get_drift(bot):#msg,comm,time,gid,uid,id 
    try:
        if not exists(join(FILE_PATH,f'bottle/data.json')):
            return '','',0,0,0,False
        with open(join(FILE_PATH,f'bottle/data.json'),'r',encoding='utf-8') as f:
            bottle_list = json.load(f)
        deleteed = 0
        for i in bottle_list:
            if i['time'] == -1:deleteed+=1
        if deleteed == len(bottle_list):
            return '','',0,0,0,False
        order = random.randint(0,len(bottle_list)-1)
        bottle = bottle_list[order]
        while(bottle['time']==-1):
            order = random.randint(0,len(bottle_list)-1)
            bottle = bottle_list[order]
        bottle['time']+=1
        bottle_list[order] = bottle
        with open(join(FILE_PATH,f'bottle/data.json'),'w',encoding='utf-8') as f:
            json.dump(bottle_list,f,indent=4, ensure_ascii=False)
        msg = await adjust_img(bot,bottle['msg'],True,False)
        if not bottle['comment']:
            comm = ''
        else:
            comm = '评论:\n'
            for i in bottle['comment']:
                comm += i+'\n'
        time = bottle['time']
        gid = bottle['gid']
        uid = bottle['uid']
        id = bottle['id']
        return msg,comm,time,gid,uid,id
    except Exception as e:
        print(e)
        return '','',0,0,0,False

async def get_bott(bot,id:str)-> str:
    with open(join(FILE_PATH,f'bottle/data.json'),'r',encoding='utf-8') as f:
        bottle_list = json.load(f)
    check_bottle = False
    for i in bottle_list:
        if i['id'] == int(id):
            check_bottle = True
            bottle = i
            break
    if not check_bottle:
        return False
    msg = await adjust_img(bot,bottle['msg'],True,False)
    msg = f'id:{id}\n{msg}'
    return msg

async def delete_bottle(id:str)->bool:
    if not id.isdigit():return False
    id = int(id)
    with open(join(FILE_PATH,f'bottle/data.json'),'r',encoding='utf-8') as f:
        bottle_list = json.load(f)
    check_id = False 
    for i in range(0,len(bottle_list)):
        if bottle_list[i]['id'] == id:
            check_id = True
            break
    if not check_id:return False
    data = [{
        'msg' : '',
        'uid' : 0,
        'gid' : 0,
        'id'  : id,
        'time' : -1,
        'comment' : []     
    }]
    bottle_list[i] = data
    with open(join(FILE_PATH,f'bottle/data.json'),'w',encoding='utf-8') as f:
        json.dump(bottle_list,f,indent=4, ensure_ascii=False)
    return True

async def add_comm(bot,comment,id,uid):
    with open(join(FILE_PATH,f'bottle/data.json'),'r',encoding='utf-8') as f:
        bottle_list = json.load(f)
    check_id = False 
    for i in range(0,len(bottle_list)):
        if bottle_list[i]['id'] == id:
            check_id = True
            break
    if not check_id:
        return -1,0,0,''
    bottle = bottle_list[i]
    if bottle['time']==-1:
        return -2,0,0,''
    comm = bottle['comment']
    if len(comm) == 5:
        comm.remove(comm[0])
    comm.append(comment+f'({uid})')
    bottle_list[i]['comment'] = comm
    with open(join(FILE_PATH,f'bottle/data.json'),'w',encoding='utf-8') as f:
        json.dump(bottle_list,f,indent=4, ensure_ascii=False)
    id = bottle['id']
    ggid = bottle['gid']
    uuid = bottle['uid']
    msg = await adjust_img(bot,bottle['msg'],True,False)
    if not check_member(bot,uuid,ggid):
        return False,0,0,''
    return True,ggid,uuid,msg