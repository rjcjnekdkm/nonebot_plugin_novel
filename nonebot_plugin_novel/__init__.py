from nonebot import on_regex,on_fullmatch
from nonebot.permission import SUPERUSER
import requests,re
from bs4 import BeautifulSoup
from typing import List
from nonebot.adapters.onebot.v11 import (
    Message,
    GroupMessageEvent,
    Bot,
    PrivateMessageEvent,
    MessageEvent,
    GROUP_ADMIN,
    GROUP_OWNER
)



get_novel = on_regex(r"查看小说",permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=2,block=True)
get_title_id = on_regex(r"^获取(.*?)章节$",permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=2,block=True)
get_Recommend = on_fullmatch("小说推荐",permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=2,block=True)
get_week = on_fullmatch("周排行榜",permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=2,block=True)
get_month = on_fullmatch("月排行榜",permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER, priority=2,block=True)


# ---------------合并消息转发------------ #
# 合并消息转发摘自作者@MRSlouzk的Nonebot-plugintutorials，感谢
async def send_forward_msg(
        bot: Bot,                                                  
        event: MessageEvent,
        name: str,
        uin: str,
        msgs: List[Message],
):
    def to_json(msg: Message):
        return {"type": "node", "data": {"name": name, "uin": uin, "content": msg}}

    messages = [to_json(msg) for msg in msgs]
    is_private = isinstance(event, PrivateMessageEvent)
    if(is_private):
        await bot.call_api(
            "send_private_forward_msg", 
            user_id=event.user_id,
            messages=messages
        )
    else:
        await bot.call_api(
            "send_group_forward_msg",
            group_id=event.group_id, 
            messages=messages
        )



# ---------------获取正文内容------------ #

@get_novel.handle()
async def _novel(bot: Bot,event: MessageEvent):
    # 从接收的消息中提取小说和章节id
    msg = str(event.message)
    ht = msg[4:]
    # 发送请求
    url = f'https://www.xbiquge.so/book/{ht}.html'
    resp = requests.get(url)

    # 获取章节名称
    page = BeautifulSoup(resp.text,'html.parser')
    title = page.find_all('h1')
    obj3 = re.compile(r'<h1>(?P<title_name>.*?)</h1>]',re.S)
    result3 = obj3.finditer(str(title))
    task = [] 

    for i3 in result3:
        title_name = i3.group('title_name')
        task.append(title_name)

    # 提取正文
    obj = re.compile(r'<div id="content" name="content">(?P<text>.*?)</div><center class="clear">',re.S)
    result = obj.finditer(resp.text)

    for i in result:
        novel = i.group('text')
        obj2 = re.compile(r'&nbsp;&nbsp;&nbsp;&nbsp;(?P<txt>.*?)<br /><br />',re.S)
        result2 = obj2.finditer(novel)
        for i2 in result2:
            novel_txt = i2.group('txt')
            task.append(novel_txt)
    resp.close()
    await send_forward_msg(bot, event, "novel", bot.self_id, task)



# ---------------获取章节列表------------ #

@get_title_id.handle()
async def title_id(bot: Bot,event: MessageEvent):
    # 从接收的消息中提取小说id
    msg = str(event.message)
    novel_id = msg[2:-2]
    # 发送请求
    url_ = f"https://www.xbiquge.so/book/{novel_id}/"
    resp_ = requests.get(url_)
    title_list=[]
    obj = re.compile(r'正文</dt>(?P<text>.*?)本站推荐',re.S)
    result = obj.finditer(resp_.text)

    # 获取章节id
    for i in result:
        title_text = i.group('text')
        page = BeautifulSoup(title_text,'html.parser')
        alist = page.find_all('a')
        for a in alist:
            title_id = a.get('href').split('.')[0]
            title_ = title_id + a.text
            title_list.append(title_)
    title_len = len(title_list)//100 + 2
    resp_.close()
    for i in range(title_len):
        if i != 0:
            await send_forward_msg(bot, event, "novel", bot.self_id, title_list[i*100-100:i*100])



# ---------------获取获取本站推荐------------ #

@get_Recommend.handle()
async def get_recommend(bot: Bot,event: MessageEvent):
    url = "https://www.xbiquge.so/top/toptime/"
    resp = requests.get(url)
    obj1 = re.compile(r'<h2>本站推荐</h2>(?P<text>.*?)<em id="pagestats">',re.S)
    result = obj1.finditer(resp.text)

    books = []
    authors=[]
    styles = []
    author_names = []
    tasks=['本站推荐']

    for i in result:
        all_text = i.group('text')
        page = BeautifulSoup(all_text,'html.parser')
        alist = page.find_all('a')
        author = page.find_all('span')
        # 获取小说id和书名
        for au in author:
            if au:
                authors.append(au.text)
        for l in range(len(alist)):
            if l % 2 == 0 :
                for a in alist[l:l+2:2]:
                    book = a.get('href').split('/')[-2]+a.get('title')
                    books.append(book)

    # 获取小说类型和小说作者
    for i in range(len(authors)):
        if i%6 == 0:
            style = authors[i]
            styles.append(style)
            author_name = authors[i+3]
            author_names.append(author_name)

    # 拼接
    for i in range(50):
        task = '类型：' + styles[i] + '\n' + books[i] + '\n' + '作者：' + author_names[i]
        tasks.append(task)
    resp.close()
    await send_forward_msg(bot, event, "本站推荐", bot.self_id, tasks)



# ---------------获取周排行榜----------- #

@get_week.handle()
async def get_week_(bot: Bot,event: MessageEvent):
    url = "https://www.xbiquge.so/top/weekvisit/"
    resp = requests.get(url)
    obj1 = re.compile(r'<h2>周排行榜</h2>(?P<text>.*?)<em id="pagestats">',re.S)
    result = obj1.finditer(resp.text)

    books = []
    authors=[]
    styles = []
    author_names = []
    tasks=['周排行榜']

    for i in result:
        all_text = i.group('text')
        page = BeautifulSoup(all_text,'html.parser')
        alist = page.find_all('a')
        author = page.find_all('span')
        # 获取小说id和书名
        for au in author:
            if au:
                authors.append(au.text)
        for l in range(len(alist)):
            if l % 2 == 0 :
                for a in alist[l:l+2:2]:
                    book = a.get('href').split('/')[-2]+a.get('title')
                    books.append(book)

    # 获取小说类型和小说作者
    for i in range(len(authors)):
        if i%6 == 0:
            style = authors[i]
            styles.append(style)
            author_name = authors[i+3]
            author_names.append(author_name)

    # 拼接
    for i in range(50):
        task = '类型：' + styles[i] + '\n' + books[i] + '\n' + '作者：' + author_names[i]
        tasks.append(task)
    resp.close()
    await send_forward_msg(bot, event, "周排行榜", bot.self_id, tasks)



# ---------------获取月排行榜------------ #
    
@get_month.handle()
async def get_month_(bot: Bot,event: MessageEvent):
    url = "https://www.xbiquge.so/top/monthvisit/"
    resp = requests.get(url)
    obj1 = re.compile(r'<h2>月排行榜</h2>(?P<text>.*?)<em id="pagestats">',re.S)
    result = obj1.finditer(resp.text)

    books = []
    authors=[]
    styles = []
    author_names = []
    tasks=['月排行榜']

    for i in result:
        all_text = i.group('text')
        page = BeautifulSoup(all_text,'html.parser')
        alist = page.find_all('a')
        author = page.find_all('span')
        # 获取小说id和书名
        for au in author:
            if au:
                authors.append(au.text)
        for l in range(len(alist)):
            if l % 2 == 0 :
                for a in alist[l:l+2:2]:
                    book = a.get('href').split('/')[-2]+a.get('title')
                    books.append(book)

    # 获取小说类型和小说作者
    for i in range(len(authors)):
        if i%6 == 0:
            style = authors[i]
            styles.append(style)
            author_name = authors[i+3]
            author_names.append(author_name)

    # 拼接
    for i in range(50):
        task = '类型：' + styles[i] + '\n' + books[i] + '\n' + '作者：' + author_names[i]
        tasks.append(task)
    resp.close()
    await send_forward_msg(bot, event, "月排行榜", bot.self_id, tasks)