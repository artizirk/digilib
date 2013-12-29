#/usr/bin/env python3
###############################################################################
# digi.ee lib for accessing digi.ee from python
###############################################################################

import requests
import bs4 

digi = "http://www.digi.ee"

def get_news(page=1):
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
