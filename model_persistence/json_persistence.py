#!/usr/bin/env python

import titus
import json
import titus.producer.tools as t
from titus.genpy import PFAEngine
import numpy as np
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

#Load Iris data set
iris = load_iris()

#Change to legal names
iris.feature_names = [ "sepal_length",
                       "sepal_width",
                       "petal_length",
                       "petal_width" ]

#Create training and testing data
idx         = np.concatenate((np.zeros(145), np.ones(5)))
trainData   = iris.data[idx == 0, :]
testData    = iris.data[idx == 1, :]

#Create associated classification results
trainTarget = iris.target[idx == 0]
testTarget  = iris.target[idx == 1]


#Create classifier and run the algorithm
rf_clf = RandomForestClassifier().fit(trainData, trainTarget)

predicted = iris.target_names[rf_clf.predict(testData)]
expected  = iris.target_names[testTarget]

for idx in range(5):
    print("Test Input %d: Expected [%s]: Predicted [%s]" % (idx, expected[idx], predicted[idx]))

#=============
#Decision Tree
#=============

class DecisionTreeExporter(object):
    """Exports the given SciKit-Learn decision tree into PFA format"""

    def __init__(self, classifier, name, feature_names, class_names):
        """Returns a new instance of a RandomForestExporter"""
        self._classifier = classifier
        self._name = name
        self._feature_names = feature_names
        self._class_names = class_names
        self._pfaDocument = {}

    def export(self):
        """Returns the PFA model as a dictionary object that can be exported to JSON"""
        self._pfaDocument = {
            "name"  : self._name,
            "method": "map",
            "input" : self._inputSchema(),
            "output": self._outputSchema(),
            "cells" : {
                "tree": {
                    "type": "TreeNode",
                    "init": self._cell(),
                    "shared": False,
                    "rollback": False
                }
            },
            "action": self._action("tree")
        }
        return self._pfaDocument

    def exportAsJson(self):
        """Returns the PFA model as a JSON string"""
        return json.dumps(self.export())


    def _inputSchema(self):
        fields = []
        for name in self._feature_names:
            fields.append({ "name": name, "type": "double" })

        return {
            "fields": fields,
            "type": "record",
            "name": "InputType"
        }

    def _outputSchema(self):
        return {
            "fields": [
                { "name": "target_id", "type": "int" },
                { "name": "target",    "type": "string" }
            ],
            "type": "record",
            "name": "OutputType"
        }

    def _cell(self):
        return self.__walk(self._classifier.tree_)

    def _action(self, cell):
        """Create model action using tree constructs

        The action is to descend through a tree testing whether we're at
        a leaf node yet.  Using function "model.tree.simpleWalk" which
        takes arguments:

          - datum: The input record to process
          - treeNode: A record with "pass" and "fail" tests
          - test: Function that takes (datum, treeNode) and returns boolean
        """

        return {
            "model.tree.simpleWalk": [
                "input",
                { "cell": cell },
                {
                    "params": [
                        { "d": "InputType" },
                        { "t": {
                            "fields": [
                                {
                                    "type": {
                                        "symbols": self._feature_names,
                                        "type": "enum",
                                        "name": "InputEnum"
                                    },
                                    "name": "field"
                                },
                                { "name": "operator", "type": "string" },
                                { "name": "value", "type": "double" },
                                { "name": "pass", "type": [ "TreeNode", "OutputType" ] },
                                { "name": "fail", "type": [ "TreeNode", "OutputType" ] }
                            ],
                            "type": "record",
                            "name": "TreeNode"
                        }}
                    ],
                    "ret": "boolean",
                    "do": [
                        { "model.tree.simpleTest": [ "d", "t" ] }
                    ]
                }
            ]
        }

    def __walk(self, tree, node_id=0):
        """Walks the decision tree and returns the resulting output
        tree structure

          {
             "field": field name to test
             "operator": "<"
             "value": threshold value
             "pass"|"fail": tree branches
          }
        """

        treeNode = {}

        left_child = tree.children_left[node_id]
        right_child = tree.children_right[node_id]

        if left_child >= 0:

            #If we are at a branch node, then we put the branch criteria
            treeNode["field"] = self._feature_names[tree.feature[node_id]]
            treeNode["operator"] = "<"
            treeNode["value"] = round(tree.threshold[node_id], 6)

            #Continue to recurse down the tree
            treeNode["pass"] = self.__walk(tree, left_child)
            treeNode["fail"] = self.__walk(tree, right_child)

            if node_id > 0:
                node = treeNode
                treeNode = {
                    "TreeNode": node
                }

        else:

            #If we are at a leaf node, then we provide the answer
            value = tree.value[node_id][0, :]
            target_id = np.argmax(value)
            treeNode["OutputType"] = {
                "target_id": target_id.item(),
                "target": self._class_names[target_id]
            }

        return treeNode

#=============
#Random Forest
#=============

class RandomForestExporter(object):
    """Exports the given SciKit-Learn Random Forest model into PFA format"""

    def __init__(self, classifier, name, feature_names, class_names):
        """Returns a new instance of a RandomForestExporter"""
        self._classifier = classifier
        self._name = name
        self._feature_names = feature_names
        self._class_names = class_names
        self._pfaDocument = {}
        self._treeExporters = []

        for idx in range(len(self._classifier.estimators_)):
            self._treeExporters.append(
                DecisionTreeExporter(self._classifier.estimators_[idx],
                                     "tree%d" % idx,
                                     feature_names,
                                     class_names))

    def export(self):
        """Returns the PFA model as a dictionary object that can be exported to JSON"""
        cells = []
        for exporter in self._treeExporters:
            cells.append(exporter._cell())

        self._pfaDocument = {
            "name"  : self._name,
            "method": "map",
            "input" : self._treeExporters[0]._inputSchema(),
            "output": self._treeExporters[0]._outputSchema(),
            "cells" : {
                "forest": {
                    "type": {
                        "type": "array",
                        "items": "TreeNode"
                    },
                    "init": cells,
                    "shared": False,
                    "rollback": False
                },
            },
            "action": self._action()
        }
        return self._pfaDocument

    def exportAsJson(self):
        """Returns the PFA model as a JSON string"""
        return json.dumps(self.export(), indent=2)

    def _action(self):
        """Create model action that takes the most frequent result

        The action is to loop over the decision trees evaluating each
        one and then returning the most frequent result.
        """

        return [
            { "let": {
                "scores": {
                    "a.map": [
                        { "cell": "forest" },
                        { "params": [
                            { "tree": {
                                "fields": [
                                    {
                                        "type": {
                                            "symbols": self._feature_names,
                                            "type": "enum",
                                            "name": "InputEnum"
                                        },
                                        "name": "field"
                                    },
                                    { "name": "operator", "type": "string" },
                                    { "name": "value", "type": "double" },
                                    { "name": "pass", "type": [ "TreeNode", "OutputType" ] },
                                    { "name": "fail", "type": [ "TreeNode", "OutputType" ] }
                                ],
                                "type": "record",
                                "name": "TreeNode"
                            }}],
                          "ret": "OutputType",
                          "do": [
                            {
                                "model.tree.simpleWalk": [
                                    "input",
                                    "tree",
                                    {
                                        "params": [
                                            { "d": "InputType" },
                                            { "t": "TreeNode" }
                                        ],
                                        "ret": "boolean",
                                        "do": [
                                            { "model.tree.simpleTest": [ "d", "t" ] }
                                        ]
                                    }
                                ]
                            }
                          ]
                        }
                    ]
                }
            }
        },
        {
            "a.mode": [ "scores" ]
        }
    ]

# Creating the PFA file
pfa = RandomForestExporter(rf_clf, "IrisRandomForestModel",
                           iris.feature_names,
                           iris.target_names).exportAsJson()

with open('IrisRandomForestModel.pfa', 'w') as f:
    f.write(pfa)
    f.write("\n")
    f.close()

