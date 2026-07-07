#encoding=utf-8
import os
import sys
import time
import logging
import logging.handlers
import smtplib
from email.mime.text import MIMEText



# Check if log exists, creat if not

# LOG_FILE_PATH = "log/log.log"

# if hasattr(sys,"_MEIPASS"):
# 	filebasepath = sys._MEIPASS
# else:
# 	filebasepath = os.path.abspath(".")


# LOG_FILE_PATH = filebasepath + '\\log.log'
# dir = os.path.dirname(LOG_FILE_PATH)
# if not os.path.exists(dir):
# 	os.makedirs(dir)

# write log level, recommand to use debug for detailed information logging
#FILE_LOG_LEVEL = "DEBUG"
FILE_LOG_LEVEL = "INFO"

# console log level 
#CONSOLE_LOG_LEVEL = "DEBUG"
CONSOLE_LOG_LEVEL = "INFO"

# memory log level, error or critical
MEMOEY_LOG_LEVEL = "ERROR"

# fatal fault log level  
URGENT_LOG_LEVEL = "CRITICAL"

# message after error buffer overflow
ERROR_THRESHOLD_ACHEIVED_MAIL_SUBJECT = "Too many errors occurred during the execution"

# error buffer overflow threshold
ERROR_MESSAGE_THRESHOLD = 50

# fatal fault message
CRITICAL_ERROR_ACHEIVED_MAIL_SUBJECT="Fatal error occurred"

# mail server setting
MAIL_HOST = "your exchange server"
FROM = "from"
MAIL_TO = ["xxxxxxxx@gofoton.cn","xxxxxxxx@qq.com"]

class OptmizedMemoryHandler(logging.handlers.MemoryHandler):
	"""
	Internal MemoryHandler threshold reached	
	send out message in mail 
	"""
	def __init__(self, capacity,mail_subject):
		logging.handlers.MemoryHandler.__init__(self, capacity,flushLevel = logging.ERROR, target = None)
		self.mail_subject = mail_subject
		self.flushed_buffers = []
	def shouldFlush(self, record):
		""" 
		check if exceed 
		"""
		if len(self.buffer) >= self.capacity:
			return True
		else:
			return False
	def flush(self):
		""" 
		Meory overflow operation
		1. send out mail 2.clear buffer 3.move buffer content to any area for later processing 
		"""
		if self.buffer != [] and len(self.buffer) >= self.capacity:
			content = ""
			for record in self.buffer:
				message = record.getMessage()
				level = record.levelname
				ctime = record.created
				t = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(ctime))
				content += t + " " + "*" + level + "* : " + message + "\n"
			self.mailNotification(self.mail_subject, content)
			self.flushed_buffers.extend(self.buffer)
			self.buffer = []
	def mailNotification(self,subject,content):
		""" 
				mail sending mode 
		"""
		msg = MIMEText(content)
		msg['Subject'] = subject
		msg['From'] = FROM
		msg['To'] = ";".join(MAIL_TO)
		try:
			s = smtplib.SMTP()
			s.connect(MAIL_HOST)
			s.sendmail(FROM,MAIL_TO,msg.as_string())
			s.close()
		except Exception as e:
			self.logger.error(str(e))
			
MAPPING = {"CRITICAL" : 50,
			"ERROR" : 40,
			"WARNING" : 30,
			"INFO" : 20,
			"DEBUG" : 10,
			"NOTSET" : 0,
			}

class logger:
	""" 
	logger setting 
	"""
	def __init__(self,logFile,file_level=FILE_LOG_LEVEL,console_level=CONSOLE_LOG_LEVEL,memory_level=MEMOEY_LOG_LEVEL,urgent_level=URGENT_LOG_LEVEL):

		self.config(logFile, file_level, console_level, memory_level,urgent_level)
	def config(self,logFile,file_level,console_level,memory_level,urgent_level):
		# create root logger
		self.logger = logging.getLogger("xn")
		self.logger.setLevel(MAPPING[file_level])
		if not self.logger.handlers:
			# create RotatingFileHandler，size set at 10M, utf-8 coding，maximum count 100，reuse 1st buffer if exceed max count
			self.fh = logging.handlers.RotatingFileHandler(logFile,mode = 'a', maxBytes = 1024*1024*10, backupCount = 10, encoding="utf-8")
			self.fh.setLevel(MAPPING[file_level])
			# create StreamHandler
			self.ch = logging.StreamHandler()
			self.ch.setLevel(MAPPING[console_level])	
			# create optimized MemoryHandler
			# self.mh = OptmizedMemoryHandler(ERROR_MESSAGE_THRESHOLD,ERROR_THRESHOLD_ACHEIVED_MAIL_SUBJECT)
			# self.mh.setLevel(MAPPING[memory_level])
			# create SMTPHandler
			# self.sh = logging.handlers.SMTPHandler(MAIL_HOST,FROM,";".join(MAIL_TO),CRITICAL_ERROR_ACHEIVED_MAIL_SUBJECT)
			# self.sh.setLevel(MAPPING[urgent_level])
			# set format
			formatter = logging.Formatter("%(asctime)s *%(levelname)s* : %(message)s",'%Y-%m-%d %H:%M:%S')	
			self.ch.setFormatter(formatter)	
			self.fh.setFormatter(formatter)
			# self.mh.setFormatter(formatter)
			# self.sh.setFormatter(formatter)
			# Put all handler to root logger
			self.logger.addHandler(self.ch)
			self.logger.addHandler(self.fh)
			# self.logger.addHandler(self.mh)
			# self.logger.addHandler(self.sh)

	def debug(self,msg):
		if msg is not None:
			self.logger.debug(msg)
	def info(self,msg):
		if msg is not None:
			self.logger.info(msg)
	def warning(self,msg):
		if msg is not None:
			self.logger.warning(msg)
	def error(self,msg):
		if msg is not None:
			self.logger.error(msg)
	def critical(self,msg):
		if msg is not None:
			self.logger.critical(msg)

# LOG = logger(LOG_FILE_PATH,FILE_LOG_LEVEL,CONSOLE_LOG_LEVEL,MEMOEY_LOG_LEVEL,URGENT_LOG_LEVEL)
