
import logging
import socket
import pickle
from utils import contains_successor
import threading
import time
import queue as Queue


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')

class node(threading.Thread):
    def __init__(self, address,nome ,id, init_address=None, timeout=3):
        threading.Thread.__init__(self)
        self.addr = address
        self.init_addr = init_address           # O Address da Entidade "central"(Restaurante), ao qual as outras Entidades se devem ligar
        self.id = id
        self.name = nome
        self.logger = logging.getLogger("{} {}".format(self.name, self.id))
        self.entities = {}
        self.IN_QUEUE = Queue.Queue()           # Queue onde cada Entidade vai buscar mensagens para processar
        self.OUT_QUEUE = Queue.Queue()          # Queue onde cada Entidade vai colocar mensagens para enviar

        if self.init_addr is None:
            self.inside_token_ring = True
            self.successor_id = self.id
            self.successor_addr = self.addr
        else:
            self.inside_token_ring = False
            self.successor_id = None
            self.successor_addr = None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)

    def send(self, address, o):
        p = pickle.dumps(o)
        self.socket.sendto(p, address)

    def recv(self):
        try:
            p, addr = self.socket.recvfrom(1024)
        except socket.timeout:
            return None, None
        else:
            if len(p) == 0:
                return None, addr
            else:
                return p, addr

    def node_join(self, args):
        self.logger.debug('Node join: %s', args)
        addr = args['addr']
        identification = args['id']
        self.logger.error('ID: %s; SUCC: %s', self.id, self.successor_id)
        if self.id == self.successor_id:                # Se ele for o seu proprio Sucessor, aceita logo o primeiro candidato
            self.successor_id = identification
            self.successor_addr = addr
            args = {'successor_id': self.id, 'successor_addr': self.addr}
            self.send(addr, {'method': 'JOIN_REP', 'args': args})
        elif contains_successor(self.id, self.successor_id, identification):        # Se já tiver Sucessor, verifica se este é um melhor candidato (tem um ID menor que o sucessor atual)...
            args = {'successor_id': self.successor_id, 'successor_addr': self.successor_addr}   #...em caso afirmativo, responde com informaçao relativa ao (ex) sucessor
            self.successor_id = identification
            self.successor_addr = addr
            self.send(addr, {'method': 'JOIN_REP', 'args': args})
        else:
            self.logger.debug('Find Successor(%d)', args['id'])                     # Se o candidato não puder ser o novo Sucessor, o Node propraga a informação para o próximo
            self.send(self.successor_addr, {'method': 'NODE_JOIN', 'args':args})
        self.logger.info(self)

    def node_discovery(self, args):
        news_name = args['name']
        news_id = args['id']
        news_NoNodes = args['noNodes']              # Nº dos outros Nodes, que um dado None conhece
        self.logger.debug('[NODE] Discovery: Name: %s -> ID:%s nNodes:(%s)', news_name, news_id, news_NoNodes)
        if (news_id != self.id):                    # Quando esta condição nao se verificar, é porque a mensagem ja deu a volta ao Ring
            self.entities[news_name] = (news_id, news_NoNodes)
            o = {'method': 'NODE_DISCOVERY', 'args': {'name': news_name, 'id': news_id, 'noNodes':len(self.entities)}}
            self.send(self.successor_addr, o)

    def check_entitiesNo(self):           # Verifica se todas as entidades estao ja registadas everywhere
        for key in self.entities:
            if self.entities[key][1] != 3:               # 3, pois é o número minimo de entidades diferentes
                return False
        return len(self.entities) == 3                  # novamente, 3, pois é o número minimo de entidades diferentes

    def checkSmallID(self):         # Verifica se é o ID mais pequeno; Importante pois será quem irá criar o TOKEN
            minID = self.id             # Esta função e a de cima estão bastante relacionadas
            for keys in self.entities:
                minID = minID if (minID < self.entities[keys][0]) else self.entities[keys][0]   # NOTA: É index [0], pois o outro indica o numero de Entidades que dada Entidade conhece, formando um tuplo
            return True if minID == self.id else False

    def run(self):
        start_time = time.time()
        self.logger.info("[NODE] RUNNING... %s", self.addr)
        self.socket.bind(self.addr)

        ''' RING JOIN SECTION '''
        while not self.inside_token_ring:
            o = {'method': 'NODE_JOIN', 'args': {'addr':self.addr, 'id':self.id}}
            self.send(self.init_addr, o)
            p, addr = self.recv()
            if p is not None:
                o = pickle.loads(p)
                self.logger.debug('[NODE] (AT JOIN) O: %s', o)
                if o['method'] == 'JOIN_REP':  # Quando recebe um REPLY, é porque foi aceito, dizendo-lhe a info do Sucessor
                    args = o['args']
                    self.successor_id = args['successor_id']
                    self.successor_addr = args['successor_addr']
                    self.inside_token_ring = True
                    self.logger.info(self)

        ''' NODE DISCOVERY SECTION '''
        counter = 0
        entities_done = False              #Verifica se todas as entidades ja conhcem todas e estamos prontos pa simulaçao (Restaurant funciona diferente das demais aqui...)
        efective_sends = 0
        while not entities_done:
            p, addr = self.recv()
            # self.logger.debug('KNOWN NODES(%s): %s', len(self.entities), self.entities)
            if p is not None:
                o = pickle.loads(p)
                self.logger.info('[NODE] (AT DISCOVERY) O: %s', o)
                if o['method'] == 'NODE_JOIN':
                    self.node_join(o['args'])
                elif o['method'] == 'NODE_DISCOVERY':
                    if (self.check_entitiesNo() and self.checkSmallID()):       # Faz-se uso de lazy-evaluation
                        o = {'method': 'RING_DONE', 'rootID': self.id, 'from:' : self.id}   # Se todas os Nodes já se conhecerem entre si E este Node for o de ID menor, então é espalhada a mensagem de RING DONE
                        self.send(self.successor_addr,o)
                    else:
                        self.node_discovery(o['args'])
                elif o['method'] == 'RING_DONE':
                    if not (o['rootID'] == self.id):
                        o = {'method': 'RING_DONE', 'rootID': self.id, 'from:' : self.id}
                        self.send(self.successor_addr, o)
                    entities_done = True
                else:
                    self.logger.error("Metodo nao Existente!!!")
            counter += 1
            if (counter % 4 == 1): # Manda com uma certa periodicidade este tipo de mensagem; o valor ideal (creio), segue uma distruibuição normal, onde o Divisor ideal é o número de Nodes no Ring
                o = {'method': 'NODE_DISCOVERY', 'args': {'name': self.name, 'id': self.id, 'noNodes': len(self.entities)}}
                efective_sends += 1
                self.send(self.successor_addr, o)

            self.logger.critical(self)

        self.logger.info("[NODE] CONFIGURATION TIME: %s; NODE_DISCOVERies = %s", time.time() - start_time, efective_sends)

        ''' SIMULATION SECTION '''
        if (self.checkSmallID()):           # Verifica se é o Node com o ID mais pequeno, para que, caso seja, cria o TOKEN e o meta logo a circular; Assume-se que não há IDs iguais
            token = {'method': 'TOKEN', 'args': None}
            self.logger.debug("[NODE]: SMALLEST ID!!")
            self.send(self.successor_addr, token)

        while True:
            p, addr = self.recv()
            if p is not None:
                o = pickle.loads(p)
                if o['method'] == 'TOKEN':
                    if o['args'] is not None:
                        if o['args']['destiny'] == self.id:
                            o['args'].pop('destiny')            # Isto visa a retirar esta (chave : valor) do dicionario, para de seguida só se por no IN_QUEUE a informação relevante
                            self.IN_QUEUE.put(o['args'])
                        else:
                            self.OUT_QUEUE.put(o['args'])

                    if not self.OUT_QUEUE.empty():
                        o['args'] = self.OUT_QUEUE.get()
                    else:
                        o['args'] = None        # Se a OUT_QUEUE está vazia, então o Node nao tem nenhuma mensagem para enviar, logo 'args' tem de ser None
                    time.sleep(0)
                    self.send(self.successor_addr, o)
                else:       # Se a mensagem não for do tipo TOKEN, então é porque é uma mensagem vinda do exterior (cliente), só podendo entao ser do tipo ORDER ou PICKUP
                    if o['method'] == 'ORDER':                      #  ↓ Para onde aponta a seta, é forçado um tuplo porque preciso de buscar o 1o index (pois no dicionario (entities) os elementos sao do tipo (id, entidades que conhece)
                        destino = self.entities.get('Receptionist', (self.id,))[0]    # Capitaliza no facto do dicionario from discovery (entities) nao o incluir o próprio Node. Caso esta key nao exista la (significa que este é o proprio Node que estamos a procura, thus retorna o proprio ID)
                                                                                          # ↑ [função get(x,y) em python: se não conseguir fazer get de x, retorna y por omissão]
                        self.logger.info("[NODE]: ORDER: %s", o)
                        o['menu'] = o.pop('args')
                        o['c_addr'] = addr
                        if self.id == destino:      # Se este for o destino da mensagem. ẽ colocado na IN_QUEUE
                            self.IN_QUEUE.put(o)
                        else:                       # Senão é colocado na OUT_QUEUE, para posteriormente ser encaminhado
                            o['destiny'] = destino
                            self.OUT_QUEUE.put(o)
                    elif o['method'] == 'PICKUP':
                        destino = self.entities.get('Employee', (self.id,))[0]  # logica identica à do ORDER
                        self.logger.info("[NODE]: PICKUP: %s", o)
                        o['cl_id'] = o.pop('args')          # O ID da ordem que o cliente recebe, vai passar a ser o seu identificador
                        o['c_addr'] = addr
                        if self.id == destino:
                            self.IN_QUEUE.put(o)
                        else:
                            o['destiny'] = destino
                            self.OUT_QUEUE.put(o)

    def __str__(self):
        return 'Entidade ID: {}; Successor: {};'.format(self.id, self.successor_id)

    def __repr__(self):
        return self.__str__()