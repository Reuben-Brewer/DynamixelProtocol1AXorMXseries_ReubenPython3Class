# -*- coding: utf-8 -*-

'''
Reuben Brewer, Ph.D.
reuben.brewer@gmail.com
www.reubotics.com

Apache 2 License
Software Revision E, 12/26/2023

Verified working on: Python 3.8 for Windows 10/11 64-bit and Raspberry Pi Buster (no Mac testing yet).
'''

__author__ = 'reuben.brewer' #unicorn

import serial
import time

##########################################################################################################
##########################################################################################################
##########################################################################################################
if __name__ == '__main__':

    SerialObject = serial.Serial()
    SerialBaudRate = 1000000
    SerialTimeout_Rx_Seconds = 0.25
    SerialTimeout_Tx_Seconds = 0.25
    SerialParity = serial.PARITY_NONE
    SerialStopBits = serial.STOPBITS_ONE
    SerialByteSize = serial.EIGHTBITS
    SerialXonXoffSoftwareFlowControl = 0  # ABSOLUTELY MUST BE 0 FOR U2D2 (UNLIKE ROBOTEQ). IF SET TO 1, WILL HAVE PROBLEMS READING WITHOUT DISCONNECTING,
    SerialPortNameCorrespondingToCorrectSerialNumber = "default"
    MainThread_StillRunningFlag = 0
    ResetSerialConnection_EventNeedsToBeFiredFlag = 0

    SerialObject = serial.Serial("COM6",
                                SerialBaudRate,
                                timeout=SerialTimeout_Rx_Seconds,
                                write_timeout=SerialTimeout_Tx_Seconds,
                                parity=SerialParity,
                                stopbits=SerialStopBits,
                                bytesize=SerialByteSize,
                                xonxoff=SerialXonXoffSoftwareFlowControl)

    LED_OFF_ListInts = [255, 255, 0, 4, 3, 25, 0, 223]
    LED_ON_ListInts = [255, 255, 0, 4, 3, 25, 1, 222]

    ##########################################################################################################
    ##########################################################################################################
    ToggleFlag = 0
    for Counter in range(0, 11):

        ##########################################################################################################
        if ToggleFlag == 0:

            SerialObject.write(LED_OFF_ListInts) #Works in Python 2 and 3

            ### Sending individual bytes one-at-a-time DOESN'T WORK in either Python 2 or Python 3!
            #for IndividualByte in LED_OFF_ListInts:
            #    SerialObject.write(IndividualByte)
            ###

            ToggleFlag = 1
        ##########################################################################################################

        ##########################################################################################################
        else:
            SerialObject.write(LED_ON_ListInts) #Works in Python 2 and 3

            ### Sending individual bytes one-at-a-time DOESN'T WORK in either Python 2 or Python 3!
            #for IndividualByte in LED_ON_ListInts:
            #    SerialObject.write(IndividualByte)
            ###

            ToggleFlag = 0
        ##########################################################################################################

        ##########################################################################################################
        print("Toggle " + str(Counter))
        time.sleep(1.0)
        ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################

    SerialObject.close()

##########################################################################################################
##########################################################################################################
##########################################################################################################