# -*- coding: utf-8 -*-

import subprocess,sys,signal,os,logging,random
import argparse
from time import sleep

parser = argparse.ArgumentParser(description='Set IP address/Set TestCases/Set running time for each TestCase', prog='PROG')
parser.add_argument('-v','--version', action='version', version='%(prog)s V3.0')
parser.add_argument('-s','--source', type=str, nargs='+', help='List all input sources which need to test: atv/dtv/hdmi1/hdmi2/hdmi3/cvbs/local')
parser.add_argument('-t','--time', type=int, nargs='+', default=10, help='Set test duration for each source')
parser.add_argument('-l','--loop', type=int, nargs='+', help='Set test duration for each source')
flag_parser = parser.add_mutually_exclusive_group(required=False)
flag_parser.add_argument('-r', dest='flag', action='store_false')
parser.set_defaults(flag=True)   # '-r'参数会置flag为False，此时会开始随机切换，默认为非随机切换

args = parser.parse_args()
test_durations = args.time  # 测试时长
random_status = args.flag   # 随机状态

if args.source:  # 如果source选项存在，source_lists变量从参数获取，如果source不存在，则source_list变量默认为全部通道
    source_lists = args.source
else:
    source_lists = ['atv','dtv','hdmi1','hdmi2','hdmi3','cvbs','local']

if args.loop is not None:  # 循环次数，如果有参数，则循环指定的次数，如果没有则是无限循环
    test_cycles = args.loop
else:
    test_cycles = float("inf")
    print(test_cycles,type(test_cycles))

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

class TvSource(object):
    def __init__(self, dsn=""):
        if dsn == "":
            self.dsn = dsn
        else:
            self.dsn = '-s %s' % dsn
        if os.name == 'posix':
            self.forceStop = 'am force-stop com.android.tv >/dev/null 2>&1'
            self.disableRC = "'echo 2 > /sys/class/remote/amremote/protocol'"
            self.enableRC = "'echo 1 > /sys/class/remote/amremote/protocol'"
        else:
            self.forceStop = 'am force-stop com.android.tv >nul'
            self.disableRC = '"echo 2 > /sys/class/remote/amremote/protocol"'
            self.enableRC = '"echo 1 > /sys/class/remote/amremote/protocol"'
        self.sourceMenu = 'input keyevent 178'
        self.up = 'input keyevent KEYCODE_DPAD_UP'
        self.down = 'input keyevent KEYCODE_DPAD_DOWN'
        self.enter = 'input keyevent KEYCODE_ENTER'
        self.channel_up = 'input keyevnt 166'
        self.channel_down = 'input keyevnt 167'
        self.home = 'input keyevent KEYCODE_HOME'
        self.decoder_path = "cat /sys/class/vfm/map | grep vdec-map-0 | grep -o '(1)' | wc -l"
        self.hdmi_path = "cat /sys/class/vfm/map | grep tvpath | grep -o '(1)' | wc -l"
        self.dtv_path = "cat /sys/class/vfm/map | grep default | grep -o '(1)' | wc -l"
        self.hdmi1 = "am start -a android.intent.action.VIEW -n com.amazon.tv.inputpreference.service/com.amazon.tv.inputpreference.player.PassthroughPlayerActivity -d " \
                     "'tvinput://tunenow?inputId=com.droidlogic.tvinput/.services.Hdmi1InputService/HW5&suppressInputTuneNotification=false&refTag=home_recents' > /dev/null 2>&1"
        self.hdmi2 = "am start -a android.intent.action.VIEW -n com.amazon.tv.inputpreference.service/com.amazon.tv.inputpreference.player.PassthroughPlayerActivity -d " \
                     "'tvinput://tunenow?inputId=com.droidlogic.tvinput/.services.Hdmi2InputService/HW5&suppressInputTuneNotification=false&refTag=home_recents' > /dev/null 2>&1"
        self.hdmi3 = "am start -a android.intent.action.VIEW -n com.amazon.tv.inputpreference.service/com.amazon.tv.inputpreference.player.PassthroughPlayerActivity -d " \
                     "'tvinput://tunenow?inputId=com.droidlogic.tvinput/.services.Hdmi3InputService/HW5&suppressInputTuneNotification=false&refTag=home_recents' > /dev/null 2>&1"
        self.livetv = "'am start -n com.amazon.tv.livetv/.TvChannelsPlayerActivity' > /dev/null 2>&1"
        self.cvbs = "am start -a android.intent.action.VIEW -n com.amazon.tv.inputpreference.service/com.amazon.tv.inputpreference.player.PassthroughPlayerActivity -d " \
                    "'tvinput://tunenow?inputId=com.droidlogic.tvinput/.services.AV1InputService/HW1&suppressInputTuneNotification=false&refTag=home_recents' > /dev/null 2>&1"

    def setUp(self):
        self.root_device()
        logging.info('Initial device...')
        self.shell_command(self.forceStop)
        self.shell_command(self.home)
        sleep(1)
        logging.info('Disable RC function')
        self.shell_command(self.disableRC)

    def tearDown(self):
        logging.info('Terminate Testing')
        logging.info('Recover RC function')
        self.shell_command(self.enableRC)
        self.shell_command(self.home)

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

    def check_hdmi_info(self):
        pass

    def test_play_atv(self, duration):
        self.shell_command(self.sourceMenu)
        sleep(2)
        logging.info('Ready to play ATV channel for {}s, loop: {}'.format(duration, loop))
        self.shell_command(self.enter)
        sleep(duration)
        self.check_path_hdmi()

    def test_play_dtv(self, duration):
        self.shell_command(self.sourceMenu)
        sleep(2)
        self.shell_command(self.down)
        sleep(1)
        logging.info('Ready to play DTV channel for {}s, loop: {}'.format(duration, loop))
        self.shell_command(self.enter)
        sleep(duration)
        self.check_path_dtv()

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
        self.check_path_hdmi()

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
        self.check_path_hdmi()

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
        self.check_path_hdmi()

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
        self.check_path_hdmi()

    def check_path_local(self):
        timer = 0
        while True:
            value = self.shell_command(self.decoder_path).strip()
            if value == '3':
                timer += 1
                logging.info('decoder path is in used, value: {}, timer: {}'.format(value, timer))
                sleep(20)
                if timer == 3:
                    break
                else:
                    continue
            elif value == '0':
                logging.info('path has released, value: {}'.format(value))
                break

    def check_path_hdmi(self):
        value = self.shell_command(self.hdmi_path).strip()
        if value == '3':
            logging.info('tvpath is in used, value: {}'.format(value))
            sleep(1)
        elif value == '0':
            logging.info('path has released, value: {}'.format(value))

    def check_path_dtv(self):
        value = self.shell_command(self.dtv_path).strip()
        if value == '3':
            logging.info('default path is in used, value: {}'.format(value))
            sleep(1)
        elif value == '0':
            logging.info('path has released, value: {}'.format(value))

    def test_movieplayer_from_udisk(self, duration):
        logging.info('Start local playback test with Movie Player')
        vpath = 'Videos'
        movieplayer = 'am start -a android.intent.action.VIEW -n com.droidlogic.videoplayer/.VideoPlayer -d file:'
        output = self.shell_command('ls /storage').strip().split(' ')
        filter = [b'emulated', b'self']
        driver = [i for i in output if i not in filter]
        if len(driver) == 0:
            logging.info('There is no udisk plugged in')
            return
        elif len(driver) == 1:
            udisk_path = os.path.join('/storage', driver[0], vpath)
        command = ('ls', udisk_path)
        cmd = ' '.join(command)
        videos = self.shell_command(cmd).strip().split(' ')
        videos = [i.strip() for i in videos if i != '']
        #print(videos)
        video_files = []
        for video in videos:
            video_files.append(os.path.join(udisk_path, video))
        if len(video_files) >= 1:
            for index,video in enumerate(video_files):
                command = movieplayer + video_files[index]
                logging.info('Play MoviePlayer with Video: {}'.format([video]))
                self.shell_command(command)
                sleep(duration)
                self.check_path()
                sleep(1)
                self.shell_command('am force-stop com.droidlogic.videoplayer')
                sleep(1)

    def test_movieplayer_from_local(self, duration):
        logging.info('Start local playback test with Movie Player')
        vpath = 'Videos'
        self.root_device()
        movieplayer = 'am start -a android.intent.action.VIEW -n com.droidlogic.videoplayer/.VideoPlayer -d file:'
        store_path = '/storage/emulated/0/Movies/'
        is_exist = self.shell_command('ls /storage/emulated/0/Movies/').strip().split(' ')
        source_path = os.path.join(os.getcwd(), vpath)
        video_list = os.listdir(source_path)
        videos = []

        if len(is_exist) != 0:
            for video in video_list:
                if video not in is_exist:
                    logging.info('{} is not exist!'.format(video))
                    logging.info('Copying {} to {}, please wait...'.format(video, store_path))
                    video_path = os.path.join(os.getcwd(), vpath, video)
                    self.push_command(video_path, store_path)
                    store_video = os.path.join(store_path, video)
                    videos.append(store_video)
                else:
                    store_video = os.path.join(store_path, video)
                    videos.append(store_video)
        else:
            for video in video_list:
                logging.info('{} is not exist!'.format(video))
                logging.info('Copying {} to {}, please wait...'.format(video, store_path))
                video_path = os.path.join(os.getcwd(), vpath, video)
                self.push_command(video_path, store_path)
                store_video = os.path.join(store_path, video)
                videos.append(store_video)

        if len(videos) >= 1:
            for video in videos:
                command = movieplayer + video
                logging.info('Play MoviePlayer with Video: {}'.format([video]))
                self.shell_command(command)
                sleep(duration)
                self.check_path_local()
                sleep(1)
                self.shell_command('am force-stop com.droidlogic.videoplayer')
                sleep(1)
                self.check_path_local()
        else:
            logging.info('Video copy failed, please check!')

def exit(signum, frame):
    print('You choose to stop me.')
    device = dsn
    TvSource(device).tearDown()
    sys.exit(1)

def main():
    global loop
    loop = 1
    running = True
    duration = test_durations[0]
    source_groups = ['atv','dtv','hdmi1','hdmi2','hdmi3','cvbs','local']
    target_source = [i for i in source_groups if i in source_lists]
    #print(source_lists, test_durations, random_status, test_cycles, duration)

    while running:
        logging.info('{:=<20} {} {:=<20}'.format('', loop, ''))
        if random_status == False:
            random.shuffle(target_source)
            duration = random.randint(5,10)
        print('source_lists:',source_lists, 'test_cycles:', test_cycles, 'duration:', duration, 'random_status:', random_status)

        for source in target_source:
            if source == 'atv':
                TvSource(dsn).test_play_atv(duration)
            elif source == 'dtv':
                TvSource(dsn).test_play_dtv(duration)
            elif source == 'hdmi1':
                TvSource(dsn).test_play_hdmi1(duration)
            elif source == 'hdmi2':
                TvSource(dsn).test_play_hdmi2(duration)
            elif source == 'hdmi3':
                TvSource(dsn).test_play_hdmi3(duration)
            elif source == 'cvbs':
                TvSource(dsn).test_play_cvbs(duration)
            else:
                TvSource(dsn).test_movieplayer_from_local(duration)

        loop += 1

        if test_cycles != float("inf"):
            if loop == (test_cycles[0]+1):
                running = False

if __name__ == '__main__':
    logging_init()
    dsn = select_device()
    TvSource(dsn).setUp()
    signal.signal(signal.SIGINT, exit)
    signal.signal(signal.SIGTERM, exit)
    main()
    TvSource(dsn).tearDown()
