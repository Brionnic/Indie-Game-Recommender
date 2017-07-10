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

class GameRecommender_v0():
    '''
    Basic Spark ALS with no fancy anything
    '''

    def fit(self, training_df):
        self.als = ALS(rank=100,
            maxIter=10,
            regParam=0.1,
            userCol="user",
            itemCol="app_id",
            ratingCol="playtime_m")

        self.v0_model = self.als.fit(training_df)

    def transform(self, requests_df):
        '''
        Return predictions from model
        '''
        return (self.v0_model.transform(requests_df))

class GameRecommender_v1():
    '''
    Basic Spark ALS with NANs replace by mean of all game playtimes
    '''

    def fit(self, training_df):
        self.avg_ratings = training_df.select("app_id", "playtime_m")\
                                        .groupBy("app_id")\
                                        .agg(F.avg("playtime_m"))\
                                        .withColumnRenamed("avg(playtime_m)")

    def transform(self, requests_df):
        return (requests_df.join(self.avg_ratings, "app_id", "left"))\
                            .withColumnRenamed("avg_rating", "prediction")

class GameRecommender():
    """Initialize class

    parquet_path so we can spark.read.parquet("game_user_playtimes.parquet")
    """
    def __init__(self, parquet_path="game_user_playtimes.parquet"):
        self.spark = ps.sql.SparkSession.builder \
                    .master("local[4]") \
                    .appName("df lecture") \
                    .getOrCreate()
        self.sc = self.spark.sparkContext  # for the pre-2.0 sparkContext
        self.gr_v0 = GameRecommender_v0()
        self.gr_v1 = GameRecommender_v1()

        # load data to model
        self.core_data = self.load_dataframe(parquet_path)

        # split into train, test, eval
        self.train, self.test, self.eval = self.split_train_test_eval()

    def split_train_test_eval(self):
        '''
        Take in the core data frame and split into:
        train, test, and evaluate sets

        returns 3 spark dataframes:
        train, test, evals
        '''
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
        '''
        Loads in the dataframe and returns it
        '''

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

        self.gr_v0.fit(self.train)

        print
        print "Starting fit model v0"
        self.gr_v1.fit(self.train)

        print
        print "Finishing fit"
        return(self)

    def transform(self, test_requests):
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
        self.logger.debug("starting predict")
        self.logger.debug("request count: {}".format(test_requests.shape[0]))

        self.requests = self.spark.createDataFrame(test_requests)

        pred_loop_v0 = self.gr_v0.transform(self.requests)\
                        .withColumnRenamed('prediction','prediction_model_v0')

        pred_loop_v1 = self.gr_v1.transform(pred_loop1)\
                        .withColumnRenamed('prediction','prediction_model_v1')

        results_loop_v1 = pred_loop_v1.withColumn('prediction',
                                      F.when(F.isnan('prediction_model_v0'),
                                             F.col('prediction_model_v1'))\
                                             .otherwise(F.col('prediction_model_v0')))

        predictions = results_loop_v1.select('user', 'appid', 'prediction')\
                                   .withColumnRenamed('prediction','rating')\
                                   .toPandas()

        self.logger.debug("finishing predict")
        return(predictions)
