##############
Software Setup
##############

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

