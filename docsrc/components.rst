##########
Components
##########

This page gives a high-level overview over the components used. It is not intended to be a comprehensive guide, refer
to the components' homepages for more information.

InfluxDB
========
Docs: `<https://docs.influxdata.com/influxdb/v1.7>`_

InfluxDB serves as data storage. It's a so-called timeseries database, meaning that it associates every data point
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
Docs: `<https://mosquitto.org>`_

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
Docs: `<https://grafana.com/docs/grafana/latest/>`_

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

Python
======
Docs: `<https://docs.python.org/3/>`_

Python is the glue code that connects the components. Any version of Python 3 should do. Please use your
distributorions repositories for security updates, and use a distribution version that still receives security
updates.
