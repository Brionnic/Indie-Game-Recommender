import csv

class GameIndexer(object):

    def __init__(self):
        '''
        Load in the data with a baked in path
        '''
        self.game_info_dict = self.load_game_info_csv("../data/game_info.csv")

    def return_game_title(self, app_id, limit_len=0):
        '''
        Takes in app_id, if it's not a string convert to string
        then look for the title that corresponds to that app_id

        returns:
        Title as a string
        '''
        if type(app_id) != str:
            app_id = str(app_id)

        _dict = self.game_info_dict[app_id]

        if limit_len != 0:
            return _dict["title"][:limit_len]

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
