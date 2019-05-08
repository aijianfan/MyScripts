#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, time, serial, platform, logging, subprocess
from time import sleep

osType = platform.system()
if(osType == 'Windows'):
    uart_config = 'COM3'
elif(osType == 'Linux'):
    uart_config = '/dev/ttyUSB0'
elif(osType == 'Darwin'):
    uart_config = '/dev/cu.SLAB_USBtoUART'

def send_command(cmd):
    output, error = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = output
    return out

def adb_command(args):
    cmd = "%s -s %s %s" % ('adb', sys.argv[1], args)
    return send_command(cmd)

def shell_command(args):
    cmd = "%s -s %s shell %s" % ('adb', sys.argv[1], args)
    return send_command(cmd)

def root_device():
    if osType == 'Linux' or osType == 'Darwin':
        return adb_command('root > /dev/null 2>&1')
    else:
        return adb_command('root >nul')

# define logging module
def logging_init():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    curr_time = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
    log_name = 'script_logs/'
    if not os.path.exists(log_name):
        os.mkdir(log_name)
    pp = os.path.join(os.getcwd(), log_name)
    log_path = ''.join(pp)
    log_name = (log_path, curr_time, '.log')
    log_file = ''.join(log_name)
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(level=logging.INFO)
    formatter1 = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(module)s - %(levelname)s: %(message)s")
    file_handler.setFormatter(formatter1)
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level=logging.INFO)
    formatter2 = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
    stream_handler.setFormatter(formatter2)
    logger.addHandler(stream_handler)

def send_serial_cmd(command):
    ''' Serial port configuration under variable OS '''
    ser = serial.Serial(uart_config, 115200, timeout=1)
    cmd = command.encode('utf-8')
    if osType == 'Linux' or osType == 'Darwin':
        cmd += '\n'.encode('utf-8')
    else:
        cmd += '\r\n'.encode('utf-8')

    if ser.isOpen():
        try:
            ser.write(cmd)
            ser.flush()
            logging.info('[send_serial_cmd] Info: Send command via serial: {}'.format(cmd.replace('\n', '')))
        except SerialException as err:
            logging.info('[send_serial_cmd] Error: {}'.format(err))
        finally:
            ser.close()
    else:
        logging.info('[send_serial_cmd] Info: serial port can not open')

def poll_devices():
    out, err = subprocess.Popen('adb devices', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = out.strip()
    serial_nos = []
    for item in out.split():
        filter1 = [b'List', b'of', b'device', b'devices', b'attached']
        filter2 = [b'offline', b'unauthorized', b'no permissions']
        if item not in filter1:
            if item in filter2:
                logging.info('Device adb status is abnormal, please check!')
                exit(1)
            else:
                serial_nos.append(item.decode('utf-8'))
    return serial_nos

def check_adb_connection(ip_address):
    p = ('adb connect ', ip_address)
    cmd2 = ''.join(p)

    try:
        for i in range(5):
            result = send_command(cmd2).split()  # output result of 'adb connect ip_address', type=list
            sleep(3)
            if 'connected' in result:
                logging.info('adb is connected to {}'.format(sys.argv[1]))
                serials = poll_devices()
                cmd_list = []
                if len(serials) > 1:
                    for j in serials:
                        o = ('adb connect ',j)
                        cmd_list.append(str(o))
                elif len(serials) == 1:
                    o = ('adb connect ', serials[0])
                    cmd_list = ''.join(o)
                    cmd_list = str(cmd_list)
                    # print(cmd_list)
                    send_command(cmd_list)
                    break
                else:
                    logging.info('No device!')
                    exit(1)
            else:
                sleep(2)
                continue
    except Exception as err:
        print(err)

def playing_atv():
    try:
        shell_command()

if __name__ == '__main__':
    logging_init()
    send_serial_cmd('xu 7411')
    check_adb_connection(sys.argv[1])
