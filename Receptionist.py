# coding: utf-8

import time
import random
import logging
import threading
import uuid

from Node import node           #Para importar a class, em vez do module

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('Receptionist')

class Receptionist(threading.Thread):
    def __init__(self, address=('localhost', 5001+1), id=1, init_address=('localhost', 5000), timeout=3):
        threading.Thread.__init__(self)
        self.node = node(address, self.__class__.__name__, id, init_address)

    def run(self):
        self.node.start()
        while True:
            o = self.node.IN_QUEUE.get()
            msg = {}
            logger.critical("[RECEPTIONIST]: %s", o)
            if o['method'] == 'ORDER':

                cl_id = uuid.uuid1()                # Gera um UUID para atribuir ao (pedido do) cliente
                msg['args'] = cl_id
                logger.warning('[RECEPTIONIST]: CL_ID:%s', msg)
                time.sleep(random.gauss(2, 0.5))
                self.node.send(o['c_addr'], msg)    # Envia a mensagem de acknowledgement ao Cliente

                ch_id = self.node.entities.get('Chef')[0]   # Vai buscar o ID do Chef
                new_o = {'method' : 'PLATE', 'menu' : o['menu'], 'destiny' : ch_id, 'cl_id' : cl_id}    # Para consecuentemente lhe enviar o Menu para ele fazer
                time.sleep(random.gauss(2, 0.5))
                self.node.OUT_QUEUE.put(new_o)

if __name__ == '__main__':      #por pa por o ID por argument line ou assim...
    rec = Receptionist(('localhost', 5001+1), 1,('localhost', 5000))
    rec.start()    ##depois mudar, para uma funçao, (tipo po proprio ciclo de vida ou assim...)

