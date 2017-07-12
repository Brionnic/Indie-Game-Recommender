# import all of the spark stuff
import pyspark as ps
from pyspark.sql.types import *
from pyspark.ml.tuning import TrainValidationSplit
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
import pyspark.sql.functions as F

import pandas as pd
import numpy as np

from GameRecommenderModel import GameRecommenderModel
from game_indexer import GameIndexer
from IndieGR import IndieGR

if __name__ == '__main__':
    igr = IndieGR()

    # shard for cross validation
    igr.split_train_test_eval()

    # train the model on the training data
    igr.train_model()

    # comment out when we don't care
    rmse = igr.evaluate_RMSE()

    get_more = True

    while get_more == True:

        print "Enter user_id to get data on: (ex: 104)"
        print "if you enter other stuff it's going to hang, you break it you bought it"
        user_id = int(raw_input("user_id="))

        print "##############################################"
        print
        print "User_ID:", repr(user_id)
        print
        print "##############################################"

        print "\nGet predictions on user_id {}".format(user_id)
        results = igr.predict_existing_user(user_id)
        test = igr.grab_existing_user_test(user_id)
        train = igr.grab_existing_user_train(user_id)

        print "\nconverting results to Pandas DF"
        # prepare for looking at test/train/predicted data
        test_pd = test.toPandas()
        train_pd = train.toPandas()
        lookup = GameIndexer()

        print "\nmake new column for the title of the games so it's human readable"
        test_pd["title"] = [lookup.return_game_title(app, 30).replace("_", " ") for app in test_pd["app_id"]]
        train_pd["title"] = [lookup.return_game_title(app, 30).replace("_", " ") for app in train_pd["app_id"]]

        # sort the data so it makes more sense for humans
        print "\nsorting dataframes by playtimes"
        sort_train_df = train_pd.sort_values("log_playtime_m", ascending=False)
        test_pd = test_pd.sort_values("log_playtime_m", ascending=False)

        print "\nSorted Train DataFrame:"
        print sort_train_df.head(100)
        print
        print
        print "\nSorted Test DataFrame:"
        print test_pd.head(20)
        print
        igr.print_sorted_predictions()

        result = raw_input("Do another? (y/n)")

        if result.lower() == "n":
            get_more = False
        elif result.lower() == "y":
            get_more = True
