# to use pandas dataframes
import pandas as pd

import numpy as np

# import MongoDB modules
from pymongo import MongoClient

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

def load_pandas_df(path):
    """
    Loads in a pandas dataframe, specifically for user_avgs and game_avgs
    which will be used for weighting and also attempting to correct biases.

    Returns dataframe corresponding to the path
    """
    data = pd.read_csv(path)

    print "\nloaded data:"
    print data.head(10)
    print

    return data

def load_weights_to_dict(column, data):
    """
    Takes in the provided dataframe and extracts the column of weights desired
    into a dictionary for faster lookup

    returns dictionary with key=app_id, value=weight
    """
    #convert weights to a dictionary for hopefully faster lookup
    apps = np.array(data["app_id"].values).astype(int)
    weights = np.array(data[column].values)

    # combine into a 2d matrix
    temp_data = np.stack((apps, weights), axis=1)

    # make dictionary
    results = {}
    for item in temp_data:
        app = int(item[0])
        results[app] = item[1]

    print "\nLength of {} dictionary: {}".format(column, len(results))

    return results


def load_user_avgs_to_dict(column, data):
    """
    Takes in the provided dataframe and extracts the column of weights desired
    into a dictionary for faster lookup

    returns dictionary with key=app_id, value=weight
    """
    #convert weights to a dictionary for hopefully faster lookup
    apps = np.array(data["user_id"].values).astype(int)
    weights = np.array(data[column].values)

    # combine into a 2d matrix
    temp_data = np.stack((apps, weights), axis=1)

    # make dictionary
    results = {}
    for item in temp_data:
        app = int(item[0])
        results[app] = item[1]

    print "\nLength of {} dictionary: {}".format(column, len(results))

    return results

def load_game_reviews_into_table(collection):
    '''
    Spark seems to ingest data via a big list and goes from there
    so make a dataframe that looks like

    user | app_id | rating (positive)
    '''
    start_time = time.time()
    data = []

    game_avgs = load_pandas_df("app_means_v2.csv")
    user_avgs = load_pandas_df("user_avgs.csv")

    ##############################################################
    ## Build dictionary to try to speed up lookups of weights ####
    ##############################################################

    # make dictionaries for different weights
    w_s1_dict = load_weights_to_dict("weights_s1", game_avgs)

    w_s2_dict = load_weights_to_dict("weights_s2", game_avgs)

    w_s3_dict = load_weights_to_dict("weights_s3", game_avgs)

    game_avg_dict = load_weights_to_dict("avg_log_min", game_avgs)

    # user_id : avg_playtime_log_m
    user_avg_dict = load_user_avgs_to_dict("avg_playtime_log_m", user_avgs)

    user_lookup_table = {}
    user_reverse_lookup_table = {}

    num_users = collection.find().count()

    for idx, user in enumerate(collection.find()):

        # keep track of users with reviews because the rest of
        # the users we have to go back and give 0's to
        #temp_user_list = []

        # if idx > 10:
        #     break

        _user = idx

        user_lookup_table[idx] = user["user"]
        user_reverse_lookup_table[user["user"]] = idx

        # try to keep track of time some
        _t = time.time() - start_time
        _ts = "{:2.2f}".format(_t)[:6]

        # completed in 46s with mod to reduce printing
        # even without the mod check it was 46s so no savings
        #if idx % 100 == 0:
        print "{}s ### {}th user of {} ###### \r".format(_ts, idx, num_users),

        for idy, review in enumerate(user["data"]):
            # if idy > 1000:
            #     break


            _appid = int(review["appid"])

            #get weighting of app from game_avgs dataframe.
            # get weighting of a certain app


            # pull the weight from the game_avgs dataframe
            #result = game_avgs[game_avgs["app_id"] == _appid]["weights_s1"]
            try:
                weight_s1 = w_s1_dict[_appid]
                weight_s2 = w_s2_dict[_appid]
                weight_s3 = w_s3_dict[_appid]

                #import pdb; pdb.set_trace()
            except Exception, e:
                #print "Item not in dictionary   {}                       {}         {} ".format(e, repr(_appid), type(_appid))
                weight_s1 = 0.0
                weight_s1 = 0.0
                weight_s1 = 0.0

            # if len(result) > 0:
            #     weight = result.values[0]
            #     # if weight >= 0:
            #     #     if weight < 1:
            #     #         print "weight seems good", weight
            #     # elif weight < 0:
            #     #     print "############## Error, seems like it didn't match {}  correctly".format(repr(_appid))
            #     # else:
            #     #     print "##############{}  Error, seems like it didn't match {}  correctly".format(weight, repr(_appid))
            # else:
            #     weight = 0.0

            # if the weight is below zero then the game probably doesn't have any plays
            # (ie no data)

            # potentially modify this to log time because then the
            # distribution is normal

            # Goodnight sweet prince, going to log10 time now
            # _playtime_m = int(review["playtime_forever"])
            _log_playtime_m = int(review["playtime_forever"])

            if _log_playtime_m > 1:
                _log_playtime_m = np.log10(_log_playtime_m + 0.0001)
            else:
                _log_playtime_m = 0

            _lpm_b0s1 = _log_playtime_m * weight_s1
            _lpm_b0s2 = _log_playtime_m * weight_s2
            _lpm_b0s3 = _log_playtime_m * weight_s3
            # modify _log_playtime_m by the weighting of the app to
            # compensate for different app biases (ie low user count/high playtime)
            # or very high user counts
            _log_playtime_m

            data.append({"app_id":_appid,
                        "user": _user,
                        "log_playtime_m":_log_playtime_m,
                        "lpm_b0s1": _lpm_b0s1,
                        "lpm_b0s2": _lpm_b0s2,
                        "lpm_b0s3": _lpm_b0s3})

        # except Exception, e:
        #     print
        #     print
        #     print "Something went wrong:", e
        #     print "user:", repr(_user)

    print "\n Converting list of dictionaries into dataframe..."

    df = pd.DataFrame(data)

    print "\nData now in pandas dataframe format"

    # now that the inital dataframe of ratings has been built try to
    # find the mean of the whole df and use that to calulate ratings
    # with the biases removed

    # print "##################################################################"
    # print "##################################################################"
    # print "##################################################################"
    #
    # print df.head()
    #
    # mu = df.log_playtime_m.mean()
    # print "mu", mu
    #
    #
    # df["o_user"] = df["user"].apply(lambda x: user_lookup_table[x])
    #
    # #import pdb; pdb.set_trace()
    #
    # df["annie"] = df["o_user"].apply(lambda x: mu - try_dict(user_avg_dict, int(x), mu))

    # df["b1_s1"] = df["log_playtime_m"] - \
    #         df["o_user"].apply(lambda x: user_avg_dict[int(x)]) -\
    #         df["app_id"].apply(lambda y: game_avg_dict[y])


    print
    print "Completed."

    return df

def try_dict(_dict, item, mu):
    '''
    tries to find item in dict, handles key error if it doesn't exist
    '''
    try:
        #print "\n%%%%%%%%%%%%%%%", _dict[item]
        return _dict[item]
    except Exception, e:
        return mu

def df_to_spark(data):
    '''
    clean up the columns a bit and convert to a spark df

    returns the spark dataframe
    '''
    print "\n\n$$$$$$$$$$$$$$$$$$$$$$$$$$$ Data Head(20):"
    print data.head(20)

    # reorder the columns because we built the dataframe from a dictionary
    # that had no concept of order
    data = data[["app_id", "user", "log_playtime_m", "lpm_b0s1", "lpm_b0s2", "lpm_b0s3"]]
    #print repr(data.keys())
    #data = data[[data.keys()]]

    print "\n\n$$$$$$$$$$$$$$$$$$$$$$$$$$$ Data Head(20):"
    print data.head(20)

    start_time = time.time()
    print "\nStarting to process pandas DF to spark DF..."

    # convert to Spark DataFrame
    #
    #   Simple old way
    #
    #game_ratings_df = spark.createDataFrame(data)

    # convert to Spark Dataframe via sharding in order to try to speed things
    # up a lot
    #
    #   Sharding:
    #

    # figure out the length of the source dataframe
    # subtract 1 because we're going to start out with a spark dataframe
    # that is seeded with the last row of data
    num_items = len(data)

    # declare how many shards to break the data into, has to be enough to make
    # the shards easier for spark to process, but not so small to make it
    # actually take longer. For testing just try 10
    steps = 1000

    # figure out how many rows per step
    step_width = num_items // steps

    # figure out how big the last, leftover step is:
    remainder = num_items % step_width

    # arrays/lists are 0 indexed so len of items is the last index
    print "\nCreate the seed of the spark dataframe"

    print data[num_items-5:]
    print
    print

    spark_df = spark.createDataFrame(data[num_items-5:num_items])

    # compensate for the seed
    num_items -= 5

    # iterate through for loop to take each step
    for step in xrange(steps):
        print "{:4.2f} Starting shard {:2d}/{:2d}\r".format(time.time() - start_time, step+1, steps),

        # see if a light sleep makes the logging to console smoother
        time.sleep(0.01)
        # create a temp dataframe from the shard
        temp_df = spark.createDataFrame(data[step_width * step: step_width * (step+1)])

        # concatenate the existing spark_df and the new temp
        spark_df = spark_df.unionAll(temp_df)

    # take care of the remainder items
    temp_df = spark.createDataFrame(data[step_width * steps + 1:])
    # concatenate the existing spark_df and the new temp
    spark_df = spark_df.unionAll(temp_df)

    print
    print "\nlength of data:", len(data)
    print "\nlength of spark_df:", spark_df.count()

    print "\n Completed operation in {:3.2f}s".format(time.time()-start_time)
    return spark_df




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
    print "Completed processing into pandas df."
    print "Size of pandas df:", len(data)
    print "now convert to spark df"

    spark_game_ratings = df_to_spark(data)

    print
    print "Conversion to spark df complete. Now attempting to write \
            spark df to disk so we don't have to rebuilt it every time."

    # write the dataframe to disk to avoid having to rebuild constantly (~6min for 100 games)
    # write the dataframe to disk using a lame sort of file system to indicate
    # what kind of weights and bias have been used to generate that file
    #
    # b0 = no bias implemented      b1 = "netflix bias" has been implemented
    # s1 = weighting stage 1 (only low unique player games weighted)
    # s2 = weighting stage 2 (low unique players weighted and very high players weighted linearly)
    # s3 = weighting stage 3 (low unique players weighted and very high players weighted exponentially)
    spark_game_ratings.write.parquet("test_v_matrix_b0s1.parquet", mode="overwrite", compression="gzip")

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

    print "spark memory:", sc._conf.get('spark.driver.memory')

    time.sleep(2)

    # if uncommented then build the dataframe
    red_data = prepare_dataframe()

    # Get dataframe from disk instead of rebuilding it every time
    # red_data = load_dataframe(spark)

    # print
    # print "attempting to split data into train/test/eval"
    #
    # # avoid fitting to final eval
    # # set seed so we keep these out of the pool
    # # (prob won't help as more data is added in the future and
    # # the pool changes but this is paranoia anyways)
    # train_test, final_eval = red_data.randomSplit([0.9, 0.1], seed=1337)
    #
    # # break the non-held back into train/test split
    # train, test = train_test.randomSplit([0.8, 0.2])
    #
    # print "Train set count:", train.count()
    # print "Test set count:", test.count()
    #
    # print
    # print "Setting up model..."
    #
    # als_model = ALS(userCol="user",
    #            itemCol="app_id",
    #            ratingCol="playtime_m",
    #            nonnegative=True,
    #            regParam=0.05,
    #            rank=10,
    #            implicitPrefs=True,
    #            maxIter=20)
    #
    # print "Attempting to fit model on training data..."
    # recommender = als_model.fit(train)
    #
    # # make a single row DataFrame
    # temp = [(1, 413150)]
    # columns = ('user', 'app_id')
    # one_row_spark_df = spark.createDataFrame(temp, columns)
    #
    # # get U/V for this particular user and app
    # user_factor_df = recommender.userFactors.filter('id = 1')
    # item_factor_df = recommender.itemFactors.filter('id = 413150')
    #
    # # do more stuff?
    # user_factors = user_factor_df.collect()[0]['features']
    # item_factors = item_factor_df.collect()[0]['features']
    #
    # # figure out dot product for user_factors/item_factors
    # print np.dot(user_factors, item_factors)
    # print
    #
    # # get prediction for row
    # print recommender.transform(one_row_spark_df).show()
    # print
    #
    # print recommender.userFactors.show()
    # print
    #
    # print "Transform the test set via recommender.transform"
    # # make predictions on the whole test set
    # predictions = recommender.transform(test)
    #
    # print
    # print "Convert results to pandas to make final calcs easier"
    # # dump the predictions to Pandas so the final calculations are easier to do
    #
    # predictions_df = predictions.toPandas()
    # train_df = train.toPandas()
    #
    # print
    # print "Pandas conversion should be complete, print out head of dataframe"
    # print
    # print predictions_df.head()
    # print
    # print
    #
    # # Fill any missing values with the mean rating
    # # probably room for improvement here
    #
    # print "predictions.count():", predictions.count()
    #
    # # print the mean rating (1.0, uh... that's not good)
    # #print "Mean rating:", train_df['rating'].mean()/predictions.count()
    # print "Mean rating:", train_df['playtime_m'].mean()
    # print
    #
    #
    # print "Fill the n/a predictions with the mean rating for now"
    # #predictions_df = predictions.toPandas().fillna(train_df['rating'].mean()/predictions.count())
    # predictions_df = predictions.toPandas().fillna(train_df['playtime_m'].mean())
    #
    # print
    # print "predictions.head(20)"
    # print predictions_df.head(20)
    #
    # print
    # print "Try to figure out the squared error of predictions"
    # predictions_df['squared_error'] = (predictions_df['playtime_m'] - predictions_df['prediction'])**2
    #
    # print
    # print "Print description of the predictions"
    # print predictions_df.describe()
    #
    # print
    #
    # print "Calculate RMSE:"
    # # Calculate RMSE
    # print np.sqrt(sum(predictions_df['squared_error']) / len(predictions_df))
    #
    # # run  val
    # # 1    0.078012435752783327
    # # 2    0.079067974734729068
