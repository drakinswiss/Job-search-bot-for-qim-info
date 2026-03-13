import pandas as pd
import sys

with open('cols.txt', 'w', encoding='utf-8') as f:
    df1 = pd.read_csv('all_swissdevjobs.csv')
    f.write('all_swissdevjobs.csv columns:\n')
    f.write(','.join(df1.columns) + '\n\n')

    df2 = pd.read_excel('ictjobs_scraped_data.xlsx')
    f.write('ictjobs_scraped_data.xlsx columns:\n')
    f.write(','.join(df2.columns) + '\n\n')

    df3 = pd.read_excel('linkedin_jobs.xlsx')
    f.write('linkedin_jobs.xlsx columns:\n')
    f.write(','.join(df3.columns) + '\n\n')
