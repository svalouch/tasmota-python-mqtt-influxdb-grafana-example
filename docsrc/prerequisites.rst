#############
Prerequisites
#############

A machine that runs 24/7
************************

First of all, you'll need a computer that is running 24/7. It will serve as the message broker and data storage. It
won't need crazy amounts of RAM, CPU or disk space, though. A RaspberryPI should be enough to get started, although
InfluxDB (any time series database in general) is not exactly going to enhance your SD cards lifetime... It will also
host the Grafana instance to view the results. All this can run on different computers, of course, but for the sake of
this guide, we'll assume it's all on one device.

A Tasmota-powered device
************************
Another thing that is quite obviously required is a device running a recent Tasmota version. Note that flashing,
wiring etc. is not part of the guide.
