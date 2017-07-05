# Author: Brian Hardenstein
# pixelatedbrian@gmail.com

def collect_users(user_list, collection):
    '''
    Takes in a list of users and attempts to pull their profile.
    If we successfully pull their profile then store it in
    MongoDB.

    There are two types of users and so two different urls/paths
    to find their info.

    user type 1: number_id
    user type 2: named alias for profile
    '''

    # step through the users in the list
    for user in user_list:

        # see if it is a numberic ID or an actual profile alias:
        if user[:5] == "76561":

            # it's a numeric profile
            path = "numeric profile path"

        else:

            # its not a numeric profile
            path = "non-numeric path"

        attempt_to_get_user_profile(user, path, collection)

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

def get_users(filepath):
    '''
    Read in the filename into a list of users

    Returns:
    list of users
    '''

    with open(filepath, "r") as source_file:

        # can we read in a file to a list with list comprehension?
        users = [line for line in source_file]

        return users

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
    # connect to the hosted MongoDB instance and get the capstone DB
    client = MongoClient('mongodb://localhost:27017/')["capstone"]

    #indie game DB raw web scrape for users
    dest_collection = db.game_review_user_scrape

    # get list of users
    users = get_users("data/username_dump.txt")

    # get the users
    collect_users(users, dest_collection)
