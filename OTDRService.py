# -*- coding: utf-8 -*-

# Tabbing in this file does not use spaces - cannot use editor that replaces tabs with spaces - generates indentation errors

import socket
import math
import sys
from LogReport import logger
import time
import struct
import os
import json
#import numpy as np
import csv
from ErrorCode import *
# from pyOTDR import read as pyotdrread

# 12-10-2021
# module not found error on 6UL with pyOTDR included in the Linux build
# pyOTDR is probably case-sensitive. Install pyOTDR with pip3 could still be fine
# 
#from pyOTDR.read import sorparse
from pyotdr.read import sorparse

Debug = 1
if hasattr(sys,"_MEIPASS"):
	filebasepath = sys._MEIPASS
else:
	filebasepath = os.path.abspath(".")
time.sleep(1)
LOG_FILE_PATH = filebasepath + '/log.log'

dir = os.path.dirname(LOG_FILE_PATH)
if not os.path.exists(dir):
	os.makedirs(dir)

LOG = logger(LOG_FILE_PATH)


def Write_Result_to_File(filename,**kwargs):
	# Save data info to file
	dir = os.path.dirname(filename)
	if not os.path.isdir(dir) and (dir != ''):
		os.makedirs(dir)
	key = list(kwargs.keys())
	value = list(kwargs.values())

	if os.path.isfile(filename) == False:
		with open(filename, "a+", newline = '') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter = ",")
			spamwriter.writerow(key)
	with open(filename, "a+", newline = '') as csvfile:
		spamwriter = csv.writer(csvfile, delimiter = ",")
		spamwriter.writerow(value)


def bytestoint(para_bytes,byteorder = 'little'):# convert string to integer
	return int.from_bytes(para_bytes, byteorder = byteorder, signed = False)

def HexStr2Bytes(str):
	str = str.replace(" ", "")
	return bytes.fromhex(str)

def Int2Bytes(Intdata, byte, byteorder='little',signed=False):
	return Intdata.to_bytes(byte,byteorder=byteorder, signed=signed)

def HexStr2Int(Hexstr,byteorder='big',signed = True):
	return int.from_bytes(bytes = bytearray.fromhex(Hexstr), byteorder = byteorder, signed = signed)

def modifySendBuffersize(sock,SEND_BUF_SIZE=4096):
	# get current socket associated options
	# socket.SOL_SOCKET —— options being used
	# socket.SO_SNDBUF —— transmit buffer size
	bsize_send = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
	# print buffer size before change
	if Debug:
		LOG.debug("Buffer size send [Before]: %d" % bsize_send)

	# set TCP socket associated options
	# socket.TCP_NODELAY TCP
	# 1 —— set TCP_NODELAY as TRUE
	sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

	# set transmit buffer socket associated options
	sock.setsockopt(
		socket.SOL_SOCKET,
		socket.SO_SNDBUF,
		SEND_BUF_SIZE)
	# get transmit buffer after change
	bsize_send = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
	if Debug:
		LOG.debug("Buffer size send [After] : %d" % bsize_send)


def modifyRecvBuffersize(sock,RECV_BUF_SIZE=4096):
	# get current socket associated options
	# socket.SOL_SOCKET —— options being used
	# socket.SO_RCVBUF —— receive buffer size
	bsize_recv = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
	# print buffer size before change
	if Debug:
		LOG.debug("Buffer size recv [Before]: %d" % bsize_recv)
	# set TCP socket associated options
	# socket.TCP_NODELAY TCP
	# 1 —— set TCP_NODELAY as TRUE
	sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
	# set receive buffer socket associated options
	sock.setsockopt(
		socket.SOL_SOCKET,
		socket.SO_RCVBUF,
		RECV_BUF_SIZE)
	# get receive buffer after change
	bsize_recv = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
	if Debug:
		LOG.debug("Buffer size recv [After] : %d" % bsize_recv)


def getRecvBuffersize(sock):
	# get current socket associated options
	# socket.SOL_SOCKET —— options being used
	# socket.SO_RCVBUF —— receive buffer size
	bsize_recv = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
	# print buffer size before change
	if Debug:
		LOG.debug("Buffer size recv [Before]: %d" % bsize_recv)
	return bsize_recv


def getSendBuffersize(sock):
	# get current socket associated options
	# socket.SOL_SOCKET —— options being used
	# socket.SO_RCVBUF —— receive buffer size
	bsize_send = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
	# print buffer size before change
	if Debug:
		LOG.debug("Buffer size send [Before]: %d" % bsize_send)
	return bsize_send


def CLientSocketConnectToOtdr(server_host,server_port):
	try:
		client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		client.connect((server_host, server_port))
		client.settimeout(10)
		return client
	except Exception as other:
		LOG.error('\nERROR: SOCKET Cannot connect to OTDR:%s\n'%other)
		return None


def CLientSendSocketToOtdr(client,request):
	try:
		#time.sleep(0.1)
		client.send(bytes(request+'\r\n', encoding = 'utf-8'))
		return True
	except Exception as other:
		LOG.error('\nERROR: SOCKET send to OTDR with error:%s\n'%other)
		return False


def CLientRecvSocketFromOtdr(client,Buffsize=1024):
	try:
		#time.sleep(0.1)
		response = client.recv(Buffsize)
		if response is not None:
			return response
		else:
			LOG.error('\nERROR: SOCKET Recv None Stream From OTDR!\n')
			raise Exception('ERROR: SOCKET Recv None Stream From OTDR!')
	except Exception as other:
		LOG.error('\nERROR: SOCKET Recv From OTDR with error:%s\n'%other)


def CLientCloseSocketToOtdr(client):
	try:
		client.close()
		if Debug:
			LOG.debug('SOCKET close with OTDR success')
		return True
	except Exception as other:
		LOG.error('\nERROR: SOCKET Close with OTDR:%s\n'%other)
		return False


def getOtdrLD(client):
	'''
	Query measurment status，return status code

	'''
	ret = CLientSendSocketToOtdr(client,request='LD?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response:
			LOG.error("[getOtdrLD] get OTDR LD with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		status = int(response.split()[-1])
		if Debug:
			LOG.debug("[getOtdrLD] get OTDR LD=%d Success!"%status)
		return status


CMD_HOST_START_MEASURE = 1
CMD_HOST_STOP_MEASURE = 0
def setOtdrLD(client,status):
	'''
	set measurement status
	status: CMD_HOST_START_MEASURE / CMD_HOST_STOP_MEASURE
	'''
	ret = CLientSendSocketToOtdr(client=client,request='LD %d'%status)
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == 'ANS' + StatusCode.ANS_OK.get_code():
			if Debug:
				LOG.debug("[setOtdrLD] set OTDR LD status= %d Success!"%status)
			return True
		else:
			LOG.error("[setOtdrLD] set OTDR LD with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)


def getOtdrWaveLength(client):
	'''
	Query wavelength
	'''
	ret = CLientSendSocketToOtdr(client,request='WLS?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response:
			LOG.error("[getOtdrWaveLength] get OTDR WaveLength with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		Lambda_nm = int(response.split()[-1])
		if Debug:
			LOG.debug("[getOtdrWaveLength] get OTDR WaveLength=%dnm Success!"%Lambda_nm)
		return Lambda_nm


def setOtdrWaveLength(client,Lambda_nm):
	'''
	Set wavelength
	Lambda_nm: WaveLength,unit - nm
	'''
	ret = CLientSendSocketToOtdr(client=client,request='WLS %d'%Lambda_nm)
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == 'ANS' + StatusCode.ANS_OK.get_code():
			if Debug:
				LOG.debug("[setOtdrWaveLength] set OTDR WaveLength=%d Success!"%Lambda_nm)
			return True
		else:
			LOG.error("[setOtdrWaveLength] set OTDR WaveLength with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)

# ALA sampling time
def getOtdrSamplingTime(client):
	'''
	Query averaging time
	'''
	ret = CLientSendSocketToOtdr(client,request='ALA?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response:
			LOG.error("[getOtdrALA] get OTDR ALA with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		
		res_data = response.split()[-1]
		[mode,value] = res_data.split(',')
		if Debug:
			LOG.debug("[getOtdrALA] get OTDR ALA with SamplingMode:%s SamplingValue:%s Success!"%(mode,value))
		return mode,value


def setOtdrSamplingTime(client,mode,SampleTime=1):
	'''
	Set sampling time
	mode：  0-count,1-time,2-auto
	Sample： range of 1-9999， not used in auto mode (mode= 2)
	'''
	if (mode in range(0,3) and SampleTime in range(1,10000)):
		ret = CLientSendSocketToOtdr(client=client,request='ALA %d,%d'%(mode,SampleTime))
	else:
		LOG.error("[setOtdrALA] set OTDR ALA with parameter(s) ERROR!")
		return False
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == 'ANS' + StatusCode.ANS_OK.get_code():
			if Debug:
				LOG.debug("[setOtdrALA] set OTDR ALA with mode=%d and SampleTime=%s Success!"%(mode,SampleTime))
			return True
		else:
			LOG.error("[setOtdrALA] set OTDR ALA with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)


# AVG averaging mode
def getOtdrAverageMode(client):
	'''
	query averaging mode
	'''
	ret = CLientSendSocketToOtdr(client,request='AVG?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response:
			LOG.error("[getOtdrAverageMode] get OTDR AverageMode with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		AvgMode = response.split()[-1]
		if Debug:
			LOG.debug("[getOtdrAverageMode] get OTDR AverageMode=%s Success!"%AvgMode)

		return AvgMode


def setOtdrAverageMode(client,AvgMode):
	'''
	set average mode
	AvgMode  0- real time,1- average
	'''
	if AvgMode in range(0,2):
		ret = CLientSendSocketToOtdr(client=client,request='AVG %d'%AvgMode)
	else:
		LOG.error("[setOtdrAverageMode] set OTDR AVG with parameter-AvgMode ERROR!")
		return False
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == 'ANS' + StatusCode.ANS_OK.get_code():
			if Debug:
				LOG.debug("[setOtdrAverageMode] set OTDR AVG with mode=%d Success!"%AvgMode)
			return True
		else:
			LOG.error("[setOtdrAverageMode] set OTDR AVG mode with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)


# STP measurment parameter(distance，pulse width、sample mode)
def getOtdrSTP(client):
	'''
	Query STP measurment parameter (distance，pulse width、sample mode)
	'''
	ret = CLientSendSocketToOtdr(client,request='STP?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response:
			LOG.error("[getOtdrSTP] get OTDR STP with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		
		res_data = response.split()[-1]
		DistanceMode,Distance_m,PluseWidthMode,PulseWidth_ns,SampleMode = res_data.split(',')
		if Debug:
			LOG.debug("[getOtdrSTP] get OTDR STP Success!")

		return DistanceMode,Distance_m,PluseWidthMode,PulseWidth_ns,SampleMode


def setOtdrSTP(client,DistanceMode,Distance_m,PluseWidthMode,PulseWidth_ns,SampleMode):
	'''
	set STP measurement parameters(distance，pulse width、sample mode)
	STP<distance mode>,<distance>,<pulse mode>,<pulse width>,<sampling mode>
	<distance mode>：  0 -- manual  1 -- auto
	<pulse width mode>：  0 -- manual  1 -- auto
	<pulse width>： valid in manual mode only. If input value is invalid or out of range, the closest setting will be used.
		pulse width selection： 3ns,5ns,10ns,30ns,50ns,100ns,275ns,500ns,1000ns,5000ns,10000ns,20000ns
	<sample mode>：  0 -- fast      1 -- precise
	'''
	if DistanceMode in range(0,2) and 0<=Distance_m<=200000 and PluseWidthMode in range(0,2) and PulseWidth_ns in range(0,20001) and SampleMode in range(0,2):
		# request = 'STP %d,%d,%d,%d,%d'%(DistanceMode,Distance_m,PluseWidthMode,PulseWidth_ns,SampleMode)
		# print("setOtdrSTP request =",request)
		ret = CLientSendSocketToOtdr(client=client,request='STP %d,%d,%d,%d,%d'%(DistanceMode,Distance_m,PluseWidthMode,PulseWidth_ns,SampleMode))
	else:
		LOG.error("[setOtdrSTP] set OTDR STP with parameter(s) ERROR!")
		return False
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == 'ANS' + StatusCode.ANS_OK.get_code():
			if Debug:
				LOG.debug("[setOtdrSTP] set OTDR STP with Success!")
			return True
		else:
			LOG.error("[setOtdrSTP] set OTDR STP with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)

# THS event loss threshold
def getOtdrEventLossThresholdofFiber(client):
	'''
	Get THS event loss threshold
	'''
	ret = CLientSendSocketToOtdr(client,request='THS?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response:
			LOG.error("[getOtdrThresholdofFiberEvent] get OTDR THS with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		Threshold = response.split()[-1]
		if Debug:
			LOG.debug("[getOtdrThresholdofFiberEvent] get OTDR THS=%sdB Success!"%Threshold)
		
		return Threshold


def setOtdrEventLossThresholdofFiber(client,Threshold):
	'''
	Set THS event loss threshold
	Threshold: float type 0.01~9.99 unit-dB
	'''
	if 0.01<=Threshold<=9.99:
		# request = 'THS %.2f'%Threshold
		ret = CLientSendSocketToOtdr(client=client,request='THS %.2f'%Threshold)
	else:
		LOG.error("[setOtdrEventLossThresholdofFiber] set OTDR THS with parameter(s) ERROR!")
		return False
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == 'ANS' + StatusCode.ANS_OK.get_code():
			if Debug:
				LOG.debug("[setOtdrEventLossThresholdofFiber] set OTDR THS=%.2fdB with Success!"%Threshold)
			return True
		else:
			LOG.error("[setOtdrEventLossThresholdofFiber] set OTDR THS with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)


# THR2 event reflection threshold
def getOtdrEventReflectThresholdofFiber(client):
	'''
	Get THR2 event reflection threshold
	'''
	ret = CLientSendSocketToOtdr(client,request='THR2?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response:
			LOG.error("[getOtdrEventReflectThresholdofFiber] get OTDR THR2 with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		Threshold = response.split()[-1]
		if Debug:
			LOG.debug("[getOtdrEventReflectThresholdofFiber] get OTDR THR2=%sdB Success!"%Threshold)
		
		return Threshold


def setOtdrEventReflectThresholdofFiber(client,Threshold):
	'''
	Set THR2 event loss reflection threshold
	Threshold: float type -14.0 ~ -65.0 unit-dB
	'''
	if -65.0<=Threshold<=-14.0:
		# request = 'THR2 %.2f'%Threshold
		ret = CLientSendSocketToOtdr(client=client,request='THR2 %.2f'%Threshold)
	else:
		LOG.error("[setOtdrEventReflectThresholdofFiber] set OTDR THR2 with parameter(s) ERROR!")
		return False
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == 'ANS' + StatusCode.ANS_OK.get_code():
			if Debug:
				LOG.debug("[setOtdrEventReflectThresholdofFiber] set OTDR THR2=%.2fdB with Success!"%Threshold)
			return True
		else:
			LOG.error("[setOtdrEventReflectThresholdofFiber] set OTDR THR2 with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)

# THF end point threshold
def getOtdrEndThresholdofFiber(client):
	'''
	Get THF end point threshold
	'''
	ret = CLientSendSocketToOtdr(client,request='THF?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response:
			LOG.error("[getOtdrEndThresholdofFiber] get OTDR THF with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		
		Threshold = response.split()[-1]
		if Debug:
			LOG.debug("[getOtdrEndThresholdofFiber] get OTDR THF=%sdB Success!"%Threshold)

		return Threshold


def setOtdrEndThresholdofFiber(client,Threshold):
	'''
	Set THF end point threshold
	Threshold: float type 1.0~65.534 unit-dB
	'''
	if 1<=Threshold<=99:
		# request = 'THF %.2f'%Threshold
		ret = CLientSendSocketToOtdr(client=client,request='THF %.2f'%Threshold)
	else:
		LOG.error("[setOtdrEndThresholdofFiber] set OTDR THF with parameter(s) ERROR!")
		return False
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == 'ANS' + StatusCode.ANS_OK.get_code():
			if Debug:
				LOG.debug("[setOtdrEndThresholdofFiber] set OTDR THF with Success!")
			return True
		else:
			LOG.error("[setOtdrEndThresholdofFiber] set OTDR THF with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)

# IOR refractivew index
def getOtdrRefractiveIndexofFiber(client):
	'''
	Get IOR refractivew index
	'''
	ret = CLientSendSocketToOtdr(client,request='IOR?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response:
			LOG.error("[getOtdrRefractiveIndexofFiber] get OTDR IOR with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		
		nGIR = response.split()[-1]
		if Debug:
			LOG.debug("[getOtdrRefractiveIndexofFiber] get OTDR IOR=%s Success!"%nGIR)
		return nGIR


def setOtdrRefractiveIndexofFiber(client,nGIR):
	'''
	Set IOR refractivew index
	nGIR: float type  1.300000 – 1.800000
	'''
	if 1.30<=nGIR<=1.80:
		# request = 'IOR %.6f'%nGIR
		ret = CLientSendSocketToOtdr(client=client,request='IOR %.6f'%nGIR)
	else:
		LOG.error("[setOtdrRefractiveIndexofFiber] set OTDR IOR with parameter:nGIR ERROR!")
		return False
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == 'ANS' + StatusCode.ANS_OK.get_code():
			if Debug:
				LOG.debug("[setOtdrRefractiveIndexofFiber] set OTDR IOR=%.8f with Success!"%nGIR)
			return True
		else:
			LOG.error("[setOtdrRefractiveIndexofFiber] set OTDR IOR with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)

# BSL2 scattering coefficient
def getOtdrScatteringCoefofFiber(client):
	'''
	Get BSL2 scattering coefficient
	'''
	ret = CLientSendSocketToOtdr(client,request='BSL2?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response:
			LOG.error("[getOtdrScatteringCoefofFiber] get OTDR BSL2 with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		
		ScatteringCoef = response.split()[-1]
		if Debug:
			LOG.debug("[getOtdrScatteringCoefofFiber] get OTDR BSL2=%sdB Success!"%ScatteringCoef)
		return ScatteringCoef


def setOtdrScatteringCoefofFiber(client,ScatteringCoef):
	'''
	Set BSL2 scattering coefficient
	BSL2: float type  -40.00 – -90.00,unit dB
	'''
	if -90.00<=ScatteringCoef<=-40.00:
		# request = 'BSL2 %.2f'%ScatteringCoef
		ret = CLientSendSocketToOtdr(client=client,request='BSL2 %.2f'%ScatteringCoef)
	else:
		LOG.error("[setOtdrScatteringCoefofFiber] set OTDR BSL2 with parameter(s) ERROR!")
		return False
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == 'ANS' + StatusCode.ANS_OK.get_code():
			if Debug:
				LOG.debug("[setOtdrScatteringCoefofFiber] set OTDR BSL2=%.2fdB with Success!"%ScatteringCoef)
			return True
		else:
			LOG.error("[setOtdrScatteringCoefofFiber] set OTDR BSL2 with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)


# SMPINF? Get sample point count and resolution
def getOtdrSampleInfo(client):
	'''
	SMPINF? Get sample point count and resolution
	'''
	ret = CLientSendSocketToOtdr(client,request='SMPINF?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response:
			LOG.error("[getOtdrSampleInfo] get OTDR SampleInfo with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		res_data = response.split()[-1]
		SamplePointNum,SampleAccuracy = res_data.split(',')
		if Debug:
			LOG.debug("[getOtdrSampleInfo] get OTDR SampleInfo Success!")
		return SamplePointNum,SampleAccuracy

# Measurement result
# AUT? Get auto mode measurment result
def getOtdrMeasureResults(client):
	'''
	AUT?  Get auto mode measurment result
	Return data：
	<Event Count>：0 – 255.
	<Fiber length>： unit in m，“***” means failure in length estimation.
	<Total loss>： unit in dB，“***” means failure in loss estimation.
	<Return loss>： unit in dB，“***” means failure in return loss estimation. 
	'''
	ret = CLientSendSocketToOtdr(client,request='AUT?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response and 'ANS40' not in response:
			LOG.error("[getOtdrMeasureResults] get OTDR Measure Results with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		elif 'ANS40' in response:
			LOG.debug("[getOtdrMeasureResults] get OTDR Measure Results with None!")
			return None,None,None,None
		
		res_data = response.split()[-1]
		EventNum,FiberLength,TotalLoss,TotalReflectLoss = res_data.split(',')
		if Debug:
			LOG.debug("[getOtdrMeasureResults] get OTDR Measure Results Success!")

		return EventNum,FiberLength,TotalLoss,TotalReflectLoss


# DAT? Get waveform data
def getOtdrWaveData(client,StartPoint=None,EndPoint=None):
	'''
	DAT? Get waveform data
	'''
	
	if StartPoint is None and EndPoint is None:
		ret = CLientSendSocketToOtdr(client,request='DAT?')
	else:
		ret = CLientSendSocketToOtdr(client,request='DAT? %f,%f'%(StartPoint,EndPoint))
	if ret is True:
		# response = CLientRecvSocketFromOtdr(client,Buffsize=1024)
		response = b''
		while 1:
			curResponse = CLientRecvSocketFromOtdr(client,Buffsize=1024)
			if curResponse is not None and curResponse != b'':
				curResponse_de = curResponse.decode('utf-8',errors='ignore')
				if 'ANS2' in curResponse_de and 'ANS20' not in curResponse_de and 'ANS22' not in curResponse_de:
					if Debug:
						LOG.debug("[getOtdrWaveData] get OTDR with NO WaveData!")
					return None,None
				elif 'ANS20' in curResponse_de and 'ANS22' in curResponse_de:
					LOG.error("[getOtdrWaveData] get OTDR Measure WaveData with ERROR response:%s!"%curResponse_de)
					raiseExceptionInfo(client,curResponse_de)
				else:
					response += curResponse
					DataNum = bytestoint(response[0:4],byteorder = 'big')
					dataLen = 2*DataNum + 4
					if dataLen != len(response):
						pass
					else:
						if Debug:
							LOG.debug("[getOtdrWaveData] get OTDR Measure WaveData Success!")
						break

		DataList = []
		DataNum = bytestoint(response[0:4],byteorder = 'big')
		for x in range(DataNum):
			datax = HexStr2Int(response[4+2*x:4+2*x+2].hex(),byteorder='big',signed = False)
			DataList.append(round(datax*0.001,3))
		return DataNum,DataList
	else:
		LOG.error("[getOtdrWaveData] get OTDR Measure WaveData with unknown ERROR!")
		return None,None


# AVE? Get current average count and time
def getOtdrAverageTimes(client):
	'''
	AVE? Get current average count and time
	'''
	ret = CLientSendSocketToOtdr(client,request='AVE?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		print("AVE response =",response)
		if response is not None:
			response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response:
			LOG.error("[getOtdrAverageTimes] get OTDR Measure Average Times with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		else:
			if Debug:
				LOG.debug("[getOtdrAverageTimes] get OTDR Measure Average Times Success!")
		res_data = response.split()[-1]
		AverageMode,AverageTimes,Count = res_data.split(',')
		return AverageMode,AverageTimes,Count

# EVN2? Get Event measurement result
def getOtdrMeasureEventInfo(client,EventID):
	'''
	EVN2? Get Event measurement result
	Return data：
	<Event index>：0 – 255
	<Location>： Event location in unit of m.
	<Loss>：Event loss in unit of dB, “***” means failure in loss estimation.
	<Reflection>： Event reflection in unit of dB, “***” means failure in reflection estimation.
	<Accumulated loss>： accumulated loss in unit of dB, “***” means failure in accumulated loss estimation.
	<event type>： 
		N： non-reflective event
		R： reflective event
		S： fiber start
		E： fiber end
		O： other events
		'''
	if EventID in range(256):
		ret = CLientSendSocketToOtdr(client,request='EVN2? %d'%EventID)
	else:
		LOG.error("[getOtdrMeasureEventInfo] get OTDR Event Info with parameter-EventID ERROR!")
		return False

	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		if response is not None:
			response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response and 'ANS2' not in response:
			LOG.error("[getOtdrMeasureEventInfo] get OTDR Measure Event Info with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		elif 'ANS2' in response:
			if Debug:
				LOG.debug("[getOtdrMeasureEventInfo] get OTDR Measure Event Info with NO Data!")
			return None
		else:
			if Debug:
				LOG.debug("[getOtdrMeasureEventInfo] get OTDR Measure Event Info Success!")
		res_data = response.split()[-1]
		EventID2,EvnDistance_m,EventLoss,EventReflectivity,EventTotalReflectLoss,EventType = res_data.split(',')
		if int(EventID2) == EventID:
			return EventID2,EvnDistance_m,EventLoss,EventReflectivity,EventTotalReflectLoss,EventType


# REFLCT? Calculate reflection
def getOtdrMeasureEventReflect(client,EventDist1,EventDist2):
	'''
	REFLCT? Calculate reflection
	input:
	EventDist1：<event location>：unit m，event location.
	EventDist2：<peak location>：unit m，event peak location.
	return：
	REFLCT <sample location>,<sample peak location>,<reflection> 
	<sample event location>：uniit m，sample event location. 
	<event peak location>：unit m，event peak sample location.
	<reflection>：unit dB，“***” mean reflection calculation failure.
	'''
	ret = CLientSendSocketToOtdr(client,request='REFLCT? %f,%f'%(EventDist1,EventDist2))
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		if response is not None:
			response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response and 'ANS2' not in response:
			LOG.error("[getOtdrMeasureEventReflect] get OTDR Measure Event Reflect with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		elif 'ANS2' in response:
			if Debug:
				LOG.debug("[getOtdrMeasureEventReflect] get OTDR Measure Event Reflect with NO Data!")
			return None,None,None
		else:
			if Debug:
				LOG.debug("[getOtdrMeasureEventReflect] get OTDR Measure Event Reflect Success!")
		res_data = response.split()[-1]
		EvnDistance1_m,EvnDistance2_m,EventReflect= res_data.split(',')
		return EvnDistance1_m,EvnDistance2_m,EventReflect


# LOS2?计算损耗
def getOtdrMeasureEventLoss(client,LengthX1,LengthX2):
	'''
	LOS2? calculate loss
	input：
	LengthX1: <X1 location>：unit m，X1 mark location.
	LengthX2: <X2 location>：unit m，X2 mark location.
	return：
	LOS2 <X1 sample location>,<sample X2 sample location>,<loss> 
	<X1 sample location>： unit m，X1 sample location.
	<X2 sample location>： unit m，X2 sample location.
	<loss>： unit dB，“***” means loss calculation failure. 
	'''
	ret = CLientSendSocketToOtdr(client,request='LOS2? %f,%f'%(LengthX1,LengthX2))

	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		if response is not None:
			response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response:
			LOG.error("[getOtdrMeasureEventLoss] get OTDR Measure Event Loss with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		else:
			if Debug:
				LOG.debug("[getOtdrMeasureEventLoss] get OTDR Measure Event Loss Success!")
		res_data = response.split()[-1]
		LengthX1_m,LengthX2_m,EventLossX1X2 = res_data.split(',')

		return LengthX1_m,LengthX2_m,EventLossX1X2


# MKDR? read start and end points
def getOtdrMeasureStartEndPoints(client):
	'''
	MKDR? read start and end points
	return：
	<start point>：“***” means query failure.
	<end point>：“***” means query failure.
 
	'''
	ret = CLientSendSocketToOtdr(client,request='MKDR?')

	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		if response is not None:
			response = str(response, encoding = 'utf-8').strip()
		if 'ANS' in response and 'ANS2' not in response:
			LOG.error("[getOtdrMeasureStartEndPoints] get OTDR StartPoint and EndPoint with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
		elif 'ANS2' in response:
			if Debug:
				LOG.debug("[getOtdrMeasureEventLoss] get OTDR StartPoint and EndPoint with NO Data!")
			return None
		else:
			if Debug:
				LOG.debug("[getOtdrMeasureStartEndPoints] get OTDR StartPoint and EndPoint Success!")
		res_data = response.split()[-1]
		StartPoint,EndPoint = res_data.split(',')

		return StartPoint,EndPoint


#**********************File settings**********************#
def getOtdrFileOfSR(client):
	'''
	read data from OTDR(SR-4731)
	Command： GETFILE?
	return：0001FF...
	remark: first 4 bytes are data size
	return：with waveform data：(fileSize,DataSequence)，no waveform data：False
	'''
	ret = CLientSendSocketToOtdr(client,request='GETFILE?')
	if ret is True:
		response = b''
		while 1:
			curResponse = CLientRecvSocketFromOtdr(client,Buffsize=1024)
			if curResponse is not None and curResponse != b'':
				response += curResponse
				fileSize = bytestoint(response[0:4],byteorder = 'big')
				dataLen = fileSize + 4
				if dataLen != len(response):
					print("TOTAL RECV len(dataLen):",dataLen)
					print("Current len(curResponse):",len(curResponse))
					pass
				else:
					print("TOTAL RECV len(dataLen):",dataLen)
					print("Recv len(response):",len(response))
					break

		response_de = response.decode('utf-8',errors='ignore')
		if 'ANS' in response_de and 'ANS2' not in response_de and len(response_de)<=7:
			LOG.error("[getOtdrFileOfSR] get OTDR File Of SR with ERROR response:%s!"%response_de)
			raiseExceptionInfo(client,response_de)
		elif 'ANS2' in response_de and len(response_de)<=7:
			if Debug:
				LOG.debug("[getOtdrFileOfSR] get OTDR File Of SR with NO Data!")
			return None
		else:
			if Debug:
				LOG.debug("[getOtdrFileOfSR] get OTDR File Of SR Success!")

		fileSize = bytestoint(response[0:4],byteorder = 'big')
		fileData = response[4:]
		# fileData = response[4:].decode('utf-8',errors='ignore')
		return fileSize,fileData,response
	else:
		return False


def setOtdrFileOfSRData(client,setData):
	'''
	send data to (SR-4731) OTDR
	command: SETFILE 00000003010203
	remark: first 4 bytes are data size. OTDR receiving limit is 500kBytes.
	setDate:
	format： "00000003010203" 
	type： string
	'''
	request = "SETFILE %s"%setData
	ret = CLientSendSocketToOtdr(client,request=setDate)
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == "ANS0":
			if Debug:
				LOG.debug("[setOtdrFileOfSRData] set OTDR SRFile Success!")
			return True
		else:
			LOG.error("[setOtdrFileOfSRData] set OTDR SRFile with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
	return False


#**********************system settings**********************#
def getOtdrDate(client):
	'''
	get local date and time
	command： DATE2?
	return： normal："2003/3/31 12：34：59"，abnormal：False
	'''
	ret = CLientSendSocketToOtdr(client,request='DATE2?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		dateInfo = str(response, encoding = 'utf-8').strip().split()[-1]
		dateInfo = dateInfo.split(",")
		retDate = "{0[0]}/{0[1]}/{0[2]} {0[3]}:{0[4]}:{0[5]}".format(dateInfo)
		return retDate
	else:
		return False


def setOtdrDate(client,setDate):
	'''
	set local date and time
	command：DATE2 2003,3,31,12,34,59
	setDate:
	format： DATE2 <year>,<month>,<date>,<hour>,<minute>,<second> 
	type：string
	'''
	ret = CLientSendSocketToOtdr(client,request=setDate)
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == "ANS0":
			if Debug:
				LOG.debug("[setOtdrDate] set OTDR Date Success!")
			return True
		else:
			LOG.error("[setOtdrDate] set OTDR Date with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
	return False


def getOtdrNet(client):
	'''
	get network parameter
	command： NET?
	return：("192.168.1.14","8000","255.255.255.0","192.168.1.1")
	'''
	ret = CLientSendSocketToOtdr(client,request='NET?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		netInfo = str(response, encoding = 'utf-8').strip().split()[-1]
		Ip,Port,Mask,Gateway = netInfo.split(",")
		return Ip,Port,Mask,Gateway
	else:
		return False


def setOtdrNet(client,Ip,Port,Mask,Gateway):
	'''
	set network parameter
	format： NET 192.168.1.14,8000,255.255.255.0,192.168.1.1
	power cycle to restart after change
	PS: testing found out no need to restart as opposed to instruction on manual
	setNet:
	format: NET <IP address>,<port>,<net mask>,<gateway> 
	type： string
	'''
	ret = CLientSendSocketToOtdr(client,request='NET %s,%d,%s,%s'%(Ip,Port,Mask,Gateway))
	if ret is True:
		if Debug:
			LOG.debug("[setOtdrNet] set OTDR Network Success!")
		return True
	LOG.error("[setOtdrNet] set OTDR Date with ERROR!")
	return False


def getOtdrSystemInfo(client):
	'''
	get network parameter
	command： MINF?
	return：OPWILL,OTC2100S-c,A0,20191105,1.0.0.8,210426,210426,0203035020A005
	'''
	ret = CLientSendSocketToOtdr(client,request='MINF?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		SysInfo = str(response, encoding = 'utf-8').strip().split()[-1]
		if Debug:
			LOG.debug("[getOtdrSystemInfo] get OTDR System Info Success!")
		return SysInfo
	else:
		LOG.error("[getOtdrSystemInfo] get OTDR System Info with unknown ERROR!")
		return False


def getOtdrTimeOut(client):
	'''
	get timeout setting
	command： CONNTM?
	command return： CONNTM 30
	return：30(unit s)
	'''
	ret = CLientSendSocketToOtdr(client,request='CONNTM?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip().split()[-1]
		if Debug:
			LOG.debug("[getOtdrTimeOut] get OTDR Parameter-TimeOut Success!")
		return int(response)
	else:
		LOG.error("[getOtdrTimeOut] get OTDR Parameter-TimeOut with unknown ERROR!")
		return False


def setOtdrTimeOut(client,timeOut_s):
	'''
	set timeout setting
	command： CONNTM [value]
	timeOut_s range： 1-7200 
	type： int
	'''
	request = "CONNTM %d"%round(timeOut_s)
	ret = CLientSendSocketToOtdr(client,request=request)
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == "ANS0":
			if Debug:
				LOG.debug("[setOtdrTimeOut] set OTDR Parameter-TimeOut Success!")
			return True
		else:
			LOG.error("[setOtdrTimeOut] set OTDR Parameter-TimeOut with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
	return False


#**********************status**********************#
def getOtdrStatus(client):
	'''
	get OTDR module status
	command： STATUS?
	return ：0 (idle)| 1 (measurement/busy)
	'''
	ret = CLientSendSocketToOtdr(client,request='STATUS?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		print("OtdrStatus RecvSocket response= ",response)
		if response is not None:
			status = str(response, encoding = 'utf-8').strip().split()[-1]
			if 'ANS2' in status:
				status = '1'
				if Debug:
					LOG.debug("[getOtdrStatus] get OTDR STATUS SKIPPED!")
			elif 'ANS' in status and 'ANS2' not in status:
				LOG.error("[getOtdrStatus] get OTDR STATUS with ERROR response:%s!"%status)
				raiseExceptionInfo(client,status)
			else:
				if Debug:
					LOG.debug("[getOtdrStatus] get OTDR STATUS Success!")
			return int(status)
		else:
			return 1
	else:
		LOG.error("[getOtdrStatus] get OTDR STATUS with unknown ERROR!")
		return False


def getOtdrErrorCode(client):
	'''
	get OTDR error code of last command
	command： ERR?
	error： 0 (no error), 1-255 (refer to error table)
	'''
	ret = CLientSendSocketToOtdr(client,request='ERR?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		if response is not None:
			ErrorCode = str(response, encoding = 'utf-8').strip().split()[-1]
			if Debug:
				LOG.debug("[getOtdrErrorCode] get OTDR ErrorCode=%s Success!"%ErrorCode)
			return int(ErrorCode)
		else:
			return 1
	else:
		LOG.error("[getOtdrErrorCode] get OTDR ErrorCode with unknown ERROR!")
		return False


def getOtdrWaveStatus(client):
	'''
	query if OTDR data is available
	command： WAV?
	return： 0 (not available) | 1 (available)
	'''
	ret = CLientSendSocketToOtdr(client,request='WAV?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		wavStatus = str(response, encoding = 'utf-8').strip().split()[-1]
		if Debug:
			LOG.debug("[getOtdrWaveStatus] get OTDR WaveStatus=%s Success!"%wavStatus)
		return int(wavStatus)
	else:
		LOG.error("[getOtdrWaveStatus] get OTDR waveform status with unknown ERROR!")
		return False


#**********************other settings**********************#
def OtdrParamInit(client):
	'''
	initialize OTDR parameter
	command： INI
	'''
	ret = CLientSendSocketToOtdr(client,request="INI")
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == "ANS0":
			if Debug:
				LOG.debug("[OtdrParamInit] OTDR Initialization Success!")
			return True
		else:
			LOG.error("[OtdrParamInit] OTDR Initialization with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
	return False


def OtdrDeviceReset(client):
	'''
	reset module
	command： RST
	'''
	ret = CLientSendSocketToOtdr(client,request="RST")
	if ret is True:
		if Debug:
			LOG.debug("[OtdrParamInit] OTDR RESET Success!")
		return True
	return False


def getOtdrMode(client):
	'''
	query current operation mode
	command： DLMODE?
	return: 0 (OTDR), 1 (download)
	'''
	ret = CLientSendSocketToOtdr(client,request='DLMODE?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip().split()[-1]
		if Debug:
			LOG.debug("[getOtdrMode] get OTDR MODE Success!")
		return int(response)
	else:
		LOG.error("[getOtdrMode] get OTDR MODE with unknown ERROR!")
		return False


def setOtdrMode(client,mode):
	'''
	set operation mode
	command： DLMODE [ 0 | 1 ]
	type： int
	'''
	request = "DLMODE %d"%mode
	ret = CLientSendSocketToOtdr(client,request=request)
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == "ANS0":
			if Debug:
				LOG.debug("[setOtdrMode] set OTDR MODE Success!")
			return True
		else:
			LOG.error("[setOtdrMode] set OTDR MODE with ERROR response:%s!"%response)
			raiseExceptionInfo(client,response)
	return False


def getOtdrDownStatus(client):
	'''
	query download mode status
	command： DWNLD?
	return: {0|1|2|3} 
			0 (ROM not available), 1 (upgrade in progress), 2 (upgrade success), 3 (operation failure)
	'''
	ret = CLientSendSocketToOtdr(client,request='DWNLD?')
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip().split()[-1]
		return int(response)
	else:
		return False


def OtdrDown(client,data):
	'''
	download firmware （restarting needed after download）
	command： DWNLD 00000001FF(data string)
	format： string
	'''
	request = "DWNLD " + data
	ret = CLientSendSocketToOtdr(client,request=request)
	if ret is True:
		response = CLientRecvSocketFromOtdr(client)
		response = str(response, encoding = 'utf-8').strip()
		if response == "ANS0":
			return True
		else:
			raiseExceptionInfo(client,response)
	return False


#**********************Error code**********************#
def raiseExceptionInfo(client,response):
	errorcode = getOtdrErrorCode(client)
	errc = code_in_Enum(StatusCode,errorcode)
	msg = 'Error Occurred with ' + response +':'+ errc.get_msg()
	raise Exception(msg)


#**********************function interface**********************#
# add function interfaces here

def showplt(x,y,title='Figure',xlabel='Distance(km)',ylabel='Attenuation(dB)',savefigname = 'squares_plot',linewidth=1,fontsize=12,labelsize=12):
	# open graphics window
	import matplotlib.pyplot as plt

	plt.rcParams['figure.figsize'] = (12.0, 6.0)
	# xy coordinates and linewidth
	plt.plot(x,y,linewidth=1)
	#SimHei font type
	# plt.rcParams['font.sans-serif'] = ['SimHei']
	plt.rcParams['axes.unicode_minus'] = False
	#title and fontsize
	plt.title(title, fontsize=fontsize)
	#X-axis label and fontsize
	plt.xlabel(xlabel, fontsize=fontsize)
	#Y-axis label and fontsize
	plt.ylabel(ylabel, fontsize=fontsize)
	#tick mark size
	plt.tick_params(axis='both', labelsize=labelsize)
	# auto save and remove white boundary
	plt.savefig(savefigname+'.png', bbox_inches='tight')
	# clear plot area
	plt.cla()


def ResponseMeasDataToFile(dict1,FileName,FileFormat='json'):
	if FileFormat.upper() == 'JSON':
		# write data to json file
		jsObj = json.dumps(dict1,indent = 4)
		with open(FileName + '.' + FileFormat, "w") as fileObj:
			fileObj.write(jsObj)
	else:
		pass


def StartMeasure(client,Vendor='OPWILL',OtdrMode=1,Lambda_nm=1550,MeasureLength_m=0,PulseWidth_ns=0,MeasureTime_s=0,nGIR=1.4670,EndThreshold=5.0,NonReflectThreshold=0,FilePath = "E:/OTDR/",FileName='TestResult.csv'):
	'''
	Vendor: vendor ID (string) default as'OPWILL'
	OtdrMode:OTDR average mode, 0(real-time) | 1(average), default as 1
	Lambda_nm: wavelength(integer), default as 1550
	MeasureLength_m: measurement range (integer), 0 for auto mode, manual setting must be larger than 500
	PulseWidth_ns: pulse width in ns (integer), 0 for auto mode
	MeasureTime_s: sampling time in s (integer) default as 0 (auto)，valid range from 1-9999
	nGIR: refractive index (float) for Lambda_nm=1550 default as 1.4670, valid range from 1.3-1.8
	EndThreshold: end point threshold (float)， default as 5, valid range 1-99
	NonReflectThreshold: non-feflective threshold in dB float), default as 0 (auto) and use 2dB internally, valid range 0.01-9.99
	'''
	FilePath = FilePath.strip()
	FilePath = FilePath.rstrip("/")
	FilePath = FilePath.rstrip("\\")
    
	tracePath = "None"

	if client == None:
		LOG.error("CLientSocketConnectToOtdr Error,Quit StartMeasure!")
		return False, tracePath
	if Vendor == 'OPWILL':
		ret = OtdrParamInit(client)
		if ret is True:
			time.sleep(2)
			
		# check OTDR current mode, exit donwload mode to OTDR mode
		Mode = getOtdrMode(client=client)
		if Mode == 1:
			LOG.error("Otdr exits measurement in download mode!")
			return False, tracePath
		status_meas	= getOtdrLD(client)
		if status_meas == 1:
			LOG.error("Otdr is under test, please wait for the end to test again!")
			return False, tracePath

		if MeasureLength_m <= 0: # 0 for auto mode
			MeasureMode = 'Auto'
			DistanceMode = 1
			Distance_m = 0
		else:
			MeasureMode = 'Manual'
			DistanceMode = 0
			if MeasureLength_m <= 500:
				MeasureLength_m = 500
			Distance_m = MeasureLength_m
		PulseWidth_ns_source = PulseWidth_ns
		if PulseWidth_ns == 0:
			PluseWidthMode = 1
			PulseWidth_ns = 0
		else:
			PluseWidthMode = 0
			if PulseWidth_ns <= 3:
				PulseWidth_ns = 3
		PulseWidth_ns_set = PulseWidth_ns

		if MeasureTime_s == 0:
			SampleTimeMode = 2 #average and auto
			SampleTime = 30
		else:
			SampleTimeMode = 1 #average time(1)/count(0)
			SampleTime = MeasureTime_s

		if EndThreshold == 0:
			EndThreshold = 5.0
		else:
			if EndThreshold < 1:
				EndThreshold = 1
			elif EndThreshold > 99:
				EndThreshold = 99
			else:
				EndThreshold = EndThreshold

		if NonReflectThreshold == 0:
			EventLossThreshold = 0.05
		else:
			EventLossThreshold = NonReflectThreshold

		EventReflectThreshold = -40.0


		setOtdrAverageMode(client = client,AvgMode = OtdrMode)
		setOtdrWaveLength(client = client,Lambda_nm = Lambda_nm)
		# set measurement parameters
		# STP
		SampleMode = 1
		if SampleMode == 0:
			strSample = 'FastMode'
		else:
			strSample = 'PrecisonMode'

		if SampleTimeMode==0:
			strSampleTime = str(SampleTime)+'c'
		elif SampleTimeMode==1:
			strSampleTime = str(SampleTime)+'s'
		elif SampleTimeMode==2:
			strSampleTime = 'auto'

		setOtdrSTP(
				client = client,
				DistanceMode = DistanceMode,
				Distance_m = Distance_m,
				PluseWidthMode = PluseWidthMode,
				PulseWidth_ns = PulseWidth_ns,
				SampleMode = SampleMode  # sampling mode 0:fast  1:precise
				)
		if OtdrMode == 1 or (OtdrMode == 0 and MeasureTime_s!=0):
			setOtdrSamplingTime(
							client = client,
							mode = SampleTimeMode,
							SampleTime = SampleTime
							)
		# IOR
		setOtdrRefractiveIndexofFiber(client = client,nGIR = nGIR)
		# set threshold parameters
		setOtdrEventLossThresholdofFiber(client = client,Threshold=EventLossThreshold)
		setOtdrEventReflectThresholdofFiber(client = client,Threshold=EventReflectThreshold)
		setOtdrEndThresholdofFiber(client = client,Threshold=EndThreshold)
		
		# create tesat data storage index
		filepath = FilePath+'/'+'AvgMode'+str(OtdrMode)+'_WL_%dnm'%Lambda_nm+'_MeasureLength_%dm'%MeasureLength_m+'_PulseWidth_%dns/'%PulseWidth_ns
		dir = os.path.dirname(filepath)
		if not os.path.exists(dir):
			os.makedirs(dir)
		# start measurement
		Time1 = time.strftime("%Y.%m.%d-%H:%M:%S", time.localtime())
		Time = time.strftime("%Y%m%d%H%M%S", time.localtime())
		csvfilename = FilePath+'/'+FileName
		
		ret_status = setOtdrLD(client = client,status=CMD_HOST_START_MEASURE)
		AVERes_list = []
		STPRes_List = []
		while 1:
			ret_Status = getOtdrStatus(client = client)
			time.sleep(0.2)
			if ret_Status == 1:
				AverageMode,AverageTimes,Count = getOtdrAverageTimes(client)
				DistanceMode_STP,Distance_m_STP,PluseWidthMode_STP,PulseWidth_ns_STP,SampleMode_STP = getOtdrSTP(client)
				# PulseWidth_ns_STP = int(PulseWidth_ns_STP)
				# AVERes_list.append((AverageMode,AverageTimes,Count))
				# STPRes_List.append((DistanceMode_STP,Distance_m_STP,PluseWidthMode_STP,int(PulseWidth_ns_STP),SampleMode_STP))
				if OtdrMode == 0:
					time.sleep(1.8)
				else:
					time.sleep(0.3)
				DataNum,DataList= getOtdrWaveData(client=client)
				# waveform data in real-time mode
				if OtdrMode == 0 and DataNum is not None:
					Time1_0 = time.strftime("%Y.%m.%d-%H:%M:%S", time.localtime())
					Time0 = time.strftime("%Y%m%d%H%M%S", time.localtime())	
					totalseconds,delta = time_delta(Time,Time0)
					print("totalseconds = ",totalseconds)
					filename_DAT = 'OTDR-2100-DAT-' + str(Time0)
					# write waveform data
					with open(filepath + filename_DAT + '.txt', "a+") as fdat:
						fdat.write("DataNum:%d\n"%DataNum)
						fdat.write("DataList:\n")
						for y in range(len(DataList)):
							fdat.write(str(DataList[y])+'\n')
					# record real-time mode parameter，reflesh ElapsedTime/DataNum
					Write_Result_to_File(
							filename = csvfilename,
							Timestamp = Time1_0,
							ElapsedTime = str(totalseconds)+'s',
							OtdrMode = OtdrMode,# average mode
							SampleMode = strSample,# sampl mode
							MeasureMode = MeasureMode,# measurement mode(Auto/Manual)
							SampleSpacing = '',# sample spacing
							MeasureLength_m = MeasureLength_m,
							PulseWidth_ns_set = PulseWidth_ns_set,
							PulseWidth_ns_parse = str(PulseWidth_ns_STP)+'ns',
							Lambda_nm = str(Lambda_nm)+'nm',
							MeasureTime_s = MeasureTime_s,
							SampleTimes = strSampleTime,
							nGIR = nGIR,
							NonReflectThreshold = EventLossThreshold,
							EndThreshold = EndThreshold,
							DataNum = DataNum,
							EventNum = '',
							EventList = '',
							TotalDistance = '',
							TotalLoss = '',
							EndLoss = '',
							TotalReflectLoss = ''
							)

					# 60s limit on real-time mode to avoid storage capacity issue
					# if totalseconds >= 60:
					# 	StopMeasure(client)
				pass
			else:
				ret_LD = getOtdrLD(client = client)
				if ret_LD == 0 and  ret_Status == 0:
					if Debug:
						LOG.debug('Test LD =0 , Finished!!!!!!!!!')
					break
		TimeEnd = time.strftime("%Y%m%d%H%M%S", time.localtime())
		totalseconds,delta = time_delta(Time,TimeEnd)
		# measurment ends, wait for statiatical result processing
		time.sleep(5)
		# get OTDR statistical result SR-4731
		fileSize,fileData,response = getOtdrFileOfSR(client=client)
		filename_GF = 'OTDR-2100-GETFILE-' + str(Time)
		filename_GFTrace = 'OTDR-2100-GETFILE-Trace-' + str(Time)

		# write data to sor file
		with open(filepath + filename_GF + '.sor', "ab+") as fsor:
			fsor.write(fileData)
		# use pyOTDR to interpret sor file from OTDR
		status, results, tracedata = sorparse(filepath + filename_GF + '.sor')
		# write result data to json document
		ResponseMeasDataToFile(dict1=results,FileName=filepath + filename_GF,FileFormat='json')
		
		# tracedata data uses matplotlib module to creast 2D trace graph
		axisX = []
		axisY = []
		tracePath = filepath + filename_GFTrace + '.txt';
		with open(filepath + filename_GFTrace + '.txt', "a+") as fgft:
			fgft.write("Tracedata Num:%d\n"%len(tracedata))
			fgft.write("Tracedata:\n")
			for y in range(len(tracedata)):
				fgft.write(tracedata[y]+'\n')
				axisX.append(float(tracedata[y].split('\t')[0]))
				axisY.append(float(tracedata[y].split('\t')[1]))
		showplt(x = axisX,y = axisY,title='Figure',xlabel='Distance(km)',ylabel='Attenuation(dB)',savefigname = filepath+'squares_plot_'+str(Time))
		
		# extract distance in km from result
		TotalDistance = 'None'
		for x in range(results["KeyEvents"]["num events"]):
			event_index = "event %d"%(x+1)
			if 'loss/drop/gain' in results["KeyEvents"][event_index]["type"] and '0E9999LS' in results["KeyEvents"][event_index]["type"]:
				TotalDistance = results["KeyEvents"][event_index]["distance"]
				break

		# result store in csv file
		Write_Result_to_File(
							filename = csvfilename,
							Timestamp = Time1,
							ElapsedTime = str(totalseconds)+'s',
							OtdrMode = OtdrMode,# average mode
							SampleMode = strSample,# sampling mode
							MeasureMode = MeasureMode,# measurment mode(Auto/Manual)
							SampleSpacing = results["FxdParams"]["sample spacing"],# sample spacing
							MeasureLength_m = MeasureLength_m,
							PulseWidth_ns_set = PulseWidth_ns_set,
							PulseWidth_ns_parse = results["FxdParams"]["pulse width"],
							Lambda_nm = results["FxdParams"]["wavelength"],
							MeasureTime_s = MeasureTime_s,
							SampleTimes = strSampleTime,
							nGIR = results["FxdParams"]["index"],
							NonReflectThreshold = results["FxdParams"]["loss thr"],
							EndThreshold = results["FxdParams"]["EOT thr"],
							DataNum = results["FxdParams"]["num data points"],
							EventNum = results["KeyEvents"]["num events"],
							EventList = results["KeyEvents"],
							TotalDistance = TotalDistance + ' km',
							TotalLoss = results["KeyEvents"]["Summary"]["total loss"],
							EndLoss = results["KeyEvents"]["Summary"]["loss end"],
							TotalReflectLoss = results["KeyEvents"]["Summary"]["ORL"]
							)
		return True, tracePath
	else:
		return False, tracePath

def StopMeasure(client):
	ret = setOtdrLD(client = client,status=CMD_HOST_STOP_MEASURE)
	if ret is True:
		if Debug:
			LOG.debug("[StopMeasure] Stop Measure Success!")


def time_delta(timestart,timeend):
	try:
		import datetime
		timeStart = datetime.datetime(int(timestart[0:4]),int(timestart[4:6]),int(timestart[6:8]),int(timestart[8:10]),int(timestart[10:12]),int(timestart[12:14]))
		timeEnd = datetime.datetime(int(timeend[0:4]),int(timeend[4:6]),int(timeend[6:8]),int(timeend[8:10]),int(timeend[10:12]),int(timeend[12:14]))
		totalseconds = int((timeEnd - timeStart).total_seconds())
		delta = str(datetime.timedelta(seconds = totalseconds))
		return totalseconds,delta
	except Exception as e:
		msg = 'Error Occurred with: ' + repr(e)
		raise Exception(msg)



if __name__=="__main__":
	server_host = '192.168.0.225'
	server_port = 8000
	date =  time.strftime("%m%d", time.localtime())

	n = 0
	Lambda_nm = 1550
	nGIR = 1.4670
	# nGIR = 1.50
	MeasureLength=[500]
	for MeasureLength_m in MeasureLength:
		if MeasureLength_m == 0:# auto mode
			PulseWidth_ns_llist = [0]
		elif MeasureLength_m == 500:# manual mode
		 	PulseWidth_ns_llist = [20000]
		# elif MeasureLength_m == 2500:
		# 	PulseWidth_ns_llist = [10,30,50,100]
		# elif MeasureLength_m == 5000:
	 	#	PulseWidth_ns_llist = [10,30,50,100,275,500]
		# elif MeasureLength_m == 15000:
		# 	PulseWidth_ns_llist = [50,100,275,500,1000]
		# elif MeasureLength_m == 40000:
		#  	PulseWidth_ns_llist = [275,500,1000,5000]
		# elif MeasureLength_m == 80000:
		#  	PulseWidth_ns_llist = [275,500,1000,5000,10000,20000]
		# elif MeasureLength_m == 120000:
		# 	PulseWidth_ns_llist = [1000,5000,10000,20000]
		# elif MeasureLength_m == 160000:
		# 	PulseWidth_ns_llist = [1000,5000,10000,20000]
		else:# semiautomatic
			PulseWidth_ns_llist = [0]

		for PulseWidth_ns in PulseWidth_ns_llist:
			for NonReflectThreshold in [0.05]:#THS
				for EndThreshold in [5.0]:#THF
					for MeasureTime_s in [15]:#pulse sequence length
						for OtdrMode in [1]:# 1-average 0-realtime
							while n < 5:
								client = CLientSocketConnectToOtdr(server_host,server_port)
								print("client =",client)
								StartMeasure(
										client = client,
										Vendor = 'OPWILL',
										OtdrMode = OtdrMode,
										Lambda_nm = Lambda_nm,
										MeasureLength_m = MeasureLength_m,
										PulseWidth_ns = PulseWidth_ns,
										MeasureTime_s = MeasureTime_s,
										nGIR = nGIR,
										EndThreshold = EndThreshold,
										NonReflectThreshold = NonReflectThreshold,
										FilePath = filebasepath + '/'+date,
										FileName = 'TestResult-avg-200m-Apc.csv'
										)

								# EventNum,FiberLength,TotalLoss,TotalReflectLoss = getOtdrMeasureResults(client)
								# print("EventNum =",EventNum)
								# print("FiberLength =",FiberLength)
								# print("TotalLoss =",TotalLoss)
								# print("TotalReflectLoss =",TotalReflectLoss)
								ret1 = CLientCloseSocketToOtdr(client)
								print("ret1 =",ret1)
								time.sleep(3)
								n += 1
							n = 0
		
	
