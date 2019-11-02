import pandas as pd
import os

df = pd.DataFrame()
for file in os.listdir('output'):
    try:
        df_read = pd.read_csv('./output/' + file)
        df = df.append(df_read)
    except:
        continue

df.to_csv("out.csv", index = None, header = True)