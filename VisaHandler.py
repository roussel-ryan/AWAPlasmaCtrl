import logging
import visa
import time

class VisaHandler(object):

    _resource_manager = visa.ResourceManager()

    def __init__(self, address, RS485_enabled=True):
        self._address = address
        self._RS485_address = None
        self._RS485_enabled = RS485_enabled
        self._connection = None
        self._logger = logging.getLogger('VisaHandler')
        self.connect()

    def connect(self):
        assert self._connection is None
        self._logger.debug('connecting to visa device'.format(self._address))
        try:
            self._connection = self._resource_manager.open_resource(self._address)
        except visa.VisaIOError as e:
            self._logger.exception(e)
            self._logger.debug('\033[31munable to connect to visa device\033[0m')

    def disconnect(self):
        if self._connection is not None:
            self._logger.debug('disconnecting from visa device')
            print(dir(self._connection))
            assert False
            self._connection = None
            self._RS485_address = None

    def write(self, command):
        if self._connection is not None:
            if self._RS485_enabled:
                assert self._RS485_address is not None
                
            self._logger.debug('sending command \'{}\' to visa device (write)'.format(command))
            self._connection.write(command)
            time.sleep(0.115)
            self.checkErrors()
            
            
    def query(self, command):
        if self._connection is not None:
            if self._RS485_enabled:
                assert self._RS485_address is not None

            self._logger.debug('sending command \'{}\' to visa device (read)'.format(command))
            result = self._connection.query(command)
            time.sleep(0.115)
            self._logger.debug('recieved response \'{}\' from visa device'.format(result))
            self.checkErrors()
            return result
        return None

    def select_RS485_device(self, RS485_address):
        assert self._RS485_enabled
        if self._connection:
            if self._RS485_address != RS485_address:
                self._RS485_address = RS485_address
                self.write('INST:SEL {:02}'.format(RS485_address))
                self._RS485_address = RS485_address
                self.checkErrors()
                self._logger.info('Selected RS485 address {:02}'.format(RS485_address))
                time.sleep(0.3)
                
    def checkErrors(self):
        if self._connection:
            if self._RS485_enabled:
                assert self._RS485_address is not None

            try:
                msg = self._connection.query('SYST:ERR?')
                time.sleep(0.050)
                assert msg.split(',')[0] is '0'
            except AssertionError:
                logging.warning(msg)

            try:
                msg = self._connection.query('ERR?')
                time.sleep(0.050)
                assert msg.split('   ')[1] is '0' or '8'
            except AssertionError:
                logging.warning(msg)

            
