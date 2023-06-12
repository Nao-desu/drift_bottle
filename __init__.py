from hoshino import Service,logger
from hoshino.typing import CQEvent
import os,re,html,json
import urllib
from os import makedirs
from os.path import join,exists
from .textfilter.filter import DFAFilter
import random
FILE_PATH = os.path.dirname(__file__)
sv_help = '''
[扔漂流瓶] 把你的话装进漂流瓶内,会被谁捡到呢？
[捡漂流瓶] 看看里面有啥
'''

sv = Service('漂流瓶',help_=sv_help)
#line16~59使用了xqa插件的代码
def beautiful(msg: str) -> str:
    beautiful_message = DFAFilter()
    beautiful_message.parse(os.path.join(os.path.dirname(__file__), 'textfilter','sensitive_words.txt'))
    msg = beautiful_message.filter(msg)
    return msg

async def doing_img(bot, img: str, is_ans: bool = False, save: bool = False) -> str:
    img_path = os.path.join(FILE_PATH, 'img/')
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
        msg = adjust_img(bot,msg,False,True)
        if not exists(join(FILE_PATH,f'bottle/data.json')):
            data = {
                'msg' : msg,
                'uid' : uid,
                'gid' : gid,
                'id'  : 1,
                'time' : 0,
                'comment' : ''     
            }
            with open(join(FILE_PATH,f'bottle/data.json'),'w') as f:
                json.dump([data],f,indent=4, ensure_ascii=False)
            return 1
        else: 
            with open(join(FILE_PATH,f'bottle/data.json'),'r') as f:
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
            with open(join(FILE_PATH,f'bottle/data.json'),'w') as f:
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
        with open(FILE_PATH,f'bottle/data.json','r') as f:
            bottle_list = json.load(f)
        order = random(0,len(bottle_list))
        bottle = bottle_list[order]
        bottle['time']+=1
        bottle_list[order] = bottle
        with open(FILE_PATH,f'bottle/data.json','w') as f:
            json.dump(bottle_list,f,indent=4, ensure_ascii=False)
        msg = adjust_img(bot,bottle['msg'],True,False)
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
    

async def add_comm(bot,comment,id,uid):
    with open(FILE_PATH,f'bottle/data.json','r') as f:
        bottle_list = json.load(f)
    check_id = False 
    for i in range(0,len(bottle_list)):
        if i['id'] == i:
            check_id = True
            break
    if not check_id:
        return -1
    bottle = bottle_list[i]
    comm = bottle['comment']
    if len(comm) == 5:
        len.remove(comm[0])
    comm.append(comment+f'({uid})')
    bottle_list[i]['comment'] = comm
    with open(FILE_PATH,f'bottle/data.json','w') as f:
        json.dump(bottle_list,f,indent=4, ensure_ascii=False)
    id = bottle['id']
    ggid = bottle['gid']
    uuid = bottle['uid']
    if not check_member(bot,uuid,ggid):
        return False
    msg = f'[CQ:at,qq={uuid}]收到漂流瓶{id}的评论:\n{comm}'
    await bot.send_group_message(group_id = ggid,message = msg)
    return True

@sv.on_prefix('扔漂流瓶')
async def drop_bottle(bot,ev:CQEvent):
    msg = ev.message.extract_plain_text().strip()
    try:
        if not msg:
            await bot.send('这个瓶子空空如也,消失在海面上')
            return
        id= await msg_save(bot,uid = ev.user_id,gid = ev.group_id,msg=msg)
        if not id:
            await bot.send('忽然间狂风大作,扔出的漂流瓶撞碎在礁石上,它再也没有被捡起的机会了')
            return
        await bot.send(ev,f'你刚刚送走了第{id}个漂流瓶，它将带着你的故事，飘向未知的远方')
    except Exception as e:
        await bot.send(ev,f'今天不是扔漂流瓶的好日子，改天再来吧\n({e})')

@sv.on_fullmatch('捡漂流瓶')
async def get_bottle(bot,ev:CQEvent):
    try:
        msg,comm,time,gid,uid,id = await get_drift(bot)
        if not id:
            await bot.send(ev,'海面空空如也，等一段时间再来吧',at_sender = True)
            return
        info = bot.get_stranger_info(uid)
        ginfo = bot.get_group_info(gid)
        message = f'bid:{id}\n'
        if ginfo.group_name:
            message += f'捡到来自群{bot.get_group_info(gid).group_name}({gid})的漂流瓶\n'
        else:
            message += f'捡到来自群{gid}的漂流瓶\n'
        if info.nickname:
            message += f'发送者{info.nickname}{uid}\n————————————————————\n'
        else:
            message += f'发送者{uid}\n————————————————————\n'
        message += f'{msg}\n————————————————————\n{comm}(此漂流瓶已被捡起{time}次,回复此消息可以评论)'
        await bot.send(ev,message)
    except Exception as e:
        await bot.send(ev,f'捡到一个破碎的瓶子,里面的东西早已被海水腐蚀，无法辨认\n({e})')

@sv.on_message('group')
async def add_comment(bot,ev: CQEvent):
    try:
        sid = ev.self_id
        uid = ev.user_id
        match = re.search(r"\[CQ:reply,id=([0-9]*)\]", str(ev.message))
        if not match:
            return
        commatch = rf'\[CQ:reply,id=\d*\]\[CQ:at,qq={sid}\](.*)'
        comment = re.search(commatch,str(ev.message))
        mid = match.group(1)
        message = bot.get_msg(mid)
        if message.sender.userid == sid:
            msg = str(message.message)
            idmatch = r'^bid:\d*'
            if re.match(idmatch,msg):
                id = re.search(r'^bid:(\d*)',msg).group(1)
                result = await add_comm(bot,comment,int(id),uid)
                if not result:
                    await bot.send(ev,'你来晚了一步，他/她已经离开了这片海域。',at_sender = True)
                if result == -1:
                    return                
                await bot.send(ev,'评论成功') 
            else:return
        else:return
    except Exception as e:
        await bot.send(ev,f'你的评论没有寄出\n{e}')



