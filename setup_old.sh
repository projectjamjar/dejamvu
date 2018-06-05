#!/bin/bash

if [ "$(id -u)" != "0" ]; then
    echo "Please run this script as sudo."
    exit 1
fi

apt-get install -y python-numpy python-scipy python-matplotlib libportaudio-dev python-PyAudio python-MySQLdb libav-tools

pip install -r requirements.txt