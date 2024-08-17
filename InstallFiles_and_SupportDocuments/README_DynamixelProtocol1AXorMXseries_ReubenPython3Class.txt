###########################

DynamixelProtocol1AXorMXseries_ReubenPython3Class

Code (including ability to hook to Tkinter GUI) to control Dynamixel motors that use Protocol 1 (AX and MX series, possibly others).

Reuben Brewer, Ph.D.

reuben.brewer@gmail.com

www.reubotics.com

Apache 2 License

Software Revision H, 08/17/2024

Verified working on:

Python 3.8

Windows 10/11, 64-bit

Raspberry Pi Buster

(no Mac testing yet)

This code works ONLY for Dynamixel's Protocol 1 (AX series and MX series, although some MX series can do either Protocol 1 OR 2).

To use this code, you'll need to find the unique Serial Number for your U2D2, following the instructions in the included image "FindingTheSerialNumberOfU2D2inWindows.png".

You will also need to configure your Dynamixel motor (including Motor ID and Baud Rate) within DynamixelWizard2.0
(downloaded from the Robotis website: https://www.robotis.com/service/download.php?no=1670).
MX-64AR motors default to 57600bps, but they can go faster (some models up to 2MBPs, some even higher).
AX-series motors default to 1Mbps (its maximum rate)

You can test sending raw byte sequences (only for blinking on/off the LED) in Python with the following file:
StandAloneTest_LEDblink_DynamixelProtocol1AXorMXseries.py

You can test sending raw byte sequences in Docklight (https://docklight.de/) with the following file:
InstallFiles_and_SupportDocuments\Docklight_StandAloneTest_DynamixelProtocol1AXorMXseries.ptp

###########################

########################### Installation instructions

This code isn't "installed" like a typical python module (no "pip install MyModule"). If you want to call it in your own code, you'll need to import a local copy of the files.

###

Windows and Raspberry Pi:

DynamixelProtocol1AXorMXseries_ReubenPython3Class, ListOfModuleDependencies: ['ftd2xx', 'LowPassFilter_ReubenPython2and3Class', 'serial', 'serial.tools']

DynamixelProtocol1AXorMXseries_ReubenPython3Class, ListOfModuleDependencies_TestProgram: ['MyPlotterPureTkinterStandAloneProcess_ReubenPython2and3Class', 'MyPrint_ReubenPython2and3Class']

DynamixelProtocol1AXorMXseries_ReubenPython3Class, ListOfModuleDependencies_NestedLayers: ['future.builtins', 'numpy', 'pexpect', 'psutil']

DynamixelProtocol1AXorMXseries_ReubenPython3Class, ListOfModuleDependencies_All:['ftd2xx', 'future.builtins', 'LowPassFilter_ReubenPython2and3Class', 'MyPlotterPureTkinterStandAloneProcess_ReubenPython2and3Class', 'MyPrint_ReubenPython2and3Class', 'numpy', 'pexpect', 'psutil', 'serial', 'serial.tools']

pip install psutil

pip install pyserial (NOT pip install serial).

pip install ftd2xx, ##https://pypi.org/project/ftd2xx/ #version 1.3.3 as of 11/08/23. For SetAllFTDIdevicesLatencyTimer function.

###

###

The official dynamixel_sdk ("import dynamixel_sdk") from Robotis appears broken for Protocol in Reuben's testing (tried DynamixelSDK-3.7.21),
so we won't install that in this case.

###

###

Set USB-Serial latency_timer

In Windows:

Manual method:

Follow the instructions in the included image "LatencyTimer_SetManuallyInWindows.png".

Automated method:

python LatencyTimer_DynamixelU2D2_ReadAndWrite_Windows.py

In Linux (including Raspberry Pi):

Run the included script:

sudo ./LatencyTimer_Set_LinuxScript.sh 1

###

###########################

########################### FTDI installation instructions, Windows

(more to come)

###########################