from hoshino import Service,logger
from hoshino.typing import CQEvent
import os,re
from message_deal import *
FILE_PATH = os.path.dirname(__file__)
sv_help = '''
[扔漂流瓶] 把你的话装进漂流瓶内,会被谁捡到呢？
[捡漂流瓶] 看看里面有啥
'''

sv = Service('漂流瓶',help_=sv_help)

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



