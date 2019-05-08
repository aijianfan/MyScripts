# -*- coding: utf-8 -*-

from uiautomator import Device
import argparse

parser = argparse.ArgumentParser(description='Parameters Configuration', prog='PROG')
parser.add_argument('-d','--device', type=str, nargs='+', help='List all external device\'s IP address')
args = parser.parse_args()
serial_nos = args.device

if len(serial_nos) == 1:
    serial_no = serial_nos[0]

d = Device(serial_no)

print(d.info)
