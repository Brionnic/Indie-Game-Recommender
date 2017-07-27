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

class IndieGR():

    def __init__(self, column, rank=50, path="v_matrix_lpm_b0_s1.parquet"):
        # sort of like __name__ == "__main__":

        self.spark = ps.sql.SparkSession.builder \
                    .master("local[14]") \
                    .appName("df lecture") \
                    .getOrCreate()

        # load datas
        self.data = self.spark.read.parquet(path)

        # make sure that the data seems ok
        print self.data.printSchema()
        print
        print self.data.show()

        # split data for cross validation
        self.train_data = None
        self.test_data = None
        self.eval_data = None

        self.model = GameRecommenderModel(self.spark, column, rank)
        self.recommender = None

        self.predictions = None

        # the V matrix from NMF/ALS U/V decomposition
        self.V = None

        # keep a list of indices for V so we can lookup the appid out of that
        self.V_indices = None

        # store the most recent predictions (this should really be done
        # in the calling method but just for testing)
        self.sorted_predictions = None

        # which column of the dataframe do we use for these predictions?
        self.column_tag = column


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
        train_test, final_eval = self.data.randomSplit([0.9, 0.1], seed=1337)

        # break the non-held back into train/test split
        train, test = train_test.randomSplit([0.8, 0.2], seed=1337)

        self.train_data = train
        self.test_data = test
        self.eval_data = final_eval

        print "Train set count:", self.train_data.count()
        print "Test set count:", self.test_data.count()
        print "Eval set count:", self.eval_data.count()

    def train_model(self):
        """
        Train the model on the train part of the data
        """
        print "\nIndieGR class: model trying to fit to training data"

        self.recommender = self.model.fit(self.train_data)

    def get_scoring_predictions(self):
        """
        Use the trained model to predict on the test data. We should
        be able to use these predictions to evaluate the accuracy of the
        model.
        """
        print "\nIndieGR class: Making predictions on test data."
        self.predictions = self.recommender.transform(self.test_data)

    def evaluate_model(self):
        """
        Use predicted vs actual values to score the model using RMSE
        """
        pass

    def process_V_matrix(self):
        """
        Take the fit model's itemFactors and turn it into a usable numpy array
        """
        print "\nPulling V matrix out of trained model and storing in memory..."
        self.V = np.array([row["features"] for row in self.recommender.itemFactors.collect()])

        print "\nSeems successful, now pull and store indices so we can lookup appind -> game titles"
        self.V_indices = np.array([row["id"] for row in self.recommender.itemFactors.collect()])

    def predict_existing_user(self, user_id=100, num_preds=10):
        """
        Take in new_U and predict the log_playtime_m for that user using
        the V matrix from the NMF/ALS modeling.

        Return:
        Returns a list of predictions of length num_preds
        """

        # get the V matrix prepared
        self.process_V_matrix()

        # grab training data for the user that we're predicting
        ex_user_training_df = self.grab_existing_user_train(user_id)

        # data for the row that we're predicting
        ex_user_test_df = self.grab_existing_user_test(user_id)

        # V matrix data that matches rows that have been reviewed
        filtered_item_factors, item_ratings = self.filter_itemFactors(ex_user_test_df)

        # U_new dot product V filtered by things rated by U_new
        # / sum(item_ratings) to normalize the predictions back to our original scale
        new_user_factors = np.dot(item_ratings, filtered_item_factors) / sum(item_ratings)

        # make new predictions, then sort them in ascending order, then reverse to get descending order

        id_list = np.array([row["id"] for row in self.recommender.itemFactors.collect()]).astype(int)

        print "Shape of V:", self.V.shape
        print "Shape of ex_user_training_df", ex_user_training_df.count, ",", len(ex_user_training_df.columns)
        print "Shape of ex_user_test_df", ex_user_test_df.count, ",", len(ex_user_test_df.columns)
        print "Shape of filtered_item_factors:", filtered_item_factors.shape
        print "shape of new_user_factors:", new_user_factors.shape
        print "shape of item_ratings:", item_ratings.shape
        print "shape of id_list:", id_list.shape

        new_predictions = np.dot(self.V, new_user_factors).astype(float)

        print "shape of new_predictions:", new_predictions.shape
        #new_predictions = np.dot(self.V, new_user_factors).sort()[::-1]

        #sorted_predictions = np.sort(new_predictions)[::-1]

        # combine the predictions and the id_list into a (items, 2) shaped np.array
        # app indexes and predictions
        a_p = np.stack([new_predictions, id_list], axis=1)

        sorted_a_p = a_p[a_p[:,0].argsort()[::-1]]
        #d = c[c[:,0].argsort()]

        self.sorted_predictions = sorted_a_p[:num_preds]
        # return new_predictions sliced by size
        return self.sorted_predictions

    def grab_existing_user_train(self, user_id):
        """
        use this to generate new_U for getting a prediction
        """

        self.train_data.registerTempTable("train")

        # original
        # new_user_df = self.spark.sql(
        #     '''
        #     SELECT user,
        #         appind,
        #         log_playtime_m
        #     FROM train
        #     WHERE user = {}
        #     '''.format(user_id))

        new_user_df = self.spark.sql(
            '''
            SELECT user,
                appind,
                {}
            FROM train
            WHERE user = {}
            '''.format(self.column_tag, user_id))

        return new_user_df

    def grab_existing_user_test(self, user_id):
        """
        use this to generate new_U for getting a prediction
        """

        self.test_data.registerTempTable("test")

        # original
        #
        # new_user_df = self.spark.sql(
        #     '''
        #     SELECT user,
        #         appind,
        #         log_playtime_m
        #     FROM test
        #     WHERE user = {}
        #     '''.format(user_id))

        new_user_df = self.spark.sql(
            '''
            SELECT user,
                appind,
                {}
            FROM test
            WHERE user = {}
            '''.format(self.column_tag, user_id))

        return new_user_df

    def filter_itemFactors(self, new_user_df):
        """
        return the filtered itemFactors based on what user has rated
        """

        item_factors_df = self.recommender.itemFactors

        filtered_item_factors_df = item_factors_df.join(new_user_df, F.col("id") == new_user_df["appind"])

        filtered_item_factors = []
        item_ratings = []

        for row in filtered_item_factors_df.collect():
            filtered_item_factors.append(row["features"])
            item_ratings.append(row[self.column_tag])

        return np.array(filtered_item_factors), np.array(item_ratings)

    def print_sorted_predictions(self):
        """
        Print out the list for ease of testing
        """
        lookup = GameIndexer()

        for idx, result in enumerate(self.sorted_predictions):
            title = lookup.game_index_to_title(int(result[1]), 40)
            print "Rank: {:2d} Prediction: {:2.2f} Game: {}".format(idx +1, result[0], title)

    def get_squared_error(self):
        """
            Returns a list of the squared error
        """
        predictions = self.recommender.transform(self.test_data)

        print "\nPredictions DF:"
        print predictions.show(5)

        print "\nConvert predictions spark to pandas"
        pred_df = predictions.toPandas()

        print "\nConvert train_data spark to pandas"
        train_df = self.train_data.toPandas()

        print "\nFill missing values with mean rating"
        # fill with mean
        # pred_df = predictions.toPandas().fillna(train_df["log_playtime_m"].mean())
        # fill with zeros
        pred_df = predictions.toPandas().fillna(0)

        pred_df["real_squared_error"] = (pred_df[self.column_tag] - pred_df["prediction"])**2

        print "other rmse", (sum(pred_df["real_squared_error"]) / (len(pred_df) * 1.0))**0.5

        pred_df["squared_error"] = pred_df[self.column_tag] - pred_df["prediction"]

        return pred_df.pop("squared_error")

    def evaluate_RMSE(self, train_predict=0):
        """
        Attempt to score the model using the RSME method

        prints out RSME

        Returns:
        RSME as float val
        """

        if train_predict==1:
            #######################3
            #########   Eval train model RMSE for overfitting examination
            ########################
            train_predictions = self.recommender.transform(self.train_data)

            print "\ntrain_predictions DF:"
            print train_predictions.show(5)

            print "\nConvert train_predictions spark to pandas"
            train_pred_df = train_predictions.toPandas()

            print "\nConvert train_data spark to pandas"
            train_df = self.train_data.toPandas()

            print "\nFill missing values with mean rating"
            train_pred_df = train_predictions.toPandas().fillna(train_df[self.column_tag].mean())
            #train_pred_df = train_predictions.toPandas().fillna(0)

            train_pred_df["squared_error"] = (train_pred_df[self.column_tag] - train_pred_df["prediction"])**2

            print "\nDo a describe on the train_predictions df"
            print train_pred_df.describe()

            # calculate the RSME
            train_rmse = np.sqrt(sum(train_pred_df["squared_error"]) / (len(train_pred_df) * 1.0))

            # print "sum of squared_error", sum(train_pred_df["squared_error"])
            # print "sum of s_e / len(train_pred_df)", sum(train_pred_df["squared_error"]) / (len(train_pred_df) * 1.0)
            # print "other rmse", (sum(train_pred_df["squared_error"]) / (len(train_pred_df) * 1.0))**0.5

            print "\nRMSE:", train_rmse


        #######################3
        #########   Eval test model RMSE like normal
        ########################


        test_predictions = self.recommender.transform(self.test_data)

        print "\ntest_predictions DF:"
        print test_predictions.show(5)

        print "\nConvert test_predictions spark to pandas"
        pred_df = test_predictions.toPandas()

        print "\nConvert train_data spark to pandas"
        # keep this as train_data because we're not supposed to see/know
        # what the test data looks like
        train_df = self.train_data.toPandas()

        print "\nFill missing values with mean rating"
        pred_df = test_predictions.toPandas().fillna(train_df[self.column_tag].mean())
        #pred_df = test_predictions.toPandas().fillna(0)

        pred_df["squared_error"] = (pred_df[self.column_tag] - pred_df["prediction"])**2

        print "\nDo a describe on the test_predictions df"
        print pred_df.describe()

        # calculate the RSME
        test_rmse = np.sqrt(sum(pred_df["squared_error"]) / (len(pred_df) * 1.0))

        # print "sum of squared_error", sum(pred_df["squared_error"])
        # print "sum of s_e / len(pred_Df)", sum(pred_df["squared_error"]) / (len(pred_df) * 1.0)
        # print "other rmse", (sum(pred_df["squared_error"]) / (len(pred_df) * 1.0))**0.5

        print "\nRMSE:", test_rmse

        if train_predict == 1:
            return train_rmse, test_rmse
        else:
            return test_rmse

        # totally untuned with rank 10, average values replacing nan
        # RMSE: 0.889612280955

        # rank 10 default others mean values into nans
        # rmse 0.889249337621

        # rank 10 zeros replacing nan
        # other rmse 0.888550601469

        # just changed rank to 75
        # RMSE: 0.876617437231  (-0.013)

        # ran rank 75 again
        # RMSE: 0.877823176352

        # ran with rank 10, maxIter=20, regParam=0.2 and got the horrible
        # RMSE: 0.931727052283

        # ran with rank 10, maxIter=20, regParam=0.1 and nan replaced by 0
        # RMSE: 0.887799907012

        # rank with rank 100, maxIter=20, regparam=0.1 and nan replaced by 0


        # evaluator = RegressionEvaluator(metricName="rmse",
        #                                 labelCol="log_playtime_m",
        #                                 predictionCol="prediction")
        #
        # rmse = evaluator.evaluate(predictions)

        print "RMSE:", rmse

        return rmse

    def evaluate_average_RMSE(self):
        """
        Attempt to score the model using the RSME method

        prints out RSME

        Returns:
        RSME as float val
        """

        #######################3
        #########   Eval train model RMSE for overfitting examination
        ########################
        train_predictions = self.recommender.transform(self.train_data)

        print "\ntrain_predictions DF:"
        print train_predictions.show(5)

        print "\nConvert train_predictions spark to pandas"
        train_pred_df = train_predictions.toPandas()

        print "\nConvert train_data spark to pandas"
        train_df = self.train_data.toPandas()

        print "\nFill missing all values with mean rating"
        train_pred_df = train_predictions.toPandas()

        temp_panda = self.train_data.toPandas()

        mu = temp_panda[self.column_tag].mean()

        train_pred_df["predictions"] = mu
        #train_pred_df = train_predictions.toPandas().fillna(0)

        print "\n\n\n"
        print train_pred_df.describe()
        print
        print

        train_pred_df["squared_error"] = (train_pred_df[self.column_tag] - train_pred_df["prediction"])**2

        print "\nDo a describe on the train_predictions df"
        print train_pred_df.describe()

        # calculate the RSME
        train_rmse = np.sqrt(sum(train_pred_df["squared_error"]) / (len(train_pred_df) * 1.0))

        # print "sum of squared_error", sum(train_pred_df["squared_error"])
        # print "sum of s_e / len(train_pred_df)", sum(train_pred_df["squared_error"]) / (len(train_pred_df) * 1.0)
        # print "other rmse", (sum(train_pred_df["squared_error"]) / (len(train_pred_df) * 1.0))**0.5

        print "\nTrain RMSE with Averages for predictions:", train_rmse


        #######################3
        #########   Eval test model RMSE like normal
        ########################


        test_predictions = self.recommender.transform(self.test_data)

        print "\ntest_predictions DF:"
        print test_predictions.show(5)

        print "\nConvert test_predictions spark to pandas"
        test_pred_df = test_predictions.toPandas()

        print "\nConvert train_data spark to pandas"
        train_df = self.train_data.toPandas()

        print "\nFill missing all values with mean rating"
        test_pred_df = test_predictions.toPandas()

        temp_panda = self.test_data.toPandas()

        mu = temp_panda[self.column_tag].mean()

        test_pred_df["predictions"] = mu
        #test_pred_df = test_predictions.toPandas().fillna(0)

        print "\n\n\n"
        print test_pred_df.describe()
        print
        print

        test_pred_df["squared_error"] = (test_pred_df[self.column_tag] - test_pred_df["prediction"])**2

        print "\nDo a describe on the test_predictions df"
        print test_pred_df.describe()

        # calculate the RSME
        test_rmse = np.sqrt(sum(test_pred_df["squared_error"]) / (len(test_pred_df) * 1.0))

        # print "sum of squared_error", sum(pred_df["squared_error"])
        # print "sum of s_e / len(pred_Df)", sum(pred_df["squared_error"]) / (len(pred_df) * 1.0)
        # print "other rmse", (sum(pred_df["squared_error"]) / (len(pred_df) * 1.0))**0.5

        print "\nTest RMSE with Averages for predictions:", test_rmse

        return train_rmse, test_rmse
