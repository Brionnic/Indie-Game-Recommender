
# version v0.17
#   v0.17 twear process_raw_game_pages to show more useful logging
#   v0.16 modify process_raw_game_pages to take source/dest_collection
#       instead of db
#   v0.15 add key_to_search to insert function to make more generic
#   v0.14 add documentation to process_raw_game_pages function
#

# import MongoDB modules
from pymongo import MongoClient

# import the Requests HTTP library
import requests

# import the Beautiful Soup module
from bs4 import BeautifulSoup

# import the time module for the sleep functionality
# in order to be polite when scraping
import time

# randomize a bit for the scraping
import random

def digest_raw_game_info(document):
    '''
    process the raw_game_info page into a dictionary that has the app_id,
    the game name, and also the path used to get the reviews

    returns:
    a list of dictionaries like:
        {"app_id":<app_id>, "title":<game_title>, "path":<path> }
    '''

    game_list = []

    page_data = BeautifulSoup(document["data"], "lxml")

    games_html = page_data.find_all("a", class_="search_result_row ds_collapse_flag")

    for game in games_html:
        str_data = game.prettify()

        app_id = str_data[str_data.index("data-ds-appid"):].split(" ")[0].split("=")[1].strip('"')

        #print "app_id", app_id,

        id_path = "/app/" + app_id + "/"

        title = str_data[len(id_path) + str_data.index(id_path):].split("/")[0]

        path = "http://steamcommunity.com/app/{}/reviews/?p=".format(app_id)

        game_info = {"app_id":app_id, "title":title, "path":path}

        game_list.append(game_info)

    # print ">>>>>>>>>>>>> Game info:", game_info

    return game_list

def process_raw_game_pages(source_collection, dest_collection):
    '''
    * Get all documents from the <source_collection>
        ** process the data from each document into however many games there
            are per web page (usually ~25)
        ** Make a dictionary holding each game's info:
                *** app_id
                *** title
                *** URL to the game's reviews
    * Attempt to insert the game info dictionary into the <dest_collection>
        in a unique manner
    '''
    count = 0

    game_list = []

    for document in source_collection.find():
        #print type(document)
        #print len(document)
        count += 1

        # limit iterations for testing
        # if count > 3:
        #     break

        # get list of games from the current document
        games_from_doc = digest_raw_game_info(document)

        #print "games_from_doc:", games_from_doc

        for game_info in games_from_doc:
            #game_list.append(item["title"])
            print game_info["title"].ljust(40),
            insert(dest_collection, game_info, "app_id")

    # print
    # print "###############################################"
    # print
    # print game_list

def insert(collection, dictionary, key_to_search):
    '''
    Attempts to uniquely insert dictionary into collection
    '''
    if not collection.find_one({key_to_search: dictionary[key_to_search]}):
        try:
            collection.insert_one(dictionary)
            print "inserted", dictionary[key_to_search]

        except Exception, e:
            print e

    else:
        print "already exists"

if __name__ == "__main__":
    # connect to the hosted MongoDB instance with the database that we want
    db = MongoClient('mongodb://localhost:27017/')["capstone"]

    # collection to pull scraped information from
    source_collection = db.game_list_scrape

    # collection to store digested information in
    dest_collection = db.game_app_name_id

    print "Size of dest_collection before operation:", dest_collection.find().count()

    process_raw_game_pages(source_collection, dest_collection)

    print
    print "Size of dest_collection after operation:", dest_collection.find().count()
