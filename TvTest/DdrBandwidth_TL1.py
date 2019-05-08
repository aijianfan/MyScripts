# -*- coding: utf-8 -*-

import os, sys, re, signal, subprocess, logging
from collections import OrderedDict, Counter
from beautifultable import BeautifulTable
from datetime import datetime
from itertools import islice
from time import sleep
from tqdm import tqdm

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
            self.enable_ddr_mode = "'echo 1 > /sys/class/aml_ddr/mode'"
            self.forceStop_livetv = 'am force-stop com.android.tv >/dev/null 2>&1'
            self.disableRC = "'echo 2 > /sys/class/remote/amremote/protocol'"
            self.enableRC = "'echo 1 > /sys/class/remote/amremote/protocol'"
            self.disable_printk = "'echo 0 > /proc/sys/kernel/printk'"
            self.underflow = "'cat /sys/module/amvideo/parameters/underflow'"
            self.enable_od = "'echo od 1 > /sys/class/lcd/tcon'"
            self.disable_od = "'echo od 0 > /sys/class/lcd/tcon'"
            self.bandwidth = "'cat /sys/class/aml_ddr/bandwidth'"
            self.ports_name = "'cat /sys/class/aml_ddr/name_of_ports'"
            self.read_value = "'cat /sys/class/aml_ddr/bandwidth' | tail -4 | awk -F ' ' '{print $5}'"
            self.read_total = "'cat /sys/class/aml_ddr/bandwidth' | head -n 1 | awk -F ' ' '{print $3}'"
            self.read_usage = "'cat /sys/class/aml_ddr/bandwidth' | head -n 1 | awk -F ' ' '{print $6}'"
        else:
            self.enable_ddr_mode = '"echo 1 > /sys/class/aml_ddr/mode"'
            self.forceStop_livetv = 'am force-stop com.android.tv >nul'
            self.disableRC = '"echo 2 > /sys/class/remote/amremote/protocol"'
            self.enableRC = '"echo 1 > /sys/class/remote/amremote/protocol"'
            self.disable_printk = '"echo 0 > /proc/sys/kernel/printk"'
            self.underflow = '"cat /sys/module/amvideo/parameters/underflow"'
            self.enable_od = '"echo od 1 > /sys/class/lcd/tcon"'
            self.disable_od = '"echo od 0 > /sys/class/lcd/tcon"'
            self.bandwidth = '"cat /sys/class/aml_ddr/bandwidth"'
            self.name_ports = '"cat /sys/class/aml_ddr/name_of_ports"'
        self.home = 'input keyevent KEYCODE_HOME'
        logPath = 'Script_logs'
        dataPath = os.path.join(os.getcwd(),logPath)
        if not os.path.exists(dataPath):
            os.mkdir(dataPath)
        currentTime = datetime.now().strftime('%Y%m%d_%H%M%S')
        split_text = ('bd_result_', currentTime, '.log')
        logResult = ''.join(split_text)
        self.logFile = os.path.join(os.getcwd(),logPath,logResult)

    def setUp(self):
        self.root_device()
        logging.info('Initial device...')
        #self.shell_command(self.forceStop_livetv)
        #self.shell_command(self.home)
        sleep(2)
        self.root_device()
        logging.info('Disable RC function')
        self.shell_command(self.disableRC)
        self.initial_ddr_mode()

    def tearDown(self):
        logging.info('Terminate Testing')
        logging.info('Recover RC function')
        self.clear_ports()
        self.shell_command(self.enableRC)
        #self.shell_command(self.home)

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

    def initial_ddr_mode(self):
        return self.shell_command(self.enable_ddr_mode)

    def clear_ports(self): # 将ports清零
        for i in range(4):
            if os.name == 'posix':
                initial = "'echo {}:-1 > /sys/class/aml_ddr/port'".format(i)
            else:
                initial = '"echo {}:-1 > /sys/class/aml_ddr/port"'.format(i)
            self.shell_command(initial)

    def check_after_clear(self):  # 检查4个ports的状态是否已clear
        self.clear_ports()
        output = self.shell_command(self.bandwidth)
        out = output.strip().split(' ')
        out = [i.strip() for i in out if i != '']
        if out.count('0:') == 4:
            # logging.info('ports have already cleared.')
            pass
        else:
            logging.info('ports have not cleared yet, please check!')

    def available_ports(self):  # 查询可以实际读到的ports信息
        output = self.shell_command(self.ports_name)
        out = output.strip().split('\n')
        group = []
        name_of_ports = {}
        for i in out:
            items = i.split(',')
            for j in items:
                j = j.strip()
                group.append(j)
        port_key = group[1::2]
        port_value = group[::2]
        if len(port_key) == len(port_value):
            for key, value in zip(port_key, port_value):
                value = int(value)
                name_of_ports[value] = key
            name_of_ports = OrderedDict(sorted(name_of_ports.items(), key=lambda name_of_ports:name_of_ports[0]))
            for k, v in name_of_ports.items():
                name_of_ports[k] = v
        return name_of_ports

    def package_commands(self, keys = [], values = []):  # 封装全部ports赋值后的命令
        ports = self.available_ports()
        for key, value in ports.items():
            keys.append(key)
            values.append(value)
        ports_range = [ i for i in range(4) ]
        commands_group = []
        if len(keys) == len(values):
            for i in range(len(keys)):
                if i < 4:
                    command = "'echo {}:{} > /sys/class/aml_ddr/port'".format(ports_range[i], keys[i])
                elif i >=4 and i < 8:
                    command = "'echo {}:{} > /sys/class/aml_ddr/port'".format(ports_range[i-4], keys[i])
                elif i >= 8 and i < 12:
                    command = "'echo {}:{} > /sys/class/aml_ddr/port'".format(ports_range[i-8], keys[i])
                elif i >= 12 and i < 16:
                    command = "'echo {}:{} > /sys/class/aml_ddr/port'".format(ports_range[i-12], keys[i])
                elif i >=16 and i < 20:
                    command = "'echo {}:{} > /sys/class/aml_ddr/port'".format(ports_range[i-16], keys[i])
                elif i >= 20 and i < 24:
                    command = "'echo {}:{} > /sys/class/aml_ddr/port'".format(ports_range[i-20], keys[i])
                elif i >= 24 and i < 28:
                    command = "'echo {}:{} > /sys/class/aml_ddr/port'".format(ports_range[i-24], keys[i])
                elif i >= 28 and i < 32:
                    command = "'echo {}:{} > /sys/class/aml_ddr/port'".format(ports_range[i-28], keys[i])
                elif i >= 32 and i < 36:
                    command = "'echo {}:{} > /sys/class/aml_ddr/port'".format(ports_range[i-32], keys[i])
                commands_group.append(command)
        return commands_group

    def sequence_execute(self):  #
        interval = 5
        ports_dict = self.available_ports()
        com = self.package_commands()
        commands = [ com[i:i+4] for i in range(0, len(com), 4) ]
        vars = []
        logging.info('pre-test to confirm the used ports information!')
        for a in tqdm(range(interval), desc='Pre-testing'):
            for i in range(len(commands)):
                self.check_after_clear()
                for k in range(len(commands[i])):
                    #print(commands[i][k])
                    self.shell_command(commands[i][k])
                values = self.shell_command(self.read_value).split('\n')
                values = [ int(n.strip()) for n in values if n != '' ]
                if i == 7:
                    values = values[:-1]
                vars.extend(values)

        end = len(com)
        for i in range(interval):
            if i == 0:
                exec 'subvars{} = vars[:{}]'.format(i,end)
            else:
                exec 'subvars{} = vars[{}:{}]'.format(i,end*i,end*(i+1))

        dict1, dict2, dict3, dict4, dict5 = {}, {}, {}, {}, {}

        if isinstance(subvars0, list):
            for item, value in enumerate(subvars0):
                if value > 20480:
                    dict1[ports_dict.keys()[item]] = value
        if isinstance(subvars1, list):
            for item, value in enumerate(subvars1):
                if value > 20480:
                    dict2[ports_dict.keys()[item]] = value
        if isinstance(subvars2, list):
            for item, value in enumerate(subvars2):
                if value > 20480:
                    dict3[ports_dict.keys()[item]] = value
        if isinstance(subvars3, list):
            for item, value in enumerate(subvars3):
                if value > 20480:
                    dict4[ports_dict.keys()[item]] = value
        if isinstance(subvars4, list):
            for item, value in enumerate(subvars4):
                if value > 20480:
                    dict5[ports_dict.keys()[item]] = value

        dict6 = dict1.items() + dict2.items() + dict3.items() + dict4.items() + dict5.items()
        count = []
        for item in dict6:
            count.append(item[0])
        calc = Counter(count)  # 当前场景下所使用的ports编号的集合
        logging.info('total available ports: {}'.format(calc))
        sleep(1)
        for item in list(calc.keys()):
            if calc[item] < 2:
                del calc[item]
        self.calc_result = sorted(calc) # 当前场景下所使用的ports字典排序
        logging.info('confirmed ports index under current scene: {}'.format(self.calc_result))
        sleep(1)

        self.ports_name = []
        for port in self.calc_result:
            self.ports_name.append(ports_dict[port])
        logging.info('confirmed ports name under current scene: {}'.format(self.ports_name))
        sleep(1)

        return self.calc_result, self.ports_name  # 返回过滤后的port编号、port名称

    def confirm_ports(self):
        ports_index, ports_name = self.sequence_execute()  # 接收过滤后的ports编号和名称
        ports = OrderedDict(zip(ports_index, ports_name))
        ports_range = [i for i in range(4)]
        command_group = []

        if len(ports) <= 4:
            ''' 如果当前测试场景所使用的ports数量<=4 '''
            regroup = OrderedDict(zip(ports_range, ports.keys()))
            for k, v in regroup.items():
                command = "'echo {}:{} > /sys/class/aml_ddr/port'".format(k, v)
                self.shell_command(command)
                command_group.append(command)
            return command_group

        else:
            ''' 如果当前测试场景所使用的ports数量>4 '''
            for i in range(len(ports)):
                if i < 4:
                    command = "'echo {}:{} > /sys/class/aml_ddr/port'".format(ports_range[i], ports_index[i])
                elif i >=4 and i < 8:
                    command = "'echo {}:{} > /sys/class/aml_ddr/port'".format(ports_range[i-4], ports_index[i])
                elif i >=8 and i < 12:
                    command = "'echo {}:{} > /sys/class/aml_ddr/port'".format(ports_range[i-8], ports_index[i])
                command_group.append(command)
            return command_group

    def execute_and_capture(self, duration):
        commands_handle = self.confirm_ports()
        logfile = self.logFile
        read_bd = 'adb -s {} shell {}'.format(dsn, self.bandwidth)

        if len(commands_handle) <= 4:
            ''' 循环一段时间，反复读取bandwidth结果，并保存到/Script_logs目录 '''
            logging.info('capture log...')
            for i in tqdm(range(duration), desc='Process'):  # 抓取60s的带宽数据，呈进度条显示
                with open(logfile, 'a+') as f:
                    out = subprocess.Popen(read_bd, shell=True, stdout=f)
                    sleep(1)
        else:
            ''' 循环一段时间，反复读取bandwidth结果，并保存到/Script_logs目录 '''
            commands = [ commands_handle[i:i+4] for i in range(0, len(commands_handle), 4) ]  #将命令分成4个一组的子列表
            for a in range(len(commands)):
                self.check_after_clear()
                for b in range(len(commands[a])):
                    self.shell_command(commands[a][b])
                logging.info('capture log...count: {}'.format(a+1))
                for i in tqdm(range(duration), desc='Process'):  # 抓取60s的带宽数据，呈进度条显示
                    with open(logfile, 'a+') as f:
                        out = subprocess.Popen(read_bd, shell=True, stdout=f)
                        sleep(1)
        return logfile

    def filter_data(self):

        ''' 筛选数出关键值添加到列表，并返回 '''

        file = self.execute_and_capture(60)
        Total, Usage, Port0, Port1, Port2, Port3 = [], [], [], [], [], []
        ports_index, ports_name = self.calc_result, self.ports_name
        logging.info('start deal with the test result')
        sleep(1)

        if len(ports_index) <= 4:
            fp = open(file, 'r')
            while True:
                line = fp.readline()
                if not line:
                    break
                pattern_total = re.compile(r'Total')
                match_total = pattern_total.search(line)
                if match_total:
                    filter_total = ['Total', 'bandwidth:', 'KB/s,', 'usage:', '']
                    bandwidth = [i.strip() for i in line.split(' ') if i not in filter_total][0]
                    usage = [i.strip() for i in line.split(' ') if i not in filter_total][1][:-1]
                    Total.append(bandwidth)
                    Usage.append(usage)
                pattern_port0 = re.compile(r'ch:0')
                match_port0 = pattern_port0.search(line)
                if match_port0:
                    filter_port0 = ['ch:0', 'port', 'bit:', '', 'KB/s']
                    port0 = [i for i in line.split(' ') if i not in filter_port0][1]
                    Port0.append(port0)
                pattern_port1 = re.compile(r'ch:1')
                match_port1 = pattern_port1.search(line)
                if match_port1:
                    filter_port1 = ['ch:1', 'port', 'bit:', '', 'KB/s']
                    port1 = [i for i in line.split(' ') if i not in filter_port1][1]
                    Port1.append(port1)
                pattern_port2 = re.compile(r'ch:2')
                match_port2 = pattern_port2.search(line)
                if match_port2:
                    filter_port2 = ['ch:2', 'port', 'bit:', '', 'KB/s']
                    port2 = [i for i in line.split(' ') if i not in filter_port2][1]
                    Port2.append(port2)
                pattern_port3 = re.compile(r'ch:3')
                match_port3 = pattern_port3.search(line)
                if match_port3:
                    filter_port3 = ['ch:3', 'port', 'bit:', '', 'KB/s']
                    port3 = [i for i in line.split(' ') if i not in filter_port3][1]
                    Port3.append(port3)

            return Total, Usage, Port0, Port1, Port2, Port3

        elif len(ports_index) > 4 and len(ports_index) <= 8:
            part1, part2 = [],[]
            Port00, Port11, Port22, Port33 = [], [], [], []

            try:
                fp = open(file, 'r')

                for l in islice(fp, 0, 300):
                    part1.append(l)

                fp = open(file, 'r')
                for k in islice(fp, 301, 999):
                    part2.append(k)
            finally:
                fp.close()

            # print('part1',part1,len(part1))
            # print('='*50)
            # print('part2',part2,len(part2))

            for line in part1:
                pattern_total = re.compile(r'Total')
                match_total = pattern_total.search(line)
                if match_total:
                    filter_total = ['Total', 'bandwidth:', 'KB/s,', 'usage:', '']
                    bandwidth = [i.strip() for i in line.split(' ') if i not in filter_total][0]
                    usage = [i.strip() for i in line.split(' ') if i not in filter_total][1][:-1]
                    Total.append(bandwidth)
                    Usage.append(usage)
                pattern_port0 = re.compile(r'ch:0')
                match_port0 = pattern_port0.search(line)
                if match_port0:
                    filter_port0 = ['ch:0', 'port', 'bit:', '', 'KB/s']
                    port0 = [i for i in line.split(' ') if i not in filter_port0][1]
                    if port0 != '0':
                        Port0.append(port0)
                pattern_port1 = re.compile(r'ch:1')
                match_port1 = pattern_port1.search(line)
                if match_port1:
                    filter_port1 = ['ch:1', 'port', 'bit:', '', 'KB/s']
                    port1 = [i for i in line.split(' ') if i not in filter_port1][1]
                    if port1 != '0':
                        Port1.append(port1)
                pattern_port2 = re.compile(r'ch:2')
                match_port2 = pattern_port2.search(line)
                if match_port2:
                    filter_port2 = ['ch:2', 'port', 'bit:', '', 'KB/s']
                    port2 = [i for i in line.split(' ') if i not in filter_port2][1]
                    if port2 != '0':
                        Port2.append(port2)
                pattern_port3 = re.compile(r'ch:3')
                match_port3 = pattern_port3.search(line)
                if match_port3:
                    filter_port3 = ['ch:3', 'port', 'bit:', '', 'KB/s']
                    port3 = [i for i in line.split(' ') if i not in filter_port3][1]
                    if port3 != '0':
                        Port3.append(port3)

            for line in part2:
                pattern_port0 = re.compile(r'ch:0')
                match_port0 = pattern_port0.search(line)
                if match_port0:
                    filter_port0 = ['ch:0', 'port', 'bit:', '', 'KB/s']
                    port0 = [i for i in line.split(' ') if i not in filter_port0][1]
                    if port0 != '0':
                        Port00.append(port0)
                pattern_port1 = re.compile(r'ch:1')
                match_port1 = pattern_port1.search(line)
                if match_port1:
                    filter_port1 = ['ch:1', 'port', 'bit:', '', 'KB/s']
                    port1 = [i for i in line.split(' ') if i not in filter_port1][1]
                    if port1 != '0':
                        Port11.append(port1)
                pattern_port2 = re.compile(r'ch:2')
                match_port2 = pattern_port2.search(line)
                if match_port2:
                    filter_port2 = ['ch:2', 'port', 'bit:', '', 'KB/s']
                    port2 = [i for i in line.split(' ') if i not in filter_port2][1]
                    if port2 != '0':
                        Port22.append(port2)
                pattern_port3 = re.compile(r'ch:3')
                match_port3 = pattern_port3.search(line)
                if match_port3:
                    filter_port3 = ['ch:3', 'port', 'bit:', '', 'KB/s']
                    port3 = [i for i in line.split(' ') if i not in filter_port3][1]
                    if port3 != '0':
                        Port33.append(port3)

            return Total, Usage, Port0, Port1, Port2, Port3, Port00, Port11, Port22, Port33

    def handle_data(self):
        recev = self.filter_data()
        logging.info('finished')
        sleep(1)

        if len(recev) == 6:
            tl, us, p0, p1, p2, p3 = recev
            tl = [int(i) for i in tl if isinstance(i, str) and '.' not in i]
            us = [float(i) for i in us if isinstance(i, str) and '.' in i]
            p0 = [int(i) for i in p0 if isinstance(i, str) and '.' not in i]
            p1 = [int(i) for i in p1 if isinstance(i, str) and '.' not in i]
            p2 = [int(i) for i in p2 if isinstance(i, str) and '.' not in i]
            p3 = [int(i) for i in p3 if isinstance(i, str) and '.' not in i]
            result = (self.calculate(tl),self.calculate(us),self.calculate(p0),
                      self.calculate(p1),self.calculate(p2),self.calculate(p3))

        elif len(recev) == 10:
            tl, us, p0, p1, p2, p3, p4, p5, p6, p7 = recev
            tl = [int(i) for i in tl if isinstance(i, str) and '.' not in i]
            us = [float(i) for i in us if isinstance(i, str) and '.' in i]
            p0 = [int(i) for i in p0 if isinstance(i, str) and '.' not in i]
            p1 = [int(i) for i in p1 if isinstance(i, str) and '.' not in i]
            p2 = [int(i) for i in p2 if isinstance(i, str) and '.' not in i]
            p3 = [int(i) for i in p3 if isinstance(i, str) and '.' not in i]
            p4 = [int(i) for i in p4 if isinstance(i, str) and '.' not in i]
            p5 = [int(i) for i in p5 if isinstance(i, str) and '.' not in i]
            p6 = [int(i) for i in p6 if isinstance(i, str) and '.' not in i]
            p7 = [int(i) for i in p7 if isinstance(i, str) and '.' not in i]
            result = (self.calculate(tl),self.calculate(us),self.calculate(p0),
                      self.calculate(p1),self.calculate(p2),self.calculate(p3),
                      self.calculate(p4),self.calculate(p5),self.calculate(p6),
                      self.calculate(p7))

        return result

    def output2screen(self):
        final = self.handle_data()
        ports_index, ports_name = self.calc_result, self.ports_name
        file_name = os.path.basename(self.logFile)
        table = BeautifulTable()
        table.column_headers = ["Item", "Unit", "Max", "Min", "Avg"]

        if len(final) == 6 and len(ports_index) <= 4:
            if len(ports_index) == 2:
                final = final[:4]
                table.append_row(["Total BW", "KB/s", final[0][0], final[0][1], final[0][2]])
                table.append_row(["Usage", "%", final[1][0], final[1][1], final[1][2]])
                table.append_row(['{},{}'.format(ports_index[0], ports_name[0]), "KB/s", final[2][0], final[2][1], final[2][2]])
                table.append_row(['{},{}'.format(ports_index[1], ports_name[1]), "KB/s", final[3][0], final[3][1], final[3][2]])
            if len(ports_index) == 3:
                final = final[:5]
                table.append_row(["Total BW", "KB/s", final[0][0], final[0][1], final[0][2]])
                table.append_row(["Usage", "%", final[1][0], final[1][1], final[1][2]])
                table.append_row(['{},{}'.format(ports_index[0], ports_name[0]), "KB/s", final[2][0], final[2][1], final[2][2]])
                table.append_row(['{},{}'.format(ports_index[1], ports_name[1]), "KB/s", final[3][0], final[3][1], final[3][2]])
                table.append_row(['{},{}'.format(ports_index[2], ports_name[2]), "KB/s", final[4][0], final[4][1], final[4][2]])
            if len(ports_index) == 4:
                table.append_row(["Total BW", "KB/s", final[0][0], final[0][1], final[0][2]])
                table.append_row(["Usage", "%", final[1][0], final[1][1], final[1][2]])
                table.append_row(['{},{}'.format(ports_index[0], ports_name[0]), "KB/s", final[2][0], final[2][1], final[2][2]])
                table.append_row(['{},{}'.format(ports_index[1], ports_name[1]), "KB/s", final[3][0], final[3][1], final[3][2]])
                table.append_row(['{},{}'.format(ports_index[2], ports_name[2]), "KB/s", final[4][0], final[4][1], final[4][2]])
                table.append_row(['{},{}'.format(ports_index[3], ports_name[3]), "KB/s", final[5][0], final[5][1], final[5][2]])

        elif len(final) == 10 and len(ports_index) <= 8:
            if len(ports_index) == 5:
                final = final[:7]
                table.append_row(["Total BW", "KB/s", final[0][0], final[0][1], final[0][2]])
                table.append_row(["Usage", "%", final[1][0], final[1][1], final[1][2]])
                table.append_row(['{},{}'.format(ports_index[0], ports_name[0]), "KB/s", final[2][0], final[2][1], final[2][2]])
                table.append_row(['{},{}'.format(ports_index[1], ports_name[1]), "KB/s", final[3][0], final[3][1], final[3][2]])
                table.append_row(['{},{}'.format(ports_index[2], ports_name[2]), "KB/s", final[4][0], final[4][1], final[4][2]])
                table.append_row(['{},{}'.format(ports_index[3], ports_name[3]), "KB/s", final[5][0], final[5][1], final[5][2]])
                table.append_row(['{},{}'.format(ports_index[4], ports_name[4]), "KB/s", final[6][0], final[6][1], final[6][2]])
            if len(ports_index) == 6:
                final = final[:8]
                table.append_row(["Total BW", "KB/s", final[0][0], final[0][1], final[0][2]])
                table.append_row(["Usage", "%", final[1][0], final[1][1], final[1][2]])
                table.append_row(['{},{}'.format(ports_index[0], ports_name[0]), "KB/s", final[2][0], final[2][1], final[2][2]])
                table.append_row(['{},{}'.format(ports_index[1], ports_name[1]), "KB/s", final[3][0], final[3][1], final[3][2]])
                table.append_row(['{},{}'.format(ports_index[2], ports_name[2]), "KB/s", final[4][0], final[4][1], final[4][2]])
                table.append_row(['{},{}'.format(ports_index[3], ports_name[3]), "KB/s", final[5][0], final[5][1], final[5][2]])
                table.append_row(['{},{}'.format(ports_index[4], ports_name[4]), "KB/s", final[6][0], final[6][1], final[6][2]])
                table.append_row(['{},{}'.format(ports_index[5], ports_name[5]), "KB/s", final[7][0], final[7][1], final[7][2]])
            if len(ports_index) == 7:
                final = final[:9]
                table.append_row(["Total BW", "KB/s", final[0][0], final[0][1], final[0][2]])
                table.append_row(["Usage", "%", final[1][0], final[1][1], final[1][2]])
                table.append_row(['{},{}'.format(ports_index[0], ports_name[0]), "KB/s", final[2][0], final[2][1], final[2][2]])
                table.append_row(['{},{}'.format(ports_index[1], ports_name[1]), "KB/s", final[3][0], final[3][1], final[3][2]])
                table.append_row(['{},{}'.format(ports_index[2], ports_name[2]), "KB/s", final[4][0], final[4][1], final[4][2]])
                table.append_row(['{},{}'.format(ports_index[3], ports_name[3]), "KB/s", final[5][0], final[5][1], final[5][2]])
                table.append_row(['{},{}'.format(ports_index[4], ports_name[4]), "KB/s", final[6][0], final[6][1], final[6][2]])
                table.append_row(['{},{}'.format(ports_index[5], ports_name[5]), "KB/s", final[7][0], final[7][1], final[7][2]])
                table.append_row(['{},{}'.format(ports_index[6], ports_name[6]), "KB/s", final[8][0], final[8][1], final[8][2]])
            if len(ports_index) == 8:
                table.append_row(["Total BW", "KB/s", final[0][0], final[0][1], final[0][2]])
                table.append_row(["Usage", "%", final[1][0], final[1][1], final[1][2]])
                table.append_row(['{},{}'.format(ports_index[0], ports_name[0]), "KB/s", final[2][0], final[2][1], final[2][2]])
                table.append_row(['{},{}'.format(ports_index[1], ports_name[1]), "KB/s", final[3][0], final[3][1], final[3][2]])
                table.append_row(['{},{}'.format(ports_index[2], ports_name[2]), "KB/s", final[4][0], final[4][1], final[4][2]])
                table.append_row(['{},{}'.format(ports_index[3], ports_name[3]), "KB/s", final[5][0], final[5][1], final[5][2]])
                table.append_row(['{},{}'.format(ports_index[4], ports_name[4]), "KB/s", final[6][0], final[6][1], final[6][2]])
                table.append_row(['{},{}'.format(ports_index[5], ports_name[5]), "KB/s", final[7][0], final[7][1], final[7][2]])
                table.append_row(['{},{}'.format(ports_index[6], ports_name[6]), "KB/s", final[8][0], final[8][1], final[8][2]])
                table.append_row(['{},{}'.format(ports_index[7], ports_name[7]), "KB/s", final[9][0], final[9][1], final[9][2]])

        logging.info('log was saved to file << {} >>.'.format(file_name))
        sleep(1)
        print(table)

    def calculate(self, target):
        length = len(target)
        flag = []
        if sum(target) == 0:
            return 0, 0, 0
        else:
            for i in range(length):
                if target[i] == 0:
                    flag.append(target[i])
            tar = [i for i in target if i not in flag]
            length = length - len(flag)
            maximum = max(tar)
            minimum = min(tar)
            for i in tar:
                if isinstance(i, float):
                    average = float('%.2f' % (sum(tar) / length))
                else:
                    average = sum(tar) / length
            return maximum, minimum, average

def exit(signum, frame):
    print('You choose to stop me.')
    device = dsn
    Tv(device).tearDown()
    sys.exit(1)

def main():
    Tv(dsn).output2screen()

if __name__ == '__main__':
    logging_init()
    dsn = select_device()
    Tv(dsn).setUp()
    signal.signal(signal.SIGINT, exit)
    signal.signal(signal.SIGTERM, exit)

    main()

    Tv(dsn).tearDown()