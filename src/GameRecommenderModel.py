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

#########################################################################
#########################################################################
################### A class specific to the model for ###################
################### the Indie Game Recommender project ##################
################### Make interface like Scikit Learn's ##################
#########################################################################
#########################################################################

class GameRecommenderModel():
    """
    Try to implement similar to scikit learn.  So have fit method, transform
    predict
    """

    # this should be done by the calling context/class
    # def __init__(self, parquet_path="game_user_log_playtimes.parquet"):
    def __init__(self, spark, rank=10):
        # initialize spark stuff
        self.spark = spark
        self.sc = self.spark.sparkContext

        self.model = ALS(rank=rank,
                    maxIter=10,
                    regParam=0.01,
                    userCol="user",
                    itemCol="app_id",
                    ratingCol="log_playtime_m")

        # start the model at None so if we try to transform before training
        # the model we can detect and throw an error
        self.recommender = None

        # this might be a waste of space
        self.trained_model = None

    def fit(self, training_data):
        """
        Fit the ALS model on the training_data provided

        Return the fitted model to the requester
        """



        print "\nStarting to fit training data to model:"
        self.recommender = self.model.fit(training_data)

        print "\nFit complete, returning fitted model to caller."
        return self.recommender

    def transform(self, test_data):
        """
        Predicts the ratings for a given set of requests
        """

        # if the trained model isn't None then we can work with it
        if self.recommender != None:
            return self.recommender.transform(test_data)
        else:
            # the trained_model is None so we haven't yet trained the model
            # print an error (prob should throw an exception)
            print "Need to call .fit() on training data first!"
            return None
