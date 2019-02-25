import sys
import logging
from PyQt5 import QtCore,QtGui,QtWidgets,uic
from PyQt5.QtCore import QThread, pyqtSignal
import time

import VisaHandler

baseUIClass, baseUIWidget = uic.loadUiType('PlasmaCtrlDlg.ui')

#decorators for setting plasma status
def _ReadyStatus(f):
    def wrapper(*args):
        out = f(args[0])
        args[0].PlasmaStatus.setText('Ready')
        return out
    return wrapper

def _SetStatus(text):
    def real_decorator(func):
        def wrapper(*args):
            args[0].PlasmaStatus.setText(text)
            return func(args[0])
        return wrapper
    return real_decorator

class HeatCathodeThread(QThread):
    def __init__(self,device):
        QThread.__init__(self)
        self._device = device 
        self._current_readback = 0
        
    def __del__(self):
        self.wait()

    def run(self):
        #logic
        while self._current_readback < 1010:
            logging.debug(self._current_readback)
            self._current_readback+=16
            self.sleep(10)

class Logic(baseUIWidget,baseUIClass):
    def __init__(self,parent=None):
        super(Logic,self).__init__(parent)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.Update)
        
        self.setupUi(self)

        
        
    def OnInitializeClicked(self):
        #open config file and initialize connections
        logging.debug("Initialize button clicked")
        self.PlasmaStatus.setText('Initialization')
        self.timer.start(5000)
        
        #connections to the TDK power supplies
        #power supplies are connected via Ethernet in a chain with the heater one
        #the main one and the discharge as secondary
        #access to either one is done via the select_RS485_device() method
       
        tdk_address = 'TCPIP0::192.168.0.73::inst0::INSTR'
        self.heater_RS485 = 1
        self.discharge_RS485 = 0
        
        self.TDK_PS = VisaHandler.VisaHandler(tdk_address)

        #set devices to output state
        self.TDK_PS.select_RS485_device(self.discharge_RS485)
        self.TDK_PS.write('OUTP:STAT 1')

        self.TDK_PS.select_RS485_device(self.heater_RS485)
        self.TDK_PS.write('OUTP:STAT 1')
        
        solenoid_address = 'TCPIP0::192.168.0.8::gpib0,25::INSTR'
        self.SOLENOID_PS = VisaHandler.VisaHandler(solenoid_address,RS485_enabled=False,error_query='ERR?')
        self.SOLENOID_PS.write('OUT 1')

        self.PlasmaStatus.setText('Ready')
        
    def OnSOLENOIDVSetChanged(self):
        #Send cmmands to DCR55 over GPIB to change voltage setting
        self.PlasmaStatus.setText('Set solenoid voltage')
        
        logging.debug("enter pressed on DCR55VSet")
        self.SOLENOID_PS.write('VSET {:3.2f}'.format(float(self.SOLENOIDVSet.text())))
        self.PlasmaStatus.setText('Ready')
        
		
    def OnSOLENOIDISetChanged(self):
        #Send cmmands to DCR55 over GPIB to change Current setting
        self.PlasmaStatus.setText('Set solenoid current')
        
        logging.debug("enter pressed on DCR55ISet")
        self.SOLENOID_PS.write('ISET {:3.2f}'.format(float(self.SOLENOIDISet.text())))
        self.PlasmaStatus.setText('Ready')
        
		
    def OnHEATERVSetChanged(self):
        #Send cmmands to Heater TDK over ethernet to change voltage setting
        logging.debug("enter pressed on TDK#1VSet")
        self.PlasmaStatus.setText('Set heater voltage')
        self.TDK_PS.select_RS485_device(self.heater_RS485)
        self.TDK_PS.write(':VOLT {:3.2f}'.format(float(self.HEATERVSet.text())))
        self.PlasmaStatus.setText('Ready')
        
        
    def OnHEATERISetChanged(self):
        #Send cmmands to Heater over ethernet to change current setting
        logging.debug("enter pressed on TDK#1ISet")
        self.PlasmaStatus.setText('Set heater current')
        self.TDK_PS.select_RS485_device(self.heater_RS485)
        self.TDK_PS.write(':CURR {:3.2f}'.format(float(self.HEATERISet.text())))
        self.PlasmaStatus.setText('Ready')
        

    def OnDISCHARGEVSetChanged(self):
        #Send cmmands to Discharge over ethernet to change voltage setting
        logging.debug("enter pressed on TDK#2VSet")
        self.PlasmaStatus.setText('Set discharge voltage')
        self.TDK_PS.select_RS485_device(self.discharge_RS485)
        self.TDK_PS.write(':VOLT {:3.2f}'.format(float(self.DISCHARGEVSet.text())))
        self.PlasmaStatus.setText('Ready')
        
        
    def OnDISCHARGEISetChanged(self):
        #Send cmmands to TDK#2 over ethernet to change current setting
        logging.debug("enter pressed on TDK#2ISet")
        self.PlasmaStatus.setText('Set discharge current')
        self.TDK_PS.select_RS485_device(self.discharge_RS485)
        self.TDK_PS.write(':CURR {:3.2f}'.format(float(self.DISCHARGEISet.text())))
        self.PlasmaStatus.setText('Ready')
                
        
    def OnCloseButtonClicked(self):
        #close the devices then close the ui
        logging.debug("enter pressed on Close button")
        self.timer.stop()
        
    def OnUpdateClicked(self):
        self.Update()
        
    def Update(self):
        self.PlasmaStatus.setText('Updating')
        #update the values of TDIK power supplies
        self.TDK_PS.select_RS485_device(self.discharge_RS485)
        self.DISCHARGEVRead.setText(self.TDK_PS.query('MEAS:VOLT?'))
        self.DISCHARGEIRead.setText(self.TDK_PS.query('MEAS:CURR?'))

        self.TDK_PS.select_RS485_device(self.heater_RS485)
        self.HEATERVRead.setText(self.TDK_PS.query('MEAS:VOLT?'))
        self.HEATERIRead.setText(self.TDK_PS.query('MEAS:CURR?'))
        #self.TDK_PS.unlock()
        
        self.SOLENOIDIRead.setText(self.SOLENOID_PS.query('IOUT?').split(' ')[-1])
        self.SOLENOIDVRead.setText(self.SOLENOID_PS.query('VOUT?').split(' ')[-1])
        self.PlasmaStatus.setText('Ready')

    def done(self):
        self.PlasmaStatus.setText('Done heating')
        
    def HeatCathodeToggle(self,pressed):
        if pressed:
            self.HEATERVSet.setStyleSheet('background-color: rgb(237,139,137);')
            self.HEATERISet.setStyleSheet('background-color: rgb(237,139,137);')

            self.heat_thread = HeatCathodeThread(None)
            #self.connect(self.heat_thread,pyqtSignal('finished()'),self.done)
            self.heat_thread.start()
            
            #self.PlasmaStatus.setText('Heating Cathode')
            #self.TDK_PS.select_RS485_device(self.heater_RS485)

            #increase heater current by 100A per 60s or 16A every 10s
            #get starting current
            #current_readback = float(self.TDK_PS.query('MEAS:CURR?')) 
            #current_readback = 0


            
            #while current_readback < 1010:
                #current_readback = current_readback + 16
                #self.TDK_PS.write(':CURR {:3.2f}'.format(current_readback + 16))
                #time.sleep(10)
                #current_readback = self.TDK_PS.query('MEAS:CURR?')
                #self.HEATERVRead.setText(self.TDK_PS.query('MEAS:VOLT?'))
                #self.HEATERIRead.setText(self.TDK_PS.query('MEAS:CURR?'))
        
            
        else:
            self.HEATERISet.setStyleSheet('background-color: white;')
            

    def CoolCathodeToggle(self):
        pass
        

def main():
    logging.basicConfig(level=logging.DEBUG)
    app = QtWidgets.QApplication(sys.argv)
    ui = Logic(None)
    ui.show()
    sys.exit(app.exec_())

if __name__=='__main__':
    main()
