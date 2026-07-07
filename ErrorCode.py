# -*- coding: utf-8 -*
""" Error Code Enumeration Class
usage：
	Structure： Error name-code-message
	# print status code
	code = Status.OK.get_code()
	print("code:", code)
	# print status code message
	msg = Status.OK.get_msg()
	print("msg:", msg)
"""
from enum import Enum, unique


@unique
class StatusCode(Enum):
	ANS_OK = {"0": "Success"}
	QUERY_ERROR = {"1": "Query failed"}
	NO_WAV_DATA = {"2": "No Wave Data"}
	CMD_or_QUERY_FMT_ERROR = {"20": "Command or Query format Error"}
	PARA_OVERFLOW_ERROR = {"21": "Parameter overflow"}
	CMD_INVAILD = {"22": "Invalid Command"}
	CMD_OTDR_MODE_UNSUPPORT = {"40": "No response in OTDR mode"}
	CMD_DOWNLOAD_MODE_UNSUPPORT = {"41": "OTDR command received in Download mode not support"}
	CMD_FMT_ERROR = {"60": "Command format error"}
	PARA_MeasureLength_ERROR = {"61": "Invalid measurement length"}
	PARA_PulseWidth_ERROR = {"62": "Invalid pulse width setting"}
	PARA_SampleTime_ERROR = {"63": "Invalid sampling time"}
	PARA_WaveLength_ERROR = {"64": "Invalid wavelength"}
	FILE_TYPE_ERROR = {"80": "Invalid file type"}
	FILE_FMT_ERROR = {"81": "Invalid or currupted file format"}
	DEVICE_ERROR = {"255": "OTDR internal error"}

	UNKNOWN_ERROR = {'':"Unknown error"}

	def get_code(self):
		"""
		From error name to get error code
		:return: error code
		"""
		return list(self.value.keys())[0]

	def get_msg(self):
		"""
		From error name to get error message
		:return: error message
		"""
		return list(self.value.values())[0]

def code_in_Enum(Enum,errcode):
	for ed in Enum:
		if ed.get_code() == str(errcode):
			return ed
	return Enum.UNKNOWN_ERROR
		
if __name__=="__main__":
	errorcode = StatusCode.CMD_INVAILD
	print(errorcode.get_msg())
	print(errorcode.get_code())
	sd = code_in_Enum(StatusCode,errcode = 82)
	print(sd)