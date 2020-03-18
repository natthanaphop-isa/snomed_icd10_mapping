from itertools import count

from fuzzywuzzy import fuzz
import pandas as pd
import numpy as np
import re
import textdistance

path = "../secret/data/"


def text_similarity(x, y):
    return fuzz.token_set_ratio(x.lower(), y.lower())


# return textdistance.hamming.normalized_similarity(x.lower(),y.lower())

def compare(text, compared_data):
    compared_data['similarity'] = compared_data['term'].apply(lambda x: text_similarity(str(text), str(x)))
    compared_data = compared_data.drop_duplicates()
    compared_data = compared_data.sort_values(by='similarity', ascending=False)
    # compared_data = compared_data[compared_data['similarity']>80]
    # print(compared_data)
    return compared_data


def convert(x):
    x = str(x).split('.')
    if len(x) > 1:
        return x[0] + x[1][:1]
    else:
        return x[0]


def calculate(dx_code, predicted_icd):
    if dx_code in predicted_icd:
        return 1
    else:
        return 0


def percent_n_score(row, subject):
    predicted_icd = subject[subject['id'] == row.id].icd10.values.tolist()
    n_actual = 0
    n_match = 0
    for i in range(1, 14):
        if row['dx' + str(i) + '_code'] is not np.nan:
            n_match = n_match + calculate(row['dx' + str(i) + '_code'], predicted_icd)
            n_actual = n_actual + 1
    return n_match * 100 / n_actual


def algorithm_validity():
    subject = pd.read_csv(path + 'tf_idf_checked.csv', index_col=0)
    standard_result = pd.read_csv(path + 'discharge_summary.csv')
    subject['icd10'] = subject['icd10'].apply(lambda x: convert(x))
    standard_result['cal_validity_percent'] = standard_result.apply(lambda x: percent_n_score(x, subject), axis=1)
    standard_result.to_csv(path + 'tf_idf_checked_algo_valid.csv')


def tf_idf():
    for df in pd.read_csv(path + 'result_100.csv', index_col=0, chunksize=50000):
        df['d'] = df['id'].groupby(df['id']).transform('count')
        d = df.groupby(['id', 'term']).size().to_frame(name='f').reset_index()
        result = pd.merge(df, d, on=["id", "term"], how='inner')
        result['tf'] = result['f'] / result['d']
        result['N'] = len(result['id'].unique())
        df_t = result.groupby(['term', 'id']).size().to_frame(name='df_t').reset_index()
        df_t = df_t['term'].groupby(df_t['term']).count().reset_index(name='df_t')
        result = pd.merge(result, df_t, on=["term"], how='inner')
        import math
        result['idf'] = result.apply(lambda x: math.log(x['N']/x['df_t']), axis=1)
        result['tf_idf'] = result['tf'] * result['idf']
        # print(result[result['id'] == 803616])
        # print(result)
        # print (df[df['id'] == 803616][['id','term']])
        # print (d[d['id'] == 803616])
        result.to_csv(path + 'tf_idf_checked.csv')
        break


