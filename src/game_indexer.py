import csv
import pandas as pd
import numpy as np

class GameIndexer(object):

    def __init__(self):
        '''
        Load in the data with a baked in path
        '''

        print "attemping to load game data..."
        self.game_info_dict = self.load_game_info_csv("../data/game_info.csv")

        # load in the game indices
        self.game_indices = self.load_game_indices()

        # build a reverse lookup dictionary so we can also go from
        # app_id to index when needed
        self.reverse_game_indices = self.build_index_reverse_lookup()

        print "loaded {} games into index.".format(len(self.game_info_dict))

    def app_id_to_game_index(self, app_id):
        '''
        Take in an app_id and

        return an index value
        '''
        return self.reverse_game_indices[app_id]

    def game_index_to_app_id(self, index):
        '''
        Take in game index and

        return a app_id
        '''
        return self.game_indices[index, 1]

    def game_index_to_title(self, index, title_len=0):
        '''
        Take in a game index and

        return the title of the matching game
        '''
        app_id = self.game_index_to_app_id(index)

        if title_len == 0:
            return self.return_game_title(app_id)
        else:
            return self.return_game_title(app_id, title_len)

    def build_index_reverse_lookup(self):
        '''
        We need a dictionary so we can convert an app_id into an index quicky
        '''

        # game[0] = index, game[1] = app_id
        return {game[1]:game[0] for game in self.game_indices}

    def load_game_indices(self, path="wrangling/app_indices.csv"):
        '''
        Load in a dataframe from CSV and convert it to a numpy array
        as well as a dictionary for reverse lookup
        '''
        data = pd.read_csv(path)
        data.columns = ["junk", "index", "game"]
        data.pop("junk")
        return data.values

    def return_game_title(self, app_id, limit_len=0):
        '''
        Takes in app_id, if it's not a string convert to string
        then look for the title that corresponds to that app_id

        returns:
        Title as a string
        '''
        if type(app_id) != str:
            app_id = str(app_id)

        _title = self.game_info_dict[app_id]["title"].replace("_", " ")

        if limit_len != 0:
            return _title[limit_len]
        else:
            return _title

#         if app_id in self.game_info_dict:
#             return self.game_info_dict[app_id]["title"]
#         else:
#             print "App_id", app_id, "not found."
#             return None


    def load_game_info_csv(self, path):
        '''
        Loads the CSV that has app_id, title, and url

        returns:
        data as dictionary
        '''

        return_dict = {}

        with open(path, "r") as csvfile:

            # read in the game data
            g_data = csv.reader(csvfile, delimiter=",")

            for idx, row in enumerate(g_data):
                #game_info = row.split(",")

                # game info looks like
                # ['', 'app_id', 'title', 'url']
                # ['0', '367520', 'Hollow_Knight', 'http://steamcommunity.com/app/367520/reviews/?p=']

                if idx != 0:
                    # create a dictionary for this game using the game_info
                    game_dict = {"app_id": row[1], "title": row[2], "url":row[3]}

                    return_dict[str(row[1])] = game_dict

#                     if idx == 1:
#                         print game_dict

        return return_dict

    def return_list_of_all_apps(self):
        '''
        Simply returns a list with all of the app_ids
        '''
        return self.game_info_dict.keys()
