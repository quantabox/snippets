#!/usr/bin/env python


import pandas
import sklearn_pandas
from sklearn.datasets import load_iris
from sklearn2pmml.pipeline import PMMLPipeline
from sklearn.ensemble import RandomForestClassifier

feed = load_iris()
iris_X = feed.data
iris_y = feed.target

iris_classifier = RandomForestClassifier(n_estimators=10)
#rfc_model = iris_classifier.fit(iris_X, iris_y)

pipeline_model = PMMLPipeline([('iris_classifier',iris_classifier)]).fit(iris_X, iris_y)

from sklearn2pmml import sklearn2pmml
sklearn2pmml(pipeline_model, 'rfc.pmml', with_repr = True)
