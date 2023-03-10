# -*- coding: utf-8 -*-
"""DQ_birthdates_advanced_stats_v1.0.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1lnXe7Ab1IVsxzz3XCHb-eeMr2yprsXUr

DQ_birthdates_advanced_stats_v1.0.ipynb

**Analysis approach of the data quality of dates using z-score (with Python)**

As a continuation of the article *Analysis approach of the data quality of dates using basic statistical methods (with Python)*, we are going to use z-score, a statistical calculation based on the standard deviation.

**Z-score**
After importing and exploring the dates of birth dataset (from the article related) we need to transform all dates to numbers (dates to simple number and dates to ages from now).
Please note that we have previously reported a potential issue with the date 01/01/2000 (mm/dd/YYYY) possibly due to a technical error or the use of the date as a dummy date, so we will remove again these dates for this analysis.
"""

import pandas as pd
from datetime import date

def years_from_now(d):
    today = d.today()
    age = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
 
    return age

#Import dataset dates from github
url = "https://raw.githubusercontent.com/mabrotons/datasets/master/birthdates.csv"


df = pd.read_csv(url, index_col=0, parse_dates=['birthdates'])

#transforming dates in numbers
df['birthdates_num'] = [int(d.strftime("%Y%m%d")) for d in df['birthdates']] 
df = df.loc[df['birthdates_num'] != 20000101]

#transforming dates in ages old
df['ages'] = [years_from_now(d) for d in df['birthdates']]

"""We will build a couple of plots to represent birthdates, in order to have a first view of the dataset. As the plots show, the data represented is identical in both plots (symmetrically), and we have to decide which date format will be most useful for analysis."""

import matplotlib.pyplot as plt
from matplotlib import ticker

fig, axes =plt.subplots(1, 2, figsize=(20,5))

dates_num = df['birthdates_num']
ages = df['ages']

axes[0].hist(dates_num, bins=50, edgecolor='black')
axes[1].hist(ages, bins=50, edgecolor='black')
plt.xticks(rotation=30)

#formating the xticks labels (year) for first subplot()
axes[0].xaxis.set_major_formatter(ticker.FuncFormatter(lambda x,pos: format(x/10000,'1.0f')))
axes[0].title.set_text('Dates (num format)')
axes[1].title.set_text('Ages (from now)')

plt.show()

"""Now it's time to start the calculation of standard deviation to know how values are distributed around all dataset, and detect possible outliers: candidates to be outliers will be multiple standard-deviations far from the mean.
As we can see with means and standard deviations calculated, it's easier to work with dates transformed to ages than to simple number.
"""

std_birthdates_num = df['birthdates_num'].std()
mean_birthdates_num = df['birthdates_num'].mean()
print("Mean of birthdates_num: " + str(mean_birthdates_num))
print("Standard deviation of birthdates_num: " + str(std_birthdates_num))

std_ages = df['ages'].std()
mean_ages = df['ages'].mean()
print("\nMean deviation of ages: " + str(mean_ages))
print("Standard deviation of ages: " + str(std_ages))

"""Now, selecting ages transformed like esay way, let's calculate z-score:

z = (x ??? ??) / ??

where Z is the score, x is the value to calculate the score, ?? is the mean and ?? is the standard deviation.
The z-score is a calculation that measure how many standard deviations a value is far away from the mean, and the probability of data to be unusual in a distribution.
It's recomended to use z-score with a normal distribution, because in a normal distribution over 99% of values fall within 3 standard deviations from the mean. For that, we can assume:
- if a z-score returned is lower than 1 shoud be a normal data value
- if a z-score returned is larger than 1 and lower than 3, could be an error
- if a z-score returned is larger than 3 should be an error
"""

df['zscore'] = [(a-mean_ages)/std_ages for a in df['ages']] 

f = plt.figure()
f.set_figwidth(15)
f.set_figheight(5)

good_ages = df.loc[(df['zscore'] <= 1) & (df['zscore'] >= -1)]['ages']
regular_ages = df.loc[((df['zscore'] > 1) & (df['zscore'] <= 3)) | ((df['zscore'] < -1) & (df['zscore'] >= -3))]['ages']
bad_ages = df.loc[(df['zscore'] > 3) | (df['zscore'] < -3)]['ages']

plt.hist([good_ages, regular_ages ,bad_ages], color=['Green', 'Orange', 'Red'], label=['good', 'regular', 'bad'], edgecolor='black', bins=60, histtype='barstacked')

#add vertical line at mean value of x
plt.axvline(x=mean_ages, color='blue', linewidth=3, label='mean')

plt.title("Ages")
plt.legend()
plt.show()

"""Another way to calculate z-score is with scipy.stats funtion:
import scipy.stats as stats
df['zscore'] = stats.zscore(df['ages'])

Now, we can print to ten ouliers detected with a z-score by both ends.
"""

sorted_df =  df.sort_values('zscore')
print("Top 10 left: ")
print(sorted_df.head(10))

print("\nTop 10 right: ")
print(sorted_df.tail(10))

"""**Isolation Forest**

IsolationForest is an unsupervised learning algorithm that identifies possible anomalies by isolating outliers in a dataset. Its calculation is inspired by the Random Forest classification and regression algorithm.

Firstly, we are going to define and fit the model. We have to instance IsolationForest with the next three parameters:
- n_estimators: number of base estimators or trees in the ensemble. It's optional and the default value is 100.
- max_samples: number of samples used to train each base estimator. The default value of max_samples is 'auto', max_samples=min(256, n_samples).
- contamination: expected proportion of outliers in the dataset. The default value is 'auto', determined as in the original paper of Isolation Forest.

"""

from sklearn.ensemble import IsolationForest
import numpy as np

model = IsolationForest(n_estimators = 1000, max_samples = 'auto', contamination=float(0.1))
print(model.get_params())

model.fit(df[['ages']])

"""After the model is defined and fitted, it will show the IsolationForest instance result as shown in the output.

Now, we will create two new columns with decision function and predict information:

- decision_function(). Average anomaly score of X of the base classifiers.
- predict(). Predict if a particular sample is an outlier or not.

To show results in a plot we have to split the ages with anomaly_score criteria.
"""

df['scores'] = model.decision_function(df[['ages']])
df['anomaly_score'] = model.predict(df[['ages']])

ok = df[df['anomaly_score']==1]
ko = df[df['anomaly_score']==-1]

f = plt.figure()
f.set_figwidth(15)
f.set_figheight(5)

plt.hist([ok['ages'], ko['ages']], color=['Green', 'Red'], label=['oks', 'kos'], edgecolor='black', bins=60, histtype='barstacked')

plt.title("Ages")
plt.legend()
plt.show()

"""Now, we can print top ten ouliers detected with a Isolation Forest algorithm, agreed with the maximum obtained with z-score."""

sorted_df =  df.sort_values('scores')
print("Top 10 left: ")
print(sorted_df.head(10))

"""**Conclusion**

With z-score and Isolation Forest algorithm are two easy ways to identify possible anomalies in a dataset, through the use of scores for each of the data and through its visualization.
"""
