import logging
import logging.handlers
import sys
import os
import time
from core import config


# 重写log的msg打印
from logging import LogRecord


def getMessage(self):
    """
    Return the message for this LogRecord.

    Return the message for this LogRecord after merging any user-supplied
    arguments with the message.
    """
    # print('getMessage')
    msg = str(self.msg)
    if self.args:
        msg += ', ' + ', '.join([str(x) for x in self.args])
    # print('getMessage msg', msg)
    return msg


setattr(LogRecord, 'getMessage', getMessage)


import traceback
import io
from logging import _srcfile


class _Formatter(logging.Formatter):
    """自定义Formatter
    :增加属性
        :caller_file_path:调用者文件路径
        :caller_file_name:调用者文件名
        :caller_line_number:调用者行号
    """

    def find_caller(self, stack_info=False):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        if hasattr(sys, '_getframe'):
            def currentframe(): return sys._getframe(9)
        else:  # pragma: no cover
            def currentframe():
                """Return the frame object for the caller's stack frame."""
                try:
                    raise Exception
                except Exception:
                    return sys.exc_info()[2].tb_frame.f_back.f_back.f_back.f_back.f_back.f_back.f_back.f_back.f_back.f_back
        f = currentframe()
        # On some versions of IronPython, currentframe() returns None if
        # IronPython isn't run with -X:Frames.
        if f is not None:
            f = f.f_back
        rv = "(unknown file)", 0
        while hasattr(f, "f_code"):
            co = f.f_code
            caller_file_path = os.path.normcase(f.f_code.co_filename)
            if caller_file_path == _srcfile:
                f = f.f_back
                continue
            sinfo = None
            if stack_info:
                sio = io.StringIO()
                sio.write('Stack (most recent call last):\n')
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == '\n':
                    sinfo = sinfo[:-1]
                sio.close()
            rv = (caller_file_path, os.path.split(
                caller_file_path)[-1], f.f_lineno)
            break
        return rv

    def format(self, record):
        """增加属性
            :caller_file_path:调用者文件路径
            :caller_file_name:调用者文件名
            :caller_line_number:调用者行号
        """
        # record.call_file_name = os.path.split(sys.argv[0])[-1]
        caller = self.find_caller()
        # print('caller', caller)
        # print('-----' * 20)
        record.caller_file_path, record.caller_file_name, record.caller_line_number = caller
        return super(_Formatter, self).format(record)


class Log(object):
    '''
    Logger类(单例模式)
    '''
    # 类实例
    __instance = None

    # 日志级别映射
    __level_mapping = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }

    __level_list = list(__level_mapping.keys())

    def __new__(cls, *args, **kwargs):
        '''
        单例模式
        '''
        if not cls.__instance:
            # print('cls', cls)
            cls.__instance = object.__new__(cls)
            # print('cls.__instance', cls.__instance)
        return cls.__instance

    def __init__(
            self,
            username=None,
            logs_dir=None,
            level='info',
            when='D',
            backupCount=10,
            fmt=None,
            stream=False):
        self.username = username  # 获取用户

        # 校验level
        if not type(level) == str:
            raise TypeError(
                "level expected type is str but get type {}".format(
                    type(level).__name__))
        elif not level in self.__level_list:
            raise NameError(
                "check level at least one corrected logLevel in: {}".format(
                    self.__level_list))
        else:
            self.level = level

        # 生成logs_dir
        if logs_dir:
            self.logs_dir = os.path.join(logs_dir, 'logs', self.level)
        else:
            # self.logs_dir = sys.argv[0][0:-3] + '.log'  # 动态获取调用文件的名字
            # print('logs_dir', self.logs_dir)
            pardir = os.path.abspath(os.path.join(
                os.path.dirname("__file__"), os.path.pardir))
            self.logs_dir = os.path.join(pardir, "logs", self.level)
        # print('logs_dir', self.logs_dir)

        # 创建logger
        self.logger = logging.getLogger(self.username or logging.__name__)
        # self.logger = logging.getLogger()

        # 为logger设置level
        self.logger.setLevel(self.__level_mapping.get(self.level))

        # 关闭logger向上级传输
        self.logger.propagate = False

        # 设置日志格式
        self.fmt = fmt or '%(asctime)-12s %(name)s %(filename)s[%(lineno)d] %(levelname)-8s %(message)-12s'
        self.formatter = _Formatter(self.fmt)

        # 输出到日志文件内
        # 普通文件输出
        # self.file = logging.FileHandler(self.logs_dir, encoding='utf-8')
        # 可按日志文件大小进行文件输出
        self.file = logging.handlers.RotatingFileHandler(
            filename=self.get_log_path(),
            mode='a',
            maxBytes=1000 * 100,
            backupCount=5,
            encoding="utf-8",
            delay=False
        )
        self.file.setFormatter(self.formatter)
        self.file.setLevel(self.__level_mapping.get(self.level))
        self.logger.addHandler(self.file)

        # 日志显示到屏幕上
        if stream:
            self.stream = logging.StreamHandler()
            self.stream.setFormatter(_Formatter(
                '<%(levelname)s> %(caller_file_name)s[%(caller_line_number)d][%(lineno)s] %(message)-12s'))
            self.stream.setLevel(self.__level_mapping.get(self.level))
            self.logger.addHandler(self.stream)

    def get_log_path(self, logs_dir=None):
        """
        创建log日志文件文件名，以当前日期进行命名
        :param logs_dir: 保存log日志文件的文件夹路径
        :return: 拼接好的log文件名。格式：path_to/logs/level/20200202.log
        """
        # 创建文件目录
        if os.path.exists(self.logs_dir) and os.path.isdir(self.logs_dir):
            pass
        else:
            try:
                os.mkdir(self.logs_dir)
            except Exception as e:
                os.makedirs(self.logs_dir)

        # 修改log保存位置
        timestamp = time.strftime("%Y%m%d", time.localtime())
        log_name = '%s.log' % timestamp
        log_path = os.path.join(self.logs_dir, log_name)
        return log_path

    def __getattr__(self, attr):
        # 简化调用logger层级(将level映射为方法): log.logger.info(msg) > log.info(msg)
        # print('__getattr__', attr)
        if attr in self.__level_list or attr == 'exception':
            # print('__getattr__ if', attr)
            return getattr(self.logger, attr)
        # print('__getattr__ else', attr)
        raise AttributeError(
            '{0} object has no attribute {1}'.format(self.__class__.__name__, attr))

    def __call__(self, msg):
        '''
        进一步简化调用logger的字符数量:
        log.info(msg) > log(msg)
        '''
        return getattr(self, self.level)(msg)


# log = Log(username='nut')
# log = Log(stream=True,)
# log.info('config.BASE_DIR')
# log = Log(level="info")
# log = Log(level="error")
# log = Log(level="critical", stream=True)
# log.info('config.BASE_DIR', dir(config))
log = Log(stream=True, logs_dir=config.BASE_DIR)
# log = Log(level="debug", stream=True, logs_dir=config.BASE_DIR)
# log = Log(level="error", stream=True, logs_dir=config.BASE_DIR)
# log = Log(level="debug", stream=True)
# log = Log()


if __name__ == '__main__':

    # print(callable(log),dir(log))
    # log.__call__(u"log.__call__")
    log("log()")
    # log.debug(u"I'm debug 中文测试")
    # log.info(u"I'm info 中文测试")
    # log.warning(u"I'm warn 中文测试")
    # log.error(u"I'm error 中文测试")
    # log.critical(u"I'm critical 中文测试")
    # log.exception("I'm debug 中文测试")

    # while True:
    #     # log.logger.debug('233')
    #     # log.logger.info('233')
    #     # log.logger.warning('233')
    #     # log.logger.error('233')
    #     # log.logger.critical('233')
    #     try:
    #         # 以只读的方式打开一个文件，向文件中写入数据，会报错
    #         # log日志信息：2020-04-01 10:28:38,214 - [line:124] - ERROR: not writable
    #         fh = open("not_exist.txt", "r")
    #         fh.write("这是一个测试文件，用于测试异常!!")
    #     except IOError as e:
    #         print(e.__repr__())
    #         # log.logger.info(e)
    #         # log.logger.error(e.__repr__())
    #         log.logger.exception(e)
    #     time.sleep(3)