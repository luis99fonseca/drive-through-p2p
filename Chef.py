# coding: utf-8

import time
import logging
import threading
import queue as Queue
import random
 
from Node import node           #Para importar a class, em vez do module

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger('Chef')

class Chef(threading.Thread):
    def __init__(self, address = ('localhost', 5001 + 2), id=2, init_address=('localhost', 5000), timeout=3):
        threading.Thread.__init__(self)
        self.node = node(address, self.__class__.__name__, id, init_address)
        self.plates = Queue.Queue()             # QUEUE de pratos(menus) que tem para fazer
        self.permitions = Queue.Queue()         # QUEUE das permissões (vindas o Restaurante) que tem, para consequentemente cozinhar
        self.cook = threading.Thread(target=self.cooking)

    def run(self):
        self.node.start()
        self.cook.start()
        while True:
            o = self.node.IN_QUEUE.get()
            logger.critical("[CHEF]: %s", o)
            if o['method'] == 'PLATE':
                self.plates.put((o['menu'], o['cl_id']))        # Guarda-se o (PRATO : ID) do cliente
            elif o['method'].split("_")[0] == "REP":            # Se por uma REP(LY) do Restaurant
                self.permitions.put(o)                              # Coloca na Queue de Permições


    def cooking(self):
        while True:
            to_do = self.plates.get()
            menu = to_do[0]
            ementa = [k for k, v in menu.items() if v >= 1] # Lista com os Ingredientes de menu, cuja quantidade é positiva [1. Cria-se uma lista nova, para não haver repercursões no "menu" original]
            cl_id = to_do[1]
            rt_id = self.node.entities.get('Restaurant')[0]
            while len(ementa) > 0:  # Sempre que um Ingrediente é feito, é retirado de "ementa", servindo assim este While como forma de verificar se já ta o Menu completamente feito
                prato = random.choice(ementa)           # Escolhe um ingrediente Random [1. Assim na eventualidade de um aparelho não estar disponivel, o Chef procuraria "provavelmente" por uma maquina diferente
                request = self.setRequest(prato)
                new_o = {'method' : request, 'destiny' : rt_id}
                self.node.OUT_QUEUE.put(new_o)
                rep = self.permitions.get()     # Fica a espera de permissão por parte do Restaurante
                if (request.split("_")[1] == rep['method'].split("_")[1]):      # Se a maquina disponibilizada for a pretendida (1.1)
                    time.sleep(rep['time'] * menu[prato])           # "Cozinha" pelo tempo estabelecido * a quantidade de Ingredientes pa fazer
                    ementa.remove(prato)
                response = self.setResponse(rep['method'].split("_")[1].lower())                            # (1.2) De qualquer das formas, devolve-se a máquina
                new_o = {'method' : response, 'destiny' : rt_id}
                self.node.OUT_QUEUE.put(new_o)
            emp_id = self.node.entities.get('Employee')[0]
            new_o = {'method' : 'DONE', 'cl_id' : cl_id, 'destiny':emp_id, 'menu': menu}
            time.sleep(random.gauss(2, 0.5))
            self.node.OUT_QUEUE.put(new_o)

    def setRequest(self, type):     # Em funçao do tipo de Ingrediente, indica qual o Pedido a fazer
        if type == 'hamburger':
            return "REQ_GRILL"
        elif type == 'fries':
            return "REQ_FRYER"
        elif type == 'drink':
            return "REQ_BOTTLE"
        else:
            logger.error("[COOKING4]: ERRO no tipo de comida!!")

    def setResponse(self, type):    # Em função do tipo de Maquina, indica qual a Resposta a mandar
        if type == 'grill':
            return "RESP_GRILL"
        elif type == 'fryer':
            return "RESP_FRYER"
        elif type == 'bottle':
            return "RESP_BOTTLE"
        else:
            logger.error("[COOKING5]: ERRO no tipo de comida!!")


if __name__ == '__main__':      #por pa por o ID por argument line ou assim...
    che = Chef(('localhost', 5001+2), 2,('localhost', 5000))
    che.start()    ##depois mudar, para uma funçao, (tipo po proprio ciclo de vida ou assim...)


