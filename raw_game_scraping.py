

# version v0.12

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



def scrape_to_collection(path, collection, pages):
    '''
    Attempt to scrape <pages> amount of web pages at <path> + <pages> URL
    Don't process these pages, simply store them in a mongoDB
    as very simple dictionaries in the format:

    game_page = {"page":<page + page#>, "data":<web page data>}

    use the insert_to_collection method to try to insert the data
    into the specified collection while avoiding duplication if possible
    '''
    # try to scrape the indie game data from all pages, inserting the unique pages into the mongoDB
    # there's 656 pages, according to http://store.steampowered.com/search/?tags=492&page=1

    # path = 'http://store.steampowered.com/search/?tags=492&page='

    # loop one time for each page request (~700 to try to get them all in case of weirdness)
    for idx in range(pages):

        # pause for a moment before starting
        snooze = random.random() * 1.0
        print "Sleeping for: {:0.2f}".format(snooze),

        time.sleep(snooze)

        # generate the path for this current page
        # ex: path = 'http://store.steampowered.com/search/?tags=492&page=247'
        true_path = path + str(idx)

        # make the request for the true path
        req = requests.get(true_path)

        print " </\> Requested Page:", idx, "with response:", str(req)

        # convert to beautifulsoup
        soup = BeautifulSoup(req.content, "lxml")

        # make a dictionary with page number and the contents

        soup_dict = {
            "page":"page_" + str(idx),
            "data":soup.prettify()
        }

        #print "Contents:" + str(soup)[:500]

        insert(collection, soup_dict)

        # provide some whitespace
        print

def insert(collection, dictionary):
    '''
    Attempts to uniquely insert dictionary into collection
    '''
    if not collection.find_one({"page": dictionary["page"]}):
        try:
            collection.insert_one(dictionary)
            print "inserted", dictionary["page"]

        except Exception, e:
            print e

    else:
        print "already exists"

if __name__ == "__main__":
    # connect to the hosted MongoDB instance with the database that we want
    db = MongoClient('mongodb://localhost:27017/')["capstone"]

    # establish required variables for use:

    # collection to store scraped information in
    collection = db.game_list_scrape

    # how many pages to scrape (as of June 20th, 2017)
    # should be 670
    _pages = 670

    # url to scrape (as of June 20th, 2017)
    _path = 'http://store.steampowered.com/search/?tags=492&page='

    # call the actual scraping function (good luck!)
    scrape_to_collection(_path, collection, _pages)
