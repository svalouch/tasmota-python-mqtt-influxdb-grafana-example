#!/usr/bin/env python3

import paho.mqtt.client as paho
from influxdb import InfluxDBClient

import os
import logging
import json
import re
from datetime import timedelta

# Script version
__version__ = '0.0.1'

# Get settings for MQTT from environment
MQTT_HOST = os.environ.get('MQTT_HOST', '127.0.0.1')
MQTT_PORT = os.environ.get('MQTT_PORT', 1883)

# Get settings for InfluxDB from environment
INFLUX_HOST = os.environ.get('INFLUX_HOST', '127.0.0.1')
INFLUX_PORT = os.environ.get('INFLUX_PORT', 8086)
INFLUX_USER = os.environ.get('INFLUX_USER', 'admin')
INFLUX_PASS = os.environ.get('INFLUX_PASS', 'admin')
INFLUX_DB = os.environ.get('INFLUX_DB', 'tasmota')

# Enable debugging by setting DEBUG=1
DEBUG = os.environ.get('DEBUG', False)

# Regular expression to pull the host name from the topic string.
# In a topic string like "tele/sonoff-pow-1/STATE", this matches "sonoff-pow-1".
HOST_RE = re.compile(r'^[a-zA-Z0-9\-_]+/([a-zA-Z0-9\-_]+)/')

# Match the components of the uptime timestamp sent by Tasmota
UPTIME_RE = re.compile(r'^(\d+)T(\d+):(\d+):(\d+)$')

# Name by which we'll be known to the MQTT broker
CLIENT_ID = 'tasmota-receiver-example_{0}'.format(__version__)

# end of configuration

# Logging
LOGFORMAT = '%(asctime)-15s %(message)s'

if DEBUG:
    logging.basicConfig(level=logging.DEBUG, format=LOGFORMAT)
else:
    logging.basicConfig(level=logging.INFO, format=LOGFORMAT)

# MQTT topics

# SENSOR topic receives sensorical data, such as energy meter, temperature sensors or ambient sensors.
TOPIC_SENSOR = 'tele/+/SENSOR'
TOPIC_STATE = 'tele/+/STATE'
TOPIC_UPTIME = 'tele/+/UPTIME'
TOPIC_RESULT = 'stat/+/RESULT'


def power_to_bool(power):
    '''
    Converts the power state to a boolean. `ON` is True, everything else False.
    '''
    return power.upper() == 'ON'


def uptime_to_seconds(uptime):
    '''
    Converts the uptime string to number of seconds.
    '''
    m = UPTIME_RE.match(uptime)
    if not m:
        return 0
    return timedelta(
        days=int(m.group(1)),
        hours=int(m.group(2)),
        minutes=int(m.group(3)),
        seconds=int(m.group(4))
    ).total_seconds()


# MQTT callback
def cb_on_connect(mqtt, userdata, flags, rc):
    '''
    Invoked after a successful connect to the MQTT broker. The callback subscribes to the interesting topics defined
    above.
    '''
    mqtt.subscribe(TOPIC_SENSOR, 0)
    mqtt.subscribe(TOPIC_STATE, 0)
    mqtt.subscribe(TOPIC_UPTIME, 0)
    mqtt.subscribe(TOPIC_RESULT, 0)


def cb_on_message(mqtt, userdata, msg):
    logging.debug('TOPIC: {0} | MESSAGE: {1}'.format(msg.topic, msg.payload))

    # the measurement that will hold the data
    measurement = None
    # the precision for influx, data is sent every few minutes, so set it to minutes
    time_precision = 'm'
    # this will store the values for this one data point
    fields = dict()

    # extract the host name, fall back to 'UNKNOWN'
    host_match = HOST_RE.match(msg.topic)
    if host_match:
        host = host_match.group(1)
    else:
        host = 'UNKNOWN'

    # tags that we'll add to the data points. The hostname is the only sensible bit of info, so we'll use that.
    # it'll allow querying by host name later. Remember that values can't be used in the WHERE part of the query.
    tags = {'host': host}

    # check which topic we got. Paho provides a nice method that understands the "+" globbing we're using.
    if paho.topic_matches_sub(TOPIC_SENSOR, msg.topic):

        # The sensor topic looks like this for a Sonoff POW R2:
        # Tasmota 5.1.12: {"Time":"2018-06-09T16:29:19","ENERGY":{"Total":0.034,"Yesterday":0.000,"Today":0.031,"Period":3,"Power":34,"Factor":0.85,"Voltage":236,"Current":0.170}}
        # Tasmota 8.1.0: {"Time":"2020-02-10T21:29:35","ENERGY":{"TotalStartTime":"2020-02-10T21:00:25","Total":1.310,"Yesterday":0.000,"Today":0.000,"Period":0,"Power":0,"ApparentPower":0,"ReactivePower":0,"Factor":0.00,"Voltage":0,"Current":0.000}}

        # NOTE: This has to be adjusted for the specific fields your Tasmota-device supports.

        # extract the payload by means of a json parser. It will raise an exception if the data is invalid.
        try:
            st = json.loads(msg.payload.decode('utf-8'))
        except Exception as e:
            logging.critical('Message decoding failed: ' + str(e))
        else:
            # check if the fields are what we look for. Other sensors use different fields.
            if 'ENERGY' in st:
                measurement = 'energy'

                energy = st['ENERGY']

                # extract all the fields, providing sensible defaults if missing.

                # we know that the following fields are always sent by the Sonoff POW R2
                fields['total'] = energy['Total']
                fields['power'] = energy['Power']
                fields['factor'] = energy['Factor']
                fields['voltage'] = energy['Voltage']
                fields['current'] = energy['Current']

                # The following fields are not sent by all versions of Tasmota on the Sonoff POW R2, so we catch that.
                fields['period'] = energy['Period'] if ('Period' in energy and energy['Period']) else 0
                fields['apparent_power'] = energy['ApparentPower'] if 'ApparentPower' in energy else 0.0
                fields['reactive_power'] = energy['ReactivePower'] if 'ReactivePower' in energy else 0.0

                # there are more fields, like "TotalStartTime", "Yesterday" and so on, but we're not interested in them.

            # elif 'OTHERSENSOR' in st:
            #     # handle other sensor data
            else:
                logging.info('No sensor measurement we expect found in message: ' + str(st))

    elif paho.topic_matches_sub(TOPIC_STATE, msg.topic):

        # The STATE topic looks like this for a Sonoff POW R2:
        # Tasmota 5.1.12: {"Time":"2018-06-09T16:29:19","Uptime":"0T04:20:40","Vcc":3.552,"POWER":"ON", "Wifi":{"AP":1,"SSId":"no_net","APMac":"82:2A:A8:D1:25:5D","RSSI":60}}
        # Tasmota 8.1.0: {"Time":"2020-02-10T21:34:35","Uptime":"0T00:10:12","UptimeSec":612,"Heap":26,"SleepMode":"Dynamic","Sleep":50,"LoadAvg":19,"MqttCount":1,"POWER":"OFF","Wifi":{"AP":1,"SSId":"no_net","BSSId":"82:2A:A8:57:58:53","Channel":1,"RSSI":44,"Signal":-78,"LinkCount":1,"Downtime":"0T00:00:05"}}

        try:
            st = json.loads(msg.payload.decode('utf-8'))
        except Exception as e:
            logging.critical('Message decoding failed: ' + str(e))
        else:
            measurement = 'state'

            fields['uptime'] = uptime_to_seconds(st['Uptime'])
            if 'Vcc' in st:
                fields['vcc'] = st['Vcc']
            if 'UptimeSec' in st:
                fields['uptime_sec'] = st['UptimeSec']
            if 'LoadAvg' in st:
                fields['load_avg'] = st['LoadAvg']
            if 'POWER' in st:
                fields['power'] = st['POWER']
            if 'POWER1' in st:
                fields['power1'] = st['POWER1']
            if 'Wifi' in st:
                wi = st['Wifi']
                if 'SSId' in wi:
                    tags['wifi_ssid'] = wi['SSId']
                if 'RSSI' in wi:
                    fields['wifi_rssi'] = wi['RSSI']
                if 'Signal' in wi:
                    fields['wifi_signal'] = wi['Signal']
                if 'Channel' in wi:
                    fields['wifi_channel'] = wi['Channel']

    elif paho.topic_matches_sub(TOPIC_UPTIME, msg.topic):

        # Uptime is already included as part of the state message above. We'll just ignore it.
        # Tasmota 5.1.12 an 8.1.0: {"Time":"2018-06-09T15:02:00","Uptime":"0T02:53:21"}
        pass

    elif paho.topic_matches_sub(TOPIC_RESULT, msg.topic):

        # The Sonff POW R2 and the S20 have a relay. Changes in its state are reported in the result topic. There's
        # more events in here, but we're only caring for the POWER result that tells us the relais state changes.
        # Tasmota 5.1.12 and 8.1.0: {"POWER":"OFF"}

        try:
            st = json.loads(msg.payload.decode('utf-8'))
        except Exception as e:
            logging.critical('Message decoding failed: ' + str(e))
        else:
            measurement = 'events'
            # the exact time is actually of interest here, as state changes can happen anytime and we want to know
            # that.
            time_precision = 's'

            if 'POWER' in st:
                # since a relay can only be on or off, convert it to a boolean as influxdb supports this data type.
                fields['POWER'] = power_to_bool(st['POWER'])

    # If data was gathered above, send it to the InfluxDB
    if measurement and fields:
        influxc.write_points(points=[
            {
                'measurement': measurement,
                'tags': tags,
                'fields': fields,
            }
        ], time_precision=time_precision)


def main():
    logging.info('Starting {0}'.format(CLIENT_ID))

    # Create a handle and connect to the InfluxDB
    global influxc
    influxc = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASS, INFLUX_DB)

    mqttc = paho.Client(CLIENT_ID, clean_session=True)
    mqttc.on_message = cb_on_message
    mqttc.on_connect = cb_on_connect

    try:
        mqttc.connect(MQTT_HOST, MQTT_PORT, 60)
    except ConnectionRefusedError as e:
        logging.critical('Could not connect to MQTT broker: ' + str(e))
    else:
        mqttc.loop_forever()


if __name__ == '__main__':
    main()
