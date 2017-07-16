# to use pandas dataframes
import pandas as pd

import numpy as np

# import MongoDB modules
from pymongo import MongoClient

import matplotlib.pyplot as plt

# we can always use more time
import time

# not tormented enough? try regex
import re

from process_playtime_to_df import load_game_reviews_into_table

#connect to the hosted MongoDB instance
db = MongoClient('mongodb://localhost:27017/')["capstone"]

source_collection = db.user_profile_scraping

mxn_data = load_game_reviews_into_table(source_collection)

print mxn_data.head(10)

print "\nwriting data to csv"
mxn_data.to_csv("mxn_data.csv")
