# -*- coding: utf-8 -*-

import os, sys, subprocess, logging, signal, time
from time import sleep
from tqdm import tqdm

"""
1. 先检查平台的/data/media分区大小，然后往/data持续写文件，直到还剩下200M左右的空间；
2. 进行恢复出厂设置，重启完成后，会再次执行第一步.
"""


def send_command(cmd):
    output, error = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = output
    return out

# Select the device with input parameter
def select_device():
    devices = subprocess.Popen(['adb','devices'],stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()[0]
    serial_nos = []
    for item in devices.split():
        filters = [b'List', b'of', b'device', b'devices', b'attached']
        if item not in filters:
            serial_nos.append(item.decode('utf-8'))
    if len(serial_nos) == 1:
        return serial_nos[0]
    else:
        devlist = {}
        print('{:=>20}'.format(''))
        for i, device in enumerate(serial_nos):
            devlist[(i+1)] = device
            print('{}{:^2}{}'.format((i+1),':', device))
        print('{:=>20}'.format(''))
        print('{0}[{1}-{2}]'.format('Input Range:', 1, len(serial_nos)))
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
                raise TypeError('\033[31m{}\033[0m'.format('*** out of range ***'))

# logging module package
def logging_init():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level=logging.INFO)
    formatter2 = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
    stream_handler.setFormatter(formatter2)
    logger.addHandler(stream_handler)

class Tv(object):
    def __init__(self, dsn=""):
        if dsn == "":
            self.dsn = dsn
        else:
            self.dsn = '-s %s' % dsn
        if os.name == 'posix':
            self.disableRC = "'echo 2 > /sys/class/remote/amremote/protocol'"
            self.enableRC = "'echo 1 > /sys/class/remote/amremote/protocol'"
        else:
            self.disableRC = '"echo 2 > /sys/class/remote/amremote/protocol"'
            self.enableRC = '"echo 1 > /sys/class/remote/amremote/protocol"'
        self.up = 'input keyevent KEYCODE_DPAD_UP'
        self.down = 'input keyevent KEYCODE_DPAD_DOWN'
        self.home = 'input keyevent KEYCODE_HOME'
        self.enter = 'input keyevent KEYCODE_ENTER'
        self.df = 'df | grep /data/media | awk -F " " \'{print $4}\''
        self.callReset = 'am start -n com.android.tv.settings/.device.storage.ResetActivity'
        self.waitDev = 'wait-for-device > /dev/null'
        self.bootComp = 'getprop sys.boot_completed'

    def setUp(self):
        self.root_device()
        logging.info('Initial device...')
        sleep(2)
        self.acquire_Selinux()
        logging.info('Disable RC function')
        self.shell_command(self.disableRC)

    def tearDown(self):
        logging.info('Terminate Testing')
        logging.info('Recover RC function')
        self.shell_command(self.enableRC)

    def adb_command(self, args):
        cmd = "%s %s %s" % ('adb', self.dsn, args)
        return send_command(cmd)

    def shell_command(self, args):
        cmd = "%s %s shell %s" % ('adb', self.dsn, args)
        return send_command(cmd)

    def root_device(self):
        return self.adb_command('root > /dev/null 2>&1')

    def disable_Selinux(self):
        return self.shell_command('setenforce 0')

    def acquire_Selinux(self):
        self.root_device()
        sleep(2)
        for i in range(5):
            self.disable_Selinux()
            state = self.shell_command('getenforce').strip()
            if state == 'Permissive':
                logging.info('Selinux is disabled')
                sleep(2)
                break
            else:
                continue

    def acquire_storage_info(self):
        bulk = self.shell_command(self.df).strip()
        logging.info('Available internal storage: [ {}KB ]'.format(bulk))
        if isinstance(bulk, str):
            bulk = int(bulk)
        total = bulk
        setteled = 1024 * 200
        object = total - setteled
        return object

    def fill_internal_space(self):
        self.acquire_Selinux()
        size = self.acquire_storage_info()
        test_obj = '/data/local/tmp/test.bin'
        creat_file = 'dd if=/dev/zero of={} bs=1024 count={} > /dev/null'.format(test_obj, size)
        logging.info('To fill the internal data partition, size: {}KB, please wait...'.format(size))
        self.shell_command(creat_file)
        logging.info('fill done')
        bulk = self.shell_command(self.df).strip()
        logging.info('Now available internal storage: [ {}KB ], ready to reboot'.format(bulk))

    def check_boot_state(self):
        while True:
            state = self.shell_command(self.bootComp).strip()
            if state == '1':
                logging.info('Boot finished')
                sleep(1)
                self.acquire_Selinux()
                break
            else:
                self.shell_command(self.waitDev)
                sleep(1)

    def factory_reset(self):
        logging.info('Prepare to do Factory Reset!')
        self.shell_command(self.home)
        sleep(1)
        self.shell_command(self.callReset)
        self.shell_command(self.down)
        sleep(0.5)
        self.shell_command(self.enter)
        sleep(1)
        self.shell_command(self.down)
        sleep(0.5)
        self.shell_command(self.enter)
        logging.info('Starting now')
        sleep(5)
        self.check_boot_state()

def exit(signum, frame):
    print('You choose to stop me.')
    device = dsn
    Tv(device).tearDown()
    sys.exit(1)

if __name__ == '__main__':
    logging_init()
    dsn = select_device()
    fc = Tv(dsn)
    fc.setUp()
    signal.signal(signal.SIGINT, exit)
    signal.signal(signal.SIGTERM, exit)

    loop = 1
    while True:
        logging.info('{:=>15} {} {:=>15}'.format('', loop, ''))
        fc.fill_internal_space()
        fc.factory_reset()
        loop += 1
