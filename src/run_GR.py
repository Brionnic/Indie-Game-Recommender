# to use pandas dataframes
import pandas as pd

import numpy as np

# import MongoDB modules
from pymongo import MongoClient

# we can always use more time
import time

# import the class that handles this stuff
from GameRecommender import GameRecommender

if __name__ == "__main__":

    recommender = GameRecommender()

    recommender.fit()
