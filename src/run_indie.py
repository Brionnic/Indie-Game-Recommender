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

    print "\nGet predictions on current user_id entered"
    results = igr.predict_existing_user(104)
    test = igr.grab_existing_user_test(104)
    train = igr.grab_existing_user_train(104)

    print "\nconverting results to Pandas DF"
    # prepare for looking at test/train/predicted data
    test_pd = test.toPandas()
    train_pd = train.toPandas()
    lookup = GameIndexer()

    print "\nmake new column for the title of the games so it's human readable"
    test_pd["title"] = [lookup.return_game_title(app).replace("_", " ") for app in test_pd["app_id"]]
    train_pd["title"] = [lookup.return_game_title(app).replace("_", " ") for app in train_pd["app_id"]]

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
