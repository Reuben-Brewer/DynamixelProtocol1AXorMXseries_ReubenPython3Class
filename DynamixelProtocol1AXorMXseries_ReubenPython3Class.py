# -*- coding: utf-8 -*-

'''
Reuben Brewer, Ph.D.
reuben.brewer@gmail.com
www.reubotics.com

Apache 2 License
Software Revision F, 06/17/2024

Verified working on: Python 3.8 for Windows 10/11 64-bit and Raspberry Pi Buster (no Mac testing yet).
'''

__author__ = 'reuben.brewer'

##########################################
from LowPassFilter_ReubenPython2and3Class import *
##########################################

##########################################
import os
import sys
from sys import platform as _platform
import time
import datetime
import threading
import collections
from copy import * #for deepcopy
import traceback
##########################################

##########################################
from tkinter import * #Python 3
import tkinter.font as tkFont #Python 3
from tkinter import ttk
##########################################

##########################################
import platform
if platform.system() == "Windows":
    import ctypes
    winmm = ctypes.WinDLL('winmm')
    winmm.timeBeginPeriod(1) #Set minimum timer resolution to 1ms so that time.sleep(0.001) behaves properly.
##########################################

##########################################
import serial
from serial.tools import list_ports
##########################################

##########################################
global ftd2xx_IMPORTED_FLAG
ftd2xx_IMPORTED_FLAG = 0
try:
    import ftd2xx #https://pypi.org/project/ftd2xx/ 'pip install ftd2xx', current version is 1.3.1 as of 05/06/22. For SetAllFTDIdevicesLatencyTimer function
    ftd2xx_IMPORTED_FLAG = 1

except:
    exceptions = sys.exc_info()[0]
    print("**********")
    print("********** DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: ERROR, failed to import ftdtxx, Exceptions: %s" % exceptions + " ********** ")
    print("**********")
##########################################

class DynamixelProtocol1AXorMXseries_ReubenPython3Class(Frame): #Subclass the Tkinter Frame

    ##########################################################################################################
    ##########################################################################################################
    def __init__(self, setup_dict): #Subclass the Tkinter Frame

        ##########################################
        if sys.version_info[0] < 3:
            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: Error, this code can only be run on Python 3 (not 2)!")
            return
        ##########################################

        self.EXIT_PROGRAM_FLAG = 0
        self.OBJECT_CREATED_SUCCESSFULLY_FLAG = 0
        self.MainThread_still_running_flag = 0
        self.GUI_ready_to_be_updated_flag = 0

        self.SerialObject = serial.Serial()
        self.SerialConnectedFlag = 0
        self.SerialTimeout_Rx_Seconds = 0.002 #This worked at 0.25 for MX series but needed to be set very low for AX-series (0.002)
        self.SerialTimeout_Tx_Seconds = 0.25
        self.SerialParity = serial.PARITY_NONE
        self.SerialStopBits = serial.STOPBITS_ONE
        self.SerialByteSize = serial.EIGHTBITS
        self.SerialXonXoffSoftwareFlowControl = 0  #ABSOLUTELY MUST BE 0 FOR U2D2 (UNLIKE ROBOTEQ). IF SET TO 1, WILL HAVE PROBLEMS READING WITHOUT DISCONNECTING,
        self.SerialPortNameCorrespondingToCorrectSerialNumber = "default"
        self.MainThread_StillRunningFlag = 0
        self.ResetSerialConnection_EventNeedsToBeFiredFlag = 0

        self.TimeBetweenCommands = 0.001

        self.ControlType = "Position"
        self.ControlType_NEEDS_TO_BE_CHANGED_FLAG = 0
        self.ControlType_GUI_NEEDS_TO_BE_CHANGED_FLAG = 0

        self.PositionUnitsAcceptableList = ["NONE", "REV", "DEG", "RAD", "PERCENT"]
        self.SpeedUnitsAcceptableList = ["NONE", "PERCENT"]

        #########################################################
        #########################################################
        self.ErrorFlagStates_DictEnglishNameAsKey = dict([("ErrorByte", -1),
                                                            ("InputVoltageError", -1),              # Bit 0 --> Input Voltage Error. Set to 1 if the voltage is out of the operating voltage range as defined in the control table.
                                                            ("AngleLimitError", -1),                # Bit 1 --> Angle Limit Error. Set as 1 if the Goal Position is set outside of the range between CW Angle Limit and CCW Angle Limit.
                                                            ("OverheatingError", -1),               # Bit 2 --> Overheating Error. Set to 1 if the internal temperature of the Dynamixel unit is above the operating temperature range as defined in the control table.
                                                            ("RangeError", -1),                     # Bit 3 --> Range Error. Set to 1 if the instruction sent is out of the defined range.
                                                            ("ChecksumError", -1),                  # Bit 4 --> Checksum Error. Set to 1 if the checksum of the instruction packet is incorrect.
                                                            ("OverloadError", -1),                  # Bit 5 --> Overload Error. Set to 1 if the specified maximum torque can't control the applied load.
                                                            ("InstructionError", -1)])              # Bit 6 --> Instruction Error. Set to 1 if an undefined instruction is sent or an action instruction is sent without a Reg_Write instruction.

        self.ErrorFlagNames_DictBitNumberAsKey = dict([(-1, "ErrorByte"),
                                                            (0, "InputVoltageError"),           # Bit 0 --> Input Voltage Error. Set to 1 if the voltage is out of the operating voltage range as defined in the control table.
                                                            (1, "AngleLimitError"),             # Bit 1 --> Angle Limit Error. Set as 1 if the Goal Position is set outside of the range between CW Angle Limit and CCW Angle Limit.
                                                            (2, "OverheatingError"),            # Bit 2 --> Overheating Error. Set to 1 if the internal temperature of the Dynamixel unit is above the operating temperature range as defined in the control table.
                                                            (3, "RangeError"),                  # Bit 3 --> Range Error. Set to 1 if the instruction sent is out of the defined range.
                                                            (4, "ChecksumError"),               # Bit 4 --> Checksum Error. Set to 1 if the checksum of the instruction packet is incorrect.
                                                            (5, "OverloadError"),               # Bit 5 --> Overload Error. Set to 1 if the specified maximum torque can't control the applied load.
                                                            (6, "InstructionError")])           # Bit 6 --> Instruction Error. Set to 1 if an undefined instruction is sent or an action instruction is sent without a Reg_Write instruction.
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if platform.system() == "Linux":

            if "raspberrypi" in platform.uname(): #os.uname() doesn't work in windows
                self.my_platform = "pi"
            else:
                self.my_platform = "linux"

        elif platform.system() == "Windows":
            self.my_platform = "windows"

        elif platform.system() == "Darwin":
            self.my_platform = "mac"

        else:
            self.my_platform = "other"

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: The OS platform is: " + self.my_platform)
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if "GUIparametersDict" in setup_dict:
            self.GUIparametersDict = setup_dict["GUIparametersDict"]

            #########################################################
            #########################################################
            if "USE_GUI_FLAG" in self.GUIparametersDict:
                self.USE_GUI_FLAG = self.PassThrough0and1values_ExitProgramOtherwise("USE_GUI_FLAG", self.GUIparametersDict["USE_GUI_FLAG"])
            else:
                self.USE_GUI_FLAG = 0

            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: USE_GUI_FLAG: " + str(self.USE_GUI_FLAG))
            #########################################################
            #########################################################

            #########################################################
            #########################################################
            if "root" in self.GUIparametersDict:
                self.root = self.GUIparametersDict["root"]
            else:
                print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: ERROR, must pass in 'root'")
                return
            #########################################################
            #########################################################

            #########################################################
            #########################################################
            if "EnableInternal_MyPrint_Flag" in self.GUIparametersDict:
                self.EnableInternal_MyPrint_Flag = self.PassThrough0and1values_ExitProgramOtherwise("EnableInternal_MyPrint_Flag", self.GUIparametersDict["EnableInternal_MyPrint_Flag"])
            else:
                self.EnableInternal_MyPrint_Flag = 0

            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: EnableInternal_MyPrint_Flag: " + str(self.EnableInternal_MyPrint_Flag))
            #########################################################
            #########################################################

            #########################################################
            #########################################################
            if "PrintToConsoleFlag" in self.GUIparametersDict:
                self.PrintToConsoleFlag = self.PassThrough0and1values_ExitProgramOtherwise("PrintToConsoleFlag", self.GUIparametersDict["PrintToConsoleFlag"])
            else:
                self.PrintToConsoleFlag = 1

            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: PrintToConsoleFlag: " + str(self.PrintToConsoleFlag))
            #########################################################
            #########################################################

            #########################################################
            #########################################################
            if "NumberOfPrintLines" in self.GUIparametersDict:
                self.NumberOfPrintLines = int(self.PassThroughFloatValuesInRange_ExitProgramOtherwise("NumberOfPrintLines", self.GUIparametersDict["NumberOfPrintLines"], 0.0, 50.0))
            else:
                self.NumberOfPrintLines = 10

            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: NumberOfPrintLines: " + str(self.NumberOfPrintLines))
            #########################################################
            #########################################################

            #########################################################
            #########################################################
            if "UseBorderAroundThisGuiObjectFlag" in self.GUIparametersDict:
                self.UseBorderAroundThisGuiObjectFlag = self.PassThrough0and1values_ExitProgramOtherwise("UseBorderAroundThisGuiObjectFlag", self.GUIparametersDict["UseBorderAroundThisGuiObjectFlag"])
            else:
                self.UseBorderAroundThisGuiObjectFlag = 0

            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: UseBorderAroundThisGuiObjectFlag: " + str(self.UseBorderAroundThisGuiObjectFlag))
            #########################################################
            #########################################################

            #########################################################
            #########################################################
            if "GUI_ROW" in self.GUIparametersDict:
                self.GUI_ROW = int(self.PassThroughFloatValuesInRange_ExitProgramOtherwise("GUI_ROW", self.GUIparametersDict["GUI_ROW"], 0.0, 1000.0))
            else:
                self.GUI_ROW = 0

            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: GUI_ROW: " + str(self.GUI_ROW))
            #########################################################
            #########################################################

            #########################################################
            #########################################################
            if "GUI_COLUMN" in self.GUIparametersDict:
                self.GUI_COLUMN = int(self.PassThroughFloatValuesInRange_ExitProgramOtherwise("GUI_COLUMN", self.GUIparametersDict["GUI_COLUMN"], 0.0, 1000.0))
            else:
                self.GUI_COLUMN = 0

            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: GUI_COLUMN: " + str(self.GUI_COLUMN))
            #########################################################
            #########################################################

            #########################################################
            #########################################################
            if "GUI_PADX" in self.GUIparametersDict:
                self.GUI_PADX = int(self.PassThroughFloatValuesInRange_ExitProgramOtherwise("GUI_PADX", self.GUIparametersDict["GUI_PADX"], 0.0, 1000.0))
            else:
                self.GUI_PADX = 0

            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: GUI_PADX: " + str(self.GUI_PADX))
            #########################################################
            #########################################################

            #########################################################
            #########################################################
            if "GUI_PADY" in self.GUIparametersDict:
                self.GUI_PADY = int(self.PassThroughFloatValuesInRange_ExitProgramOtherwise("GUI_PADY", self.GUIparametersDict["GUI_PADY"], 0.0, 1000.0))
            else:
                self.GUI_PADY = 0

            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: GUI_PADY: " + str(self.GUI_PADY))
            #########################################################
            #########################################################

            ##########################################
            if "GUI_ROWSPAN" in self.GUIparametersDict:
                self.GUI_ROWSPAN = int(self.PassThroughFloatValuesInRange_ExitProgramOtherwise("GUI_ROWSPAN", self.GUIparametersDict["GUI_ROWSPAN"], 1.0, 1000.0))
            else:
                self.GUI_ROWSPAN = 1

            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: GUI_ROWSPAN: " + str(self.GUI_ROWSPAN))
            #########################################################
            #########################################################

            #########################################################
            #########################################################
            if "GUI_COLUMNSPAN" in self.GUIparametersDict:
                self.GUI_COLUMNSPAN = int(self.PassThroughFloatValuesInRange_ExitProgramOtherwise("GUI_COLUMNSPAN", self.GUIparametersDict["GUI_COLUMNSPAN"], 1.0, 1000.0))
            else:
                self.GUI_COLUMNSPAN = 1

            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: GUI_COLUMNSPAN: " + str(self.GUI_COLUMNSPAN))
            #########################################################
            #########################################################

            #########################################################
            #########################################################
            if "GUI_STICKY" in self.GUIparametersDict:
                self.GUI_STICKY = str(self.GUIparametersDict["GUI_STICKY"])
            else:
                self.GUI_STICKY = "w"

            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: GUI_STICKY: " + str(self.GUI_STICKY))
            #########################################################
            #########################################################

        else:
            self.GUIparametersDict = dict()
            self.USE_GUI_FLAG = 0
            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: No GUIparametersDict present, setting USE_GUI_FLAG: " + str(self.USE_GUI_FLAG))

        #print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: GUIparametersDict: " + str(self.GUIparametersDict))
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if "DesiredSerialNumber_USBtoSerialConverter" in setup_dict:
            self.DesiredSerialNumber_USBtoSerialConverter = setup_dict["DesiredSerialNumber_USBtoSerialConverter"]
            
        else:
            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: ERROR, must initialize object with 'DesiredSerialNumber_USBtoSerialConverter' argument.")
            return
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if "NameToDisplay_UserSet" in setup_dict:
            self.NameToDisplay_UserSet = setup_dict["NameToDisplay_UserSet"]
        else:
            self.NameToDisplay_UserSet = ""
            
        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: NameToDisplay_UserSet" + str(self.NameToDisplay_UserSet))
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if "SerialBaudRate" in setup_dict:
            self.SerialBaudRate = int(self.PassThroughFloatValuesInRange_ExitProgramOtherwise("SerialBaudRate", setup_dict["SerialBaudRate"], 9600, 4500000))

        else:
            self.SerialBaudRate = 1000000

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: SerialBaudRate: " + str(self.SerialBaudRate))
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if "SerialRxBufferSize" in setup_dict:
            self.SerialRxBufferSize = round(self.PassThroughFloatValuesInRange_ExitProgramOtherwise("SerialRxBufferSize", setup_dict["SerialRxBufferSize"], 0.0, 4096.0)) #Maybe 64 to 4096

        else:
            self.SerialRxBufferSize = 4096

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class: SerialRxBufferSize: " + str(self.SerialRxBufferSize))
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if "SerialTxBufferSize" in setup_dict:
            self.SerialTxBufferSize = round(self.PassThroughFloatValuesInRange_ExitProgramOtherwise("SerialTxBufferSize", setup_dict["SerialTxBufferSize"], 0.0, 4096.0)) #Maybe 64 to 4096

        else:
            self.SerialTxBufferSize = 4096

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class: SerialTxBufferSize: " + str(self.SerialTxBufferSize))
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if "ENABLE_GETS" in setup_dict:
            self.ENABLE_GETS = self.PassThrough0and1values_ExitProgramOtherwise("ENABLE_GETS", setup_dict["ENABLE_GETS"])
        else:
            self.ENABLE_GETS = 0

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: ENABLE_GETS: " + str(self.ENABLE_GETS))
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if "ENABLE_SETS" in setup_dict:
            self.ENABLE_SETS = self.PassThrough0and1values_ExitProgramOtherwise("ENABLE_SETS", setup_dict["ENABLE_SETS"])
        else:
            self.ENABLE_SETS = 0

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: ENABLE_SETS: " + str(self.ENABLE_SETS))
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if "AskForInfrequentDataReadLoopCounterLimit" in setup_dict:
            self.AskForInfrequentDataReadLoopCounterLimit = int(self.PassThroughFloatValuesInRange_ExitProgramOtherwise("AskForInfrequentDataReadLoopCounterLimit", setup_dict["AskForInfrequentDataReadLoopCounterLimit"], 0.0, 1000000))

        else:
            self.AskForInfrequentDataReadLoopCounterLimit = 200

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: AskForInfrequentDataReadLoopCounterLimit: " + str(self.AskForInfrequentDataReadLoopCounterLimit))
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if "GlobalPrintByteSequencesDebuggingFlag" in setup_dict:
            self.GlobalPrintByteSequencesDebuggingFlag = self.PassThrough0and1values_ExitProgramOtherwise("GlobalPrintByteSequencesDebuggingFlag", setup_dict["GlobalPrintByteSequencesDebuggingFlag"])
        else:
            self.GlobalPrintByteSequencesDebuggingFlag = 0

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: GlobalPrintByteSequencesDebuggingFlag: " + str(self.GlobalPrintByteSequencesDebuggingFlag))
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if "MainThread_TimeToSleepEachLoop" in setup_dict:
            self.MainThread_TimeToSleepEachLoop = self.PassThroughFloatValuesInRange_ExitProgramOtherwise("MainThread_TimeToSleepEachLoop", setup_dict["MainThread_TimeToSleepEachLoop"], 0.001, 100000)

        else:
            self.MainThread_TimeToSleepEachLoop = 0.005

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: MainThread_TimeToSleepEachLoop: " + str(self.MainThread_TimeToSleepEachLoop))
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        self.MotorType_AcceptableDict = dict([("None", dict([("MotorType_DynamixelInteger", -1)])),
                                                     ("NONE", dict([("MotorType_DynamixelInteger", -1)])),
                                                     ("AX", dict([("MotorType_DynamixelInteger", 0)])),
                                                     ("MX", dict([("MotorType_DynamixelInteger", 1)]))])

        self.MotorType_DynamixelIntegerList = []
        if "MotorType_StringList" not in setup_dict:
            self.MyPrint_WithoutLogFile("DynamixelProtocol1AXorMXseries_ReubenPython3Class ERROR: Must initialize object with 'MotorType_StringList' argument.")
            return

        else:
            self.MotorType_StringList = setup_dict["MotorType_StringList"]

            for index, MotorType_element in enumerate(self.MotorType_StringList):
                if MotorType_element not in self.MotorType_AcceptableDict:
                    self.MyPrint_WithoutLogFile("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: Error, MotorType of " + str(MotorType_element) + " is not a supported type.")
                else:
                    servo_type_dict_temp = self.MotorType_AcceptableDict[MotorType_element]
                    self.MotorType_DynamixelIntegerList.append(servo_type_dict_temp["MotorType_DynamixelInteger"])

        self.NumberOfMotors = len(setup_dict["MotorType_StringList"])

        if self.NumberOfMotors == 0:
            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: Error, 'MotorType_StringList' argument must be a list of length >= 1.")
            return
        else:
            for element in self.MotorType_DynamixelIntegerList:
                if element != self.MotorType_DynamixelIntegerList[0]:
                    print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: Error, all elements in the list 'MotorType_StringList' must be the same type")
                    return

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: NumberOfMotors: " + str(self.NumberOfMotors))
        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: MotorType_StringList: " + str(self.MotorType_StringList))
        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: MotorType_DynamixelIntegerList: " + str(self.MotorType_DynamixelIntegerList))
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if self.MotorType_StringList[0] == "AX":
            self.Position_DynamixelUnits_Max_FWlimit = 1023.0
            self.Position_DynamixelUnits_Min_FWlimit = 0.0

            self.Speed_DynamixelUnits_Max_FWlimit = 1023.0
            self.Speed_DynamixelUnits_Min_FWlimit = 0.0 #1.0

            self.ConversionFactorFromDynamixelUnitsToDegrees = 300.0/self.Position_DynamixelUnits_Max_FWlimit
            self.ConversionFactorFromDegreesToDynamixel_Units = 1.0/self.ConversionFactorFromDynamixelUnitsToDegrees

        elif self.MotorType_StringList[0] == "MX":
            self.Position_DynamixelUnits_Max_FWlimit = 4095.0
            self.Position_DynamixelUnits_Min_FWlimit = 0.0

            self.Speed_DynamixelUnits_Max_FWlimit = 1023.0 #Should this be 2047 for velocity mode?
            self.Speed_DynamixelUnits_Min_FWlimit = 0.0 #1.0

            self.ConversionFactorFromDynamixelUnitsToDegrees = 360.0/self.Position_DynamixelUnits_Max_FWlimit
            self.ConversionFactorFromDegreesToDynamixel_Units = 1.0 / self.ConversionFactorFromDynamixelUnitsToDegrees

        else:
            self.Position_DynamixelUnits_Max_FWlimit = 1023.0
            self.Position_DynamixelUnits_Min_FWlimit = 0.0

            self.Speed_DynamixelUnits_Max_FWlimit = 1023.0
            self.Speed_DynamixelUnits_Min_FWlimit = 0.0

            self.ConversionFactorFromDynamixelUnitsToDegrees = 1.0
            self.ConversionFactorFromDegreesToDynamixel_Units = 1.0 / self.ConversionFactorFromDynamixelUnitsToDegrees
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        #########################################################
        if "Position_DynamixelUnits_StartingValueList" in setup_dict:
            
            #########################################################
            #########################################################
            self.Position_DynamixelUnits_StartingValueList = []
            temp_list = setup_dict["Position_DynamixelUnits_StartingValueList"]

            if len(temp_list) != self.NumberOfMotors:
                print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: "+\
                      "Error, all input lists in setup_dict must be the same length as "+\
                      "'MotorType_StringList' (length = " +\
                      str(self.NumberOfMotors) + ").")
                return

            for element in temp_list:
                #########################################################
                element = self.PassThroughFloatValuesInRange_ExitProgramOtherwise("Position_DynamixelUnits_StartingValueList_element", element, self.Position_DynamixelUnits_Min_FWlimit, self.Position_DynamixelUnits_Max_FWlimit)

                if element != -11111.0:
                    self.Position_DynamixelUnits_StartingValueList.append(element)
                else:
                    return
                #########################################################
                
            #########################################################
            #########################################################

        else:
            self.Position_DynamixelUnits_StartingValueList = [(self.Position_DynamixelUnits_Max_FWlimit + self.Position_DynamixelUnits_Min_FWlimit)/2.0] * self.NumberOfMotors

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: Position_DynamixelUnits_StartingValueList valid: " + str(self.Position_DynamixelUnits_StartingValueList))
        #########################################################
        #########################################################
        #########################################################
        
        #########################################################
        #########################################################
        #########################################################
        if "Position_DynamixelUnits_Max_UserSet" in setup_dict:
            
            #########################################################
            #########################################################
            self.Position_DynamixelUnits_Max_UserSet = []
            temp_list = setup_dict["Position_DynamixelUnits_Max_UserSet"]

            if len(temp_list) != self.NumberOfMotors:
                print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: "+\
                      "Error, all input lists in setup_dict must be the same length as "+\
                      "'MotorType_StringList' (length = " +\
                      str(self.NumberOfMotors) + ").")
                return

            for element in temp_list:
                #########################################################
                element = self.PassThroughFloatValuesInRange_ExitProgramOtherwise("Position_DynamixelUnits_Max_UserSet_element", element, self.Position_DynamixelUnits_Min_FWlimit, self.Position_DynamixelUnits_Max_FWlimit)

                if element != -11111.0:
                    self.Position_DynamixelUnits_Max_UserSet.append(element)
                else:
                    return
                #########################################################
                
            #########################################################
            #########################################################

        else:
            self.Position_DynamixelUnits_Max_UserSet = [self.Position_DynamixelUnits_Max_FWlimit] * self.NumberOfMotors

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: Position_DynamixelUnits_Max_UserSet valid: " + str(self.Position_DynamixelUnits_Max_UserSet))
        #########################################################
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        #########################################################
        if "Position_DynamixelUnits_Min_UserSet" in setup_dict:
            
            #########################################################
            #########################################################
            self.Position_DynamixelUnits_Min_UserSet = []
            temp_list = setup_dict["Position_DynamixelUnits_Min_UserSet"]

            if len(temp_list) != self.NumberOfMotors:
                print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: "+\
                      "Error, all input lists in setup_dict must be the same length as "+\
                      "'MotorType_StringList' (length = " +\
                      str(self.NumberOfMotors) + ").")
                return

            for element in temp_list:
                #########################################################
                element = self.PassThroughFloatValuesInRange_ExitProgramOtherwise("Position_DynamixelUnits_Min_UserSet_element", element, self.Position_DynamixelUnits_Min_FWlimit, self.Position_DynamixelUnits_Max_FWlimit)

                if element != -11111.0:
                    self.Position_DynamixelUnits_Min_UserSet.append(element)
                else:
                    return
                #########################################################
                
            #########################################################
            #########################################################

        else:
            self.Position_DynamixelUnits_Min_UserSet = [self.Position_DynamixelUnits_Min_FWlimit] * self.NumberOfMotors

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: Position_DynamixelUnits_Min_UserSet valid: " + str(self.Position_DynamixelUnits_Min_UserSet))
        #########################################################
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        #########################################################
        if "Speed_DynamixelUnits_StartingValueList" in setup_dict:
            
            #########################################################
            #########################################################
            self.Speed_DynamixelUnits_StartingValueList = []
            temp_list = setup_dict["Speed_DynamixelUnits_StartingValueList"]

            if len(temp_list) != self.NumberOfMotors:
                print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: "+\
                      "Error, all input lists in setup_dict must be the same length as "+\
                      "'MotorType_StringList' (length = " +\
                      str(self.NumberOfMotors) + ").")
                return

            for element in temp_list:
                #########################################################
                element = self.PassThroughFloatValuesInRange_ExitProgramOtherwise("Speed_DynamixelUnits_StartingValueList_element", element, self.Speed_DynamixelUnits_Min_FWlimit, self.Speed_DynamixelUnits_Max_FWlimit)

                if element != -11111.0:
                    self.Speed_DynamixelUnits_StartingValueList.append(element)
                else:
                    return
                #########################################################
                
            #########################################################
            #########################################################

        else:
            self.Speed_DynamixelUnits_StartingValueList = [(self.Speed_DynamixelUnits_Max_FWlimit + self.Speed_DynamixelUnits_Min_FWlimit)/2.0] * self.NumberOfMotors

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: Speed_DynamixelUnits_StartingValueList valid: " + str(self.Speed_DynamixelUnits_StartingValueList))
        #########################################################
        #########################################################
        #########################################################
        
        #########################################################
        #########################################################
        #########################################################
        if "Speed_DynamixelUnits_Max_UserSet" in setup_dict:
            
            #########################################################
            #########################################################
            self.Speed_DynamixelUnits_Max_UserSet = []
            temp_list = setup_dict["Speed_DynamixelUnits_Max_UserSet"]

            if len(temp_list) != self.NumberOfMotors:
                print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: "+\
                      "Error, all input lists in setup_dict must be the same length as "+\
                      "'MotorType_StringList' (length = " +\
                      str(self.NumberOfMotors) + ").")
                return

            for element in temp_list:
                #########################################################
                element = self.PassThroughFloatValuesInRange_ExitProgramOtherwise("Speed_DynamixelUnits_Max_UserSet_element", element, self.Speed_DynamixelUnits_Min_FWlimit, self.Speed_DynamixelUnits_Max_FWlimit)

                if element != -11111.0:
                    self.Speed_DynamixelUnits_Max_UserSet.append(element)
                else:
                    return
                #########################################################
                
            #########################################################
            #########################################################

        else:
            self.Speed_DynamixelUnits_Max_UserSet = [self.Speed_DynamixelUnits_Max_FWlimit] * self.NumberOfMotors

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: Speed_DynamixelUnits_Max_UserSet valid: " + str(self.Speed_DynamixelUnits_Max_UserSet))
        #########################################################
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        #########################################################
        if "Speed_DynamixelUnits_Min_UserSet" in setup_dict:
            
            #########################################################
            #########################################################
            self.Speed_DynamixelUnits_Min_UserSet = []
            temp_list = setup_dict["Speed_DynamixelUnits_Min_UserSet"]

            if len(temp_list) != self.NumberOfMotors:
                print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: "+\
                      "Error, all input lists in setup_dict must be the same length as "+\
                      "'MotorType_StringList' (length = " +\
                      str(self.NumberOfMotors) + ").")
                return

            for element in temp_list:
                #########################################################
                element = self.PassThroughFloatValuesInRange_ExitProgramOtherwise("Speed_DynamixelUnits_Min_UserSet_element", element, -1.0*self.Speed_DynamixelUnits_Max_FWlimit, -1.0*self.Speed_DynamixelUnits_Min_FWlimit)

                if element != -11111.0:
                    self.Speed_DynamixelUnits_Min_UserSet.append(element)
                else:
                    return
                #########################################################
                
            #########################################################
            #########################################################

        else:
            self.Speed_DynamixelUnits_Min_UserSet = [-1.0*self.Speed_DynamixelUnits_Max_FWlimit] * self.NumberOfMotors

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: Speed_DynamixelUnits_Min_UserSet valid: " + str(self.Speed_DynamixelUnits_Min_UserSet))
        #########################################################
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        #########################################################
        if "MaxTorque_DynamixelUnits_StartingValueList" in setup_dict:
            
            #########################################################
            #########################################################
            self.MaxTorque_DynamixelUnits_StartingValueList = []
            temp_list = setup_dict["MaxTorque_DynamixelUnits_StartingValueList"]

            if len(temp_list) != self.NumberOfMotors:
                print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: "+\
                      "Error, all input lists in setup_dict must be the same length as "+\
                      "'MotorType_StringList' (length = " +\
                      str(self.NumberOfMotors) + ").")
                return

            for element in temp_list:
                #########################################################
                element = self.PassThroughFloatValuesInRange_ExitProgramOtherwise("MaxTorque_DynamixelUnits_StartingValueList_element", element, 0.0, 1023.0)

                if element != -11111.0:
                    self.MaxTorque_DynamixelUnits_StartingValueList.append(element)
                else:
                    return
                #########################################################
                
            #########################################################
            #########################################################

        else:
            self.MaxTorque_DynamixelUnits_StartingValueList = [1023.0] * self.NumberOfMotors

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: MaxTorque_DynamixelUnits_StartingValueList valid: " + str(self.MaxTorque_DynamixelUnits_StartingValueList))
        #########################################################
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        #########################################################
        if "CWlimit_StartingValueList" in setup_dict:
            
            #########################################################
            #########################################################
            self.CWlimit_StartingValueList = []
            temp_list = setup_dict["CWlimit_StartingValueList"]

            if len(temp_list) != self.NumberOfMotors:
                print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: "+\
                      "Error, all input lists in setup_dict must be the same length as "+\
                      "'MotorType_StringList' (length = " +\
                      str(self.NumberOfMotors) + ").")
                return

            for element in temp_list:
                #########################################################
                element = self.PassThroughFloatValuesInRange_ExitProgramOtherwise("CWlimit_StartingValueList_element", element, self.Position_DynamixelUnits_Min_FWlimit, self.Position_DynamixelUnits_Max_FWlimit)

                if element != -11111.0:
                    self.CWlimit_StartingValueList.append(element)
                else:
                    return
                #########################################################
                
            #########################################################
            #########################################################

        else:
            self.CWlimit_StartingValueList = [self.Position_DynamixelUnits_Min_FWlimit] * self.NumberOfMotors

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: CWlimit_StartingValueList valid: " + str(self.CWlimit_StartingValueList))
        #########################################################
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        #########################################################
        if "CCWlimit_StartingValueList" in setup_dict:
            
            #########################################################
            #########################################################
            self.CCWlimit_StartingValueList = []
            temp_list = setup_dict["CCWlimit_StartingValueList"]

            if len(temp_list) != self.NumberOfMotors:
                print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: "+\
                      "Error, all input lists in setup_dict must be the same length as "+\
                      "'MotorType_StringList' (length = " +\
                      str(self.NumberOfMotors) + ").")
                return

            for element in temp_list:
                #########################################################
                element = self.PassThroughFloatValuesInRange_ExitProgramOtherwise("CCWlimit_StartingValueList_element", element, self.Position_DynamixelUnits_Min_FWlimit, self.Position_DynamixelUnits_Max_FWlimit)

                if element != -11111.0:
                    self.CCWlimit_StartingValueList.append(element)
                else:
                    return
                #########################################################
                
            #########################################################
            #########################################################

        else:
            self.CCWlimit_StartingValueList = [self.Position_DynamixelUnits_Max_FWlimit] * self.NumberOfMotors

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: CCWlimit_StartingValueList valid: " + str(self.CCWlimit_StartingValueList))
        #########################################################
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        #########################################################
        if "ContinuousRotationState_StartingValueList" in setup_dict:

            #########################################################
            #########################################################
            self.ContinuousRotationState_StartingValueList = []
            temp_list = setup_dict["ContinuousRotationState_StartingValueList"]

            if len(temp_list) != self.NumberOfMotors:
                print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: "+\
                      "Error, all input lists in setup_dict must be the same length as "+\
                      "'MotorType_StringList' (length = " +\
                      str(self.NumberOfMotors) + ").")
                return

            for element in temp_list:
                
                #########################################################
                element = self.PassThrough0and1values_ExitProgramOtherwise("ContinuousRotationState_StartingValueList_element", element)
                if element != -1:
                    self.ContinuousRotationState_StartingValueList.append(element)
                else:
                    return
                #########################################################

            #########################################################
            #########################################################

        else:
            #########################################################
            #########################################################
            self.ContinuousRotationState_StartingValueList = [0] * self.NumberOfMotors
            #########################################################
            #########################################################

        print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: ContinuousRotationState_StartingValueList valid: " + str(self.ContinuousRotationState_StartingValueList))
        #########################################################
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        try:
            self.DataStreamingFrequency_CalculatedFromMainThread_LowPassFilter_ReubenPython2and3ClassObject = LowPassFilter_ReubenPython2and3Class(dict([("UseMedianFilterFlag", 1),
                                                                                                            ("UseExponentialSmoothingFilterFlag", 1),
                                                                                                            ("ExponentialSmoothingFilterLambda", 0.05)])) #new_filtered_value = k * raw_sensor_value + (1 - k) * old_filtered_value

        except:
            exceptions = sys.exc_info()[0]
            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: DataStreamingFrequency_CalculatedFromMainThread_LowPassFilter_ReubenPython2and3ClassObject, Exceptions: %s" % exceptions)
            traceback.print_exc()
            return
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        self.PrintToGui_Label_TextInputHistory_List = [" "]*self.NumberOfPrintLines
        self.PrintToGui_Label_TextInput_Str = ""
        self.GUI_ready_to_be_updated_flag = 0
        #########################################################
        #########################################################

        self.Position_DynamixelUnits = self.Position_DynamixelUnits_StartingValueList
        self.Position_DynamixelUnits_TO_BE_SET = self.Position_DynamixelUnits_StartingValueList
        self.PositionReceived_DynamixelUnits = [-11111.0] * self.NumberOfMotors

        self.PositionReceived_Degrees = [-11111.0] * self.NumberOfMotors
        self.SpeedReceived_DegreesPerSecond = [-11111.0] * self.NumberOfMotors

        self.Position_DynamixelUnits_NeedsToBeChangedFlag = [0] * self.NumberOfMotors
        self.Position_DynamixelUnits_GUI_NeedsToBeChangedFlag = [0] * self.NumberOfMotors
        self.MotionDirectionCommandedByExternalProgram = [-1] * self.NumberOfMotors

        self.Speed_DynamixelUnits = self.Speed_DynamixelUnits_StartingValueList
        self.Speed_DynamixelUnits_TO_BE_SET = self.Speed_DynamixelUnits_StartingValueList
        self.SpeedReceived_DynamixelUnits = [-1] * self.NumberOfMotors
        self.Speed_DynamixelUnits_NeedsToBeChangedFlag = [0] * self.NumberOfMotors
        self.Speed_DynamixelUnits_GUI_NeedsToBeChangedFlag = [0] * self.NumberOfMotors

        #self.MaxTorque_DynamixelUnits_max = [1023.0] * self.NumberOfMotors
        #self.MaxTorque_DynamixelUnits_min = [0.0] * self.NumberOfMotors
        self.MaxTorque_DynamixelUnits = self.MaxTorque_DynamixelUnits_StartingValueList
        self.MaxTorque_DynamixelUnits_TO_BE_SET = self.MaxTorque_DynamixelUnits_StartingValueList
        self.MaxTorque_DynamixelUnits = [-1] * self.NumberOfMotors
        self.MaxTorque_DynamixelUnits_NeedsToBeChangedFlag = [0] * self.NumberOfMotors
        self.MaxTorque_DynamixelUnits_GUI_NeedsToBeChangedFlag = [0] * self.NumberOfMotors

        #self.CWlimit_max = [1023.0] * self.NumberOfMotors
        #self.CWlimit_min = [0.0] * self.NumberOfMotors
        self.CWlimit = self.CWlimit_StartingValueList
        self.CWlimit_TO_BE_SET = self.CWlimit_StartingValueList
        #self.CWlimitReceived = [-1] * self.NumberOfMotors
        self.CWlimit_NeedsToBeChangedFlag = [0] * self.NumberOfMotors
        self.CWlimit_GUI_NeedsToBeChangedFlag = [0] * self.NumberOfMotors

        #self.CCWlimit_max = [1023.0] * self.NumberOfMotors
        #self.CCWlimit_min = [0.0] * self.NumberOfMotors
        self.CCWlimit = self.CCWlimit_StartingValueList
        self.CCWlimit_TO_BE_SET = self.CCWlimit_StartingValueList
        #self.CCWlimitReceived = [-1] * self.NumberOfMotors
        self.CCWlimit_NeedsToBeChangedFlag = [0] * self.NumberOfMotors
        self.CCWlimit_GUI_NeedsToBeChangedFlag = [0] * self.NumberOfMotors

        self.TorqueReceived_DynamixelUnits = [-1] * self.NumberOfMotors
        self.VoltageReceived_Volts = [-1] * self.NumberOfMotors
        self.TemperatureReceived_DegC = [-1] * self.NumberOfMotors
        self.MovingStateReceived_DynamixelUnits = [-1] * self.NumberOfMotors

        self.ModelNumber_Received = [-1] * self.NumberOfMotors
        self.FWversion_Received = [-1] * self.NumberOfMotors
        self.ID_Received = [-1] * self.NumberOfMotors
        self.ReturnDelayTimeMicroSeconds_Received = [-1] * self.NumberOfMotors
        self.TemperatureHighestLimit_Received = [-1] * self.NumberOfMotors
        self.VoltageLowestLimit_Received = [-1] * self.NumberOfMotors
        self.VoltageHighestLimit_Received = [-1] * self.NumberOfMotors
        self.CWangleLimit_Received = [-1] * self.NumberOfMotors
        self.CCWangleLimit_Received = [-1] * self.NumberOfMotors
        self.GoalPositionReceived_DynamixelUnits = [-1] * self.NumberOfMotors
        self.GoalPositionReceived_Degrees = [-1] * self.NumberOfMotors

        self.AskForInfrequentDataReadLoopCounter = 0

        self.EngagedState = [1]*self.NumberOfMotors #TO BE SET LATER. DEFINED HERE TO PREVENT GUI THREAD CREATION ERRORS.
        self.EngagedState_TO_BE_SET = [1]*self.NumberOfMotors
        self.EngagedState_NeedsToBeChangedFlag = [0]*self.NumberOfMotors
        self.EngagedState_GUI_NeedsToBeChangedFlag = [0]*self.NumberOfMotors
        self.StoppedState = [-1]*self.NumberOfMotors

        self.LEDstate = [1]*self.NumberOfMotors #TO BE SET LATER. DEFINED HERE TO PREVENT GUI THREAD CREATION ERRORS.
        self.LEDstate_TO_BE_SET = [1]*self.NumberOfMotors
        self.LEDstate_NeedsToBeChangedFlag = [0]*self.NumberOfMotors
        self.LEDstate_GUI_NeedsToBeChangedFlag = [0]*self.NumberOfMotors

        self.ContinuousRotationState = self.ContinuousRotationState_StartingValueList
        self.ContinuousRotationState_TO_BE_SET = self.ContinuousRotationState_StartingValueList
        self.ContinuousRotationState_NeedsToBeChangedFlag = [0]*self.NumberOfMotors
        self.ContinuousRotationState_GUI_NeedsToBeChangedFlag = [0]*self.NumberOfMotors

        self.CurrentTime_CalculatedFromMainThread = -111111111111111
        self.LastTime_CalculatedFromMainThread = -111111111111111
        self.DataStreamingFrequency_CalculatedFromMainThread = -1 #THE MAX THAT WE EVER SAW WITH THE CALLBACK FUNCTIONS WAS 125HZ
        self.DataStreamingDeltaT_CalculatedFromMainThread = -1
        self.DataStreamingLoopCounter_CalculatedFromMainThread = 0

        self.MostRecentDataDict = dict()

        self.LEDalarm_InstructionBad_Enabled = 0
        self.LEDalarm_Overload_Enabled = 0
        self.LEDalarm_Checksum_Enabled = 0
        self.LEDalarm_InstructionOutOfRange_Enabled = 0
        self.LEDalarm_Overheating_Enabled = 0
        self.LEDalarm_AngleLimit_Enabled = 1
        self.LEDalarm_InputVoltage_Enabled = 0

        self.LEDalarmSettingsBYTE = 0
        if self.LEDalarm_InstructionBad_Enabled == 1:
            self.LEDalarmSettingsBYTE = self.LEDalarmSettingsBYTE | 0b01000000 #Bit 6 --> Instruction Error. Set to 1 if an undefined instruction is sent or an action instruction is sent without a Reg_Write instruction.
        if self.LEDalarm_Overload_Enabled == 1:
            self.LEDalarmSettingsBYTE = self.LEDalarmSettingsBYTE | 0b00100000 #Bit 5 --> Overload Error. Set to 1 if the specified maximum torque can't control the applied load.
        if self.LEDalarm_Checksum_Enabled == 1:
            self.LEDalarmSettingsBYTE = self.LEDalarmSettingsBYTE | 0b00010000   #Bit 4 --> Checksum Error. Set to 1 if the checksum of the instruction packet is incorrect.
        if self.LEDalarm_InstructionOutOfRange_Enabled == 1:
            self.LEDalarmSettingsBYTE = self.LEDalarmSettingsBYTE | 0b00001000 #Bit 3 --> Range Error. Set to 1 if the instruction sent is out of the defined range.
        if self.LEDalarm_Overheating_Enabled == 1:
            self.LEDalarmSettingsBYTE = self.LEDalarmSettingsBYTE | 0b00000100 #Bit 2 --> Overheating Error. Set to 1 if the internal temperature of the Dynamixel unit is above the operating temperature range as defined in the control table.
        if self.LEDalarm_AngleLimit_Enabled == 1:
            self.LEDalarmSettingsBYTE = self.LEDalarmSettingsBYTE | 0b00000010 #Bit 1 --> Angle Limit Error. Set as 1 if the Goal Position is set outside of the range between CW Angle Limit and CCW Angle Limit.
        if self.LEDalarm_InputVoltage_Enabled == 1:
            self.LEDalarmSettingsBYTE = self.LEDalarmSettingsBYTE | 0b00000001 #Bit 0 --> Input Voltage Error. Set to 1 if the voltage is out of the operating voltage range as defined in the control table.

        self.MyPrint_WithoutLogFile("LEDalarmSettingsBYTE: " + str(self.LEDalarmSettingsBYTE))

        #########################################################
        #########################################################

        #########################################################
        #########################################################
        try:

            #########################################################
            if ftd2xx_IMPORTED_FLAG == 1:
                self.SetAllFTDIdevicesLatencyTimer()
            #########################################################

            #########################################################
            self.FindAssignAndOpenSerialPort()
            #########################################################

            #########################################################
            if self.SerialConnectedFlag != 1:
                return
            #########################################################

        except:
            exceptions = sys.exc_info()[0]
            print("DynamixelProtocol1AXorMXseries_ReubenPython3Class __init__: Exceptions: %s" % exceptions)
            traceback.print_exc()
            return
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        self.MainThread_ThreadingObject = threading.Thread(target=self.MainThread, args=())
        self.MainThread_ThreadingObject.start()
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        if self.USE_GUI_FLAG == 1:
            self.StartGUI(self.root)
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        time.sleep(0.25)
        #########################################################
        #########################################################

        #########################################################
        #########################################################
        self.OBJECT_CREATED_SUCCESSFULLY_FLAG = 1
        #########################################################
        #########################################################

    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def __del__(self):
        pass
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    def PassThrough0and1values_ExitProgramOtherwise(self, InputNameString, InputNumber, ExitProgramIfFailureFlag = 0):

        ##########################################################################################################
        ##########################################################################################################
        try:

            ##########################################################################################################
            InputNumber_ConvertedToFloat = float(InputNumber)
            ##########################################################################################################

        except:

            ##########################################################################################################
            exceptions = sys.exc_info()[0]
            print("PassThrough0and1values_ExitProgramOtherwise Error. InputNumber must be a numerical value, Exceptions: %s" % exceptions)

            ##########################
            if ExitProgramIfFailureFlag == 1:
                sys.exit()
            else:
                return -1
            ##########################

            ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        try:

            ##########################################################################################################
            if InputNumber_ConvertedToFloat == 0.0 or InputNumber_ConvertedToFloat == 1.0:
                return InputNumber_ConvertedToFloat

            else:

                print("PassThrough0and1values_ExitProgramOtherwise Error. '" +
                              str(InputNameString) +
                              "' must be 0 or 1 (value was " +
                              str(InputNumber_ConvertedToFloat) +
                              "). Press any key (and enter) to exit.")

                ##########################
                if ExitProgramIfFailureFlag == 1:
                    sys.exit()

                else:
                    return -1
                ##########################

            ##########################################################################################################

        except:

            ##########################################################################################################
            exceptions = sys.exc_info()[0]
            print("PassThrough0and1values_ExitProgramOtherwise Error, Exceptions: %s" % exceptions)

            ##########################
            if ExitProgramIfFailureFlag == 1:
                sys.exit()
            else:
                return -1
            ##########################

            ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    def PassThroughFloatValuesInRange_ExitProgramOtherwise(self, InputNameString, InputNumber, RangeMinValue, RangeMaxValue, ExitProgramIfFailureFlag = 0):

        ##########################################################################################################
        ##########################################################################################################
        try:
            ##########################################################################################################
            InputNumber_ConvertedToFloat = float(InputNumber)
            ##########################################################################################################

        except:
            ##########################################################################################################
            exceptions = sys.exc_info()[0]
            print("PassThroughFloatValuesInRange_ExitProgramOtherwise Error. InputNumber must be a float value, Exceptions: %s" % exceptions)

            ##########################
            if ExitProgramIfFailureFlag == 1:
                sys.exit()
            else:
                return -11111.0
            ##########################

            ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        try:

            ##########################################################################################################
            InputNumber_ConvertedToFloat_Limited = self.LimitNumber_FloatOutputOnly(RangeMinValue, RangeMaxValue, InputNumber_ConvertedToFloat)

            if InputNumber_ConvertedToFloat_Limited != InputNumber_ConvertedToFloat:
                print("PassThroughFloatValuesInRange_ExitProgramOtherwise Error. '" +
                      str(InputNameString) +
                      "' must be in the range [" +
                      str(RangeMinValue) +
                      ", " +
                      str(RangeMaxValue) +
                      "] (value was " +
                      str(InputNumber_ConvertedToFloat) + ")")

                ##########################
                if ExitProgramIfFailureFlag == 1:
                    sys.exit()
                else:
                    return -11111.0
                ##########################

            else:
                return InputNumber_ConvertedToFloat_Limited
            ##########################################################################################################

        except:
            ##########################################################################################################
            exceptions = sys.exc_info()[0]
            print("PassThroughFloatValuesInRange_ExitProgramOtherwise Error, Exceptions: %s" % exceptions)

            ##########################
            if ExitProgramIfFailureFlag == 1:
                sys.exit()
            else:
                return -11111.0
            ##########################

            ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def LimitNumber_IntOutputOnly(self, min_val, max_val, test_val):
        if test_val > max_val:
            test_val = max_val

        elif test_val < min_val:
            test_val = min_val

        else:
            test_val = test_val

        test_val = int(test_val)

        return test_val
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def LimitNumber_FloatOutputOnly(self, min_val, max_val, test_val):
        if test_val > max_val:
            test_val = max_val

        elif test_val < min_val:
            test_val = min_val

        else:
            test_val = test_val

        test_val = float(test_val)

        return test_val
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def LimitTextEntryInput(self, min_val, max_val, test_val, TextEntryObject):

        try:
            test_val = float(test_val)  # MUST HAVE THIS LINE TO CATCH STRINGS PASSED INTO THE FUNCTION

            if test_val > max_val:
                test_val = max_val
            elif test_val < min_val:
                test_val = min_val
            else:
                test_val = test_val

        except:
            pass

        try:
            if TextEntryObject != "":
                if isinstance(TextEntryObject, list) == 1:  # Check if the input 'TextEntryObject' is a list or not
                    TextEntryObject[0].set(str(test_val))  # Reset the text, overwriting the bad value that was entered.
                else:
                    TextEntryObject.set(str(test_val))  # Reset the text, overwriting the bad value that was entered.
        except:
            pass

        return test_val
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SetAllFTDIdevicesLatencyTimer(self, FTDI_LatencyTimer_ToBeSet = 1):

        FTDI_LatencyTimer_ToBeSet = self.LimitNumber_IntOutputOnly(1, 16, FTDI_LatencyTimer_ToBeSet)

        FTDI_DeviceList = ftd2xx.listDevices()
        print("FTDI_DeviceList: " + str(FTDI_DeviceList))

        if FTDI_DeviceList != None:

            for Index, FTDI_SerialNumber in enumerate(FTDI_DeviceList):

                #################################
                try:
                    if sys.version_info[0] < 3: #Python 2
                        FTDI_SerialNumber = str(FTDI_SerialNumber)
                    else:
                        FTDI_SerialNumber = FTDI_SerialNumber.decode('utf-8')

                    FTDI_Object = ftd2xx.open(Index)
                    FTDI_DeviceInfo = FTDI_Object.getDeviceInfo()

                    '''
                    print("FTDI device with serial number " +
                          str(FTDI_SerialNumber) +
                          ", DeviceInfo: " +
                          str(FTDI_DeviceInfo))
                    '''

                except:
                    exceptions = sys.exc_info()[0]
                    print("FTDI device with serial number " + str(FTDI_SerialNumber) + ", could not open FTDI device, Exceptions: %s" % exceptions)
                #################################

                #################################
                try:
                    FTDI_Object.setLatencyTimer(FTDI_LatencyTimer_ToBeSet)
                    time.sleep(0.005)

                    FTDI_LatencyTimer_ReceivedFromDevice = FTDI_Object.getLatencyTimer()
                    FTDI_Object.close()

                    if FTDI_LatencyTimer_ReceivedFromDevice == FTDI_LatencyTimer_ToBeSet:
                        SuccessString = "succeeded!"
                    else:
                        SuccessString = "failed!"

                    print("FTDI device with serial number " +
                          str(FTDI_SerialNumber) +
                          " commanded setLatencyTimer(" +
                          str(FTDI_LatencyTimer_ToBeSet) +
                          "), and getLatencyTimer() returned: " +
                          str(FTDI_LatencyTimer_ReceivedFromDevice) +
                          ", so command " +
                          SuccessString)

                except:
                    exceptions = sys.exc_info()[0]
                    print("FTDI device with serial number " + str(FTDI_SerialNumber) + ", could not set/get Latency Timer, Exceptions: %s" % exceptions)
                #################################

        else:
            print("SetAllFTDIdevicesLatencyTimer ERROR: FTDI_DeviceList is empty, cannot proceed.")
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def FindAssignAndOpenSerialPort(self):
        self.MyPrint_WithoutLogFile("FindAssignAndOpenSerialPort: Finding all serial ports...")

        ##############
        SerialNumberToCheckAgainst = str(self.DesiredSerialNumber_USBtoSerialConverter)
        if self.my_platform == "linux" or self.my_platform == "pi":
            SerialNumberToCheckAgainst = SerialNumberToCheckAgainst[:-1] #The serial number gets truncated by one digit in linux
        else:
            SerialNumberToCheckAgainst = SerialNumberToCheckAgainst
        ##############

        ##############
        SerialPortsAvailable_ListPortInfoObjetsList = serial.tools.list_ports.comports()
        ##############

        ###########################################################################
        SerialNumberFoundFlag = 0
        for SerialPort_ListPortInfoObjet in SerialPortsAvailable_ListPortInfoObjetsList:

            SerialPortName = SerialPort_ListPortInfoObjet[0]
            Description = SerialPort_ListPortInfoObjet[1]
            VID_PID_SerialNumber_Info = SerialPort_ListPortInfoObjet[2]
            self.MyPrint_WithoutLogFile(SerialPortName + ", " + Description + ", " + VID_PID_SerialNumber_Info)

            if VID_PID_SerialNumber_Info.find(SerialNumberToCheckAgainst) != -1 and SerialNumberFoundFlag == 0: #Haven't found a match in a prior loop
                self.SerialPortNameCorrespondingToCorrectSerialNumber = SerialPortName
                SerialNumberFoundFlag = 1 #To ensure that we only get one device
                self.MyPrint_WithoutLogFile("FindAssignAndOpenSerialPort: Found serial number " + SerialNumberToCheckAgainst + " on port " + self.SerialPortNameCorrespondingToCorrectSerialNumber)
                #WE DON'T BREAK AT THIS POINT BECAUSE WE WANT TO PRINT ALL SERIAL DEVICE NUMBERS WHEN PLUGGING IN A DEVICE WITH UNKNOWN SERIAL NUMBE RFOR THE FIRST TIME.
        ###########################################################################

        ###########################################################################
        if(self.SerialPortNameCorrespondingToCorrectSerialNumber != "default"): #We found a match

            try: #Will succeed as long as another program hasn't already opened the serial line.

                self.SerialObject = serial.Serial(self.SerialPortNameCorrespondingToCorrectSerialNumber,
                                                  self.SerialBaudRate,
                                                  timeout=self.SerialTimeout_Rx_Seconds,
                                                  write_timeout=self.SerialTimeout_Tx_Seconds,
                                                  parity=self.SerialParity,
                                                  stopbits=self.SerialStopBits,
                                                  bytesize=self.SerialByteSize,
                                                  xonxoff=self.SerialXonXoffSoftwareFlowControl)

                try:
                    if self.my_platform == "windows":
                        #pass
                        self.SerialObject.set_buffer_size(rx_size=self.SerialRxBufferSize, tx_size=self.SerialTxBufferSize)
                except:
                    self.SerialConnectedFlag = 0
                    exceptions = sys.exc_info()[0]
                    self.MyPrint_WithoutLogFile("FindAssignAndOpenSerialPort, 'set_buffer_size' call failed, exception: %s" % exceptions)

                self.SerialObject.flushInput()
                self.SerialObject.flushOutput()

                self.SerialConnectedFlag = 1
                self.MyPrint_WithoutLogFile("FindAssignAndOpenSerialPort: Serial is connected and open on port: " + self.SerialPortNameCorrespondingToCorrectSerialNumber)

            except:
                self.SerialConnectedFlag = 0
                print("FindAssignAndOpenSerialPort: ERROR: Serial is physically plugged in but IS IN USE BY ANOTHER PROGRAM.")
                exceptions = sys.exc_info()[0]
                print("FindAssignAndOpenSerialPort, exception: %s" % exceptions)
        else:
            self.SerialConnectedFlag = -1
            self.MyPrint_WithoutLogFile("FindAssignAndOpenSerialPort: ERROR: Could not find the serial device. IS IT PHYSICALLY PLUGGED IN?")
        ###########################################################################

    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def ResetSerialConnection(self):

        try:
            self.SerialObject.reset_input_buffer()
            self.SerialObject.reset_output_buffer()
            self.SerialObject.close()
            self.SerialConnectedFlag = 0

            self.SerialObject = serial.Serial(self.SerialPortNameCorrespondingToCorrectSerialNumber,
                                              self.SerialBaudRate,
                                              timeout=self.SerialTimeout_Rx_Seconds,
                                              write_timeout=self.SerialTimeout_Tx_Seconds,
                                              parity=self.SerialParity,
                                              stopbits=self.SerialStopBits,
                                              bytesize=self.SerialByteSize,
                                              xonxoff=self.SerialXonXoffSoftwareFlowControl)

            if self.my_platform == "windows":
                self.SerialObject.set_buffer_size(rx_size=self.SerialRxBufferSize, tx_size=self.SerialTxBufferSize)

            self.SerialConnectedFlag = 1

            print("########## ResetSerialConnection EVENT FIRED! ##########")

        except:
            self.SerialConnectedFlag = 0
            exceptions = sys.exc_info()[0]
            self.MyPrint_WithoutLogFile("ResetSerialConnection, exception: %s" % exceptions)

    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def CloseSerialPort(self):

        if self.SerialConnectedFlag == 1:
            self.SerialObject.close()
            self.MyPrint_WithoutLogFile("Closed serial connection.")
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def ConvertByteAarrayObjectToIntsList(self, Input_ByteArrayObject):

        if type(Input_ByteArrayObject) != bytes:
            print("ConvertByteAarrayObjectToIntsList ERROR, Input_ByteArrayObject must be type 'bytes', not the current type '" + str(type(Input_ByteArrayObject)) + "' and value " + str(Input_ByteArrayObject))
            return list()

        else:
            Output_IntsList = list()
            for element in Input_ByteArrayObject:
                Output_IntsList.append(int(element))

            return Output_IntsList
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def getPreciseSecondsTimeStampString(self):
        ts = time.time()

        return ts
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def GetMostRecentDataDict(self):

        if self.EXIT_PROGRAM_FLAG == 0:

            return deepcopy(self.MostRecentDataDict) #deepcopy IS required as MostRecentDataDict contains lists.

        else:
            return dict()  # So that we're not returning variables during the close-down process.
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SetPosition_FROM_EXTERNAL_PROGRAM(self, MotorIndex, PositionFromExternalProgram, Units = "None"):
        Units = Units.upper()

        if Units not in self.PositionUnitsAcceptableList:
            self.MyPrint_WithoutLogFile("SetPosition_FROM_EXTERNAL_PROGRAM ERROR: units of " + Units + " is not in the acceptable list of " + str(self.PositionUnitsAcceptableList))
            return 0

        PositionFromExternalProgram_ConvertedToDeg = 0
        PositionFromExternalProgram_DynamixelUnits_unlimited = 0

        if Units == "NONE":
            PositionFromExternalProgram_ConvertedToDeg = PositionFromExternalProgram
        elif Units == "DEG":
            PositionFromExternalProgram_ConvertedToDeg = PositionFromExternalProgram
        elif Units == "REV":
            PositionFromExternalProgram_ConvertedToDeg = PositionFromExternalProgram*360.0
        elif Units == "RAD":
            PositionFromExternalProgram_ConvertedToDeg = PositionFromExternalProgram*360.0/(2*math.pi)

        PositionFromExternalProgram_DynamixelUnits_unlimited = PositionFromExternalProgram_ConvertedToDeg*self.ConversionFactorFromDegreesToDynamixel_Units

        if Units == "PERCENT":
            PositionFromExternalProgram = self.LimitNumber_FloatOutputOnly(0.0, 100.0, PositionFromExternalProgram) #To limit the input to [0,100]%
            PositionFromExternalProgram_DynamixelUnits_unlimited = ((self.Position_DynamixelUnits_Max_UserSet[MotorIndex] - self.Position_DynamixelUnits_Min_UserSet[MotorIndex])/100.0)*PositionFromExternalProgram + self.Position_DynamixelUnits_Min_UserSet[MotorIndex]

        self.Position_DynamixelUnits_TO_BE_SET[MotorIndex] = self.LimitNumber_FloatOutputOnly(self.Position_DynamixelUnits_Min_UserSet[MotorIndex], self.Position_DynamixelUnits_Max_UserSet[MotorIndex], PositionFromExternalProgram_DynamixelUnits_unlimited)
        self.Position_DynamixelUnits_NeedsToBeChangedFlag[MotorIndex] = 1
        self.Position_DynamixelUnits_GUI_NeedsToBeChangedFlag[MotorIndex] = 1

        return 1
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SetPosition_FROM_INTERNAL_PROGRAM(self, MotorIndex, PositionFromExternalProgram, Units = "None"):
        Units = Units.upper()

        if Units not in self.PositionUnitsAcceptableList:
            self.MyPrint_WithoutLogFile("SetPosition_FROM_EXTERNAL_PROGRAM ERROR: units of " + Units + " is not in the acceptable list of " + str(self.PositionUnitsAcceptableList))
            return 0

        PositionFromExternalProgram_ConvertedToDeg = 0
        PositionFromExternalProgram_unlimited = 0

        if Units == "NONE":
            PositionFromExternalProgram_ConvertedToDeg = PositionFromExternalProgram
        elif Units == "DEG":
            PositionFromExternalProgram_ConvertedToDeg = PositionFromExternalProgram
        elif Units == "REV":
            PositionFromExternalProgram_ConvertedToDeg = PositionFromExternalProgram*360.0
        elif Units == "RAD":
            PositionFromExternalProgram_ConvertedToDeg = PositionFromExternalProgram*360.0/(2*math.pi)

        PositionFromExternalProgram_unlimited = PositionFromExternalProgram_ConvertedToDeg

        if Units == "PERCENT":
            PositionFromExternalProgram = self.LimitNumber_FloatOutputOnly(0.0, 100.0, PositionFromExternalProgram) #To limit the input to [0,100]%
            PositionFromExternalProgram_unlimited = ((self.Position_DynamixelUnits_Max_UserSet[MotorIndex] - self.Position_DynamixelUnits_Min_UserSet[MotorIndex])/100.0)*PositionFromExternalProgram + self.Position_DynamixelUnits_Min_UserSet[MotorIndex]

        self.Position_DynamixelUnits_TO_BE_SET[MotorIndex] = self.LimitNumber_FloatOutputOnly(self.Position_DynamixelUnits_Min_UserSet[MotorIndex], self.Position_DynamixelUnits_Max_UserSet[MotorIndex], PositionFromExternalProgram_unlimited)
        self.Position_DynamixelUnits_NeedsToBeChangedFlag[MotorIndex] = 1
        self.Position_DynamixelUnits_GUI_NeedsToBeChangedFlag[MotorIndex] = 1

        return 1
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SetSpeed_FROM_EXTERNAL_PROGRAM(self, MotorIndex, SpeedFromExternalProgram, Units = "None"):
        Units = Units.upper()

        if Units not in self.SpeedUnitsAcceptableList:
            self.MyPrint_WithoutLogFile("SetSpeed_FROM_EXTERNAL_PROGRAM ERROR: units of " + Units + " is not in the acceptable list of " + str(self.SpeedUnitsAcceptableList))
            return 0

        SpeedFromExternalProgram_unlimited = 0
        if Units == "NONE":
            SpeedFromExternalProgram_unlimited = SpeedFromExternalProgram

        if Units == "PERCENT":
            SpeedFromExternalProgram = self.LimitNumber_FloatOutputOnly(0.0, 100.0, SpeedFromExternalProgram) #To limit the input to [0,100]%
            SpeedFromExternalProgram_unlimited = ((self.Speed_DynamixelUnits_Max_UserSet[MotorIndex] - self.Speed_DynamixelUnits_Min_UserSet[MotorIndex])/100.0)*SpeedFromExternalProgram + self.Speed_DynamixelUnits_Min_UserSet[MotorIndex]

        self.Speed_DynamixelUnits_TO_BE_SET[MotorIndex] = self.LimitNumber_FloatOutputOnly(self.Speed_DynamixelUnits_Min_UserSet[MotorIndex], self.Speed_DynamixelUnits_Max_UserSet[MotorIndex], SpeedFromExternalProgram_unlimited)
        self.Speed_DynamixelUnits_NeedsToBeChangedFlag[MotorIndex] = 1
        self.Speed_DynamixelUnits_GUI_NeedsToBeChangedFlag[MotorIndex] = 1

        return 1
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SetEngagedState_FROM_EXTERNAL_PROGRAM(self, MotorIndex, EngagedStateExternalProgram):

        if EngagedStateExternalProgram != 0 and EngagedStateExternalProgram != 1:
            self.MyPrint_WithoutLogFile("SetEngagedState_FROM_EXTERNAL_PROGRAM ERROR: EngagedState must be 0 or 1.")
            return 0

        #self.MyPrint_WithoutLogFile("SetEngagedState_FROM_EXTERNAL_PROGRAM changing EngagedState on motor " + str(MotorIndex) + " to a value of " + str(EngagedStateExternalProgram))

        self.EngagedState_TO_BE_SET[MotorIndex] = EngagedStateExternalProgram
        self.EngagedState_NeedsToBeChangedFlag[MotorIndex] = 1
        self.EngagedState_GUI_NeedsToBeChangedFlag[MotorIndex] = 1

        return 1
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def ToggleLEDstate_FROM_EXTERNAL_PROGRAM(self, MotorIndex):

        #self.MyPrint_WithoutLogFile("SetLEDstate_FROM_EXTERNAL_PROGRAM changing LEDstate on motor " + str(MotorIndex) + " to a value of " + str(LEDstateExternalProgram))

        if self.LEDstate[MotorIndex] == 0:
            self.SetLEDstate_FROM_EXTERNAL_PROGRAM(MotorIndex, 1)
        else:
            self.SetLEDstate_FROM_EXTERNAL_PROGRAM(MotorIndex, 0)


        return 1
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SetLEDstate_FROM_EXTERNAL_PROGRAM(self, MotorIndex, LEDstateExternalProgram):

        if LEDstateExternalProgram != 0 and LEDstateExternalProgram != 1:
            self.MyPrint_WithoutLogFile("SetLEDstate_FROM_EXTERNAL_PROGRAM ERROR: LEDstate must be 0 or 1.")
            return 0

        #self.MyPrint_WithoutLogFile("SetLEDstate_FROM_EXTERNAL_PROGRAM changing LEDstate on motor " + str(MotorIndex) + " to a value of " + str(LEDstateExternalProgram))

        self.LEDstate_TO_BE_SET[MotorIndex] = LEDstateExternalProgram
        self.LEDstate_NeedsToBeChangedFlag[MotorIndex] = 1
        self.LEDstate_GUI_NeedsToBeChangedFlag[MotorIndex] = 1

        return 1
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SetContinuousRotationState_FROM_EXTERNAL_PROGRAM(self, MotorIndex, ContinuousRotationStateExternalProgram):

        if self.MotorType_DynamixelIntegerList[MotorIndex] == -1:
            self.MyPrint_WithoutLogFile("SetContinuousRotationState_FROM_EXTERNAL_PROGRAM ERROR: Servo Number " + str(MotorIndex) + " was set as not connected, cannot change ContinuousRotationState.")
            return 0

        if ContinuousRotationStateExternalProgram != 0 and ContinuousRotationStateExternalProgram != 1:
            self.MyPrint_WithoutLogFile("SetContinuousRotationState_FROM_EXTERNAL_PROGRAM ERROR: ContinuousRotationState must be 0 or 1.")
            return 0

        #self.MyPrint_WithoutLogFile("SetContinuousRotationState_FROM_EXTERNAL_PROGRAM changing ContinuousRotationState on motor " + str(MotorIndex) + " to a value of " + str(ContinuousRotationStateExternalProgram))

        self.ContinuousRotationState_TO_BE_SET[MotorIndex] = ContinuousRotationStateExternalProgram
        self.ContinuousRotationState_NeedsToBeChangedFlag[MotorIndex] = 1
        self.ContinuousRotationState_GUI_NeedsToBeChangedFlag[MotorIndex] = 1

        return 1
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def UpdateFrequencyCalculation_MainThread_Filtered(self):

        try:
            self.DataStreamingDeltaT_CalculatedFromMainThread = self.CurrentTime_CalculatedFromMainThread - self.LastTime_CalculatedFromMainThread

            if self.DataStreamingDeltaT_CalculatedFromMainThread != 0.0:
                DataStreamingFrequency_CalculatedFromMainThread_TEMP = 1.0/self.DataStreamingDeltaT_CalculatedFromMainThread
                self.DataStreamingFrequency_CalculatedFromMainThread = self.DataStreamingFrequency_CalculatedFromMainThread_LowPassFilter_ReubenPython2and3ClassObject.AddDataPointFromExternalProgram(DataStreamingFrequency_CalculatedFromMainThread_TEMP)["SignalOutSmoothed"]

            self.LastTime_CalculatedFromMainThread = self.CurrentTime_CalculatedFromMainThread
        except:
            exceptions = sys.exc_info()[0]
            print("UpdateFrequencyCalculation_MainThread_Filtered ERROR with Exceptions: %s" % exceptions)
            traceback.print_exc()
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def shortIntegerToBytes(self, integerInput):
        bytesListToReturn = bytearray([0, 0])
        bytesListToReturn[0] = integerInput & 0xFF #Low Byte
        integerInput >>= 8
        bytesListToReturn[1] = integerInput & 0xFF #High Byte
        return bytesListToReturn
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SendSerialMessage_ListOfInts(self, SerialMessage_ListOfInts, print_bytes_for_debugging = 0):

        try:
            if print_bytes_for_debugging == 1:
                print("SerialMessage_ListOfInts: " + str(SerialMessage_ListOfInts))

            self.SerialObject.write(SerialMessage_ListOfInts) #As of 12/22/23, must write as a list, not byte-by-byte.

        except:
            exceptions = sys.exc_info()[0]
            print("SendSerialMessage_ListOfInts, exceptions: %s" % exceptions)
            self.ResetSerialConnection()
            print("########## SendSerialMessage_ListOfInts: RESET ALL SERIAL BUFFERS ##########")
            # traceback.print_exc()
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SendInstructionPacket_SetLED(self, MotorID, LEDstate, print_bytes_for_debugging = 0):

        Length = 4
        Instruction = 0x03
        PortRegister = 0x19
        Parameter = LEDstate

        Checksum = (MotorID + Length + Instruction + PortRegister + Parameter)
        Checksum = ~Checksum
        Checksum = Checksum % 256 #Take lower byte

        SerialMessage = []
        SerialMessage.append(0xFF)  # The two 0XFF bytes indicate the start of an incoming packet.
        SerialMessage.append(0xFF)  # The two 0XFF bytes indicate the start of an incoming packet.
        SerialMessage.append(MotorID)  # The unique ID of a Dynamixel unit. There are 254 available ID values, ranging from 0X00 to 0XFD.
        SerialMessage.append(Length)  # LENGTH The length of the packet where its value is "Number of parameters (N) + 2"
        SerialMessage.append(Instruction)  # Instruction
        SerialMessage.append(PortRegister)
        SerialMessage.append(LEDstate)  # PARAMETER 0...N, Used if there is additional information needed to be sent other than the instruction it
        SerialMessage.append(Checksum)  # CHECKSUM, #Check Sum = ~ (ID + Length + Instruction + Parameter1 + ... Parameter N)
        # If the calculated value is larger than 255, the lower byte is defined as the checksum value.
        # ~ represents the NOT logic operation.

        if print_bytes_for_debugging == 1:
            print("############### Begin byte sequence for SendInstructionPacket_SetLED()")
            print("LEDstate: " + str(LEDstate))

        self.SendSerialMessage_ListOfInts(SerialMessage, print_bytes_for_debugging)

        if print_bytes_for_debugging == 1:
            print("############### End byte sequence for SendInstructionPacket_SetLED()")

        self.LEDstate[MotorID] = LEDstate
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SendInstructionPacket_SetLEDalarmSettings(self, MotorID, LEDalarmSettingsByte, print_bytes_for_debugging = 0):

        Length = 4
        Instruction = 0x03
        PortRegister = 0x11
        Parameter = LEDalarmSettingsByte

        Checksum = (MotorID + Length + Instruction + PortRegister + Parameter)
        Checksum = ~Checksum
        Checksum = Checksum % 256 #Take lower byte

        SerialMessage = []
        SerialMessage.append(0xFF)  # The two 0XFF bytes indicate the start of an incoming packet.
        SerialMessage.append(0xFF)  # The two 0XFF bytes indicate the start of an incoming packet.
        SerialMessage.append(MotorID)  # The unique ID of a Dynamixel unit. There are 254 available ID values, ranging from 0X00 to 0XFD.
        SerialMessage.append(Length)  # LENGTH The length of the packet where its value is "Number of parameters (N) + 2"
        SerialMessage.append(Instruction)  # Instruction
        SerialMessage.append(PortRegister)
        SerialMessage.append(LEDalarmSettingsByte)  # PARAMETER 0...N, Used if there is additional information needed to be sent other than the instruction it
        SerialMessage.append(Checksum)  # CHECKSUM, #Check Sum = ~ (ID + Length + Instruction + Parameter1 + ... Parameter N)
        # If the calculated value is larger than 255, the lower byte is defined as the checksum value.
        # ~ represents the NOT logic operation.

        if print_bytes_for_debugging == 1:
            print("############### Begin byte sequence for SendInstructionPacket_SetLEDalarmSettings()")
            print("LEDalarmSettingsByte: " + str(LEDalarmSettingsByte))

        self.SendSerialMessage_ListOfInts(SerialMessage, print_bytes_for_debugging)

        if print_bytes_for_debugging == 1:
            print("############### End byte sequence for SendInstructionPacket_SetLEDalarmSettings()")
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SendInstructionPacket_SetTorqueEnable(self, MotorID, TorqueEnableState, print_bytes_for_debugging = 0):

        Length = 4
        Instruction = 0x03
        PortRegister = 0x18
        Parameter = TorqueEnableState

        Checksum = (MotorID + Length + Instruction + PortRegister + Parameter)
        Checksum = ~Checksum
        Checksum = Checksum % 256 #Take lower byte

        SerialMessage = []
        SerialMessage.append(0xFF)
        SerialMessage.append(0xFF)
        SerialMessage.append(MotorID)
        SerialMessage.append(Length)
        SerialMessage.append(Instruction)
        SerialMessage.append(PortRegister)
        SerialMessage.append(TorqueEnableState)
        SerialMessage.append(Checksum)

        if print_bytes_for_debugging == 1:
            print("############### Begin byte sequence for SendInstructionPacket_SetTorqueEnable()")
            print("TorqueEnableState: " + str(TorqueEnableState))

        self.SendSerialMessage_ListOfInts(SerialMessage, print_bytes_for_debugging)

        if print_bytes_for_debugging == 1:
            print("############### End byte sequence for SendInstructionPacket_SetTorqueEnable()")
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SendInstructionPacket_SetStatusReturnLevel(self, MotorID, StatusReturnLevel, print_bytes_for_debugging = 0):

        # 0: Do not respond to any instructions
        # 1: Respond only to READ_DATA instructions
        # 2: Respond to all instructions

        Length = 4
        Instruction = 0x03
        PortRegister = 0x10
        Parameter = StatusReturnLevel

        Checksum = (MotorID + Length + Instruction + PortRegister + Parameter)
        Checksum = ~Checksum
        Checksum = Checksum % 256 #Take lower byte

        SerialMessage = []
        SerialMessage.append(0xFF)
        SerialMessage.append(0xFF)
        SerialMessage.append(MotorID)
        SerialMessage.append(Length)
        SerialMessage.append(Instruction)
        SerialMessage.append(PortRegister)
        SerialMessage.append(StatusReturnLevel)
        SerialMessage.append(Checksum)

        if print_bytes_for_debugging == 1:
            print("############### Begin byte sequence for SendInstructionPacket_SetStatusReturnLevel()")
            print("StatusReturnLevel: " + str(StatusReturnLevel))

        self.SendSerialMessage_ListOfInts(SerialMessage, print_bytes_for_debugging)

        if print_bytes_for_debugging == 1:
            print("############### End byte sequence for SendInstructionPacket_SetStatusReturnLevel()")
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SendInstructionPacket_SetPositionAndSpeed(self, MotorID, Position, Speed, print_bytes_for_debugging = 0):

        #Goal Position Requested angular position for the Dynamixel actuator output to move to. Setting this value to 0x3ff moves the output shaft to the position at 300deg.
        #Moving Speed. Sets the angular Speed of the output moving to the Goal Position.
        #Setting this value to its maximum value of 0x3ff moves the output with an angular Speed of 114 RPM,
        #provided that there is enough power supplied (The lowest Speed is when this value is set to 1.
        #When set to 0, the Speed is the largest possible for the supplied voltage, e.g. no Speed control is applied.)

        Length = 7 # LENGTH The length of the packet where its value is "Number of parameters (N) + 2"
        Instruction = 0x03
        PortRegister = 0x1E

        Position_limited = int(self.LimitNumber_FloatOutputOnly(self.Position_DynamixelUnits_Min_UserSet[MotorID], self.Position_DynamixelUnits_Max_UserSet[MotorID], Position))
        Position_limited_BYTES_LIST = self.shortIntegerToBytes(Position_limited)
        Position_limited_LOW_BYTE = Position_limited_BYTES_LIST[0]
        Position_limited_HIGH_BYTE = Position_limited_BYTES_LIST[1]

        Speed_limited = int(self.LimitNumber_FloatOutputOnly(self.Speed_DynamixelUnits_Min_UserSet[MotorID], self.Speed_DynamixelUnits_Max_UserSet[MotorID], abs(Speed)))
        Speed_limited_BYTES_LIST = self.shortIntegerToBytes(Speed_limited)
        Speed_limited_LOW_BYTE = Speed_limited_BYTES_LIST[0]
        Speed_limited_HIGH_BYTE = Speed_limited_BYTES_LIST[1]

        if Speed < 0:
            Speed_limited_HIGH_BYTE = Speed_limited_BYTES_LIST[1] | 0b00000100 #To set negative bit high

        Checksum = (MotorID + Length + Instruction + PortRegister + Position_limited_LOW_BYTE + Position_limited_HIGH_BYTE + Speed_limited_LOW_BYTE + Speed_limited_HIGH_BYTE)
        Checksum = ~Checksum
        Checksum = Checksum % 256 #Take lower byte

        #print("Checksum: " + str(Checksum))

        SerialMessage = []
        SerialMessage.append(0xFF)
        SerialMessage.append(0xFF)
        SerialMessage.append(MotorID)
        SerialMessage.append(Length)
        SerialMessage.append(Instruction)
        SerialMessage.append(PortRegister)
        SerialMessage.append(Position_limited_LOW_BYTE) #Parameter list:
        SerialMessage.append(Position_limited_HIGH_BYTE) #Parameter list:
        SerialMessage.append(Speed_limited_LOW_BYTE) #Parameter list:
        SerialMessage.append(Speed_limited_HIGH_BYTE) #Parameter list:
        SerialMessage.append(Checksum)

        if print_bytes_for_debugging == 1:
            print("############### Begin byte sequence for SendInstructionPacket_SetPositionAndSpeed()")
            print("Position_limited: " + str(Position_limited) + ", Speed_limited: " + str(Speed_limited))

        self.SendSerialMessage_ListOfInts(SerialMessage, print_bytes_for_debugging)

        if print_bytes_for_debugging == 1:
            print("############### End byte sequence for SendInstructionPacket_SetPositionAndSpeed()")

        self.Position_DynamixelUnits[MotorID] = Position_limited
        self.Speed_DynamixelUnits[MotorID] = Speed_limited
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SendInstructionPacket_SetCWandCCWlimits(self, MotorID, CWlimit, CCWlimit, print_bytes_for_debugging = 0, DONT_UPDATE_CC_AND_CCW_LIMITS_FLAG = 0):

        #Goal Position Requested angular position for the Dynamixel actuator output to move to. Setting this value to 0x3ff moves the output shaft to the position at 300deg.
        #Moving Speed. Sets the angular Speed of the output moving to the Goal Position.
        #Setting this value to its maximum value of 0x3ff moves the output with an angular Speed of 114 RPM,
        #provided that there is enough power supplied (The lowest Speed is when this value is set to 1.
        #When set to 0, the Speed is the largest possible for the supplied voltage, e.g. no Speed control is applied.)

        print("SendInstructionPacket_SetCWandCCWlimits: CWlimit: " + str(CWlimit) + ", CCWlimit: " + str(CCWlimit))

        CWlimit_limited = int(self.LimitNumber_FloatOutputOnly(self.Position_DynamixelUnits_Min_UserSet[MotorID], self.Position_DynamixelUnits_Max_UserSet[MotorID], CWlimit))
        CCWlimit_limited = int(self.LimitNumber_FloatOutputOnly(self.Position_DynamixelUnits_Min_UserSet[MotorID], self.Position_DynamixelUnits_Max_UserSet[MotorID], CCWlimit))

        Length = 7 # LENGTH The length of the packet where its value is "Number of parameters (N) + 2"
        Instruction = 0x03
        PortRegister = 0x06

        CWlimit_limited_BYTES_LIST = self.shortIntegerToBytes(CWlimit_limited)
        CWlimit_limited_LOW_BYTE = CWlimit_limited_BYTES_LIST[0]
        CWlimit_limited_HIGH_BYTE = CWlimit_limited_BYTES_LIST[1]

        CCWlimit_limited_BYTES_LIST = self.shortIntegerToBytes(CCWlimit_limited)
        CCWlimit_limited_LOW_BYTE = CCWlimit_limited_BYTES_LIST[0]
        CCWlimit_limited_HIGH_BYTE = CCWlimit_limited_BYTES_LIST[1]

        Checksum = (MotorID + Length + Instruction + PortRegister + CWlimit_limited_LOW_BYTE + CWlimit_limited_HIGH_BYTE + CCWlimit_limited_LOW_BYTE + CCWlimit_limited_HIGH_BYTE)
        Checksum = ~Checksum
        Checksum = Checksum % 256 #Take lower byte

        #print("Checksum: " + str(Checksum))

        SerialMessage = []
        SerialMessage.append(0xFF)
        SerialMessage.append(0xFF)
        SerialMessage.append(MotorID)
        SerialMessage.append(Length)
        SerialMessage.append(Instruction)
        SerialMessage.append(PortRegister)
        SerialMessage.append(CWlimit_limited_LOW_BYTE) #Parameter list:
        SerialMessage.append(CWlimit_limited_HIGH_BYTE) #Parameter list:
        SerialMessage.append(CCWlimit_limited_LOW_BYTE) #Parameter list:
        SerialMessage.append(CCWlimit_limited_HIGH_BYTE) #Parameter list:
        SerialMessage.append(Checksum)

        if print_bytes_for_debugging == 1:
            print("############### Begin byte sequence for SendInstructionPacket_SetCWandCCWlimits()")
            print("CWlimit_limited: " + str(CWlimit_limited) + ", CCWlimit_limited: " + str(CCWlimit_limited))

        self.SendSerialMessage_ListOfInts(SerialMessage, print_bytes_for_debugging)

        if print_bytes_for_debugging == 1:
            print("############### End byte sequence for SendInstructionPacket_SetCWandCCWlimits()")

        if DONT_UPDATE_CC_AND_CCW_LIMITS_FLAG == 0:
            self.CWlimit[MotorID] = CWlimit_limited
            self.CCWlimit[MotorID] = CCWlimit_limited
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SendInstructionPacket_MaxTorque(self, MotorID, MaxTorque, print_bytes_for_debugging = 0):

        '''
        Max Torque. The maximum torque output for the Dynamixel actuator.
        When this value is set to 0, the Dynamixel actuator enters the Free Run mode.
        There are two locations where this maximum torque limit is defined;
        in the EEPROM (Address 0X0E, 0x0F) and in the RAM (Address 0x22, 0x23).
        When the power is turned on, the maximum torque limit value defined in the EEPROM is copied to the location in the RAM.
        The torque of the Dynamixel actuator is limited by the values located in the RAM (Address 0x22, 0x23).
        '''

        Length = 5 # LENGTH The length of the packet where its value is "Number of parameters (N) + 2"
        Instruction = 0x03
        PortRegister = 0x22

        MaxTorque_limited = int(self.LimitNumber_FloatOutputOnly(0.0, 1023.0, MaxTorque))
        MaxTorque_limited_BYTES_LIST = self.shortIntegerToBytes(MaxTorque_limited)
        MaxTorque_limited_LOW_BYTE = MaxTorque_limited_BYTES_LIST[0]
        MaxTorque_limited_HIGH_BYTE = MaxTorque_limited_BYTES_LIST[1]

        Checksum = (MotorID + Length + Instruction + PortRegister + MaxTorque_limited_LOW_BYTE + MaxTorque_limited_HIGH_BYTE)
        Checksum = ~Checksum
        Checksum = Checksum % 256 #Take lower byte

        #print("Checksum: " + str(Checksum))

        SerialMessage = []
        SerialMessage.append(0xFF)
        SerialMessage.append(0xFF)
        SerialMessage.append(MotorID)
        SerialMessage.append(Length)
        SerialMessage.append(Instruction)
        SerialMessage.append(PortRegister)
        SerialMessage.append(MaxTorque_limited_LOW_BYTE) #Parameter list:
        SerialMessage.append(MaxTorque_limited_HIGH_BYTE) #Parameter list:
        SerialMessage.append(Checksum)

        if print_bytes_for_debugging == 1:
            print("############### Begin byte sequence for SendInstructionPacket_MaxTorque()")
            print("MaxTorque_limited: " + str(MaxTorque_limited))

        self.SendSerialMessage_ListOfInts(SerialMessage, print_bytes_for_debugging)

        if print_bytes_for_debugging == 1:
            print("############### End byte sequence for SendInstructionPacket_MaxTorque()")

        self.MaxTorque_DynamixelUnits[MotorID] = MaxTorque_limited
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def SendInstructionPacket_ContinuousRotationState(self, MotorID, ContinuousRotationState, print_bytes_for_debugging = 0):

        DONT_UPDATE_CC_AND_CCW_LIMITS_FLAG = 1

        if ContinuousRotationState == 0:
            self.SendInstructionPacket_SetCWandCCWlimits(MotorID, self.CWlimit[MotorID], self.CCWlimit[MotorID], print_bytes_for_debugging, DONT_UPDATE_CC_AND_CCW_LIMITS_FLAG)
        else:
            self.SendInstructionPacket_SetCWandCCWlimits(MotorID, 0, 0, print_bytes_for_debugging, DONT_UPDATE_CC_AND_CCW_LIMITS_FLAG) #Both limits have to be 0 for continuous rotation

        self.ContinuousRotationState[MotorID] = ContinuousRotationState
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def InterpretErrorByte(self, ErrorByteToIntrepret):
        '''
        Each bit in the error byte represents a different error state.
        Note that complete error handling has not yet been implemented
        –most of these errors will print out the error state and then sit in an infinite loop until power cycled.
        '''

        ##########################################################################################################
        for BitNumber in self.ErrorFlagNames_DictBitNumberAsKey:
            if BitNumber == -1:
                self.ErrorFlagStates_DictEnglishNameAsKey["ErrorByte"] = ErrorByteToIntrepret
            else:
                EnglishName = self.ErrorFlagNames_DictBitNumberAsKey[BitNumber]
                self.ErrorFlagStates_DictEnglishNameAsKey[EnglishName] = ErrorByteToIntrepret & (1 << BitNumber)
        ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    def ReadVariable(self, MotorID, VariableName, print_bytes_for_debugging = 0):

        try:

            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            if VariableName == "Ping":
                Length = 2
                Instruction = 0x01
                PortRegister = -1 #Starting address of the location where the data is to be read
                ReadLength = 1
                SerialMessage_Received_ExpectedWholePacketLength = 6
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 2 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "Position":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x24 #Starting address of the location where the data is to be read
                ReadLength = 2  #Low byte, High byte
                SerialMessage_Received_ExpectedWholePacketLength = 8
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 4 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "GoalPosition":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x1E #Starting address of the location where the data is to be read
                ReadLength = 2  #Low byte, High byte
                SerialMessage_Received_ExpectedWholePacketLength = 8
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 4 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "Speed":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x26 #Starting address of the location where the data is to be read
                ReadLength = 2  #Low byte, High byte
                SerialMessage_Received_ExpectedWholePacketLength = 8
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 4 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "Torque":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x28 #Starting address of the location where the data is to be read
                ReadLength = 2  #Low byte, High byte
                SerialMessage_Received_ExpectedWholePacketLength = 8
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 4 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "Voltage":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x2A #Starting address of the location where the data is to be read
                ReadLength = 1
                SerialMessage_Received_ExpectedWholePacketLength = 7
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 3 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "Temperature":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x2B #Starting address of the location where the data is to be read
                ReadLength = 1
                SerialMessage_Received_ExpectedWholePacketLength = 7
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 3 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "MovingState":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x2E #Starting address of the location where the data is to be read
                ReadLength = 1
                SerialMessage_Received_ExpectedWholePacketLength = 7
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 3 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "PositionAndSpeed":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x24 #Starting address of the location where the data is to be read
                ReadLength = 4  #Low byte, High byte #Low byte, High byte
                SerialMessage_Received_ExpectedWholePacketLength = 10
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 6 #Requested data + checksum
                ReturnValueForError = [-1, -1]

            elif VariableName == "ModelNumber":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x00 #Starting address of the location where the data is to be read
                ReadLength = 2  #Low byte, High byte
                SerialMessage_Received_ExpectedWholePacketLength = 8
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 4 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "FWversion":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x02 #Starting address of the location where the data is to be read
                ReadLength = 1
                SerialMessage_Received_ExpectedWholePacketLength = 7
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 3 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "ID":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x03 #Starting address of the location where the data is to be read
                ReadLength = 1
                SerialMessage_Received_ExpectedWholePacketLength = 7
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 3 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "ReturnDelayTimeMicroSeconds":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x05 #Starting address of the location where the data is to be read
                ReadLength = 1
                SerialMessage_Received_ExpectedWholePacketLength = 7
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 3 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "TemperatureHighestLimit":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x0B #Starting address of the location where the data is to be read
                ReadLength = 1
                SerialMessage_Received_ExpectedWholePacketLength = 7
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 3 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "VoltageLowestLimit":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x0C #Starting address of the location where the data is to be read
                ReadLength = 1
                SerialMessage_Received_ExpectedWholePacketLength = 7
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 3 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "VoltageHighestLimit":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x0D #Starting address of the location where the data is to be read
                ReadLength = 1
                SerialMessage_Received_ExpectedWholePacketLength = 7
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 3 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "CWangleLimit":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x06 #Starting address of the location where the data is to be read
                ReadLength = 2  #Low byte, High byte
                SerialMessage_Received_ExpectedWholePacketLength = 8
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 4 #Requested data + checksum
                ReturnValueForError = -1

            elif VariableName == "CCWangleLimit":
                Length = 4
                Instruction = 0x02
                PortRegister = 0x08 #Starting address of the location where the data is to be read
                ReadLength = 2  #Low byte, High byte
                SerialMessage_Received_ExpectedWholePacketLength = 8
                SerialMessage_Received_ExpectedDataAndChecksumReadLength = 4 #Requested data + checksum
                ReturnValueForError = -1

            else:
                self.MyPrint_WithoutLogFile("ReadVariable ERROR: Don't recognize the VariableName.")
                return -11111

            DataValue = ReturnValueForError
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################

            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            Checksum = (MotorID + Length + Instruction + PortRegister + ReadLength)
            Checksum = ~Checksum
            Checksum = Checksum % 256 #Take lower byte

            SerialMessage = []
            SerialMessage.append(0xFF)
            SerialMessage.append(0xFF)
            SerialMessage.append(MotorID)
            SerialMessage.append(Length)
            SerialMessage.append(Instruction)

            if PortRegister != -1:
                SerialMessage.append(PortRegister)

            SerialMessage.append(ReadLength)
            SerialMessage.append(Checksum)

            if print_bytes_for_debugging == 1:
                print("############### Begin byte sequence for ReadVariable()")
                print("Reading variable '" + VariableName + "'")

            self.SendSerialMessage_ListOfInts(SerialMessage, print_bytes_for_debugging)

            ##################
            ################## THIS PAUSE IS CRITICAL TO BEING ABLE TO PROPERLY READ THE RESPONSE.
            ################## When self.SerialXonXoffSoftwareFlowControl = 0, it can be only 0.001.
            ################## When self.SerialXonXoffSoftwareFlowControl = 0, must go up to more like 0.050 to 0.100.
            ##################
            time.sleep(0.001)
            ##################
            ##################
            ##################
            ##################
            ##################

            if print_bytes_for_debugging == 1:
                print("############### End byte sequence for ReadVariable()")

            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################

            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            SerialMessage_Received = self.ConvertByteAarrayObjectToIntsList(self.SerialObject.read(SerialMessage_Received_ExpectedWholePacketLength))
            #print("SerialMessage_Received: " + str(SerialMessage_Received))

            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            if len(SerialMessage_Received) == SerialMessage_Received_ExpectedWholePacketLength and SerialMessage_Received[0] == 0xFF and SerialMessage_Received[1] == 0xFF and SerialMessage_Received[2] == MotorID and SerialMessage_Received[3] == SerialMessage_Received_ExpectedDataAndChecksumReadLength:
                
                ##########################################################################################################
                checksum_value_received = SerialMessage_Received[-1]

                list_subset_for_checksum_computation = SerialMessage_Received[2:-1]
                checksum_computed_from_received_massage = 0
                for element in list_subset_for_checksum_computation:
                    checksum_computed_from_received_massage = checksum_computed_from_received_massage + element
                checksum_computed_from_received_massage = ~checksum_computed_from_received_massage
                checksum_computed_from_received_massage = checksum_computed_from_received_massage % 256  # Take lower byte
                ##########################################################################################################

                ##########################################################################################################
                if VariableName == "Position" or VariableName == "GoalPosition" or VariableName == "ModelNumber" or VariableName == "CWangleLimit" or VariableName == "CCWangleLimit":
                    Data_Low_BYTE = SerialMessage_Received[5]
                    Data_High_BYTE = SerialMessage_Received[6]

                    Data_Value = Data_Low_BYTE|(Data_High_BYTE<<8)
                ##########################################################################################################

                ##########################################################################################################
                elif VariableName == "Speed" or VariableName == "Torque":
                    Data_Low_BYTE = SerialMessage_Received[5]
                    Data_High_BYTE = SerialMessage_Received[6] & 0b0000011

                    Data_Sign_unscaled = (SerialMessage_Received[6] & 0b11111100)
                    if Data_Sign_unscaled != 0:
                        Data_Sign = -1
                    else:
                        Data_Sign = 1

                    Data_Value = Data_Sign*(Data_Low_BYTE|(Data_High_BYTE<<8))
                ##########################################################################################################

                ##########################################################################################################
                elif VariableName == "Voltage" or VariableName == "VoltageLowestLimit" or VariableName == "VoltageHighestLimit":
                    Data_Low_BYTE = SerialMessage_Received[5]

                    Data_Value = Data_Low_BYTE/10.0 #The voltage currently applied to the Dynamixel actuator. The value is 10 times the actual voltage. For example, 10V is represented as 100 (0x64).
                ##########################################################################################################

                ##########################################################################################################
                elif VariableName == "ReturnDelayTimeMicroSeconds":
                    #Return Delay Time.
                    # The time it takes for the Status Packet to return after the Instruction Packet is sent.
                    # The delay time is given by 2uSec * Address5 value.
                    Data_Low_BYTE = SerialMessage_Received[5]

                    Data_Value = 2.0*Data_Low_BYTE
                ##########################################################################################################

                ##########################################################################################################
                elif VariableName == "Temperature" or VariableName == "MovingState" or VariableName == "TemperatureHighestLimit" or VariableName == "FWversion" or VariableName == "ID":
                    Data_Low_BYTE = SerialMessage_Received[5]

                    Data_Value = Data_Low_BYTE
                ##########################################################################################################

                ##########################################################################################################
                elif VariableName == "PositionAndSpeed":
                    Position_Low_BYTE = SerialMessage_Received[5]
                    Position_High_BYTE = SerialMessage_Received[6]
                    Position_Value_DynamixelUnits = (Position_Low_BYTE | (Position_High_BYTE << 8))

                    Speed_Low_BYTE = SerialMessage_Received[7]
                    Speed_High_BYTE = SerialMessage_Received[8] & 0b0000011
                    Speed_Sign_unscaled = (SerialMessage_Received[8]) & 0b11111100
                    if Speed_Sign_unscaled != 0:
                        Speed_Sign = -1
                    else:
                        Speed_Sign = 1

                    Speed_Value_DynamixelUnits = Speed_Sign * (Speed_Low_BYTE | (Speed_High_BYTE << 8))

                    Data_Value = [Position_Value_DynamixelUnits, Speed_Value_DynamixelUnits]
                ##########################################################################################################

                ##########################################################################################################
                if checksum_value_received == checksum_computed_from_received_massage:
                    
                    self.InterpretErrorByte(SerialMessage_Received[4])
                    
                    return Data_Value

                else:
                    self.MyPrint_WithoutLogFile("ReadVariable Error! Checksum is bad. Packet = " +
                                  str(SerialMessage_Received) +
                                  ", checksum_value_received = " +
                                  str(checksum_value_received) +
                                  "checksum_computed_from_received_massage = "  +
                                  str(checksum_computed_from_received_massage))

                    return ReturnValueForError
                ##########################################################################################################

            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################

            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            else:
                return ReturnValueForError
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################


        except:
            exceptions = sys.exc_info()[0]
            print("ReadVariable, exceptions: %s" % exceptions)
            return ReturnValueForError
            #traceback.print_exc()

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    def MainThread(self): #unicorn

        self.StartingTime_CalculatedFromMainThread = self.getPreciseSecondsTimeStampString()

        self.MyPrint_WithoutLogFile("Started the MainThread for DynamixelProtocol1AXorMXseries_ReubenPython3Class object.")
        self.MainThread_StillRunningFlag = 1

        ########################################################################################################## Initialize motors
        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        for MotorIndex in range(0, self.NumberOfMotors):

            self.ModelNumber_Received[MotorIndex] = self.ReadVariable(MotorIndex, "ModelNumber")
            time.sleep(self.TimeBetweenCommands)
            self.FWversion_Received[MotorIndex] = self.ReadVariable(MotorIndex, "FWversion")
            time.sleep(self.TimeBetweenCommands)
            self.ID_Received[MotorIndex] = self.ReadVariable(MotorIndex, "ID")
            time.sleep(self.TimeBetweenCommands)
            self.ReturnDelayTimeMicroSeconds_Received[MotorIndex] = self.ReadVariable(MotorIndex, "ReturnDelayTimeMicroSeconds")
            time.sleep(self.TimeBetweenCommands)
            self.TemperatureHighestLimit_Received[MotorIndex] = self.ReadVariable(MotorIndex, "TemperatureHighestLimit")
            time.sleep(self.TimeBetweenCommands)
            self.VoltageLowestLimit_Received[MotorIndex] = self.ReadVariable(MotorIndex, "VoltageLowestLimit")
            time.sleep(self.TimeBetweenCommands)
            self.VoltageHighestLimit_Received[MotorIndex] = self.ReadVariable(MotorIndex, "VoltageHighestLimit")
            time.sleep(self.TimeBetweenCommands)

            self.SendInstructionPacket_SetLEDalarmSettings(MotorIndex, self.LEDalarmSettingsBYTE)
            time.sleep(self.TimeBetweenCommands)
            self.SendInstructionPacket_SetStatusReturnLevel(MotorIndex, 1) #Respond only to READ_DATA instructions
            time.sleep(self.TimeBetweenCommands)
            self.SendInstructionPacket_SetLED(MotorIndex, 1)
            time.sleep(self.TimeBetweenCommands)
            self.SendInstructionPacket_MaxTorque(MotorIndex, self.MaxTorque_DynamixelUnits_StartingValueList[MotorIndex])
            time.sleep(self.TimeBetweenCommands)
            self.SendInstructionPacket_SetCWandCCWlimits(MotorIndex, self.CWlimit_StartingValueList[MotorIndex], self.CCWlimit_StartingValueList[MotorIndex])
            time.sleep(self.TimeBetweenCommands)
            self.SendInstructionPacket_SetPositionAndSpeed(MotorIndex, self.Position_DynamixelUnits_StartingValueList[MotorIndex], self.Speed_DynamixelUnits_StartingValueList[MotorIndex])
            time.sleep(self.TimeBetweenCommands)

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        while self.EXIT_PROGRAM_FLAG == 0:

            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            self.CurrentTime_CalculatedFromMainThread = self.getPreciseSecondsTimeStampString() - self.StartingTime_CalculatedFromMainThread
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################

            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            if self.ResetSerialConnection_EventNeedsToBeFiredFlag == 1:
                self.ResetSerialConnection()
                self.ResetSerialConnection_EventNeedsToBeFiredFlag = 0
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################

            ##########################################################################################################  Start GETs
            ##########################################################################################################
            ##########################################################################################################
            if self.ENABLE_GETS == 1 and self.SerialConnectedFlag == 1:
                try:

                    self.AskForInfrequentDataReadLoopCounter = self.AskForInfrequentDataReadLoopCounter + 1

                    ##########################################################################################################
                    ##########################################################################################################
                    for MotorIndex in range(0, self.NumberOfMotors):
                        [self.PositionReceived_DynamixelUnits[MotorIndex], self.SpeedReceived_DynamixelUnits[MotorIndex]] = self.ReadVariable(MotorIndex, "PositionAndSpeed")

                        #self.GoalPositionReceived[MotorIndex] = self.ReadVariable(MotorIndex, "GoalPosition")
                        #time.sleep(self.TimeBetweenCommands)
                        #self.PositionReceived_DynamixelUnits[MotorIndex] = self.ReadVariable(MotorIndex, "Position")
                        #time.sleep(self.TimeBetweenCommands)
                        #self.SpeedReceived_DynamixelUnits[MotorIndex] = self.ReadVariable(MotorIndex, "Speed")
                        #time.sleep(self.TimeBetweenCommands)

                        #self.GoalPositionReceived_Degrees[MotorIndex] = self.GoalPositionReceived_DynamixelUnits[MotorIndex]*self.ConversionFactorFromDynamixelUnitsToDegrees
                        self.PositionReceived_Degrees[MotorIndex] = self.PositionReceived_DynamixelUnits[MotorIndex]*self.ConversionFactorFromDynamixelUnitsToDegrees
                        self.SpeedReceived_DegreesPerSecond[MotorIndex] = self.SpeedReceived_DynamixelUnits[MotorIndex]*self.ConversionFactorFromDynamixelUnitsToDegrees

                        self.TorqueReceived_DynamixelUnits[MotorIndex] = self.ReadVariable(MotorIndex, "Torque")
                        time.sleep(self.TimeBetweenCommands)

                        if self.AskForInfrequentDataReadLoopCounter == 1:
                            self.VoltageReceived_Volts[MotorIndex] = self.ReadVariable(MotorIndex, "Voltage")
                            time.sleep(self.TimeBetweenCommands)

                        elif self.AskForInfrequentDataReadLoopCounter == 2:
                            self.TemperatureReceived_DegC[MotorIndex] = self.ReadVariable(MotorIndex, "Temperature")
                            time.sleep(self.TimeBetweenCommands)

                        elif self.AskForInfrequentDataReadLoopCounter == 3:
                            self.ReadVariable(MotorIndex, "Ping")
                            time.sleep(self.TimeBetweenCommands)

                        elif self.AskForInfrequentDataReadLoopCounter == 4:
                            self.CWangleLimit_Received[MotorIndex] = self.ReadVariable(MotorIndex, "CWangleLimit")
                            time.sleep(self.TimeBetweenCommands)

                        elif self.AskForInfrequentDataReadLoopCounter == 5:
                            self.CCWangleLimit_Received[MotorIndex] = self.ReadVariable(MotorIndex, "CCWangleLimit")
                            time.sleep(self.TimeBetweenCommands)

                        elif self.AskForInfrequentDataReadLoopCounter == self.AskForInfrequentDataReadLoopCounterLimit:
                            self.AskForInfrequentDataReadLoopCounter = 0

                        #self.MovingStateReceived_DynamixelUnits[MotorIndex] = self.ReadVariable(MotorIndex, "MovingState")
                        #time.sleep(self.TimeBetweenCommands)

                        time.sleep(self.TimeBetweenCommands)  # MUST PAUSE IN BETWEEN MOTORS

                    ##########################################################################################################
                    ##########################################################################################################

                    ##########################################################################################################
                    ##########################################################################################################
                    self.MostRecentDataDict = dict([("PositionReceived_DynamixelUnits", self.PositionReceived_DynamixelUnits),
                                                    ("PositionReceived_Degrees", self.PositionReceived_Degrees),
                                                    ("SpeedReceived_DynamixelUnits", self.SpeedReceived_DynamixelUnits),
                                                    ("SpeedReceived_DegreesPerSecond", self.SpeedReceived_DegreesPerSecond),
                                                    ("TorqueReceived_DynamixelUnits", self.TorqueReceived_DynamixelUnits),
                                                    ("VoltageReceived_Volts", self.VoltageReceived_Volts),
                                                    ("TemperatureReceived_DegC", self.TemperatureReceived_DegC),
                                                    ("Time", self.CurrentTime_CalculatedFromMainThread)])
                    ##########################################################################################################
                    ##########################################################################################################


                except:
                    exceptions = sys.exc_info()[0]
                    print("DynamixelProtocol1AXorMXseries_ReubenPython3Class, MainThread GETs, exceptions: %s" % exceptions)
                    #traceback.print_exc()
            ##########################################################################################################
            ##########################################################################################################
            ########################################################################################################## End GETs

            time.sleep(self.TimeBetweenCommands)

            ########################################################################################################## Start SETs
            ##########################################################################################################
            ##########################################################################################################
            if self.ENABLE_SETS == 1 and self.SerialConnectedFlag == 1:
                try:
                    for MotorIndex in range(0, self.NumberOfMotors):

                        ##########################################################################################################
                        ##########################################################################################################
                        if self.ContinuousRotationState_NeedsToBeChangedFlag[MotorIndex] == 1:
                            self.SendInstructionPacket_ContinuousRotationState(MotorIndex, self.ContinuousRotationState_TO_BE_SET[MotorIndex], self.GlobalPrintByteSequencesDebuggingFlag)
                            time.sleep(self.TimeBetweenCommands)
                            self.ContinuousRotationState_NeedsToBeChangedFlag[MotorIndex] = 0
                        ##########################################################################################################
                        ##########################################################################################################

                        ##########################################################################################################
                        ##########################################################################################################
                        if self.CWlimit_NeedsToBeChangedFlag[MotorIndex] == 1:
                            self.SendInstructionPacket_SetCWandCCWlimits(MotorIndex, self.CWlimit_TO_BE_SET[MotorIndex], self.CCWlimit_TO_BE_SET[MotorIndex], self.GlobalPrintByteSequencesDebuggingFlag)
                            time.sleep(self.TimeBetweenCommands)
                            self.CWlimit_NeedsToBeChangedFlag[MotorIndex] = 0
                        ##########################################################################################################
                        ##########################################################################################################

                        ##########################################################################################################
                        ##########################################################################################################
                        if self.CCWlimit_NeedsToBeChangedFlag[MotorIndex] == 1:
                            self.SendInstructionPacket_SetCWandCCWlimits(MotorIndex, self.CWlimit_TO_BE_SET[MotorIndex], self.CCWlimit_TO_BE_SET[MotorIndex], self.GlobalPrintByteSequencesDebuggingFlag)
                            time.sleep(self.TimeBetweenCommands)
                            self.CCWlimit_NeedsToBeChangedFlag[MotorIndex] = 0
                        ##########################################################################################################
                        ##########################################################################################################

                        ##########################################################################################################
                        ##########################################################################################################
                        if self.EngagedState_NeedsToBeChangedFlag[MotorIndex] == 1:
                            self.SendInstructionPacket_SetTorqueEnable(MotorIndex, self.EngagedState_TO_BE_SET[MotorIndex], self.GlobalPrintByteSequencesDebuggingFlag)
                            time.sleep(self.TimeBetweenCommands)
                            self.EngagedState_NeedsToBeChangedFlag[MotorIndex] = 0
                        ##########################################################################################################
                        ##########################################################################################################

                        ##########################################################################################################
                        ##########################################################################################################
                        if self.LEDstate_NeedsToBeChangedFlag[MotorIndex] == 1:
                            self.SendInstructionPacket_SetLED(MotorIndex, self.LEDstate_TO_BE_SET[MotorIndex], self.GlobalPrintByteSequencesDebuggingFlag)
                            time.sleep(self.TimeBetweenCommands)
                            self.LEDstate_NeedsToBeChangedFlag[MotorIndex] = 0
                        ##########################################################################################################
                        ##########################################################################################################

                        ##########################################################################################################
                        ##########################################################################################################
                        if self.MaxTorque_DynamixelUnits_NeedsToBeChangedFlag[MotorIndex] == 1:
                            self.SendInstructionPacket_MaxTorque(MotorIndex, self.MaxTorque_DynamixelUnits_TO_BE_SET[MotorIndex], self.GlobalPrintByteSequencesDebuggingFlag)
                            time.sleep(self.TimeBetweenCommands)
                            self.MaxTorque_DynamixelUnits_NeedsToBeChangedFlag[MotorIndex] = 0
                        ##########################################################################################################
                        ##########################################################################################################

                        ##########################################################################################################
                        ##########################################################################################################
                        if self.Position_DynamixelUnits_NeedsToBeChangedFlag[MotorIndex] or self.Speed_DynamixelUnits_NeedsToBeChangedFlag[MotorIndex] == 1:

                            Position_limited = self.LimitNumber_FloatOutputOnly(self.Position_DynamixelUnits_Min_UserSet[MotorIndex], self.Position_DynamixelUnits_Max_UserSet[MotorIndex], self.Position_DynamixelUnits_TO_BE_SET[MotorIndex])
                            Speed_limited = self.LimitNumber_FloatOutputOnly(self.Speed_DynamixelUnits_Min_UserSet[MotorIndex], self.Speed_DynamixelUnits_Max_UserSet[MotorIndex], self.Speed_DynamixelUnits_TO_BE_SET[MotorIndex])
                            self.SendInstructionPacket_SetPositionAndSpeed(MotorIndex, Position_limited, Speed_limited, self.GlobalPrintByteSequencesDebuggingFlag)

                            time.sleep(self.TimeBetweenCommands)

                            if self.Position_DynamixelUnits_NeedsToBeChangedFlag[MotorIndex] == 1:
                                self.Position_DynamixelUnits_NeedsToBeChangedFlag[MotorIndex] = 0
                            elif self.Speed_DynamixelUnits_NeedsToBeChangedFlag[MotorIndex] == 1:
                                self.Speed_DynamixelUnits_NeedsToBeChangedFlag[MotorIndex] = 0
                        ##########################################################################################################
                        ##########################################################################################################

                        time.sleep(self.TimeBetweenCommands)  # MUST PAUSE IN BETWEEN MOTORS

                except:
                    exceptions = sys.exc_info()[0]
                    print("DynamixelProtocol1AXorMXseries_ReubenPython3Class, MainThread SETS, exceptions: %s" % exceptions)
                    traceback.print_exc()
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################  End SETs
            self.UpdateFrequencyCalculation_MainThread_Filtered()
            
            if self.MainThread_TimeToSleepEachLoop > 0.0:
                if self.MainThread_TimeToSleepEachLoop > 0.001:
                    time.sleep(self.MainThread_TimeToSleepEachLoop - 0.001) #The "- 0.001" corrects for slight deviation from intended frequency due to other functions being called.
                else:
                    time.sleep(self.MainThread_TimeToSleepEachLoop)
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################

        self.CloseSerialPort()

        self.MyPrint_WithoutLogFile("Finished the MainThread for DynamixelProtocol1AXorMXseries_ReubenPython3Class object.")
        self.MainThread_StillRunningFlag = 0

    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def ExitProgram_Callback(self):

        print("Exiting all threads for DynamixelProtocol1AXorMXseries_ReubenPython3Class object")

        self.EXIT_PROGRAM_FLAG = 1
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def StartGUI(self, GuiParent):

        self.GUI_Thread(GuiParent)
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    def GUI_Thread(self, parent):

        print("Starting the GUI_Thread for DynamixelProtocol1AXorMXseries_ReubenPython3Class object.")

        ##########################################################################################################
        ##########################################################################################################
        self.root = parent
        self.parent = parent
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.myFrame = Frame(self.root)

        if self.UseBorderAroundThisGuiObjectFlag == 1:
            self.myFrame["borderwidth"] = 2
            self.myFrame["relief"] = "ridge"

        self.myFrame.grid(row = self.GUI_ROW,
                          column = self.GUI_COLUMN,
                          padx = self.GUI_PADX,
                          pady = self.GUI_PADY,
                          rowspan = self.GUI_ROWSPAN,
                          columnspan= self.GUI_COLUMNSPAN,
                          sticky = self.GUI_STICKY)
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.TKinter_LightGreenColor = '#%02x%02x%02x' % (150, 255, 150) #RGB
        self.TKinter_LightRedColor = '#%02x%02x%02x' % (255, 150, 150) #RGB
        self.TKinter_LightYellowColor = '#%02x%02x%02x' % (255, 255, 150)  # RGB
        self.TKinter_DefaultGrayColor = '#%02x%02x%02x' % (240, 240, 240)  # RGB
        self.TkinterScaleLabelWidth = 30
        self.TkinterScaleWidth = 10
        self.TkinterScaleLength = 250
        ##########################################################################################################
        ##########################################################################################################

        ########################################################################################################## SET THE DEFAULT FONT FOR ALL WIDGETS CREATED AFTTER/BELOW THIS CALL
        ##########################################################################################################
        default_font = tkFont.nametofont("TkDefaultFont") #TkTextFont, TkFixedFont
        default_font.configure(size=8)
        self.root.option_add("*Font", default_font)
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.LabelsFrame = Frame(self.myFrame)
        self.LabelsFrame["borderwidth"] = 1
        #self.LabelsFrame["relief"] = "ridge"
        self.LabelsFrame.grid(row=0, column=0, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.DeviceInfo_Label = Label(self.LabelsFrame, text="Device Info", width=50)
        self.DeviceInfo_Label.grid(row=0, column=0, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.Data_Label = Label(self.LabelsFrame, text="Data_Label", width=50)
        self.Data_Label.grid(row=0, column=1, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.Error_Label = Label(self.LabelsFrame, text="Error_Label", width=50)
        self.Error_Label.grid(row=0, column=2, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.ButtonsFrame = Frame(self.myFrame)
        self.ButtonsFrame["borderwidth"] = 1
        #self.ButtonsFrame["relief"] = "ridge"
        self.ButtonsFrame.grid(row=1, column=0, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.DisengageAllMotorsButton = Button(self.ButtonsFrame, text="Disengage All Motors", state="normal", bg = "red", width=20,command=lambda i=1: self.DisengageAllMotorsButtonResponse())
        self.DisengageAllMotorsButton.grid(row=0, column=0, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.EngageAllMotorsButton = Button(self.ButtonsFrame, text="Engage All Motors", state="normal", bg = "green", width=20,command=lambda i=1: self.EngageAllMotorsButtonResponse())
        self.EngageAllMotorsButton.grid(row=0, column=1, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.ResetSerialConnectionButton = Button(self.ButtonsFrame, text="Reset Serial", state="normal", bg = "green", width=20,command=lambda i=1: self.ResetSerialConnectionButtonResponse())
        self.ResetSerialConnectionButton.grid(row=0, column=2, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.ScalesFrame = Frame(self.myFrame)
        self.ScalesFrame["borderwidth"] = 1
        #self.ScalesFrame["relief"] = "ridge"
        self.ScalesFrame.grid(row=2, column=0, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.CheckButtonsFrame = Frame(self.myFrame)
        self.CheckButtonsFrame["borderwidth"] = 1
        #self.CheckButtonsFrame["relief"] = "ridge"
        self.CheckButtonsFrame.grid(row=3, column=0, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.Position_Degrees_ScaleLabel = []
        self.Position_Degrees_ScaleValue = []
        self.Position_DynamixelUnits_Scale = []
        self.Speed_Degrees_ScaleLabel = []
        self.Speed_DynamixelUnits_ScaleValue = []
        self.Speed_DynamixelUnits_Scale = []
        self.CWlimit_label = []
        self.CWlimit_StringVar = []
        self.CWlimit_Entry = []
        self.CCWlimit_label = []
        self.CCWlimit_StringVar = []
        self.CCWlimit_Entry = []
        self.MaxTorque_DynamixelUnits_label = []
        self.MaxTorque_DynamixelUnits_StringVar = []
        self.MaxTorque_DynamixelUnits_Entry = []
        self.EngagedState_Checkbutton = []
        self.EngagedState_Checkbutton_Value = []
        self.LEDstate_Checkbutton = []
        self.LEDstate_Checkbutton_Value = []
        self.ContinuousRotationState_Checkbutton = []
        self.ContinuousRotationState_Checkbutton_Value = []
        
        self.ScaleLabelWidth = 8

        for MotorIndex in range(0, self.NumberOfMotors):
            ##########################################################################################################
            self.Position_Degrees_ScaleLabel.append(Label(self.ScalesFrame, text="PosM" + str(MotorIndex), width=self.ScaleLabelWidth))
            self.Position_Degrees_ScaleLabel[MotorIndex].grid(row=0+MotorIndex, column=0, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)

            self.Position_Degrees_ScaleValue.append(DoubleVar())
            self.Position_DynamixelUnits_Scale.append(Scale(self.ScalesFrame, \
                                            #label="Position Deg for Motor : " + str(MotorIndex), \
                                            from_=self.Position_DynamixelUnits_Min_UserSet[MotorIndex],\
                                            to=self.Position_DynamixelUnits_Max_UserSet[MotorIndex],\
                                            #tickinterval=(self.Position_DynamixelUnits_Max_UserSet[MotorIndex] - self.Position_DynamixelUnits_Min_UserSet[MotorIndex]) / 2.0,\
                                            orient=HORIZONTAL,\
                                            borderwidth=2,\
                                            showvalue=1,\
                                            width=self.TkinterScaleWidth,\
                                            length=self.TkinterScaleLength,\
                                            resolution=1,\
                                            variable=self.Position_Degrees_ScaleValue[MotorIndex]))
            self.Position_DynamixelUnits_Scale[MotorIndex].bind('<Button-1>', lambda event, name=MotorIndex: self.Position_DynamixelUnits_ScaleResponse(event, name))
            self.Position_DynamixelUnits_Scale[MotorIndex].bind('<B1-Motion>', lambda event, name=MotorIndex: self.Position_DynamixelUnits_ScaleResponse(event, name))
            self.Position_DynamixelUnits_Scale[MotorIndex].bind('<ButtonRelease-1>', lambda event, name=MotorIndex: self.Position_DynamixelUnits_ScaleResponse(event, name))
            self.Position_DynamixelUnits_Scale[MotorIndex].set(self.Position_DynamixelUnits_StartingValueList[MotorIndex])
            self.Position_DynamixelUnits_Scale[MotorIndex].grid(row=0+MotorIndex, column=1, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
            ##########################################################################################################

            ##########################################################################################################
            self.Speed_Degrees_ScaleLabel.append(Label(self.ScalesFrame, text="SpeedM" + str(MotorIndex), width=self.ScaleLabelWidth))
            self.Speed_Degrees_ScaleLabel[MotorIndex].grid(row=0+MotorIndex, column=2, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)

            self.Speed_DynamixelUnits_ScaleValue.append(DoubleVar())
            self.Speed_DynamixelUnits_Scale.append(Scale(self.ScalesFrame,\
                                                        #label="Speed DynamixelUnits for Motor : " + str(MotorIndex),\
                                                        from_=self.Speed_DynamixelUnits_Min_UserSet[MotorIndex],\
                                                        to=self.Speed_DynamixelUnits_Max_UserSet[MotorIndex],\
                                                        #tickinterval=(self.Speed_DynamixelUnits_Max_UserSet[MotorIndex] - self.Speed_DynamixelUnits_Min_UserSet[MotorIndex]) / 2.0,\
                                                        orient=HORIZONTAL,\
                                                        showvalue=1,\
                                                        width=self.TkinterScaleWidth,\
                                                        length=self.TkinterScaleLength,\
                                                        resolution=1,\
                                                        variable=self.Speed_DynamixelUnits_ScaleValue[MotorIndex]))
            self.Speed_DynamixelUnits_Scale[MotorIndex].bind('<Button-1>', lambda event, name=MotorIndex: self.Speed_DynamixelUnits_ScaleResponse(event, name))
            self.Speed_DynamixelUnits_Scale[MotorIndex].bind('<B1-Motion>', lambda event, name=MotorIndex: self.Speed_DynamixelUnits_ScaleResponse(event, name))
            self.Speed_DynamixelUnits_Scale[MotorIndex].bind('<ButtonRelease-1>', lambda event, name=MotorIndex: self.Speed_DynamixelUnits_ScaleResponse(event, name))
            self.Speed_DynamixelUnits_Scale[MotorIndex].set(self.Speed_DynamixelUnits_StartingValueList[MotorIndex])
            self.Speed_DynamixelUnits_Scale[MotorIndex].grid(row=0+MotorIndex, column=3, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
            ##########################################################################################################

            self.ENTRY_WIDTH = 5
            self.ENTRY_LABEL_WIDTH = 10

            ##########################################################################################################
            self.CWlimit_label.append(Label(self.CheckButtonsFrame, text="CWlimit", width=self.ENTRY_LABEL_WIDTH))
            self.CWlimit_label[MotorIndex].grid(row=0+MotorIndex, column=0, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)

            self.CWlimit_StringVar.append(StringVar())
            self.CWlimit_StringVar[MotorIndex].set(self.CWlimit_StartingValueList[MotorIndex])
            self.CWlimit_Entry.append(Entry(self.CheckButtonsFrame, width=self.ENTRY_WIDTH, state="normal", textvariable=self.CWlimit_StringVar[MotorIndex]))
            self.CWlimit_Entry[MotorIndex].grid(row=0+MotorIndex, column=1, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
            self.CWlimit_Entry[MotorIndex].bind('<Return>', lambda event, name=MotorIndex: self.CWlimit_Entry_Response(event, name))
            ##########################################################################################################

            ##########################################################################################################
            self.CCWlimit_label.append(Label(self.CheckButtonsFrame, text="CCWlimit", width=self.ENTRY_LABEL_WIDTH))
            self.CCWlimit_label[MotorIndex].grid(row=0+MotorIndex, column=2, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)

            self.CCWlimit_StringVar.append(StringVar())
            self.CCWlimit_StringVar[MotorIndex].set(self.CCWlimit_StartingValueList[MotorIndex])
            self.CCWlimit_Entry.append(Entry(self.CheckButtonsFrame, width=self.ENTRY_WIDTH, state="normal", textvariable=self.CCWlimit_StringVar[MotorIndex]))
            self.CCWlimit_Entry[MotorIndex].grid(row=0+MotorIndex, column=3, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
            self.CCWlimit_Entry[MotorIndex].bind('<Return>', lambda event, name=MotorIndex: self.CCWlimit_Entry_Response(event, name))
            ##########################################################################################################

            ##########################################################################################################
            self.MaxTorque_DynamixelUnits_label.append(Label(self.CheckButtonsFrame, text="MaxTorque", width=self.ENTRY_LABEL_WIDTH))
            self.MaxTorque_DynamixelUnits_label[MotorIndex].grid(row=0+MotorIndex, column=4, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)

            self.MaxTorque_DynamixelUnits_StringVar.append(StringVar())
            self.MaxTorque_DynamixelUnits_StringVar[MotorIndex].set(self.MaxTorque_DynamixelUnits_StartingValueList[MotorIndex])
            self.MaxTorque_DynamixelUnits_Entry.append(Entry(self.CheckButtonsFrame, width=self.ENTRY_WIDTH, state="normal", textvariable=self.MaxTorque_DynamixelUnits_StringVar[MotorIndex]))
            self.MaxTorque_DynamixelUnits_Entry[MotorIndex].grid(row=0+MotorIndex, column=5, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
            self.MaxTorque_DynamixelUnits_Entry[MotorIndex].bind('<Return>', lambda event, name=MotorIndex: self.MaxTorque_DynamixelUnits_Entry_Response(event, name))
            ##########################################################################################################

            ##########################################################################################################
            self.EngagedState_Checkbutton_Value.append(DoubleVar())

            if self.EngagedState[MotorIndex] == 1:
                self.EngagedState_Checkbutton_Value[MotorIndex].set(1)
            else:
                self.EngagedState_Checkbutton_Value[MotorIndex].set(0)

            self.EngagedState_Checkbutton.append(Checkbutton(self.CheckButtonsFrame,
                                                            width=15,
                                                            text='Engage M' + str(MotorIndex),
                                                            state="normal",
                                                            variable=self.EngagedState_Checkbutton_Value[MotorIndex]))
            self.EngagedState_Checkbutton[MotorIndex].bind('<ButtonRelease-1>', lambda event,name=MotorIndex: self.EngagedState_CheckbuttonResponse(event, name))
            self.EngagedState_Checkbutton[MotorIndex].grid(row=0+MotorIndex, column=6, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
            ##########################################################################################################

            ##########################################################################################################
            self.LEDstate_Checkbutton_Value.append(DoubleVar())
            self.LEDstate_Checkbutton_Value[MotorIndex].set(0)
            self.LEDstate_Checkbutton.append(Checkbutton(self.CheckButtonsFrame,
                                                            width=15,
                                                            text='LED M' + str(MotorIndex),
                                                            state="normal",
                                                            variable=self.LEDstate_Checkbutton_Value[MotorIndex]))
            self.LEDstate_Checkbutton[MotorIndex].bind('<ButtonRelease-1>', lambda event,name=MotorIndex: self.LEDstate_CheckbuttonResponse(event, name))
            self.LEDstate_Checkbutton[MotorIndex].grid(row=0+MotorIndex, column=7, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
            ##########################################################################################################

            ##########################################################################################################
            self.ContinuousRotationState_Checkbutton_Value.append(DoubleVar())
            self.ContinuousRotationState_Checkbutton_Value[MotorIndex].set(0)
            self.ContinuousRotationState_Checkbutton.append(Checkbutton(self.CheckButtonsFrame,
                                                            width=15,
                                                            text='ContRot M' + str(MotorIndex),
                                                            state="normal",
                                                            variable=self.ContinuousRotationState_Checkbutton_Value[MotorIndex]))
            self.ContinuousRotationState_Checkbutton[MotorIndex].bind('<ButtonRelease-1>', lambda event,name=MotorIndex: self.ContinuousRotationState_CheckbuttonResponse(event, name))
            self.ContinuousRotationState_Checkbutton[MotorIndex].grid(row=0+MotorIndex, column=8, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=1, rowspan=1)
            ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.PrintToGui_Label = Label(self.myFrame, text="PrintToGui_Label", width=75)
        if self.EnableInternal_MyPrint_Flag == 1:
            self.PrintToGui_Label.grid(row=4, column=0, padx=self.GUI_PADX, pady=self.GUI_PADY, columnspan=10, rowspan=10)
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        self.GUI_ready_to_be_updated_flag = 1
        ##########################################################################################################
        ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def CWlimit_Entry_Response(self, event = None, name = "default"):

        MotorNumber = int(name)
        CWlimit_temp = float(self.CWlimit_StringVar[MotorNumber].get())
        self.CWlimit[MotorNumber] = self.LimitTextEntryInput(0.0, 1023.0, CWlimit_temp, self.CWlimit_StringVar[MotorNumber])

        self.CWlimit_TO_BE_SET[MotorNumber] = self.CWlimit[MotorNumber]

        self.CWlimit_NeedsToBeChangedFlag[MotorNumber] = 1

        self.MyPrint_WithoutLogFile("New CWlimit: " + str(self.CWlimit[MotorNumber]))
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def CCWlimit_Entry_Response(self, event = None, name = "default"):

        MotorNumber = int(name)
        CCWlimit_temp = float(self.CCWlimit_StringVar[MotorNumber].get())
        self.CCWlimit[MotorNumber] = self.LimitTextEntryInput(0.0, 1023.0, CCWlimit_temp, self.CCWlimit_StringVar[MotorNumber])

        self.CCWlimit_TO_BE_SET[MotorNumber] = self.CCWlimit[MotorNumber]

        self.CCWlimit_NeedsToBeChangedFlag[MotorNumber] = 1

        self.MyPrint_WithoutLogFile("New CCWlimit: " + str(self.CCWlimit[MotorNumber]))
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def MaxTorque_DynamixelUnits_Entry_Response(self, event = None, name = "default"):

        MotorNumber = int(name)
        MaxTorque_DynamixelUnits_temp = float(self.MaxTorque_DynamixelUnits_StringVar[MotorNumber].get())
        self.MaxTorque_DynamixelUnits[MotorNumber] = self.LimitTextEntryInput(0.0, 1023.0, MaxTorque_DynamixelUnits_temp, self.MaxTorque_DynamixelUnits_StringVar[MotorNumber])

        self.MaxTorque_DynamixelUnits_TO_BE_SET[MotorNumber] = self.MaxTorque_DynamixelUnits[MotorNumber]

        self.MaxTorque_DynamixelUnits_NeedsToBeChangedFlag[MotorNumber] = 1

        self.MyPrint_WithoutLogFile("New MaxTorque_DynamixelUnits: " + str(self.MaxTorque_DynamixelUnits[MotorNumber]))
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    def GUI_update_clock(self):

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        if self.USE_GUI_FLAG == 1 and self.EXIT_PROGRAM_FLAG == 0:

            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            if self.GUI_ready_to_be_updated_flag == 1:

                ##########################################################################################################
                ##########################################################################################################
                ##########################################################################################################
                try:
                    ##########################################################################################################
                    ##########################################################################################################
                    self.DeviceInfo_Label["text"] = "NameToDisplay_UserSet: " + str(self.NameToDisplay_UserSet) + \
                                            "\nModelNumber: " + str(self.ModelNumber_Received) + \
                                            "\nFWversion: " + str(self.FWversion_Received) + \
                                            "\nID: " + str(self.ID_Received) + \
                                            "\nReturnDelayTimeMicroSeconds: " + str(self.ReturnDelayTimeMicroSeconds_Received) + \
                                            "\nTemperatureHighestLimit_Received: " + str(self.TemperatureHighestLimit_Received) + \
                                            "\nVoltageLowestLimit: " + str(self.VoltageLowestLimit_Received) + \
                                            "\nVoltageHighesttLimit: " + str(self.VoltageLowestLimit_Received)
                    ##########################################################################################################
                    ##########################################################################################################

                    ##########################################################################################################
                    ##########################################################################################################
                    self.Data_Label["text"] = "Position_DynamixelUnits_TO_BE_SET: " + self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(self.Position_DynamixelUnits_TO_BE_SET, 0, 3) + \
                                            "\nPos: " + self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(self.PositionReceived_Degrees, 0, 3) + \
                                            "\nSpeed: " + self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(self.SpeedReceived_DegreesPerSecond, 0, 3) + \
                                            "\nTorque: " + self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(self.TorqueReceived_DynamixelUnits, 0, 3) + \
                                            "\nVoltage: " + self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(self.VoltageReceived_Volts, 0, 3) + \
                                            "\nTemperature DegC: " + self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(self.TemperatureReceived_DegC, 0, 3) + \
                                            "\nCWangleLimit: " + self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(self.CWangleLimit_Received, 0, 3) + \
                                            "\nCCWangleLimit: " + self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(self.CCWangleLimit_Received, 0, 3) + \
                                            "\nEngaged: " + str(self.EngagedState) + \
                                            "\nLEDstate: " + str(self.LEDstate) + \
                                            "\n" +\
                                            "\nTime: " + self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(self.CurrentTime_CalculatedFromMainThread) +\
                                            "\nData Frequency: " + self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(self.DataStreamingFrequency_CalculatedFromMainThread)

                                            #"\nGoalPos: " + self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(self.GoalPositionReceived_Degrees, 0, 3) + \

                    ##########################################################################################################
                    ##########################################################################################################

                    ##########################################################################################################
                    ##########################################################################################################
                    self.Error_Label["text"] = self.ConvertDictToProperlyFormattedStringForPrinting(self.ErrorFlagStates_DictEnglishNameAsKey)
                    ##########################################################################################################
                    ##########################################################################################################

                    ##########################################################################################################
                    ##########################################################################################################
                    for MotorIndex in range(0, self.NumberOfMotors):
                        
                        ##########################################################################################################
                        if self.Position_DynamixelUnits_GUI_NeedsToBeChangedFlag[MotorIndex] == 1:
                            self.Position_DynamixelUnits_Scale[MotorIndex].set(self.Position_DynamixelUnits_TO_BE_SET[MotorIndex])
                            self.Position_DynamixelUnits_GUI_NeedsToBeChangedFlag[MotorIndex] = 0
                        ##########################################################################################################

                        ##########################################################################################################
                        if self.Speed_DynamixelUnits_GUI_NeedsToBeChangedFlag[MotorIndex] == 1:
                            self.Speed_DynamixelUnits_Scale[MotorIndex].set(self.Speed_DynamixelUnits_TO_BE_SET[MotorIndex])
                            self.Speed_DynamixelUnits_GUI_NeedsToBeChangedFlag[MotorIndex] = 0
                        ##########################################################################################################

                        ##########################################################################################################
                        if self.EngagedState_GUI_NeedsToBeChangedFlag[MotorIndex] == 1:

                            if self.EngagedState_TO_BE_SET[MotorIndex] == 1: #This actually changes how the widget looks
                                self.EngagedState_Checkbutton[MotorIndex].select()
                            elif self.EngagedState_TO_BE_SET[MotorIndex] == 0:
                                self.EngagedState_Checkbutton[MotorIndex].deselect()

                            self.EngagedState_GUI_NeedsToBeChangedFlag[MotorIndex] = 0
                        ##########################################################################################################

                        ##########################################################################################################
                        if self.LEDstate_GUI_NeedsToBeChangedFlag[MotorIndex] == 1:

                            if self.LEDstate_TO_BE_SET[MotorIndex] == 1: #This actually changes how the widget looks
                                self.LEDstate_Checkbutton[MotorIndex].select()
                            elif self.LEDstate_TO_BE_SET[MotorIndex] == 0:
                                self.LEDstate_Checkbutton[MotorIndex].deselect()

                            self.LEDstate_GUI_NeedsToBeChangedFlag[MotorIndex] = 0
                        ##########################################################################################################

                        ##########################################################################################################
                        if self.ContinuousRotationState_GUI_NeedsToBeChangedFlag[MotorIndex] == 1:

                            if self.ContinuousRotationState_TO_BE_SET[MotorIndex] == 1: #This actually changes how the widget looks
                                self.ContinuousRotationState_Checkbutton[MotorIndex].select()
                            elif self.ContinuousRotationState_TO_BE_SET[MotorIndex] == 0:
                                self.ContinuousRotationState_Checkbutton[MotorIndex].deselect()

                            self.ContinuousRotationState_GUI_NeedsToBeChangedFlag[MotorIndex] = 0
                        ##########################################################################################################

                        ##########################################################################################################
                        if self.EngagedState[MotorIndex] == 1:
                            self.Position_DynamixelUnits_Scale[MotorIndex]["troughcolor"] = self.TKinter_LightGreenColor
                            self.Speed_DynamixelUnits_Scale[MotorIndex]["troughcolor"] = self.TKinter_LightGreenColor
                        else:
                            self.Position_DynamixelUnits_Scale[MotorIndex]["troughcolor"] = self.TKinter_LightRedColor
                            self.Speed_DynamixelUnits_Scale[MotorIndex]["troughcolor"] = self.TKinter_LightRedColor
                        ##########################################################################################################

                    ##########################################################################################################
                    ##########################################################################################################
                    
                    ##########################################################################################################
                    self.PrintToGui_Label.config(text=self.PrintToGui_Label_TextInput_Str)
                    ##########################################################################################################

                ##########################################################################################################
                ##########################################################################################################
                ##########################################################################################################

                ##########################################################################################################
                ##########################################################################################################
                ##########################################################################################################
                except:
                    exceptions = sys.exc_info()[0]
                    print("DynamixelProtocol1AXorMXseries_ReubenPython3Class GUI_update_clock ERROR: Exceptions: %s" % exceptions)
                    traceback.print_exc()
                ##########################################################################################################
                ##########################################################################################################
                ##########################################################################################################

            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################
            ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def Position_DynamixelUnits_ScaleResponse(self, event, name):

        MotorIndex = name
        self.Position_DynamixelUnits_TO_BE_SET[MotorIndex] = self.Position_Degrees_ScaleValue[MotorIndex].get()
        self.Position_DynamixelUnits_NeedsToBeChangedFlag[MotorIndex] = 1

        #self.MyPrint_WithoutLogFile("ScaleResponse: Position set to: " + str(self.Position_DynamixelUnits_TO_BE_SET[MotorIndex]) + " on motor " + str(MotorIndex))
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def Speed_DynamixelUnits_ScaleResponse(self, event, name):

        MotorIndex = name
        self.Speed_DynamixelUnits_TO_BE_SET[MotorIndex] = self.Speed_DynamixelUnits_ScaleValue[MotorIndex].get()
        self.Speed_DynamixelUnits_NeedsToBeChangedFlag[MotorIndex] = 1

        #self.MyPrint_WithoutLogFile("ScaleResponse: Speed set to: " + str(self.Speed_DynamixelUnits_TO_BE_SET[MotorIndex]) + " on motor " + str(MotorIndex))
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def EngagedState_CheckbuttonResponse(self, event, name):

        MotorIndex = name
        temp_value = self.EngagedState_Checkbutton_Value[MotorIndex].get()

        if temp_value == 0:
            self.EngagedState_TO_BE_SET[MotorIndex] = 1 ########## This reversal is needed for the variable state to match the checked state, but we don't know why
        elif temp_value == 1:
            self.EngagedState_TO_BE_SET[MotorIndex] = 0

        self.EngagedState_NeedsToBeChangedFlag[MotorIndex] = 1
        self.MyPrint_WithoutLogFile("EngagedState_CheckbuttonResponse: EngagedState changed to " + str(self.EngagedState_TO_BE_SET[MotorIndex]) + " on motor " + str(MotorIndex))
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def LEDstate_CheckbuttonResponse(self, event, name):

        MotorIndex = name
        temp_value = self.LEDstate_Checkbutton_Value[MotorIndex].get()

        if temp_value == 0:
            self.LEDstate_TO_BE_SET[MotorIndex] = 1 ########## This reversal is needed for the variable state to match the checked state, but we don't know why
        elif temp_value == 1:
            self.LEDstate_TO_BE_SET[MotorIndex] = 0

        self.LEDstate_NeedsToBeChangedFlag[MotorIndex] = 1
        #self.MyPrint_WithoutLogFile("LEDstate_CheckbuttonResponse: LEDstate changed to " + str(self.LEDstate_TO_BE_SET[MotorIndex]) + " on motor " + str(MotorIndex))
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def ContinuousRotationState_CheckbuttonResponse(self, event, name):

        MotorIndex = name
        temp_value = self.ContinuousRotationState_Checkbutton_Value[MotorIndex].get()

        if temp_value == 0:
            self.ContinuousRotationState_TO_BE_SET[MotorIndex] = 1 ########## This reversal is needed for the variable state to match the checked state, but we don't know why
        elif temp_value == 1:
            self.ContinuousRotationState_TO_BE_SET[MotorIndex] = 0

        self.ContinuousRotationState_NeedsToBeChangedFlag[MotorIndex] = 1
        self.MyPrint_WithoutLogFile("ContinuousRotationState_CheckbuttonResponse: ContinuousRotationState changed to " + str(self.ContinuousRotationState_TO_BE_SET[MotorIndex]) + " on motor " + str(MotorIndex))
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def DisengageAllMotorsButtonResponse(self):

        for MotorIndex in range(0, len(self.EngagedState_TO_BE_SET)):
            if self.MotorType_StringList[MotorIndex] != "None":
                self.EngagedState_TO_BE_SET[MotorIndex] = 0
                self.EngagedState_NeedsToBeChangedFlag[MotorIndex] = 1

        self.MyPrint_WithoutLogFile("DisengageAllMotorsButtonResponse")
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def EngageAllMotorsButtonResponse(self):

        for MotorIndex in range(0, len(self.EngagedState_TO_BE_SET)):
            if self.MotorType_StringList[MotorIndex]  != "None":
                self.EngagedState_TO_BE_SET[MotorIndex] = 1
                self.EngagedState_NeedsToBeChangedFlag[MotorIndex] = 1

        self.MyPrint_WithoutLogFile("EngageAllMotorsButtonResponse")
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def ResetSerialConnectionButtonResponse(self):

        self.ResetSerialConnection_EventNeedsToBeFiredFlag = 1

        self.MyPrint_WithoutLogFile("ResetSerialConnectionButtonResponse")
    ##########################################################################################################
    ##########################################################################################################
    
    ##########################################################################################################
    ##########################################################################################################
    def MyPrint_WithoutLogFile(self, input_string):

        input_string = str(input_string)

        if input_string != "":

            #input_string = input_string.replace("\n", "").replace("\r", "")

            ################################ Write to console
            # Some people said that print crashed for pyinstaller-built-applications and that sys.stdout.write fixed this.
            # http://stackoverflow.com/questions/13429924/pyinstaller-packaged-application-works-fine-in-console-mode-crashes-in-window-m
            if self.PrintToConsoleFlag == 1:
                sys.stdout.write(input_string + "\n")
            ################################

            ################################ Write to GUI
            self.PrintToGui_Label_TextInputHistory_List.append(self.PrintToGui_Label_TextInputHistory_List.pop(0)) #Shift the list
            self.PrintToGui_Label_TextInputHistory_List[-1] = str(input_string) #Add the latest value

            self.PrintToGui_Label_TextInput_Str = ""
            for Counter, Line in enumerate(self.PrintToGui_Label_TextInputHistory_List):
                self.PrintToGui_Label_TextInput_Str = self.PrintToGui_Label_TextInput_Str + Line

                if Counter < len(self.PrintToGui_Label_TextInputHistory_List) - 1:
                    self.PrintToGui_Label_TextInput_Str = self.PrintToGui_Label_TextInput_Str + "\n"
            ################################

    ##########################################################################################################
    ##########################################################################################################
    
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    def ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(self, input, number_of_leading_numbers = 4, number_of_decimal_places = 3):

        number_of_decimal_places = max(1, number_of_decimal_places) #Make sure we're above 1

        ListOfStringsToJoin = []

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        if isinstance(input, str) == 1:
            ListOfStringsToJoin.append(input)
        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        elif isinstance(input, int) == 1 or isinstance(input, float) == 1:
            element = float(input)
            prefix_string = "{:." + str(number_of_decimal_places) + "f}"
            element_as_string = prefix_string.format(element)

            ##########################################################################################################
            ##########################################################################################################
            if element >= 0:
                element_as_string = element_as_string.zfill(number_of_leading_numbers + number_of_decimal_places + 1 + 1)  # +1 for sign, +1 for decimal place
                element_as_string = "+" + element_as_string  # So that our strings always have either + or - signs to maintain the same string length
            else:
                element_as_string = element_as_string.zfill(number_of_leading_numbers + number_of_decimal_places + 1 + 1 + 1)  # +1 for sign, +1 for decimal place
            ##########################################################################################################
            ##########################################################################################################

            ListOfStringsToJoin.append(element_as_string)
        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        elif isinstance(input, list) == 1:

            if len(input) > 0:
                for element in input: #RECURSION
                    ListOfStringsToJoin.append(self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(element, number_of_leading_numbers, number_of_decimal_places))

            else: #Situation when we get a list() or []
                ListOfStringsToJoin.append(str(input))

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        elif isinstance(input, tuple) == 1:

            if len(input) > 0:
                for element in input: #RECURSION
                    ListOfStringsToJoin.append("TUPLE" + self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(element, number_of_leading_numbers, number_of_decimal_places))

            else: #Situation when we get a list() or []
                ListOfStringsToJoin.append(str(input))

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        elif isinstance(input, dict) == 1:

            if len(input) > 0:
                for Key in input: #RECURSION
                    ListOfStringsToJoin.append(str(Key) + ": " + self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(input[Key], number_of_leading_numbers, number_of_decimal_places))

            else: #Situation when we get a dict()
                ListOfStringsToJoin.append(str(input))

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        else:
            ListOfStringsToJoin.append(str(input))
        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################

        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################
        if len(ListOfStringsToJoin) > 1:

            ##########################################################################################################
            ##########################################################################################################

            ##########################################################################################################
            StringToReturn = ""
            for Index, StringToProcess in enumerate(ListOfStringsToJoin):

                ################################################
                if Index == 0: #The first element
                    if StringToProcess.find(":") != -1 and StringToProcess[0] != "{": #meaning that we're processing a dict()
                        StringToReturn = "{"
                    elif StringToProcess.find("TUPLE") != -1 and StringToProcess[0] != "(":  # meaning that we're processing a tuple
                        StringToReturn = "("
                    else:
                        StringToReturn = "["

                    StringToReturn = StringToReturn + StringToProcess.replace("TUPLE","") + ", "
                ################################################

                ################################################
                elif Index < len(ListOfStringsToJoin) - 1: #The middle elements
                    StringToReturn = StringToReturn + StringToProcess + ", "
                ################################################

                ################################################
                else: #The last element
                    StringToReturn = StringToReturn + StringToProcess

                    if StringToProcess.find(":") != -1 and StringToProcess[-1] != "}":  # meaning that we're processing a dict()
                        StringToReturn = StringToReturn + "}"
                    elif StringToProcess.find("TUPLE") != -1 and StringToProcess[-1] != ")":  # meaning that we're processing a tuple
                        StringToReturn = StringToReturn + ")"
                    else:
                        StringToReturn = StringToReturn + "]"

                ################################################

            ##########################################################################################################

            ##########################################################################################################
            ##########################################################################################################

        elif len(ListOfStringsToJoin) == 1:
            StringToReturn = ListOfStringsToJoin[0]

        else:
            StringToReturn = ListOfStringsToJoin

        return StringToReturn
        ##########################################################################################################
        ##########################################################################################################
        ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################
    ##########################################################################################################

    ##########################################################################################################
    ##########################################################################################################
    def ConvertDictToProperlyFormattedStringForPrinting(self, DictToPrint, NumberOfDecimalsPlaceToUse = 3, NumberOfEntriesPerLine = 1, NumberOfTabsBetweenItems = 3):

        ProperlyFormattedStringForPrinting = ""
        ItemsPerLineCounter = 0

        for Key in DictToPrint:

            ##########################################################################################################
            if isinstance(DictToPrint[Key], dict): #RECURSION
                ProperlyFormattedStringForPrinting = ProperlyFormattedStringForPrinting + \
                                                     str(Key) + ":\n" + \
                                                     self.ConvertDictToProperlyFormattedStringForPrinting(DictToPrint[Key], NumberOfDecimalsPlaceToUse, NumberOfEntriesPerLine, NumberOfTabsBetweenItems)

            else:
                ProperlyFormattedStringForPrinting = ProperlyFormattedStringForPrinting + \
                                                     str(Key) + ": " + \
                                                     self.ConvertFloatToStringWithNumberOfLeadingNumbersAndDecimalPlaces_NumberOrListInput(DictToPrint[Key], 0, NumberOfDecimalsPlaceToUse)
            ##########################################################################################################

            ##########################################################################################################
            if ItemsPerLineCounter < NumberOfEntriesPerLine - 1:
                ProperlyFormattedStringForPrinting = ProperlyFormattedStringForPrinting + "\t"*NumberOfTabsBetweenItems
                ItemsPerLineCounter = ItemsPerLineCounter + 1
            else:
                ProperlyFormattedStringForPrinting = ProperlyFormattedStringForPrinting + "\n"
                ItemsPerLineCounter = 0
            ##########################################################################################################

        return ProperlyFormattedStringForPrinting
    ##########################################################################################################
    ##########################################################################################################
