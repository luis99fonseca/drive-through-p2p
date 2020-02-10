# coding: utf-8

import random
import logging
import threading

from Node import node           #Para importar a class, em vez do module


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('Restaurant')

class Restaurant(threading.Thread):

    def __init__(self, address=('localhost', 5000), id=0, init_address=None, timeout=3):
        threading.Thread.__init__(self)
        self.node = node(address, self.__class__.__name__, id, init_address)
        self.grill = True      # As maquinas...
        self.fryer = True
        self.bottle = True

    def run(self):
        self.node.start()
        while True:
            o = self.node.IN_QUEUE.get()
            logger.critical("[RESTAURANT]: %s", o)
            if o['method'].split("_")[0] == "REQ":
                reply = self.setUsage(o['method'])
                ch_id = self.node.entities.get('Chef')[0]
                new_o = {'method' : reply[0], "time" : reply[1], 'destiny' : ch_id}
                self.node.OUT_QUEUE.put(new_o)
            elif o['method'].split("_")[0] == "RESP":
                self.returnUsage(o['method'])

            logger.debug("[RESTAURANT] (STATUS): grill:%s; fryer:%s; bottle:%s", self.grill, self.fryer, self.bottle)

    def setUsage(self, type):       #MUDAR OS TEMPOS DEPOIS
        if type == 'REQ_GRILL' and self.grill:
            self.grill = False
            return ("REP_GRILL", abs(self.setTime(3, 0.5)))
        elif type == 'REQ_FRYER' and self.fryer:
            self.fryer = False
            return ("REP_FRYER", abs(self.setTime(5, 0.5)))
        elif type == 'REQ_BOTTLE' and self.bottle:
            self.bottle = False
            return ("REP_BOTTLE",abs(self.setTime(1, 0.5)))
        else:
            logger.error("[MACHINE2]: Nao disponivel-DENIED!!")
            return ("REP_DENIED", 0)             #captizaliar no facto de isto fazer split de "REP"

    def returnUsage(self, type):
        if type == 'RESP_GRILL' and not self.grill:
            self.grill = True
        elif type == 'RESP_FRYER' and not self.fryer:
            self.fryer = True
        elif type == 'RESP_BOTTLE' and not self.bottle:
            self.bottle = True
        else:
            logger.error("[MACHINE5]: Nao disponivel / DENIED!!")

    def setTime(self, media, desvio):           # Inicialmente tinha esta função recursiva para nao returnar tempos negativos, antes de simplesmente usar "abs()"
        time = random.gauss(media, desvio)      # Embora já nao seja usada, achei conveniente mantê-la
        return time if time > 0 else self.setTime(media, desvio)


if __name__ == '__main__':
    res = Restaurant(('localhost', 5000), 0)
    res.start()        ##depois mudar, para uma funçao, (tipo po proprio ciclo de vida ou assim...)