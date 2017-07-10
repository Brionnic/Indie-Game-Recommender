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

# import all of the spark stuff
import pyspark
from pyspark.sql.types import *
from pyspark.ml.tuning import TrainValidationSplit
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator

#
# Pipeline for model/system
#
# Scrape Data         -> Process data        -> Fit Model        -> Eval Model
#
# have game reviews     read in data         Prob easy           hmm
# for sparse crappy     into dataframe
# first model

def load_game_reviews_into_table(collection):
    '''
    Spark seems to ingest data via a big list and goes from there
    so make a dataframe that looks like

    user | app_id | rating (positive)
    '''
    start_time = time.time()
    data = []

    num_users = collection.find().count()

    for idx, user in enumerate(collection.find()):

        # keep track of users with reviews because the rest of
        # the users we have to go back and give 0's to
        #temp_user_list = []

        for ix, review in enumerate(user["data"]):

            try:
                #if re.search('[a-zA-Z]', user["user"]) == None:
                # username was too big for int, oops. This crashed spark
                # Making smaller...

                # integer val still too high, do a hack and just put the
                # index of the loop in for now.  It's shit because can't reverse
                # lookup the index back to the user but just get this working
                #_user = int(str(user["user"]).split("7656119")[1])
                _user = idx

                _appid = int(review["appid"])

                # potentially modify this to log time because then the
                # distribution is normal
                _playtime_m = int(review["playtime_forever"])


                _t = time.time() - start_time
                _ts = "{:2.2f}".format(_t)[:6]

                print "{}s ### {}th user of {} ### AppID:{} ###  {}\r".format(_ts, idx, num_users, _appid, ix),

                data.append({"app_id":_appid, "user": _user, "playtime_m":_playtime_m})
            except Exception, e:
                print
                print
                print "Something went wrong:", e
                print "user:", repr(_user)
                print "appid", repr(_appid)
                print "playtime_m", repr(_playtime_m)

    df = pd.DataFrame(data)

    print
    print "Completed."

    return df

def df_to_spark(data):
    '''
    clean up the columns a bit and convert to a spark df

    returns the spark dataframe
    '''
    data = data[["app_id", "user", "playtime_m"]]

    # convert to Spark DataFrame
    game_ratings_df = spark.createDataFrame(data)

    return game_ratings_df

# def main():
#     ''' like __name__ == "__main__"'''
#
#     # connect to the hosted MongoDB instance
#     db = MongoClient('mongodb://localhost:27017/')["capstone"]
#
#     source_collection = db.user_profile_scraping
#
#     # data = load_game_reviews_into_table(source_collection, user_list)
#     data = load_game_reviews_into_table(source_collection)
#
#     return data
#
#     #spark_game_ratings = df_to_spark(data)
#
#     #return spark_game_ratings

def prepare_dataframe():
    '''
    Returns a spark dataframe (hopefully)
    '''

    ########################################################################z
    ############ Read data from collection and build dataframe #############z
    ########################################################################z

    #connect to the hosted MongoDB instance
    db = MongoClient('mongodb://localhost:27017/')["capstone"]

    source_collection = db.user_profile_scraping

    print
    print "Established connection to MongoDB collection"

    data = load_game_reviews_into_table(source_collection)

    print
    print "Completed processing into pandas df, now convert to spark df"

    spark_game_ratings = df_to_spark(data)

    print
    print "Conversion to spark df complete. Now attempting to write \
            spark df to disk so we don't have to rebuilt it every time."

    # write the dataframe to disk to avoid having to rebuild constantly (~6min for 100 games)
    spark_game_ratings.write.parquet("game_user_playtimes.parquet", mode="overwrite", compression="gzip")

    print
    print "Seems like the write completed, now just show a summary of the df"
    print

    print spark_game_ratings.show(20)

    return spark_game_ratings

def load_dataframe(spark):
    '''
    Loads in the dataframe and returns it
    '''

    ########################################################################z
    ############ Read dataframe from disk after we've built it #############z
    ########################################################################z

    # read it in to make sure that it's working
    red_data = spark.read.parquet("game_user_playtimes.parquet")

    print "Seems like loading dataframe passed successfully"
    print
    print "Items in DataFrame:", red_data.count()
    print
    print "First twenty items in DF:"
    print red_data.show(20)

    print
    print "red_data.count() = ", red_data.count()

    return red_data






if __name__ == "__main__":
    # Build our Spark Session and Context
    spark = pyspark.sql.SparkSession.builder.getOrCreate()
    sc = spark.sparkContext
    spark, sc

    # if uncommented then build the dataframe
    # red_data = prepare_dataframe()

    # Get dataframe from disk instead of rebuilding it every time
    red_data = load_dataframe(spark)

    print
    print "attempting to split data into train/test/eval"

    # avoid fitting to final eval
    # set seed so we keep these out of the pool
    # (prob won't help as more data is added in the future and
    # the pool changes but this is paranoia anyways)
    train_test, final_eval = red_data.randomSplit([0.9, 0.1], seed=1337)

    # break the non-held back into train/test split
    train, test = train_test.randomSplit([0.8, 0.2])

    print "Train set count:", train.count()
    print "Test set count:", test.count()

    print
    print "Setting up model..."

    als_model = ALS(userCol="user",
               itemCol="app_id",
               ratingCol="playtime_m",
               nonnegative=True,
               regParam=0.05,
               rank=10,
               implicitPrefs=True,
               maxIter=20)

    print "Attempting to fit model on training data..."
    recommender = als_model.fit(train)

    # make a single row DataFrame
    temp = [(1, 413150)]
    columns = ('user', 'app_id')
    one_row_spark_df = spark.createDataFrame(temp, columns)

    # get U/V for this particular user and app
    user_factor_df = recommender.userFactors.filter('id = 1')
    item_factor_df = recommender.itemFactors.filter('id = 413150')

    # do more stuff?
    user_factors = user_factor_df.collect()[0]['features']
    item_factors = item_factor_df.collect()[0]['features']

    # figure out dot product for user_factors/item_factors
    print np.dot(user_factors, item_factors)
    print

    # get prediction for row
    print recommender.transform(one_row_spark_df).show()
    print

    print recommender.userFactors.show()
    print

    print "Transform the test set via recommender.transform"
    # make predictions on the whole test set
    predictions = recommender.transform(test)

    print
    print "Convert results to pandas to make final calcs easier"
    # dump the predictions to Pandas so the final calculations are easier to do

    predictions_df = predictions.toPandas()
    train_df = train.toPandas()

    print
    print "Pandas conversion should be complete, print out head of dataframe"
    print
    print predictions_df.head()
    print
    print

    # Fill any missing values with the mean rating
    # probably room for improvement here

    print "predictions.count():", predictions.count()

    # print the mean rating (1.0, uh... that's not good)
    #print "Mean rating:", train_df['rating'].mean()/predictions.count()
    print "Mean rating:", train_df['playtime_m'].mean()
    print


    print "Fill the n/a predictions with the mean rating for now"
    #predictions_df = predictions.toPandas().fillna(train_df['rating'].mean()/predictions.count())
    predictions_df = predictions.toPandas().fillna(train_df['playtime_m'].mean())

    print
    print "predictions.head(20)"
    print predictions_df.head(20)
