# to use pandas dataframes
import pandas as pd

import numpy as np

# import MongoDB modules
from pymongo import MongoClient

# we can always use more time
import time

# import all of the spark stuff
import pyspark as ps
from pyspark.sql.types import *
from pyspark.ml.tuning import TrainValidationSplit
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
import pyspark.sql.functions as F

class Model_s1():
    """
    Basic Spark ALS with no fancy anything
    """

    def fit(self, training_df):
        self.als = ALS(rank=50,
            maxIter=10,
            regParam=0.1,
            userCol="user",
            itemCol="app_id",
            ratingCol="playtime_m")

        self.s1_model = self.als.fit(training_df)

    def transform(self, requests_df):
        '''
        Return predictions from model
        '''
        return (self.s1_model.transform(requests_df))

class Model_s2():
    """
    Basic Spark ALS with NANs replace by mean of all game playtimes
    """

    def fit(self, training_df):
        self.avg_ratings = training_df.select("app_id", "playtime_m")\
                                        .groupBy("app_id")\
                                        .agg(F.avg("playtime_m"))\
                                        .withColumnRenamed("avg(playtime_m)", "avg_playtime_m")

    def transform(self, requests_df):
        return (requests_df.join(self.avg_ratings, "app_id", "left"))\
                            .withColumnRenamed("avg_playtime_m", "prediction")

class GameRecommender():
    """
    Initialize class

    parquet_path so we can spark.read.parquet("game_user_playtimes.parquet")
    """
    def __init__(self, parquet_path="game_user_playtimes.parquet"):
        self.spark = ps.sql.SparkSession.builder \
                    .master("local[4]") \
                    .appName("df lecture") \
                    .getOrCreate()
        self.sc = self.spark.sparkContext  # for the pre-2.0 sparkContext
        self.model_stage_1 = Model_s1()
        self.model_stage_2 = Model_s2()

        # load data to model
        self.core_data = self.load_dataframe(parquet_path)

        # split into train, test, eval
        self.train, self.test, self.eval = self.split_train_test_eval()

        # make a holder for predictions which starts as None
        self.predictions = None

        # make holders for user factor dataframe and item factor dataframe
        # essentially U and V matrices coming from the transform via NMF/ALS

        # user factors
        self.U = None

        # item factors
        self.V = None

    def split_train_test_eval(self):
        """
        Take in the core data frame and split into:
        train, test, and evaluate sets

        returns 3 spark dataframes:
        train, test, evals
        """
        # avoid fitting to final eval
        # set seed so we keep these out of the pool
        # (prob won't help as more data is added in the future and
        # the pool changes but this is paranoia anyways)
        train_test, final_eval = self.core_data.randomSplit([0.9, 0.1], seed=1337)

        # break the non-held back into train/test split
        train, test = train_test.randomSplit([0.8, 0.2])

        print "Train set count:", train.count()
        print "Test set count:", test.count()
        print "Eval set count:", final_eval.count()

        return train, test, final_eval


    def load_dataframe(self, parquet_path):
        """
        Loads in the dataframe and returns it
        """

        ########################################################################z
        ############ Read dataframe from disk after we've built it #############z
        ########################################################################z

        # read it in to make sure that it's working
        red_data = self.spark.read.parquet(parquet_path)

        print "Seems like loading dataframe passed successfully"
        print
        print "Items in DataFrame:", red_data.count()
        print
        print "First twenty items in DF:"
        print red_data.show(20)

        print
        print "red_data.count() = ", red_data.count()

        return red_data

    def evaluate_model(self):
        '''

        '''

    def fit(self):
        """
        Trains the recommender on a given set of ratings.
        (Implicit from playtime_m)

        Parameters
        ----------
        ratings : pandas dataframe, shape = (n_ratings, 3)
                  with columns 'user', 'appid', 'playtime_m'
        Returns
        -------
        self : object
            Returns self.
        """

        self.train.persist()

        print
        print "Starting fit model v0"

        self.model_stage_1.fit(self.train)

        print
        print "Starting fit model v1"
        self.model_stage_2.fit(self.train)

        #import pdb; pdb.set_trace()

        # print "\nStoring calculated U/V matrices"
        # self.U = self.model_stage_1.userFactors
        # self.V = self.model_stage_1.itemFactors
        #
        # print "\n\nShow first five of U"
        # print self.U.show(5)
        #
        # print "\n\nShow first five of V"
        # print self.V.show(5)

        print "\nFinishing fit"
        return(self)

    def transform(self):
        """
        Predicts the ratings for a given set of requests.
        Parameters
        ----------
        requests : pandas dataframe, shape = (n_ratings, 2)
                  with columns 'user', 'appid'
        Returns
        -------
        dataframe : a *pandas* dataframe with columns:
                    'user', 'movie', 'predicted_playtime_m'
                    column 'predicted_playtime_m' containing
                    the predicted rating
        """
        print "\nStarting to predict"
        #print("\nrequest count: {}".format(self.test.shape[0]))

        pred_loop_s1 = self.model_stage_1.transform(self.test)\
                        .withColumnRenamed('prediction','prediction_loop_s1')

        print "\nStarting to predict stage 2"
        pred_loop_s2 = self.model_stage_2.transform(pred_loop_s1)\
                        .withColumnRenamed('prediction','prediction_loop_s2')

        print "\nDo some SQLey sparkdf stuff"
        results_loop_s2 = pred_loop_s2.withColumn('prediction',
                                        F.when(F.isnan('prediction_loop_s1'),
                                        F.col('prediction_loop_s2'))\
                                        .otherwise(F.col('prediction_loop_s1')))

        print "\nSeems like spark SQLey stuff went through"

        print "\nConverting to Pandas df"
        predictions = results_loop_s2.select('user', 'app_id', 'prediction')\
                                   .withColumnRenamed('prediction','playtime_m')\
                                   .toPandas()

        print "Finishing predict"
        self.predictions = predictions

    def return_predictions(self):
        """
        Returns the predictions dataframe if it is needed for some reason.
        """

        return self.predictions

    def evaluate(self):
        """
        Looks at predicted values vs actual values and figures out
        RMSE

        Prints out RMSE

        Returns:
        RMSE as a float
        """
        pass

    def predict(self, U_o, num_predictions=10):
        """
        Takes in a new user row and makes predictions on it.

        ALS is a form of NMF dimensionality reduction.  NMF gives us two
        matrices:  U and V   from a 2d matrix that is (M x N) ie (users * apps)

        U is the decomposed user factors
        V is the decomposed application factors

        U_o * V.T => U_ov sort of synthetic entry in U for the U_o data
            ^ Dot product

        Then to get the actual predictions we want from the model:
        U_ov * V => predictions
             ^ Dot product

        ############## Stretch goal ######################
        Can optimize this some by taking the subset of V.T that matches the
        apps that have been rated in U_o.  This should speed things up a lot.
        ##################################################

        Sort the predictions in order descending and return the k amount of
        predictions

        Returns a list of predictions sorted in order from highest to lowest
        """
