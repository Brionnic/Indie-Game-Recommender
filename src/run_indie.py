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

def score(column):
    #####################################
    ####### Section for scoring RMSE #########
    #####################################

    # try to load test matrix
    file_name = "v_matrix_{}.parquet".format(column)

    # log RMSE filename
    rmse_file = "new_nan_to_mean_rmse_{}.csv".format(column)
    first_row = "rmse_train, rmse_test, rank\n"

    with open(rmse_file, "w") as outfile:
        outfile.write(first_row)

    print "\nFind the score of the mean as a 'model' first"
    igr = IndieGR(column, 1, file_name)
    igr.split_train_test_eval()
    igr.train_model()
    av_train_rmse, av_test_rmse = igr.evaluate_average_RMSE()

    # write the average RMSEs to a file
    with open("new_baseline_RMSEs.csv", "a") as rmse_outfile:
        _output = "{}, {}, {}\n".format(column, av_train_rmse, av_test_rmse)
        rmse_outfile.write(_output)

    # loop for however many steps that are desired
    for x in range(1, 11, 1):
        rank = x
        print "##################################"
        print "####  Test model for rank: {}".format(rank)
        print "##################################"

        igr = IndieGR(column, rank, file_name)
        # igr = IndieGR(column, "v_matrix_b0s1.parquet")

        # shard for cross validation
        igr.split_train_test_eval()

        # train the model on the training data
        igr.train_model()

        # comment out when we don't care
        train_rmse, test_rmse = igr.evaluate_RMSE(1)

        add_line = "{}, {}, {}\n".format(train_rmse, test_rmse, rank)

        with open(rmse_file, "a") as outfile:
            outfile.write(add_line)

def get_predictions(column):
    '''
    Load data from parquet format and show predictions of existing users.
    Make a while loop so multiple users can be looked at.
    Column specifies which parquet file to load in order to access different
    types of weighting and/or model iterations.
    '''

    # try to load test matrix
    file_name = "v_matrix_{}.parquet".format(column)

    print "Loading {}....".format(file_name)

    # column to use, 3 is the rank, which file to use
    igr = IndieGR(column, 25, file_name)
    igr.split_train_test_eval()
    igr.train_model()

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
        # get 25 predictions so we can remove the duplicates from train
        # and still have ~10 predictions
        results = igr.predict_existing_user(user_id, 25)
        test = igr.grab_existing_user_test(user_id)
        train = igr.grab_existing_user_train(user_id)

        print "\nconverting results to Pandas DF"
        # prepare for looking at test/train/predicted data
        test_pd = test.toPandas()
        train_pd = train.toPandas()
        lookup = GameIndexer()

        print "\nmake new column for the title of the games so it's human readable"
        test_pd["title"] = [lookup.game_index_to_title(app, 40) for app in test_pd["appind"]]
        train_pd["title"] = [lookup.game_index_to_title(app, 40) for app in train_pd["appind"]]
        # sort the data so it makes more sense for human
        print "\nsorting dataframes by playtimes"
        sort_train_df = train_pd.sort_values(column, ascending=False)
        test_pd = test_pd.sort_values(column, ascending=False)

        print "\nSorted Train DataFrame:"
        print sort_train_df.head(20)
        print
        print
        print "\nSorted Test DataFrame:"
        print test_pd.head(20)
        print
        #igr.print_sorted_predictions()

        igr.print_filtered_predictions(train_pd, test_pd, 10)

        result = raw_input("Do another? (y/n)")

        if result.lower() == "n":
            get_more = False
        elif result.lower() == "y":
            get_more = True


def serialize(column):
    '''
    Write CSV files for the U/V matrix decompositions in order
    to make fast predictions for webpage/user interface
    '''

    # try to load test matrix
    file_name = "v_matrix_{}.parquet".format(column)





if __name__ == '__main__':
    # appind  lpm_b0_s0  lpm_b0_s1  lpm_b0_s2  lpm_b0_s3  user
    columns = ["lpm_b0_s0", "lpm_b0_s1", "lpm_b0_s2", "lpm_b0_s3"]
    column = columns[1]

    #score(column)

    get_predictions(column)
