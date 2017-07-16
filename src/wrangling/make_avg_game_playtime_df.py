# import MongoDB modules
from pymongo import MongoClient

# get numpy to use random.shuffle
import numpy as np

# import the Requests HTTP library
import requests

# import the Beautiful Soup module
from bs4 import BeautifulSoup

# import the time module for the sleep functionality
# in order to be polite when scraping
import time

# randomize a bit for the scraping
import random

import json

from game_indexer import GameIndexer

# connect to the hosted MongoDB instance
db = MongoClient('mongodb://localhost:27017/')["capstone"]

##############################################################################
##############################################################################
########### Create a very simple DF that is simply the average ###############
########### playtimes of all apps    #########################################
##############################################################################
##############################################################################


source_collection = db.user_profile_scraping

###################################################################################
##### Find number of unique app ids in stored data (should be ~8700)   ############
###################################################################################
user_count = source_collection.find().count()

print user_count

# a dict of dicts, the dicts consist of play times (min) when they're > 0min
# <app_id>: [<list of playtimes]
game_dict = {}

# go through all of the users in the user scrape db
for idx, user in enumerate(source_collection.find()):

    #print user.keys()

    # step through all of the games that the user has
    for idy, game in enumerate(user["data"]):

        try:
            _appid = int(game["appid"])
            _ptf = int(game["playtime_forever"])
            _user = int(user["user"])
            # make sure we only include games that have been played
            if _ptf >= 1:

                # ok, it's been played, see if it is already in the set
                if _appid in game_dict:
                    # add the current playtime to the dictionary
                    game_dict[_appid][_appid].append(_ptf)
                else:
                    # make a new dictionary for the game and add that to the set
                    _dict = {_appid : [_ptf]}
                    game_dict[_appid] = _dict

                print "User: {} Game: {} Playtime: {}\r".format(_user, _appid, _ptf),
        except Exception, e:
            print
            print
            print "Something went wrong:", e


        if idy > 10:
            break
    if idx > 10:
        break


print "completed operation"

for x, item in enumerate(game_dict):
    print item

    import pdb; pdb.set_trace()
    if x > 5:
        break
