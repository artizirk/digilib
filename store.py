#/usr/bin/env python3
#####################
# code for mirroring/storing copy of digi.ee forum

from pymongo import MongoClient
import digilib

client = MongoClient()
db = client.digi_mirror

forums = db.forums
for forum in digilib.get_forums():
    if not forums.find_one({"id": forum["id"]}):
        print("inserting forum", forum["title"])
        forums.insert(forum)

threads = db.threads
for forum in forums.find():
    forum_id = forum["id"]
    print("geting threads from forum id", forum_id)
    for thread in digilib.get_all_threads_in_forum(forum_id):
        thread["forum_id"] = forum_id
        if not threads.find_one({"id": thread["id"]}):
            print("inserting thread", thread["id"], thread["title"])
            threads.insert(thread)

posts = db.posts
for thread in threads.find():
    thread_id = thread["id"]
    print("getting posts from thread id:", thread_id)
    for post in digilib.get_all_posts_in_thread(thread_id):
        post["thread_id"] = thread_id
        if not posts.find_one({"post_id": post["post_id"]}):
            print("inserting post", post["post_id"], post["user"])
            posts.insert(post)
