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

import matplotlib.pyplot as plt

igr = IndieGR()

igr.split_train_test_eval()

igr.train_model()

errors = igr.get_squared_error()

print "Error DF head"
print errors.head()

fig, ax = plt.subplots(figsize=(14,10))

file_name = "Nan mean Rank10 mI 10 rP 0_01.png"

ax.set_title("Log Error Histogram\nReplacing Prediction NaN with Mean, Rating Rank:10, maxIter=10, regParam=0.1", fontsize=22)
ax.set_xlabel("Log Error", fontsize=18)
ax.set_ylabel("Percentage of Distribution", fontsize=18)
ax.set_xlim(-4,4)
ax.set_facecolor("#EEEEEE")
ax.hist(errors, alpha=0.7, bins=30, normed=True, color="#9999FF")

y,binEdges=np.histogram(errors,bins=500, normed=True)
bincenters = 0.5*(binEdges[1:]+binEdges[:-1])
ax.plot(bincenters,y,'-', lw=3, color="#333377", alpha=0.7)
plt.savefig('pics/' + file_name, bbox_inches='tight', facecolor="white")
