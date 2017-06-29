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

# version v0.22

def scrape_user_to_db(collection):
    path = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=5DA6749271B3262B589F2980379B9AE2&steamids='

    user_id =   "76561197900000000"
    user_id = "765611979"
    # user_id = "76561197960435530" # valid
    # user_id = "765611979468871517" # invalid

    # API profile: this represents an empty response, if we get this then it's not a good profile, try again
    none_soup = BeautifulSoup('<html><body><p>{\n\t"response": {\n\t\t"players": [\n\n\t\t]\n\t\t\n\t}\n}</p></body></html>', "lxml")

    # User web profile, intentionally generate an error/empty profile so we can skip storing that
    error_path = "https://steamcommunity.com/id/{}/games/?tab=all".format("stas350")
    bad_req = requests.get(error_path)

    # this is what we will check against to make sure that the response isn't an error
    profile_error = BeautifulSoup(bad_req.content, "lxml")
    #   ^
    #   |   currently not used but may be needed if the length valid page
    #       filtering isn't working

    # path for generating a request will be used like this
    # good_path = "https://steamcommunity.com/id/{}/games/?tab=all".format("Dart")
    good_path = "https://steamcommunity.com/id/{}/games/?tab=all"

    # attempt to avoid pointlessly repeating requests
    tried_ids = []

    # keep track of how many profiles attempted
    profiles_attempted = []

    for idx in xrange(450000):
        user_id = "765611979"
        user_num = ""

        if idx % 100 == 0:
            print "\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", collection.find().count()

        # generate random numbers for user_id to try
        for idy in xrange(8):
            user_num += str(random.randint(0, 9))

        # try to be nice to steam servers
        time.sleep(random.random() * 1.0)

        # coalesce the user_id
        user_id = user_id + user_num

        # try to prevent duplicate requests
        if user_id not in tried_ids:
            # add id so it will show in request checks
            tried_ids.append(user_id)

            #print user_id

            req = requests.get(path + user_id)

            print str(req), "Attempt:", idx, "profiles attempted/responded so far:", len(profiles_attempted), "/", len(tried_ids)

            soup = BeautifulSoup(req.content, "lxml")

            if soup != none_soup:
                try:
                    profiles_attempted.append(user_id)

                    # find the username in the profile info stuff
                    para = soup.find_all("p")
                    user_id = str(para)[str(para).find("personaname"):].split(",")[0].split(" ")[1].strip('"')
                    attempt_to_get_user_profile(user_id, good_path.format(user_id), collection)
                    print
                except Exception, exc:
                    print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX Something weird happened:", exc


def attempt_to_get_user_profile(user_id, path, collection):
    '''
    Using the user_id and path generate a valid url path to request
    all of the games that a player owns.

    About 3/4 profiles that are pulled will be error pages because the profile
    is not public. As a lightweight workaround see if the page is small as the
    pages with user profiles are longer. (Need to verify if a user with a
    small profile, ex they only have one game, does not get filtered out this
    way)

    If the profile_page that we scraped is big enough then convert it to a
    dictionary and then call the insert function to try to put it into the
    mongodb collection
    '''

    # make real request
    good_req = requests.get(path)

    # convert to soup object
    profile_good = BeautifulSoup(good_req.content, "lxml")

    # see if we got the error page
    if len(profile_good.prettify()) < 21000:
        print "error page for", user_id
    else:

        # make dict for mongo_db
        mongo_dict = {
            "user":user_id,
            "data":profile_good.prettify()
        }

        insert(collection, mongo_dict)

def insert(collection, dictionary):
    '''
    Using the provided collection attempt to add the provided dictionary
    to the collection. Check to see if the new dictionary being added
    already exists in the collection before adding.
    '''
    if not collection.find_one({"user": dictionary["user"]}):
        try:
            collection.insert_one(dictionary)
            print "inserted", dictionary["user"]

        except Exception, e:
            print e

    else:
        print dictionary["user"], "already exists"

if __name__ == "__main__":
    # connect to the hosted MongoDB instance
    client = MongoClient('mongodb://localhost:27017/')

    # connect to our mongodb indie game database collection
    db = client.capstone

    #indie game DB raw web scrape for users

    raw_user_scrape = db.raw_user_scrape

    scrape_user_to_db(raw_user_scrape)
