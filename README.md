# vibration-logger
This is an ESP32-based acceleration and GPS datalogger.
It records accelerometer data at 100 samples per second in geo-tagged 3-second chunks, into a binary file on an SD card.
It is intended for use on automobiles during long road trips.
It allows the user to collect data on road condition and to deduce the time and place of shock damage to sensitive cargo.

This project uses the Arduino IDE and language with the ESP32 expansion pack.

Components used:
1. ESP32 WROOM development board
2. MPU6050 3-axis accelerometer module
3. Neo-6M GPS module
4. spi-based SD Card module

The Python scripts visualize the recorded data on a map and as waveforms, selectable by percentile of maximum shock.
The Python are for demonstrative purposes only; they work within certain fixed geographical bounds and for short trips.
A different parser and plotter will be required for longer trips.
