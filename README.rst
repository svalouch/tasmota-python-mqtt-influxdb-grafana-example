#####################################
Tasmota MQTT Influxdb Grafana Example
#####################################

This repository provides a starting point for wiring up an IoT-device running Tasmota_ to an InfluxDB_ over MQTT_ and
displaying the results in Grafana_.

The guide fokuses on measurement data provided by the Tasmota firmware running on a suitable device. That means that
running this on a device like the `Sonoff S20` will only yield wifi metrics. A `Sonoff POW R2` will export power
measurements, too, which is of much higher interest in general.

Let's first get some things straight:

Warnings and clarifications
***************************

.. warning::

   Use at your own risk. Everything in this repository comes **without warranty**.

.. warning::

   Devices running Tasmota often deal with potentially lethal amounts of energy.

.. warning::

   The solution provided is meant to get you started. It does **not** focus on securing access to the device, database
   or message broker. This is intentionally left as an excercise for the reader.

Components
**********

InfluxDB
========
InfluxDB_ serves as data storage. It's a so-called timeseries database, meaning that it associates every data point
with an accurate timestamp. Its main interface is via a JSON API over HTTP(S), a command line interface is also
available. The interface has some ressemblance to the popular MySQL/MariaDB prompt and structure.

The following parts all use the command line interface tool ``influx``. As this guide is just a jumpstart, we won't
concern ourselves with security.

Enter ``influx`` into your terminal and you should be greeted with a message similar to the following:

::

   Connected to http://localhost:8086 version unknown
   InfluxDB shell version: unknown
   >

The ``>`` is the prompt, type commands here and submit them using Enter/Return.

Databases
---------
Databases are similar to schemas in traditional databases. They contain a set of time series' and access can be
limited to certain users.

To view available databases, use ``show databases``

::

   > show databases
   name: databases
   name
   ----
   _internal
   tasmota

The `tasmota` database was created using this guide, initially you won't see it.

To create a database, issue ``create database databasename``. Similar to MySQL, use ``use databasename`` to select a
specific database, additional commands will then be executed in the context of the mentioned database.

Measurements
------------
Measurements look a lot like traditional database tables, but behave different in some aspects. Use ``show
measurements`` to view them after having selected a database.

Measurements are created on the fly when a data point is submitted to the database. The types of the fields in this
initial data point decide the type used, submitting further points with different data types results in an error.

View the measurements using ``show measurements``:

::

   > show measurements
   name: measurements
   name
   ----
   energy
   events
   state

Series
------
Time series are what the name implies, series of data points associated with time. Each set of `tags` (see below) in a
`measurement` (see above) results in its own unique series. For example, with two  devices submitting their points to
the `energy` measurement results in the following output of ``show series``:

::

   > show series
   key
   ---
   energy,host=sonoff-pow-1
   energy,host=shelly-pm-1

Mosquitto / MQTT
================
Mosquitto is an MQTT message broker. We'll be using a very small subset of its many features. MQTT (the protocol) is
centered around topics to which receiving clients subscribe to. Basically, a sender sends a message to a topic and
every client that subscribed to it is notified. There are some details that are not handled by this guide, such as
message QoS (we're using QoS 0 to be exact), ACLs and authentication. Refer to the MQTT and Mosquitto documentation
for more.

Mosquitto has two very useful utilities  ``mosquitto_pub`` and ``mosquitto_sub``, these are very useful when
debugging and can be used when writing clients in shellscripts.

Mosquitto is a very powerful piece of software and supports advanced security models utilizing TLS mutual
authentication and TLS transport encryption, last will (a message sent when a client disconnects to let the others
know) and many more.

Topics and Messages
-------------------
Topics are like topics in a discussion, their name should describe them. They form a hierarchical structure not unlike
a typical filesystem hierarchy or tree. The elements are divided by forward slashes (``/``). A typical topic in this
guide is ``tele/sonoff-pow-1/ENERGY``. This is also the format used in this guide, where ``sonoff-pow-1`` is the
hostname of one of the devices. This can be configured rather freely in Tasmota, however.

Topics are by default generated on the fly by sending (publishing) messages or by subscribing to them.

**Messages** are usually strings, but they can really be any kind of data. Tasmota usually sends JSON encoded as a string.

Subscribing to topics
---------------------
Clients can subscribe to topics and are then notified of any messages posted to these topics by publishers (see
below). Usually, clients subscribe only to topics they're actually interested in. In this guide, we'll subscribe to
all topic of of the form ``tele/<somename>/SENSOR`` (and some others), so we'll be using the wildcard format:
``tele/+/SENSOR``

Using ``mosquitto_sub``, we can subscribe to all these messages and watch them scroll by in the terminal:

.. code-block:: shell-session

   $ mosquitto_sub -t 'tele/+/STATE' -t 'tele/+/SENSOR'
   {"Time":"2020-03-11T17:49:33","Uptime":"0T18:30:12","UptimeSec":66612,"Heap":28,"SleepMode":"Dynamic","Sleep":50,"LoadAvg":19,"MqttCount":1,"POWER":"ON","Wifi":{"AP":1,"SSId":"no_net","BSSId":"82:2A:A8:D1:25:5D","Channel":6,"RSSI":62,"Signal":-69,"LinkCount":1,"Downtime":"0T00:00:05"}}
   {"Time":"2020-03-11T17:49:33","ENERGY":{"TotalStartTime":"2020-02-12T18:49:35","Total":14.834,"Yesterday":0.553,"Today":0.176,"Period":0,"Power":0,"ApparentPower":0,"ReactivePower":0,"Factor":0.00,"Voltage":230,"Current":0.000}}

As you can see, multiple topics can be watched at the same time by repeating ``-t <topic>``.


Publishing to topics
--------------------
Publishing using ``mosquitto_pub`` is similar to subscribing, but now we're always specifying a specific topic name
and send a payload.

For example, sending a message can be as easy as: ``mosquitto_pub -t test -m hello``.

If you open a second terminal and subscribe to it using ``mosquitto_sub -t test`` you should receive the message
``hello``:

.. code-block:: shell-session

   $ mosquitto_sub -t test
   hello

Grafana
=======
Grafana let's you view time series data (among others). We'll use it to create dashboards that query InfluxDB and lets
us view the sensor measurements from the Tasmotas.

Data sources
------------
Data sources are Grafanas representation of time series databases, and it supports a lot of different ones. A data
source also defines how to connect to the actual data storage. In this guide, we'll setup the ``InfluxDB`` data source
and use it to query sensor measurements.

Dashboards
----------
Dashboards are collections of (graph) panels. They provide a grid structure to snap panels into. They can be ordered
by using folders.

Panels
------
Panels show data, plain and simple. There are many types of panels, such as traditional graph panels showing lines and
Grafana comes with a lot of different panels. Panels are always associated with a dashboard and (usually) one data
source. They provide an interactive editor specific to the selected data source and usually provide hints while typing
the queries.

Prerequisites
*************

First of all, you'll need a computer that is running 24/7. It will serve as the message broker and data storage. It
won't need crazy amounts of RAM, CPU or disk space, though. A RaspberryPI should be enough to get started, although
InfluxDB (any time series database in general) is not exactly going to enhance your SD cards lifetime... It will also
host the Grafana instance to view the results. All this can run on different computers, of course, but for the sake of
this guide, we'll assume it's all on one device.

Another thing that is quite obviously required is a device running a recent Tasmota version. Note that flashing,
wiring etc. is not part of the guide.

Getting the software and basic setup
************************************
Depending on your distribution of choice, getting the software can be a challenge. Some popular distributions are
listed below:

InfluxDB
========
There is no real version-specific feature in use, most versions of InfluxDB will work.

Installing
----------
First, check if your distribution already provides the neccessary package. It is usually called ``influxdb``.

* Arch packages it in ``community/influxdb``: ``pacman -S influxdb``.
* Debian includes ``influxdb`` since `Stretch`, just use this using ``apt install influxdb``.
* Gentoo has it included in ``~arch``. Unmask the package and ``emerge dev-db/influxdb``.
* Ubuntu and Ubuntu-based such as Mint, RHEL and RHEL-based such as CentOS: Use the vendor repositories at
  `<https://docs.influxdata.com/influxdb/v1.7/introduction/installation#installing-influxdb-oss>`_.

With the database installed, start it (if it is not auto-started) using ``systemctl start influxdb.serive`` for
systemd-based distributions or ``/etc/init.d/influxdb start`` for SysVInit and OpenRC.

Setup
-----
The main config file is usually found at ``/etc/influxd.conf`` and is an `ini` file. The database listens on port
``8086`` on ``localhost`` by default, which is sufficient for this guide.

Connect to it using the client program supplied with it and create the database ``tasmota``:

.. code-block:: shell-session

   $ influx
   Connected to http://localhost:8086 version 1.6.1
   InfluxDB shell version: 1.6.1
   > create database tasmota
   > quit

Mosquitto
=========
All major distributions have ``mosquitto`` packaged. No special features are required by this guide, so any version
included in a distribution that still receives support should suffice.

The main configuration file can usually be found at ``/etc/mosquitto/mosquitto.conf``. The default config should
suffice, though it by default listens on all interfaces, so restricting it via ``bind_address`` is highly recommended.

The daemon listens on port ``1883`` by default.

Python
======
Python should be provided by your distribution of choice. For obvious reasons, the guide does not care for Python 2.
The minimum Python version the code is tested with is Python 3.6, but it should work on 3.5 (Debian Stretch), too.

Required packages
-----------------
* ``influxdb`` for interfacing with InfluxDB. It handles many of the specialties, though one could also use the API
  directly using `requests`.
* ``paho-mqtt`` for working with the MQTT broker.

MQTT
----
In order to connect to the MQTT broker and to subscribe, we'll use the ``paho-mqtt`` library and some callbacks. The
general way this library works is:

#. Create an instance of the client
#. Set up the ``on_connect`` callback. It is called uppon successful connection. The callback will subscribe to the
   interesting topics, as this information is not persistent.
#. Set up the ``on_message`` callback that is called for every message in any subscribed topic.
#. Connect using ``connect()``.
#. Use ``loop_forever()``, this will never return and from now on everything is managed by the MQTT library. It will
   call the previously set callbacks.

In code, it looks like the following:

.. code-block:: python

   import paho.mqtt.client as paho

   # this is the on_connect callback method
   def cb_on_connect(mqtt, userdata, flags, rc):
       mqttc.subscribe('tele/+/SENSOR')
       # subscribe to other topics

   # this is the on_message callback method
   def cb_on_message(mqtt, userdata, message):
       print('Topic: {0} | Message: {1}'.format(msg.topic, msg.payload))
       # work with the data

   def main():
       global mqttc  # bad style, but enough for the example

       # create a client instance with a "client id" (like a user agent). clean_session means that we don't care for
       # stored messages (concern of QoS > 0).
       mqttc = paho.Client('python-test-0.1', clean_session=True)

       mqttc.on_connect = cb_on_connect
       mqttc.on_message = cb_on_message

       # connect to the broker on localhost with a 60 seconds timeout
       mqttc.connect('localhost', 1883, 60)

       # enter the endless loop
       mqttc.loop_forever()

   if __name__ == '__main__':
       main()


InfluxDB
--------
The ``influxdb`` package provides a nice interface. One important bit especially with Grafana is the use of the
correct time precision. By default, points are stored with a nano-second precision which causes Grafana to fail to
display a continous line. Tasmota usually sends messages every few minutes, so a minute precision is perfect for us.

#. Create an instance of the client. The instance is bound to a database (that has to exist prior to writing data)
#. Write data

.. code-block:: python

   from influxdb import InfluxDBClient

   # precision is in minutes as stated above
   time_precision = 'm'

   # Create a client instance. admin/admin are dummy-credentials unless the database is configured for authentication
   influxc = InfluxDBClient('localhost', 8086, 'admin', 'admin', 'tasmota')

   # assemble one data point (the interface can work with many points at the same time, though)
   points = [{'measurement': 'test', 'tags': {'host': 'sonoff-pow-r1'}, 'fields': {'testtemperature': 21.0})
   # write the datapoint
   influxc.write_points(points=points, time_precision=time_precision)

That's basically it.

Grafana
=======
Grafana is packaged by some distributions:

* Arch has ``community/grafana``, install using ``pacman -S grafana``.
* Gentoo has ``www-apps/grafana-bin``, unmask it and ``emerge grafana-bin``.

For most of the distributions, relying on the vendor packages is recommended:
`<https://grafana.com/grafana/download>`_

Any reasonably recent version should suffice.

Setup
-----
After installation, find the config file in ``/etc/grafana/grafana.ini`` and make a few adjustments. Grafana hosts its
content on its own and listens on port ``3000`` by default. Its default credentials are:

* User: ``admin`` 
* Password: ``admin``

And these should be changed.

TODO datasource setup
TODO dashboard setup

