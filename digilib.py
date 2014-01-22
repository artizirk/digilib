#/usr/bin/env python3
########################################################################
# digi.ee lib for accessing digi.ee from python
########################################################################
#this is horrible
import requests
import bs4


digi = "http://www.digi.ee"

def get_news(page=1):
    """Get one page worth of news"""
    r = requests.get(digi+"/?page={}".format(page))
    soup = bs4.BeautifulSoup(r.content.decode())
    for news in soup.findAll("div", {"class":"article"}):
        dnews = {}
        dnews["id"] = news.find("a", {"class":"comments"})
        dnews["news_name"] = dnews["id"].attrs["href"][27:]
        dnews["id"] = dnews["id"].contents[1][47:-19]
        dnews["text"] = news.find("p").contents[1][3:]
        dnews["user"] = news.find("span", {"class":"user"}).string
        dnews["title"] = news.h2.a.string
        dnews["image"] = news.find("img", {"class":"article_image"})
        if dnews["image"] is not None:
            dnews["image"] = dnews["image"].attrs["src"]
        yield dnews

def get_all_news():
    """Get all the news"""
    current_page = 1
    empty = True
    while True:
        for news in get_news(current_page):
            yield news
            empty=False
            print("page:{}, news_id:{}".format(current_page,news["id"]))
        else:
            print("end of page:{}".format(current_page))
            current_page += 1
            if empty:
                break
            else:
                empty = True

def get_forums():
    """Returns list of main forums"""
    r = requests.get(digi+"/foorum/index.php")
    soup = bs4.BeautifulSoup(r.content.decode())
    for x, forum in enumerate(soup.find("table", {"class":"forums"}).children):
        if x < 3:  # first 3 results are useless
            continue
        if forum == '\n':
            continue
        if x == 15: #15'th element is useless
            break
        dforum = {}
        #dforum["raw"] = forum
        dforum["title"] = forum.find("td", {"class":"caption1", "style":"width:100%"}).contents
        dforum["id"] = dforum["title"][0].contents[0]
        dforum["comment"] = str(dforum["title"][2])
        dforum["title"] = str(dforum["id"].text)
        dforum["id"] = int(dforum["id"].attrs["href"][56:])
        dforum["numb_threads"] = int(forum.find("td", {"class":"author"}).text)
        yield dforum

def get_page_of_threads_in_forum(forum_id, page=0):
    """returns a list of threads in a from in one page"""
    r = requests.get(digi+"/foorum/index.php?action=vtopic&forum={}&sortBy=1&page={}".format(forum_id, page), allow_redirects=False)
    if r.status_code != 200:
        raise Exception("failed to get the page")
    soup = bs4.BeautifulSoup(r.content.decode())
    threads = soup.find("table", {"class":"forumsmb"})
    numb_of_elements = len(threads.contents)
    for x, thread in enumerate(threads.children):
        if x < 3:  # first 3 results are useless
            continue
        if thread == '\n':
            continue
        if x > numb_of_elements-4:
            break
        dt = {}
        dt["title"] = thread.contents[3].text
        dt["id"] = int(thread.contents[3].strong.contents[0].attrs["href"][67:])
        dt["user"] = list(thread.contents[9].strings)[0]
        dt["posts"] = int(thread.contents[5].text)
        dt["views"] = int(thread.contents[7].text)
        yield dt

def get_all_threads_in_forum(forum_id):
    """returns all threads in a forum"""
    page=0
    while True:
        try:
            print("page {} forum {}".format(page, forum_id))
            for thread in get_page_of_threads_in_forum(forum_id=forum_id, page=page):
                yield thread
            page += 1
        except Exception as err:
            break

def minibb_to_plainbb(post):
    """convert minibb html code to normal bb code"""
    p=[]
    for child in post.children:
        if child.name == 'br':
            p.append("\n")
        elif child.name == "img":
            if "showspoiler" in child.attrs.get("onclick", ""):
                continue
            else:
                p.append("[img]{}[/img]".format(child.attrs["src"]))
        elif child.name == "a":
            if child.next.next.name == "img":
                addr = child.next.next.attrs["src"]
                desc = child.next.next.attrs["alt"]
                p.append("[imgs={}]{}[/imgs]".format(addr, desc))
            else:
                p.append("[url={}]{}[/url]".format(child.attrs["href"], child.text))
        elif child.name == "div":
            if child.attrs.get("style", "") == "text-align:center":
                p.append("[aligncenter]{}[/align]".format("".join(minibb_to_plainbb(child))))
            elif child.attrs.get("class", [])[0] == "jscript":
                p.append("".join(minibb_to_plainbb(child)))
            elif child.attrs.get("class", [])[0] == "hl":
                p.append("[hl]{}[/hl]".format("".join(minibb_to_plainbb(child))))
            elif child.attrs.get("class", [])[0] == "spoiler":
                p.append("[spoiler]{}[/spoiler]".format("".join(minibb_to_plainbb(child))))
            elif child.attrs.get("class", [])[0] == "quote":
                if child.next.attrs.get("class", [])[0] == "quoting":
                    quoting = str(child.next.text).strip()
                    p.append("[quote={}]{}[/quote]".format(quoting, "".join(minibb_to_plainbb(child))))
                else:
                    p.append("[quote]{}[/quote]".format("".join(minibb_to_plainbb(child))))
            elif child.attrs.get("class", [])[0] == "quoting":
                pass 
            else:
                p.append(child)
        elif child.name == "pre":
            p.append("[code]{}[/code]".format("".join(minibb_to_plainbb(child))))
        elif child.name == "strong":
            p.append("[b]{}[/b]".format("".join(minibb_to_plainbb(child))))
        elif child.name == "span":
            if "color:" in child.attrs.get("style", ""):
                p.append("[color={}]{}[/color]".format(child.attrs["style"][6:], "".join(minibb_to_plainbb(child))))
            else:
                p.append(child)
        elif child.name == "em":
            p.append("[i]{}[/i]".format("".join(minibb_to_plainbb(child))))
        elif child.name == "object":
            p.append("[youtube=http://www.youtube.com/watch?v={}]".format(child.param.attrs["value"][25:]))
        else:
            print("ERROR: can't decode:", child)
            p.append(str(child))

    return p

def get_page_in_thread(thread_id, page):
    """returns posts from one page in a thread"""
    forumid = requests.get(digi+"/foorum/index.php?action=vthread&topic={}&page={}".format(thread_id, page), allow_redirects=False).headers["location"][57:][:3]
    r = requests.get(digi+"/foorum/index.php?action=vthread&forum={}&topic={}&page={}".format(forumid, thread_id, page), allow_redirects=False)
    if r.status_code != 200:
        raise Exception("failed to get the page")
    soup = bs4.BeautifulSoup(r.content.decode())
    posts = soup.find("form", {"id":"allMsgs"})
    for post in posts.findAll("table", {"class":"forumsmb"}):
        dp = {}
        dp["user"] = list(post.contents[1].contents[1].strings)
        dp["role"] = dp["user"][1]
        dp["user"] = dp["user"][0]
        dp["user_id"] = int(post.contents[1].contents[1].findAll("a")[1].attrs["href"][57:])
        dp["post_id"] = int(post.contents[1].contents[3].find("a").attrs["href"][4:])
        dp["post_date"] = list(post.contents[1].contents[3].strings)[3][13:][:-1].replace("\xa0", " ")
        dp["post"] = "".join(minibb_to_plainbb(post.contents[3].contents[1].contents[1]))
        dp["signature"] = "".join(minibb_to_plainbb(post.contents[3].contents[1].contents[5]))
        yield dp

def get_all_posts_in_thread(thread_id):
    """returns all posts from all pages in a thread"""
    page=0
    while True:
        try:
            print("page {} thread {}".format(page, thread_id))
            for post in get_page_in_thread(thread_id, page):
                yield post
            page += 1
        except Exception as err:
            print("error", err)
            break
