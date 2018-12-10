
## Author: Akbar Mohammed 
## date created: 7th December 2018
## date modified: 8th December 2018
## incomplete interview submission: multiclass classification images
## scene dataset 
##  files: Train and test sets along with their union and the XML header [scene.rar]
##  paper: M.R. Boutell, J. Luo, X. Shen, and C.M. Brown. Learning multi-labelscene classiffication. Pattern Recognition, 37(9):1757-1771, 2004
##  url: http://mulan.sourceforge.net/datasets-mlc.html
##  url: https://datahub.io/machine-learning/scene
##  url:


## Crude Approach
## requirements: install.packages(c('mlr','OpenML','farff'))

library(mlr)
library(OpenML)
setOMLConfig(apikey = "c1994bdb7ecb3c6f3c8f3b35f4b47f1f") #read only api key
oml.id = listOMLDataSets(tag = "2016_multilabel_r_benchmark_paper")$data.id
scene = getOMLDataSet(data.id = oml.id[8])
# Data str - Target Classes are set to logical bool
target = scene$target.features
feats = setdiff(colnames(scene$data), target)

set.seed(1991)
scene.task = makeMultilabelTask(data = scene$data, target = target)
# initiating a chain classifier 
binary.learner = makeLearner("classif.rpart")
lrncc = makeMultilabelClassifierChainsWrapper(binary.learner)
# training model
n = getTaskSize(scene.task)
train.set = seq(1, n, by = 2)
test.set = seq(2, n, by = 2)
scene.mod.cc = train(lrncc, scene.task, subset = train.set)
scene.pred.cc = predict(scene.mod.cc, task = scene.task, subset = test.set)
# classifier chain - performance output
performance(scene.pred.cc, measures = list(multilabel.hamloss, multilabel.subset01, multilabel.f1, multilabel.acc))

# initiating a binary relevance
lrnbr = makeMultilabelBinaryRelevanceWrapper(binary.learner)

scene.mod.br = train(lrnbr, scene.task, subset = train.set)
scene.pred.br = predict(scene.mod.br, task = scene.task, subset = test.set)
# binary relevance - performance
performance(scene.pred.br, measures = list(multilabel.hamloss, multilabel.subset01, multilabel.f1, multilabel.acc))


## Base line example
## requirements: install.packages(c("utiml","e1071", "randomForest"),type='source')

library(utiml)

# Create three partitions (train, val, test) of emotions dataset
partitions <- c(train = 0.6, val = 0.2, test = 0.2)
ds <- create_holdout_partition(emotions, partitions, method="iterative")

# Create an Ensemble of Classifier Chains using Random Forest (randomForest package)
eccmodel <- ecc(ds$train, "RF", m=3, cores=parallel::detectCores(), seed=123)

# Predict
val <- predict(eccmodel, ds$val, cores=parallel::detectCores())
test <- predict(eccmodel, ds$test, cores=parallel::detectCores())

# Apply a threshold
thresholds <- scut_threshold(val, ds$val, cores=parallel::detectCores())
new.val <- fixed_threshold(val, thresholds)
new.test <- fixed_threshold(test, thresholds)

# Evaluate the models
measures <- c("subset-accuracy", "F1", "hamming-loss", "macro-based") 

result <- cbind(
  Test = multilabel_evaluate(ds$tes, test, measures),
  TestWithThreshold = multilabel_evaluate(ds$tes, new.test, measures),
  Validation = multilabel_evaluate(ds$val, val, measures),
  ValidationWithThreshold = multilabel_evaluate(ds$val, new.val, measures)
)

print(round(result, 3))
