# -*- coding: utf-8 -*-

import subprocess,sys,signal,os,logging,time,re,datetime,argparse
from time import sleep

parser = argparse.ArgumentParser(description='', prog='PROG')

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
            raise TypeError('{}'.format('*** out of range ***'))

# logging module package
def logging_init():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    curr_time = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
    log_name = 'Script_logs/'
    if not os.path.exists(log_name):
        os.mkdir(log_name)
    if os.name == 'posix':
        p = (os.getcwd(), '/', log_name)
    else:
        p = (os.getcwd(), '\\', log_name)
    log_path = ''.join(p)
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

class TvSource(object):
    def __init__(self, dsn=""):
        if dsn == "":
            self.dsn = dsn
        else:
            self.dsn = '-s %s' % dsn
        if os.name == 'posix':
            self.forceStop = 'am force-stop com.android.tv >/dev/null 2>&1'
            self.fullscreen = 'am start -n com.android.tv/.MainActivity >/dev/null 2>&1'
            self.disableRC = "'echo 2 > /sys/class/remote/amremote/protocol'"
            self.enableRC = "'echo 1 > /sys/class/remote/amremote/protocol'"
            self.default = "'cat /sys/class/vfm/map | grep -w default | grep -o 1 | wc -l'"
            self.tvpath = "'cat /sys/class/vfm/map | grep -w tvpath | grep -o 1 | wc -l'"
            self.axis = "'cat /sys/class/video/axis'"
        else:
            self.forceStop = 'am force-stop com.android.tv >nul'
            self.fullscreen = 'am start - n com.android.tv/.MainActivity >nul'
            self.disableRC = '"echo 2 > /sys/class/remote/amremote/protocol"'
            self.enableRC = '"echo 1 > /sys/class/remote/amremote/protocol"'
            self.default = '"cat /sys/class/vfm/map | grep -w default | grep -o 1 | wc -l"'
            self.tvpath = '"cat /sys/class/vfm/map | grep -w tvpath | grep -o 1 | wc -l"'
            self.axis = '"cat /sys/class/video/axis"'
        self.sourceMenu = 'input keyevent 178'
        self.up = 'input keyevent KEYCODE_DPAD_UP'
        self.down = 'input keyevent KEYCODE_DPAD_DOWN'
        self.enter = 'input keyevent KEYCODE_ENTER'
        self.channel_up = 'input keyevent 166'
        self.channel_down = 'input keyevent 167'
        self.default = '"cat /sys/class/vfm/map | grep -w default | grep -o 1 | wc -l"'

    def setUp(self):
        self.root_device()
        logging.info('Initial device...')
        self.shell_command(self.forceStop)
        sleep(2)
        logging.info('Disable RC function')
        self.shell_command(self.disableRC)
        sleep(3)
        axis = self.shell_command(self.axis).strip()
        #print('axis:',axis,type(axis))
        if axis == '180 296 644 556':
            logging.info('Playing in PIP now, switch to full screen')
            self.shell_command(self.fullscreen)
            sleep(8)

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

    def is_dtv_playing(self):
        vfmstatus = self.shell_command(self.default).strip()
        #print('vfmstatus',vfmstatus,type(vfmstatus))
        if vfmstatus == '3':
            logging.info('DTV is playing...')
            return True
        else:
            logging.info('DTV is not playing...')
            return False

    def switch_channel(self, duration):
        if (loop % 2) == 0:
            self.shell_command(self.channel_up)
            logging.info('Press \'Channel +\' and wait for {}s'.format(duration))
            sleep(duration)
        else:
            self.shell_command(self.channel_down)
            logging.info('Press \'Channel -\' and wait for {}s'.format(duration))
            sleep(duration)

    def capture_logs(self, source1, source2, loop):
        # 决定通道切换的起点是哪个通道,如果起始通道和目标通道不一样，则开始正常的进入起始通道先，如果起始通道和目标通道一致，则先检查当前播放的是否是准备选择的通道，如果不是，先切过去
        if source1 == 'atv' and source2 != source1:
            self.test_play_atv(10)
        elif source1 == 'dtv' and source2 != source1:
            self.test_play_dtv(10)
        elif source1 == 'hdmi1' and source2 != source1:
            self.test_play_hdmi1(10)
        elif source1 == 'hdmi2' and source2 != source1:
            self.test_play_hdmi2(10)
        elif source1 == 'hdmi3' and source2 != source1:
            self.test_play_hdmi3(10)
        elif source1 == 'avin' and source2 != source1:
            self.test_play_cvbs(10)
        elif source1 == source2 == 'atv':
            if self.is_dtv_playing():
                self.test_play_atv(10)
        elif source1 == source2 == 'dtv':
            if not self.is_dtv_playing():
                self.test_play_dtv(10)

        currentTime = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
        logPath = 'Script_logs'
        result = 'result.log'
        capCmd = 'logcat -s DroidLogicTvInputService tvserver'  # 抓取过滤后的logcat
        logCmd = '{0} {1} {2} {3}'.format('adb -s', dsn, 'shell', capCmd)

        if os.name == 'posix':
            if not os.path.exists(logPath):
                os.mkdir(logPath)

        group = (currentTime, source1, 'to', source2, str(loop), '.log')  # log命名规则
        file1 = '_'.join(group)
        file2 = os.path.join(os.getcwd(), logPath, file1)   # 保存每一次切换的log到具体文件
        file3 = os.path.join(os.getcwd(), logPath, result)  # 保存测试结果到result.log
        logfile = file2

        self.shell_command('shell logcat -c')

        # 开始抓取logcat并保存到文件中
        with open(logfile, 'a+') as f:
            out = subprocess.Popen(logCmd, shell=True, stdout=f, stderr=subprocess.PIPE)
            logging.info('Capturing log...')

            if source2 == 'atv' and source2 != source1:
                self.test_play_atv(15)
                pattern1 = re.compile(r'doTuneInService')   # doTuneInService doSetSurface'
                pattern2 = re.compile(r'show source on screen') # onSigChange4TVIN_SIG_STATUS_STABLE , show source on screen'
            elif source2 == 'dtv' and source2 != source1:
                self.test_play_dtv(15)
                pattern1 = re.compile(r'doTuneInService')   # doTuneInService doSetSurface'
                pattern2 = re.compile(r'video available ok') # onSigChange4TVIN_SIG_STATUS_STABLE , show source on screen'
            elif source2 == 'hdmi1' and source2 != source1:
                self.test_play_hdmi1(15)
                pattern1 = re.compile(r'doSetSurface')   # doTuneInService doSetSurface'
                pattern2 = re.compile(r'show source on screen') # onSigChange4TVIN_SIG_STATUS_STABLE , show source on screen'
            elif source2 == 'hdmi2' and source2 != source1:
                self.test_play_hdmi2(15)
                pattern1 = re.compile(r'doSetSurface')   # doTuneInService doSetSurface'
                pattern2 = re.compile(r'show source on screen') # onSigChange4TVIN_SIG_STATUS_STABLE , show source on screen'
            elif source2 == 'hdmi3' and source2 != source1:
                self.test_play_hdmi3(15)
                pattern1 = re.compile(r'doSetSurface')   # doTuneInService doSetSurface'
                pattern2 = re.compile(r'show source on screen') # onSigChange4TVIN_SIG_STATUS_STABLE , show source on screen'
            elif source2 == 'avin' and source2 != source1:
                self.test_play_cvbs(15)
                pattern1 = re.compile(r'doSetSurface')   # doTuneInService doSetSurface'
                pattern2 = re.compile(r'show source on screen') # onSigChange4TVIN_SIG_STATUS_STABLE , show source on screen'
            elif source2 == source1 == 'atv':
                self.switch_channel(15)
                pattern1 = re.compile(r'doTuneInService')   # doTuneInService doSetSurface'
                pattern2 = re.compile(r'show source on screen') # onSigChange4TVIN_SIG_STATUS_STABLE , show source on screen'
            elif source2 == source1 == 'dtv':
                self.switch_channel(15)
                pattern1 = re.compile(r'doTuneInService')   # doTuneInService doSetSurface'
                pattern2 = re.compile(r'video available ok') # onSigChange4TVIN_SIG_STATUS_STABLE , show source on screen'

            out.terminate()  # 结束抓取log
            #logging.info('Finish captured!')
            sleep(1)

        startDate = None  # 初始化起始时间为None
        endDate = None  # 初始化结束时间为None
        # 正则匹配log中的关键字来寻找起点和终点的时间
        fp = open(logfile, 'r')  # 打开每一次切换通道后保存的logcat
        while True:
            line = fp.readline()
            if not line:
                break
            match1 = pattern1.search(line)
            match2 = pattern2.search(line)

            if match1:  # 匹配起点时间
                obj1 = line.split(' ')
                startTime = obj1[1]  # 具体起点的时间
                startDate = datetime.datetime.strptime(startTime,'%H:%M:%S.%f') # 将字符串转化为时间格式

            if match2:  # 匹配终点时间
                obj2 = line.split(' ')
                endTime = obj2[1]  # 具体终点的时间
                endDate = datetime.datetime.strptime(endTime,'%H:%M:%S.%f')  # 将字符串转化为时间格式

        # 转化过滤log后的两个时间值，并保存到相应的文件中
        if startDate and endDate:
            distance = endDate - startDate  # 两个时间之间的差值
            if distance != 0:
                distance = float(str(distance)[5:])  # 转换时间差值为浮点数
            logging.info('From {} switch to {}, Cost: < \033[33m{}s\033[0m >'.format(source1, source2, distance))
            with open(file3, 'a+') as s:
                s.write('{}. {} to {}: {}\n'.format(loop, source1, source2, distance))  # 保存每一次切换的数据到result.log
        else:
            logging.info('Data captured is failed')  # 起始时间和结束时间两者任一抓取失败则打印failed！

def exit(signum, frame):
    print('You choose to stop me.')
    device = dsn
    TvSource(device).tearDown()
    sys.exit(1)

if __name__ == '__main__':

    logging_init()
    dsn = select_device()
    TvSource(dsn).setUp()
    loop = 1
    resultfile = os.path.join(os.getcwd(), 'Script_logs', 'result.log')
    if os.path.exists(resultfile):
        os.remove(resultfile)

    signal.signal(signal.SIGINT, exit)
    signal.signal(signal.SIGTERM, exit)

    while True:

        logging.info('{:=<20} {} {:=<20}'.format('', loop, ''))

        try:

            #TvSource(dsn).capture_logs('atv','dtv',loop)
            #TvSource(dsn).capture_logs('atv','avin',loop)
            #TvSource(dsn).capture_logs('atv','hdmi1',loop)
            #TvSource(dsn).capture_logs('atv','hdmi2',loop)
            #TvSource(dsn).capture_logs('atv','hdmi3',loop)
            #TvSource(dsn).capture_logs('dtv','dtv',loop)
            #TvSource(dsn).capture_logs('dtv','atv',loop)
            #TvSource(dsn).capture_logs('dtv','avin',loop)
            #TvSource(dsn).capture_logs('dtv','hdmi1',loop)
            #TvSource(dsn).capture_logs('dtv','hdmi2',loop)
            #TvSource(dsn).capture_logs('dtv','hdmi3',loop)
            #TvSource(dsn).capture_logs('avin','atv',loop)
            #TvSource(dsn).capture_logs('avin','dtv',loop)
            #TvSource(dsn).capture_logs('avin','hdmi2',loop)
            #TvSource(dsn).capture_logs('hdmi1','atv',loop)
            #TvSource(dsn).capture_logs('hdmi1','dtv',loop)
            TvSource(dsn).capture_logs('hdmi1','hdmi2',loop)
            # TvSource(dsn).capture_logs('hdmi1','hdmi3',loop)
            # TvSource(dsn).capture_logs('hdmi2','atv',loop)
            #TvSource(dsn).capture_logs('hdmi2','dtv',loop)
            #TvSource(dsn).capture_logs('hdmi2','avin',loop)
            TvSource(dsn).capture_logs('hdmi2','hdmi1',loop)
            #TvSource(dsn).capture_logs('hdmi2','hdmi3',loop)
            #TvSource(dsn).capture_logs('hdmi3','atv',loop)
            #TvSource(dsn).capture_logs('hdmi3','dtv',loop)
            #TvSource(dsn).capture_logs('hdmi3','hdmi1',loop)
            #TvSource(dsn).capture_logs('hdmi3','hdmi2',loop)

        except Exception as err:
            print(err)
        finally:
            loop += 1
