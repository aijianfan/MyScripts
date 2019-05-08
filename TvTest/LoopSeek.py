# -*- coding: utf-8 -*-

import subprocess,sys,signal,os,logging
from time import sleep
import random

def send_command(cmd):
    output, error = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = output
    return out

def select_device():
    devices = subprocess.Popen(['adb','devices'],stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[0]
    serial_nos = []
    for item in devices.split():
        filters = [b'List', b'of', b'device', b'devices', b'attached']
        if item not in filters:
            serial_nos.append(item.decode('utf-8'))
    d = serial_nos
    devlist = {}
    print('{:=>20}'.format(''))
    for i, device in enumerate(d):
        devlist[(i+1)] = device
        print('{}{:^2}{}'.format((i+1),':', device))
    print('{:=>20}'.format(''))
    print('{0}[{1}-{2}]'.format('Input Range:', 1, len(d)))
    inp = input('Please select device:')
    inp = int(inp)
    for key in devlist.keys():
        if inp in devlist.keys():
            if key == inp:
                serial_id = devlist[key]
                print('Your selectiton is:[ {} ]'.format(serial_id))
                return serial_id
            else:
                continue
        else:
            raise TypeError('{}'.format('*** out of range ***'))

def logging_init():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level=logging.INFO)
    formatter2 = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
    stream_handler.setFormatter(formatter2)
    logger.addHandler(stream_handler)

class SeekWhilePlaying(object):
    def __init__(self, dsn=""):
        if dsn == "":
            self.dsn = dsn
        else:
            self.dsn = '-s %s' % dsn
        if os.name == 'posix':
            self.callNetflix = 'am start -n com.netflix.ninja/com.netflix.ninja.MainActivity -a android.intent.action.VIEW ' \
                          '-d \'https://www.netflix.com/watch/80006792?source=99\' >/dev/null 2>&1'
        else:
            self.callNetflix = "am start -n com.netflix.ninja/com.netflix.ninja.MainActivity -a android.intent.action.VIEW -d 'https://www.netflix.com/watch/80006792?source=99' >nul"
    def setUp(self):
        logging.info('Ready to play title in NETFLIX app')
        sleep(2)
        self.shell_command(self.callNetflix)
        sleep(15)

    def tearDown(self):
        logging.info('Terminate Testing')

    def adb_command(self, args):
        cmd = "%s %s %s" % ('adb', self.dsn, args)
        return send_command(cmd)

    def shell_command(self, args):
        cmd = "%s %s shell %s" % ('adb', self.dsn, args)
        return send_command(cmd)

    def fast_forward(self, duration):
        logging.info('Implement FF for {}s'.format(duration))
        self.shell_command('sendevent /dev/input/event3 4 4 786501')
        self.shell_command('sendevent /dev/input/event3 1 106 1')
        self.shell_command('sendevent /dev/input/event3 0 0 0')
        sleep(duration)
        self.shell_command('sendevent /dev/input/event3 4 4 786501')
        self.shell_command('sendevent /dev/input/event3 1 106 0')
        self.shell_command('sendevent /dev/input/event3 0 0 0')
        sleep(1)
        self.shell_command('sendevent /dev/input/event3 4 4 786497')
        self.shell_command('sendevent /dev/input/event3 1 161 1')
        self.shell_command('sendevent /dev/input/event3 0 0 0')
        self.shell_command('sendevent /dev/input/event3 4 4 786497')
        self.shell_command('sendevent /dev/input/event3 1 161 0')
        self.shell_command('sendevent /dev/input/event3 0 0 0')
        sleep(5)

    def back_forward(self, duration):
        logging.info('Implement rewind for {}s'.format(duration))
        self.shell_command('sendevent /dev/input/event3 4 4 786500')
        self.shell_command('sendevent /dev/input/event3 1 69 1')
        self.shell_command('sendevent /dev/input/event3 0 0 0')
        sleep(duration)
        self.shell_command('sendevent /dev/input/event3 4 4 786500')
        self.shell_command('sendevent /dev/input/event3 1 69 0')
        self.shell_command('sendevent /dev/input/event3 0 0 0')
        sleep(1)
        self.shell_command('sendevent /dev/input/event3 4 4 786497')
        self.shell_command('sendevent /dev/input/event3 1 161 1')
        self.shell_command('sendevent /dev/input/event3 0 0 0')
        self.shell_command('sendevent /dev/input/event3 4 4 786497')
        self.shell_command('sendevent /dev/input/event3 1 161 0')
        self.shell_command('sendevent /dev/input/event3 0 0 0')
        sleep(5)

def check_state(command):
    if os.name == 'posix':
        command += ' >/dev/null 2>&1'
    else:
        command += ' >nul'
    #print('command',command)
    state = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = state.communicate()
    if state.returncode == 0:
        logging.info('device is still alive')
        sleep(3)
    else:
        logging.info('device is dead')
        sys.exit(1)

def exit(signum, frame):
    print('You choose to stop me.')
    device = dsn
    TvSource(device).tearDown()
    sys.exit(1)

def main():
    logging_init()
    dsn = select_device()
    logging.info('Start loop seek stress testing')
    SeekWhilePlaying(dsn).setUp()
    running = True
    signal.signal(signal.SIGINT, exit)
    signal.signal(signal.SIGTERM, exit)

    while running:
        SeekWhilePlaying(dsn).fast_forward(random.uniform(0.5,1))
        sleep(random.randint(8,15))
        SeekWhilePlaying(dsn).back_forward(random.uniform(0.5,1))
        check_state('adb shell date')

if __name__ == '__main__':
    main()