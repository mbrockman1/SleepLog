import sqlite3
import time
import logging
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session

'''
Nachos
'''

table_name = 'sleep_wake_table'
id_column = 'ID'
ID_col_type = 'INTEGER'
sleep_column = 'sleep'
column_type = 'REAL'
default_val = "Null"
field_type = 'REAL'
wake_column = 'wake'
diff_column = 'diff'
time_db = sqlite3.connect('time.db', check_same_thread=False)
db_cursor = time_db.cursor()

app = Flask(__name__)
ask = Ask(app, "/")

try:
    db_cursor.execute('CREATE TABLE {tn} ({nf} {ft} PRIMARY KEY)'
                      .format(tn=table_name, nf=id_column, ft=ID_col_type))
    db_cursor.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct} DEFAULT '{df}'"
                      .format(tn=table_name, cn=sleep_column, ct=column_type,
                              df=default_val))
    db_cursor.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct} DEFAULT '{df}'"
                      .format(tn=table_name, cn=wake_column, ct=column_type,
                              df=default_val))
    db_cursor.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct} DEFAULT '{df}'"
                      .format(tn=table_name, cn=diff_column, ct=column_type,
                              df=default_val))
    time_db.commit()
except:
    pass

logging.getLogger("flask_ask").setLevel(logging.DEBUG)


def _delete_null_vals():
    db_cursor.execute('DELETE FROM {tn} WHERE {cn} = "Null"'
                      .format(tn=table_name, cn=wake_column))
    time_db.commit()


def how_many_rows():
    db_cursor.execute('SELECT * FROM {tn}'
                      .format(tn=table_name))
    list_of_items = db_cursor.fetchall()
    print list_of_items
    return len(list_of_items)


def _diff_time(last_val):
    db_cursor.execute('SELECT * FROM {tn} ORDER BY {id} DESC LIMIT 1'
                      .format(tn=table_name, id=id_column))
    list_of_items = db_cursor.fetchone()
    diff = list_of_items[2] - list_of_items[1]
    db_cursor.execute('UPDATE {tn} SET {cn}={sleep_time} WHERE {id}={last}'
                      .format(tn=table_name, cn=diff_column, sleep_time=diff,
                              id=id_column, last=last_val))
    time_db.commit()
    return diff


def return_last_id_value():
    db_cursor.execute('SELECT * FROM {tn} ORDER BY {idf} DESC LIMIT 1'
                      .format(tn=table_name, idf=id_column))
    list_of_items = db_cursor.fetchone()
    return list_of_items[0]


@ask.intent("SleepIntent")
def go_to_bed_insertion():
    _delete_null_vals()
    db_cursor.execute("INSERT OR IGNORE INTO {tn} ({id}, {cn}) VALUES ({id_num}, {sleep_time})"
                      .format(tn=table_name, id=id_column, cn=sleep_column,
                              id_num=how_many_rows(), sleep_time=time.time()))
    time_db.commit()
    night_msg = render_template('night')
    return statement(night_msg)


@ask.intent("WakeIntent")
def wake_up_insertion():
    last_val = return_last_id_value()
    db_cursor.execute('UPDATE {tn} SET {cn}={sleep_time} WHERE {id}={last}'
                      .format(tn=table_name, cn=wake_column,
                              sleep_time=time.time(), id=id_column,
                              last=last_val))
    sleep_wake_differential = _diff_time(last_val)
    # import pdb
    # pdb.set_trace()
    time_db.commit()
    morning_msg = render_template(
        'morning', numbers=int(sleep_wake_differential))
    return statement(morning_msg)

if __name__ == '__main__':
    app.run(debug=True)
