'''
Read in raw user webpages from MongoDB and extract the games that the user
has played as well as how many hours the user has played each game
Create a master dictionary that contains the user_id: val for one key/value
pair and then create a data: {} key/value pair where the dictionary value is
a dictionary of the game titles that a user has and then the hours that the
user has played the game.
'''

# import MongoDB modules
from pymongo import MongoClient

# can always use more time
import time

def insert(collection, dictionary, match_key):
    '''
    Abstracted insert method which, attempts to add the dictionary to the
    provided collection in MongoDB.

    The method attempts to avoid duplicate inserts by checking the collection
    to see if there's already an item who's key matches the one being inserted.
    If there is a matching item then the new one is not inserted.
    '''
    if not collection.find_one({match_key: dictionary[match_key]}):
        try:
            collection.insert_one(dictionary)
            print "inserted", dictionary[match_key]

        except Exception, e:
            print "Execption when attempting to insert into collection:", e

    else:
        print match_key, "already exists"


def get_userinfo_from_doc(document):
    '''
    Extracts the user info from the user all games owned website into a dictionary with the username as one
    key/value and then a list of user_game_data as the user_game_data value.


    Ex:  {"user": "bob", user_game_data: [{game_1}, {game_2"}, {etc}]}
    Ex: game_1 = {"game_name":_name, "app_id":_appid, "hours_played":_hours_played, "last_played":_last_played}

    returns:
    the dictionary specified above
    '''
    data = document["data"].lower()

    # remove useless front part of data
    data = data[data.index("var rggames = [".lower()):(3+data.index("}}];".lower()))]

    # attempt to split the block of game info into sub-blocks specific to each game
    raw_user_game_data = data.split("},{")

    # be overly explicit in where each variable will be stored which will assemble
    # the dictionary specific for each user's game playtime, name, etc
#     _name = ""
#     _appid = ""
#     _hours_played = ""
#     _last_played = ""

    # make a list to hold the individual game info dictionaries
    game_info = []

    # raw_user_data is a list of game data so walk over that and process each
    # item into a dictionary to be added to the overall user profile
    for raw_game_info in raw_user_game_data:

        # split the individual raw_game_info into each specific attribute
        raw_game_attributes = raw_game_info.split(",")

        # walk all of the attributes
        for item in raw_game_attributes:
#             print attribute

            if "appid" in item:
                _appid = item.split(":")[1]

            if "name" in item:
                _name = item[7:]

            if "hours_forever" in item:
                _hours_played = float(item.split(":")[1].strip('"'))

            if "last_played" in item:
                _last_played = int(item.split(":")[1])

        this_game_info_dict = {"game_name":_name, "app_id":_appid, "hours_played":_hours_played, "last_played":_last_played}
        #print
        game_info.append(this_game_info_dict)

        #print this_game_info_dict

        #print sub_info

    # make the total player game data dictionary:
    player_dict = {"player":document["user"], "game_data": game_info}

    # return to caller
    return player_dict


def digest_user_info_into_collection(source_collection, destination_collection):
    '''
    Takes in a source collection of MongoDB. For each document in that collection
    call get_userinfo_from_doc to extra the data that we need. Temporarily
    store that information and then insert it into the destination_collection.
    '''

    start_size = destination_collection.find().count()
    print "Length of destination collection at start:", start_size


    # pause for a few minutes so user can see starting size of collection
    time.sleep(3)

    # loop over source_collection
    for doc in source_collection.find():

        # extract data from raw web page into a dictionary
        temp_data = get_userinfo_from_doc(doc)

        # add the cleaned data to the proper collection
        insert(destination_collection, temp_data, "player")

    # after the work is done check the finished size
    final_size = destination_collection.find().count()

    # print how many items were added to the collection
    print "Added", final_size - start_size, "to the collection."

if __name__ == '__main__':
    # connect to the hosted MongoDB instance with the database that we want
    db = MongoClient('mongodb://localhost:27017/')["capstone"]

    # collection to pull scraped information from
    source_collection = db.raw_user_scrape

    # collection to store digested information in
    dest_collection = db.user_data_digest


    digest_user_info_into_collection(source_collection, dest_collection)
