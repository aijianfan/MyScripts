# -*- coding: utf-8 -*-

import os, sys, subprocess,logging, signal, time, threading
from time import sleep

"""

1. 准备一个U盘或移动硬盘，并在其根目录创建一个名为"Videos"的目录，里面放置一部或多部体积较大的视频文件；
2. 将U盘或移动硬盘接入待测试平台，执行脚本即可；
3. 脚本会开始执行USB的读写并发测试。

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
            self.movieplayer = "'am start -a android.intent.action.VIEW -n com.droidlogic.videoplayer/.VideoPlayer -d file:'"
            self.disableRC = "'echo 2 > /sys/class/remote/amremote/protocol'"
            self.enableRC = "'echo 1 > /sys/class/remote/amremote/protocol'"
        else:
            self.movieplayer = '"am start -a android.intent.action.VIEW -n com.droidlogic.videoplayer/.VideoPlayer -d file:"'
            self.disableRC = '"echo 2 > /sys/class/remote/amremote/protocol"'
            self.enableRC = '"echo 1 > /sys/class/remote/amremote/protocol"'
        self.home = 'input keyevent KEYCODE_HOME'
        self.decoder_path = "cat /sys/class/vfm/map | grep vdec-map-0 | grep -o '(1)' | wc -l"
        self.dtv_path = "cat /sys/class/vfm/map | grep default | grep -o '(1)' | wc -l"
        self.frame_count = "cat /sys/module/amvideo/parameters/display_frame_count"

    def setUp(self):
        self.root_device()
        logging.info('Initial device...')
        sleep(2)
        self.root_device()
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

    def push_command(self, file, target_path):
        cmd = "%s %s push %s %s" % ('adb', self.dsn, file, target_path)
        return send_command(cmd)

    def root_device(self):
        return self.adb_command('root > /dev/null 2>&1')

    def check_path_local(self):
        for i in range(3):
            value1 = self.shell_command(self.decoder_path).strip()
            value2 = self.shell_command(self.dtv_path).strip()
            if value1 == '3' or value2 == '3':
                logging.info('decoder path is in used, value: {}, {}'.format(value1, value2))
                sleep(20)
            else:
                logging.info('path has released, value: {}, {}'.format(value1, value2))
                break

    def check_frame_count(self, cycle, count = None):
        if count is None:
            count = []
        for i in range(cycle):
            frame_status = self.shell_command(self.frame_count).strip()
            sleep(0.5)
            count.append(frame_status)
        for i in range(len(count)):
            if (i + 1) < len(count):
                if count[i+1] > count[i] > 0:
                    logging.info('Frame count is increasing, value: {}'.format(count[i+1]))
                    sleep(0.5)
                elif count[i+1] == count[i]:
                    logging.info('Display is in abnormal status, please check!, value: {}'.format(count[i+1]))

    def get_udisk_path(self):
        vpath = 'Videos'
        output = self.shell_command('ls /storage').strip().split(' ')
        filter = [ b'emulated', b'self' ]
        driver = [ i for i in output if i not in filter ]
        if len(driver) == 0:
            logging.info('There is no udisk plugged in')
            return
        elif len(driver) == 1:
            udisk = os.path.join('/storage', driver[0])
            udisk_path = os.path.join('/storage', driver[0], vpath)
        return udisk, udisk_path

    def test_local_playback_via_udisk(self, duration):
        logging.info('>>> [Read]:Start USB read testing <<<')
        udisk_path = self.get_udisk_path()[1]
        command = ('ls', udisk_path)
        cmd = ' '.join(command)
        videos = self.shell_command(cmd).strip().split(' ')
        videos = [ i.strip() for i in videos if i != '' ]
        # print(videos)
        video_files = []
        for video in videos:
            video_files.append(os.path.join(udisk_path, video))
        if len(video_files) >= 1:
            for index, video in enumerate(video_files):
                command = self.movieplayer + video_files[index]
                combine = 'md5sum {}'.format(video)
                logging.info('[Read]:ready to check the 1st time, please wait...')
                start_time = time.time()
                video_md51 = self.shell_command(combine).strip().split(' ')[0]
                logging.info('[Read]:The 1st time, MD5: {}'.format([video_md51]))
                logging.info('[Read]:Play MoviePlayer with Video: {}'.format([video]))
                self.shell_command(command)
                sleep(2)

                if self.shell_command(self.decoder_path).strip() != '3':
                    try:
                        from uiautomator import Device
                        d = Device(dsn)

                        if d(text='Allow', resourceId='com.android.packageinstaller:id/permission_allow_button').exists:
                            logging.info('[Read]:detect this\'s the first time to play!')
                            d.press.enter()
                    except Exception as err:
                        print(err)

                sleep(duration)
                #self.check_path_local()
                self.check_frame_count(5)
                # logging.info('Exit playback and back Home')
                # self.shell_command(self.home)
                # sleep(1)
                # self.check_path_local()
                # sleep(1)
                logging.info('[Read]:ready to check the 2nd time, please wait...')
                video_md52 = self.shell_command(combine).strip().split(' ')[0]
                logging.info('[Read]:The 2nd time, MD5: {}'.format([video_md52]))
                end_time = time.time()
                logging.info('[Read]:Playback cost time: < {}s >'.format((end_time - start_time)))

        if video_md51 == video_md52:
            logging.info('>>> [Read]:Video file test passed <<<')
            sleep(1)
        else:
            logging.info('[Read]:Please check the video file, MD5 has changed.')
            sys.exit(-1)

    def test_write2_storage(self, size):
        logging.info('>>> [Write]:Start USB write testing <<<')
        udisk = self.get_udisk_path()[0]
        test_obj = '/data/local/tmp/test.bin'
        creat_file = 'dd if=/dev/zero of={} bs=1024 count={} > /dev/null'.format(test_obj, size)
        file_md51 = 'md5sum /data/local/tmp/test.bin'
        logging.info('[Write]:Creat new file, size: {}MB'.format((size / 1024)))
        self.shell_command(creat_file)
        logging.info('[Write]:ready to check the 1st time, please wait...')
        original_md5 = self.shell_command(file_md51).strip().split(' ')[0]
        logging.info('[Write]:The 1st time, MD5: {}'.format([original_md5]))
        cp2udisk = 'cp {} {}'.format(test_obj, udisk)
        logging.info('[Write]:Copying file to Udisk...')
        start_time = time.time()
        self.shell_command(cp2udisk)
        end_time = time.time()
        logging.info('[Write]:Cost time: < {}s >, Speed: < {}KB/s >'.format((end_time - start_time),(size / (end_time - start_time))))
        file_md52 = 'md5sum {}/{}'.format(udisk, 'test.bin')
        logging.info('[Write]:ready to check the 2nd time, please wait...')
        after_md5 = self.shell_command(file_md52).strip().split(' ')[0]
        logging.info('[Write]:The 2nd time, MD5: {}'.format([after_md5]))

        if original_md5 == after_md5:
            logging.info('>>> [Write]:Write file test passed <<<')
            sleep(1)
        else:
            logging.info('[Write]:Please check the video file, MD5 has changed.')
            sys.exit(-1)

def exit(signum, frame):
    print('You choose to stop me.')
    device = dsn
    Tv(device).tearDown()
    sys.exit(1)

if __name__ == '__main__':
    logging_init()
    dsn = select_device()
    method = Tv(dsn)
    method.setUp()
    signal.signal(signal.SIGINT, exit)
    signal.signal(signal.SIGTERM, exit)

    while True:
        thread1 = threading.Thread(target=method.test_local_playback_via_udisk, args=(15,))
        thread2 = threading.Thread(target=method.test_write2_storage, args=(1048576,))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

    method.tearDown()

