# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: p12
#     language: python
#     name: python3
# ---

# Created base on this:
# https://www.datacamp.com/tutorial/pyspark-tutorial-getting-started-with-pyspark

#

import os
import time
from pyspark.sql.types import *
from pyspark.sql.functions import *
from pyspark.sql import SparkSession

# # create spark session

# +
spark = (
    SparkSession
    .builder
    .appName('spark-local')
    .master('local[8]')
    .config('spark.memory.offHeap.enabled', 'true')
    .config('spark.memory.offHeap.size', '1g')
    .getOrCreate()
)

# spark.conf.set('spark.default.parallelism', 4)
# spark.conf.set('spark.sql.shuffle.partitions', 4)

def sp_shape(df):
    return (df.count(), len(df.columns))
def sp_show(df):
    print(sp_shape(df))
    df.show(5,0)


# -

spark.stop()

print(spark.conf.get('spark.sql.shuffle.partitions'))

# # load data

t0 = time.time()
d = spark.read.csv('c:/test/data/online_retail.csv', header=True, escape='\"')
#d = spark.read.parquet('c:/test/elchapo/position-20230622000009.parquet')
d.show(5,0)
print(f'time: {time.time() - t0:.3f}')

print(sp_shape(d))
print(d.printSchema())
d.summary().show() #will return None

t0 = time.time()
d.withColumn('cd', when(col('InvoiceNo').isin([536365, 541909]), col('CustomerID')).otherwise(col('Country'))).show(5,0)
print(f'time: {time.time() - t0:.3f}')

t0 = time.time()
#convert col types
d1 = (
    d
    .withColumn('InvoiceNo', col('InvoiceNo').cast('int'))
    .withColumn('StockCode', col('StockCode').cast('int'))
    .withColumn('Quantity', col('Quantity').cast('double'))
    .withColumn('UnitPrice', col('UnitPrice').cast('double'))
    .withColumn('InvoiceDate', to_timestamp('InvoiceDate', 'd/M/yyyy H:mm'))
    .withColumn('CustomerID', col('CustomerID').cast('int'))
)
d1.show(5,0)
print(f'time: {time.time() - t0:.3f}')

t0 = time.time()
d1.describe().show()
print(f'time: {time.time() - t0:.3f}')

t0 = time.time()
d1.summary().show()
print(f'time: {time.time() - t0:.3f}')

# # explore data

d1.select('CustomerID').distinct().count()

d1.agg({'InvoiceDate': 'min', 'InvoiceDate': 'max'}).first()[0]

from pyspark.sql import functions as f
agg = d1.agg(f.min('InvoiceDate').alias('mn'), f.max('InvoiceDate').alias('mx'), f.avg('InvoiceDate').alias('ag'), f.sum('InvoiceDate').alias('sm')).first()

agg[:-1]

d1.groupBy('Country').agg(countDistinct('CustomerID').alias('country_count')).orderBy(desc('country_count')).show()

# spark.sql("set spark.sql.legacy.timeParserPolicy=LEGACY")
# df = df.withColumn('date', to_timestamp("InvoiceDate", 'dd/MM/yyyy HH:mm'))
d1.select(max('InvoiceDate')).show()

d1.select(min('InvoiceDate')).show()

# # pre-process data

d1.show(5,0)

# ## Recency

d2 = d1.withColumn('from_date', to_timestamp(lit('2010-12-01 08:26'), 'yyyy-MM-dd HH:mm'))
d2.show(5,0)

# +
df = df.withColumn('from_date', lit('2010-12-01 08:26'))
df = df.withColumn('from_date', to_timestamp('from_date', 'yyyy-MM-dd HH:mm'))

d2 = (
    df
    .withColumn('from_date', to_timestamp(col('from_date')))
    .withColumn('recency', col('date').cast('long') - col('from_date').cast('long'))
)

d2 = d2.join(
    d2.groupBy('CustomerID').agg(max('recency').alias('recency')),
    on='recency',
    how='leftsemi',
)

d2.show(5,0)
# -

d2.printSchema()

# ## Frequency

df_freq = d2.groupBy('CustomerID').agg(count('InvoiceDate').alias('frequency'))
df_freq.show(5,0)

d3 = d2.join(df_freq, on='CustomerID', how='inner')
d3.show(5,0)

# ## Monetary Value

m_val = d3.withColumn('TotalAmount', col('Quantity') * col('UnitPrice'))
m_val = m_val.groupBy('CustomerID').agg(sum('TotalAmount').alias('monetary_value'))
d4 = m_val.join(d3, on='CustomerID', how='inner')
d4.show(5,0)

# # standardize

d = d4.select(['recency','frequency','monetary_value','CustomerID']).distinct()
d.show(5,0)

# +
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.feature import StandardScaler

assemble = VectorAssembler(
    inputCols=['recency','frequency','monetary_value'],
    outputCol='features',
)
assembled_data = assemble.transform(d)

scale = StandardScaler(inputCol='features', outputCol='standardized')
data_scale = scale.fit(assembled_data)
data_scale_output = data_scale.transform(assembled_data)

data_scale_output.select('standardized').show(2,0)
# -

# # build ml model

# ## Number of cluster

# +
import numpy as np
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator

cost = np.zeros(10)
evaluator = ClusteringEvaluator(predictionCol='prediction', featuresCol='standardized', metricName='silhouette', distanceMeasure='squaredEuclidean')

for i in range(2,10):
    KMeans_algo = KMeans(featuresCol='standardized', k=i)
    KMeans_fit = KMeans_algo.fit(data_scale_output)
    output = KMeans_fit.transform(data_scale_output)
    cost[i] = KMeans_fit.summary.trainingCost
# -

import pylab as pl
cluster = range(2,10)
cost_ = cost[2:]
pl.plot(cluster, cost_)
pl.xlabel('Number of Clusters')
pl.ylabel('Score')
pl.title('Elbow Curve')
pl.show()

# ## Build clustering model and make prediction

# +
KMeans_algo = KMeans(featuresCol='standardized', k=5)
KMeans_fit = KMeans_algo.fit(data_scale_output)

preds = KMeans_fit.transform(data_scale_output)
preds.show(5,0)
# -

# # cluster analysis

df_viz = preds.select('recency','frequency','monetary_value','prediction').toPandas()
avg_df = df_viz.groupby(['prediction']).mean()
avg_df.head()

dx = avg_df.stack().reset_index().set_axis(['prediction', 'typ', 'val'], axis=1)
dx.head()

# +
import matplotlib.pyplot as plt
import seaborn as sns

g = sns.catplot(
    kind='bar',
    data=dx,
    x='prediction',
    y='val',
    col='typ',
    sharey=False,
    # ci=None,                  #remove error bars
    height=4,
    aspect=1.5,
)
# -

# # create df

cols = ['language','user_count']
data = [
    ('Java', 20000),
    ('Python', 100000),
    ('Scala', 3000),
]
schema = StructType([
    StructField('language', StringType(), True),
    StructField('user_count', IntegerType(), True),
])

# ## from rdd

rdd = spark.sparkContext.parallelize(data)

t0 = time.time()
d1 = rdd.toDF(cols)
d1.show(5,0)
print(f'time: {time.time() - t0:.3f}')
# time: 18.728

t0 = time.time()
d2 = spark.createDataFrame(rdd, schema=cols)
d2.show(5,0)
print(f'time: {time.time() - t0:.3f}')
# time: 18.494

# ## from list

t0 = time.time()
d3 = spark.createDataFrame(data=data, schema=schema)
d3.show(5,0)
print(f'time: {time.time() - t0:.3f}')
# time: 9.046

t0 = time.time()
df = spark.createDataFrame(spark.sparkContext.emptyRDD(), schema)
df.show(5,0)
print(f'time: {time.time() - t0:.3f}')

t0 = time.time()
df = spark.createDataFrame([], schema)
df.show(5,0)
print(f'time: {time.time() - t0:.3f}')
