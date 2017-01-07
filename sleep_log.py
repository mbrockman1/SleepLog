import boto3
import time
from decimal import Decimal
import logging
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session

app = Flask(__name__)
ask = Ask(app, "/")

# Create Table

# Get the service resource.
dynamodb =\
    boto3.resource('dynamodb',
                   region_name='us-east-2',
                   endpoint_url="https://dynamodb.us-east-2.amazonaws.com")

try:
    # Create the DynamoDB table.
    table = dynamodb.create_table(
        TableName='sleep_wake_table',
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'id_2',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'id_2',
                'AttributeType': 'N'
            },

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    # Wait until the table exists.
    table.meta.client.get_waiter(
        'table_exists').wait(TableName='sleep_wake_table')
except:
    # Connect if already created
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('sleep_wake_table')

logging.getLogger("flask_ask").setLevel(logging.DEBUG)


def _check_if_last_val_has_none(id_num):
    # check if values contain 0, then delete
    try:
        response = table.get_item(
            Key={
                'id': id_num,
                'id_2': id_num
            }
        )
        if response['Item']['wake_time'] == 0:
            table.delete_item(
                Key={
                    'id': id_num,
                    'id_2': id_num
                }
            )
    except:
        pass


def _add_diff_time(id_num):
    response = table.get_item(
        Key={
            'id': id_num,
            'id_2': id_num
        }
    )
    wake_time = response['Item']['wake_time']
    sleep_time = response['Item']['sleep_time']
    diff_time = wake_time - sleep_time
    table.update_item(
        Key={
            'id': id_num,
            'id_2': id_num
        },
        UpdateExpression='SET diff_time = :val1',
        ExpressionAttributeValues={
            ':val1': Decimal(diff_time)
        }
    )
    return diff_time


@ask.intent("SleepIntent")
def go_to_bed_insertion():
    id_num = table.scan()['Count']
    _check_if_last_val_has_none(id_num - 1)
    # Create Item
    table.put_item(
        Item={
            'id': id_num,
            'id_2': id_num,
            'sleep_time': Decimal(time.time()),
            'wake_time': Decimal(0),
            'diff_time': Decimal(0)
        }
    )
    night_msg = render_template('night')
    return statement(night_msg)


def _second_converter(return_time):
    minute, second = divmod(return_time, 60)
    hour, minute = divmod(minute, 60)
    hour_phrase = ""
    minute_phrase = ""
    second_phrase = ""

    if hour == 1:
        hour_phrase = "%d hour" % (hour)
    elif hour > 1:
        hour_phrase = "%d hours" % (hour)
    else:
        pass
    if minute == 1:
        minute_phrase = "%d minute" % (minute)
    elif minute > 1:
        minute_phrase = "%d minutes" % (minute)
    else:
        pass
    if second == 1:
        second_phrase = "%d second" % (int(round(second)))
    elif second > 1:
        second_phrase = "%d seconds" % (int(round(second)))
    else:
        pass

    if hour_phrase + minute_phrase != "":
        return hour_phrase + minute_phrase
    else:
        return second_phrase


@ask.intent("WakeIntent")
def wake_up_insertion():
    id_num = table.scan()['Count'] - 1
    response = table.get_item(
        Key={
            'id': id_num,
            'id_2': id_num
            }
        )
    if Decimal(time.time()) - response['Item']['sleep_time'] < 61200:
        # Update Attributes of item
        table.update_item(
            Key={
                'id': id_num,
                'id_2': id_num
            },
            UpdateExpression='SET wake_time = :val1',
            ExpressionAttributeValues={
                ':val1': Decimal(time.time())
            }
        )
    else:
        pass
    sleep_wake_differential = _add_diff_time(id_num)
    adjusted_time = _second_converter(sleep_wake_differential)
    morning_msg = render_template(
        'morning', time_string=adjusted_time)
    return statement(morning_msg)

if __name__ == '__main__':
    app.run(debug=True)
