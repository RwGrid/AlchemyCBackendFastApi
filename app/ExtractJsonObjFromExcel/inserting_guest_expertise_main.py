# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import os
import pandas
import pandas as pd
import json
import random

chars = '0123456789ABCDEF'

try:
    os.mkdir('json_files')
except:
    pass
shet_name = "Expertise"
excel = pandas.read_excel('lastmayadeen4.xlsx', sheet_name=shet_name)
column_data = "Expertise"
data = excel[column_data]
lst = []
import psycopg2

# Connect to an existing database
conn = psycopg2.connect("host=0.0.0.0 port=5446 dbname=mayadeen user=postgres password=postgres_ali")

# Open a cursor to perform database operations

# table_name= input("> please give me the table u want to insert data into: ")

for d in data:
    x = {}
    x['value'] = d
    x['label'] = d
    x['color'] = '#' + ''.join(random.sample(chars, 6))
    lst.append(x)
    cur = conn.cursor()
    cur.execute("INSERT INTO guests_expertise ( guest_expertise) VALUES (%s)",
                (d,))
    conn.commit()
    cur.close()
xxxx = pd.DataFrame(lst)
oo = xxxx.to_dict(orient='records')
with open('json_files/' + column_data + '.json', 'w', encoding='utf-8-sig') as fp:
    json.dump(oo, fp, ensure_ascii=False)

sss = 0
conn.close()
