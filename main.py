import sys
import logging
from PyQt5 import QtCore,QtGui,QtWidgets,uic

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
        

class Logic(baseUIWidget,baseUIClass):
    def __init__(self,parent=None):
        super(Logic,self).__init__(parent)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.Update)
        self.timer.start(5000)
        
        self.setupUi(self)

    def OnInitializeClicked(self):
        #open config file and initialize connections
        logging.debug("Initialize button clicked")
        #self.timer.start(2000)
        
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

        #self.PlasmaStatus.setText('Ready')
        
    def OnSOLENOIDVSetChanged(self):
        #Send cmmands to DCR55 over GPIB to change voltage setting
        logging.debug("enter pressed on DCR55VSet")
        self.SOLENOID_PS.write('VSET {:3.2f}'.format(float(self.SOLENOIDVSet.text())))
        
		
    def OnSOLENOIDISetChanged(self):
        #Send cmmands to DCR55 over GPIB to change Current setting
        logging.debug("enter pressed on DCR55ISet")
        self.SOLENOID_PS.write('ISET {:3.2f}'.format(float(self.SOLENOIDISet.text())))

		
    def OnHEATERVSetChanged(self):
        #Send cmmands to Heater TDK over ethernet to change voltage setting
        logging.debug("enter pressed on TDK#1VSet")
        self.TDK_PS.select_RS485_device(self.heater_RS485)
        self.TDK_PS.write(':VOLT {:3.2f}'.format(float(self.HEATERVSet.text())))
        
        
    def OnHEATERISetChanged(self):
        #Send cmmands to Heater over ethernet to change current setting
        logging.debug("enter pressed on TDK#1ISet")
        self.TDK_PS.select_RS485_device(self.heater_RS485)
        self.TDK_PS.write(':CURR {:3.2f}'.format(float(self.HEATERISet.text())))
        

    def OnDISCHARGEVSetChanged(self):
        #Send cmmands to Discharge over ethernet to change voltage setting
        logging.debug("enter pressed on TDK#2VSet")
        self.TDK_PS.select_RS485_device(self.discharge_RS485)
        self.TDK_PS.write(':VOLT {:3.2f}'.format(float(self.DISCHARGEVSet.text())))
        logging.debug('done setting voltage')
        
    def OnDISCHARGEISetChanged(self):
        #Send cmmands to TDK#2 over ethernet to change current setting
        logging.debug("enter pressed on TDK#2ISet")
        self.TDK_PS.select_RS485_device(self.discharge_RS485)
        self.TDK_PS.write(':CURR {:3.2f}'.format(float(self.DISCHARGEISet.text())))
        #self.TDK_PS.unlock()
        
    def OnHeatCathodeClicked(self):
        pass

    def OnCoolCathodeClicked(self):
        pass
        
        
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
    
    
        

def main():
    logging.basicConfig(level=logging.DEBUG)
    app = QtWidgets.QApplication(sys.argv)
    ui = Logic(None)
    ui.show()
    sys.exit(app.exec_())

if __name__=='__main__':
    main()
