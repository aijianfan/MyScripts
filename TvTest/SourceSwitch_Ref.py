# -*- coding: utf-8 -*-

import subprocess,sys,signal,os,logging
from time import sleep

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

class TvSource(object):
    def __init__(self, dsn=""):
        if dsn == "":
            self.dsn = dsn
        else:
            self.dsn = '-s %s' % dsn
        if os.name == 'posix':
            self.sourceMenu = 'am start -n com.droidlogic.tv.settings/.TvSourceActivity >/dev/null 2>&1'
            self.forceStop = 'am force-stop com.android.tv >/dev/null 2>&1'
            self.disableRC = "'echo 2 > /sys/class/remote/amremote/protocol'"
            self.enableRC = "'echo 1 > /sys/class/remote/amremote/protocol'"
        else:
            self.sourceMenu = 'am start -n com.droidlogic.tv.settings/.TvSourceActivity >nul'
            self.forceStop = 'am force-stop com.android.tv >nul'
            self.disableRC = '"echo 2 > /sys/class/remote/amremote/protocol"'
            self.enableRC = '"echo 1 > /sys/class/remote/amremote/protocol"'
        self.up = 'input keyevent KEYCODE_DPAD_UP'
        self.down = 'input keyevent KEYCODE_DPAD_DOWN'
        self.enter = 'input keyevent KEYCODE_ENTER'

    def setUp(self):
        self.root_device()
        logging.info('Initial device...')
        self.shell_command(self.forceStop)
        sleep(2)
        logging.info('Disable RC function')
        self.shell_command(self.disableRC)
        sleep(1)

    def tearDown(self):
        logging.info('Terminate Testing')
        sleep(1)
        logging.info('Recover RC function')
        self.shell_command(self.enableRC)
        sleep(1)

    def adb_command(self, args):
        cmd = "%s %s %s" % ('adb', self.dsn, args)
        return send_command(cmd)

    def shell_command(self, args):
        cmd = "%s %s shell %s" % ('adb', self.dsn, args)
        return send_command(cmd)

    def root_device(self):
        return self.adb_command('root > /dev/null 2>&1')

    def test_play_atv(self, duration):
        self.shell_command(self.sourceMenu)
        sleep(2)
        logging.info('Ready to play ATV channel for {}s, loop: {}'.format(duration, loop))
        self.shell_command(self.enter)
        sleep(duration)

    def test_play_dtv(self, duration):
        self.shell_command(self.sourceMenu)
        sleep(2)
        self.shell_command(self.down)
        sleep(1)
        logging.info('Ready to play DTV channel for {}s, loop: {}'.format(duration, loop))
        self.shell_command(self.enter)
        sleep(duration)

    def test_play_hdmi1(self, duration):
        self.shell_command(self.sourceMenu)
        sleep(2)
        self.shell_command(self.down)
        sleep(1)
        self.shell_command(self.down)
        sleep(1)
        logging.info('Ready to play HDMI1 source for {}s, loop: {}'.format(duration, loop))
        self.shell_command(self.enter)
        sleep(duration)

    def test_play_hdmi2(self, duration):
        self.shell_command(self.sourceMenu)
        sleep(2)
        self.shell_command(self.down)
        sleep(1)
        self.shell_command(self.down)
        sleep(1)
        self.shell_command(self.down)
        sleep(1)
        logging.info('Ready to play HDMI2 source for {}s, loop: {}'.format(duration, loop))
        self.shell_command(self.enter)
        sleep(duration)

    def test_play_hdmi3(self, duration):
        self.shell_command(self.sourceMenu)
        sleep(2)
        self.shell_command(self.down)
        sleep(1)
        self.shell_command(self.down)
        sleep(1)
        self.shell_command(self.down)
        sleep(1)
        self.shell_command(self.down)
        sleep(1)
        logging.info('Ready to play HDMI3 source for {}s, loop: {}'.format(duration, loop))
        self.shell_command(self.enter)
        sleep(duration)

    def test_play_cvbs(self, duration):
        self.shell_command(self.sourceMenu)
        sleep(2)
        self.shell_command(self.down)
        sleep(1)
        self.shell_command(self.down)
        sleep(1)
        self.shell_command(self.down)
        sleep(1)
        self.shell_command(self.down)
        sleep(1)
        self.shell_command(self.down)
        sleep(1)
        logging.info('Ready to play AV source for {}s, loop: {}'.format(duration, loop))
        self.shell_command(self.enter)
        sleep(duration)

def exit(signum, frame):
    print('You choose to stop me.')
    device = dsn
    TvSource(device).tearDown()
    sys.exit(1)

if __name__ == '__main__':

    logging_init()
    dsn = select_device()
    loop = 1
    TvSource(dsn).setUp()

    signal.signal(signal.SIGINT, exit)
    signal.signal(signal.SIGTERM, exit)

    while True:

        logging.info('{:=<20} {} {:=<20}'.format('', loop, ''))

        try:
            TvSource(dsn).test_play_atv(15)
            TvSource(dsn).test_play_dtv(15)
            TvSource(dsn).test_play_hdmi1(15)
            TvSource(dsn).test_play_hdmi2(15)
            TvSource(dsn).test_play_hdmi3(15)
            TvSource(dsn).test_play_cvbs(10)

            loop += 1

        except Exception as err:
            print(err)

