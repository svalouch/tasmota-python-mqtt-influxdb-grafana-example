tasmota-python-mqtt-influxdb-grafana-example
============================================

This guide provides a starting point for wiring up an IoT-device running Tasmota_ to an InfluxDB_ over MQTT_ and
displaying the results in Grafana_.

The guide fokuses on measurement data provided by the Tasmota firmware running on a suitable device. That means that
running this on a device like the `Sonoff S20` will only yield wifi metrics. A `Sonoff POW R2` will export power
measurements, too, which is of much higher interest in general.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   warnings-and-clarifications
   prerequisites
   components
   software-setup

.. _Tasmota: https://tasmota.github.io/docs/
.. _InfluxDB: https://docs.influxdata.com/influxdb/v1.7/
.. _MQTT: https://mosquitto.org/
.. _Grafana: https://grafana.com/docs/grafana/latest/
