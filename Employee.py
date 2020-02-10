# coding: utf-8

import time
import random
import logging
import threading

from Node import node           #Para importar a class, em vez do module

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('Employee')

class Employee(threading.Thread):
    def __init__(self, address=('localhost', 5001+3), id=3, init_address=('localhost', 5000), timeout=3):
        threading.Thread.__init__(self)
        self.node = node(address, self.__class__.__name__, id, init_address)
        self.deliveries = {}        # Dicionario pa guardar o ID : ADDR do cliente

    def run(self):
        self.node.start()
        while True:
            o = self.node.IN_QUEUE.get()
            logger.critical("[EMPLOYEE]: %s", o)

            if o['method'] == 'PICKUP':
                self.deliveries[o['cl_id']] = o['c_addr']
                logger.debug("[EMPLOYEE]: PENDINGS (n=%s):%s", len(self.deliveries), self.deliveries)
            elif o['method'] == 'DONE':         # Como normalmente o Menu se acaba de fazer depois do pedido de Pickup, vai-se ao self.deliveries buscar o ADDR para saber a quem entregar o Menu
                msg = {}
                to_cl_id = o['cl_id']
                msg['args'] = (to_cl_id, o['menu'])
                to_cl_addr = self.deliveries.pop(to_cl_id)  # Retira e returna o ADDR do cliente com o dado ID
                time.sleep(random.gauss(2, 0.5))
                self.node.send(to_cl_addr, msg)         # Envia o comer ao Cliente


if __name__ == '__main__':      #por pa por o ID por argument line ou assim...
    emp = Employee(('localhost', 5001+3), 3,('localhost', 5000))
    emp.start()            ##depois mudar, para uma funçao, (tipo po proprio ciclo de vida ou assim...)

