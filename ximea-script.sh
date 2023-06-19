#!/usr/bin/bash

# Increase default memory usage limits of Linux kernel USB stack

# After every boot run: 
echo 0 | sudo tee /sys/module/usbcore/parameters/usbfs_memory_mb

# or run this script at startup:
# echo 0 > /sys/module/usbcore/parameters/usbfs_memory_mb

# You can use this script to run at startup
# like rc.local using systemd.
# This program should be placed in /usr/local/bin and use conjunction with ximea-script.service
