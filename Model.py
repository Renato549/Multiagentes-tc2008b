from mesa import Agent, Model
from mesa.space import SingleGrid
from mesa.time import BaseScheduler
from mesa.datacollection import DataCollector

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
plt.rcParams["animation.html"] = "jshtml"
matplotlib.rcParams['animation.embed_limit'] = 2**128

import numpy as np
import pandas as pd

import time
import datetime
import random
import json

from http.server import BaseHTTPRequestHandler, HTTPServer
import logging

def get_grid(model):
    grid = np.zeros( (model.grid.width, model.grid.height) )
    for (content, x, y) in model.grid.coord_iter(): 
        if (model.grid.is_cell_empty((x, y)) == False):
            grid[x][y] = content.isActive
    return grid



class CarAgent(Agent):
    def __init__(self, unique_id, model, x, y):
        super().__init__(unique_id, model)
        
        self.isActive = True
        self.x = x
        self.y = y
        self.move = True
        self.speed = 60

        

    def step(self):
  
        #Si eres cierto auto y llevas mitad de camino detente
        
        if self.unique_id == 30 and self.y >= self.model.quint:
            self.speed -= 5
            self.move = False
            if self.speed <= 0:
                self.speed = 0
                return
            else:
                if self.check_Fneighbors() == True:
                    self.y = self.y + 1
                    self.model.grid.move_agent(self, (self.x, self.y))
                else:
                #De no ser posible escoge entre derecha-izquierda
                    rand = np.random.choice([1,2])
                #Muevete a la Derecha
                    if rand == 1 and self.check_Rneighbors() == True:
                        self.x = self.x + 1
                        self.model.grid.move_agent(self, (self.x, self.y))
                    #Si no muevete al izquierda
                    elif self.check_Lneighbors() == True:
                        self.x = self.x - 1
                        self.model.grid.move_agent(self, (self.x, self.y))
        else:
            if self.check_Fneighbors() == True:
                self.y = self.y + 1
                self.model.grid.move_agent(self, (self.x, self.y))
            else:
                #De no ser posible escoge entre derecha-izquierda
                rand = np.random.choice([1,2])
                self.speed = 0
                #Muevete a la Derecha
                if rand == 1 and self.check_Rneighbors() == True:
                    self.x = self.x + 1
                    self.model.grid.move_agent(self, (self.x, self.y))
                #Si no muevete al izquierda
                elif self.check_Lneighbors() == True:
                    self.x = self.x - 1
                    self.model.grid.move_agent(self, (self.x, self.y))
                        

    #Sal del camino si llegaste al limite
    def get_out(self):
        if self.model.grid.out_of_bounds((self.x, (self.y + 1))) == True:
            return True
        return False


    #Verifica si puedes moverte hacia enfrente y manda afirmativo
    def check_Fneighbors(self):
        if self.get_out() == True and not(self in self.model.out):
            self.model.out.append(self)
            return False
        else:
            if self.get_out() == False and self.model.grid.is_cell_empty((self.x, (self.y + 1))) == True:
                return True
            else:
                self.model.trafic.append(self)
                return False
                
    #Verifica si puedes moverte hacia la derecha y manda afirmativo
    def check_Rneighbors(self):
        if self.get_out() == True and not(self in self.model.out):    
            self.model.out.append(self)
            return False
        else:
            if ((self.x + 1) <= 2) and (self.y < self.model.height):
                if  self.get_out() == False and self.model.grid.is_cell_empty(((self.x + 1), (self.y))) == True:
                    return True
                else:
                    return False
            return False


    #Verifica si puedes moverte hacia la izquierda y manda afirmativo
    def check_Lneighbors(self):
        if self.get_out() == True and not(self in self.model.out):
            self.model.out.append(self)
            return False  
        else:
            if((self.x - 1) >= 0) and (self.y < self.model.height):
                if  self.get_out() == False and self.model.grid.is_cell_empty(((self.x - 1), (self.y))) == True:
                    return True
                else:
                    return False
            return False

class CarModel(Model):
    def __init__(self, width, height):
        self.uids = 1
        self.quint = height / 5
        self.out = []
        self.widht = width
        self.height = height
        self.grid = SingleGrid(width, height, False)
        self.schedule = BaseScheduler(self)
        self.datacollector = DataCollector(model_reporters={"Grid": get_grid})
        self.prob = 0.5
        self.stop = False
        self.trafic = []
  
        
        
    def step(self): 
        self.datacollector.collect(self)
        for agent in self.out:
            #print("Delete")
            self.grid.remove_agent(agent)
            self.schedule.remove(agent)
            #self.agents.remove(agent)
        self.out = [] 
        self.schedule.step()
        rand = np.random.choice([0.1,0.2,0.3,0.5,0.6,0.7,0.8,0.9,1])
        if rand <= self.prob:
            if self.uids == 30:
                agent = CarAgent(self.uids, self, 1, 0)
                self.grid.place_agent(agent, (1, 0))
                self.schedule.add(agent)
                self.uids += 1
            else:
                pos = np.random.choice([0, 1, 2])
                agent = CarAgent(self.uids, self, pos, 0)
                self.grid.place_agent(agent, (pos, 0))
                self.schedule.add(agent)
                self.uids += 1
        # print(len(self.trafic))


WIDTH = 3
HEIGHT = 100
MAX_ITERATIONS = 200


start_time = time.time()
model = CarModel(WIDTH, HEIGHT)


def Get(model):

    list = []
    for agent in model.schedule.agent_buffer(False):
        if agent.pos != None:
            pista = agent.pos[0]
        else:
            pista = -1
        aux = {"Id" : agent.unique_id, "Speed" : agent.speed, "Pista" : int(pista)}
        list.append(aux)
    
    a = {"agents" : list}

    jsonOut = json.dumps(a, sort_keys=True)
    model.step()

    return jsonOut

class Server(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        jsonOut = Get(model)    
        self._set_response()      
        self.wfile.write(str(jsonOut).encode('utf-8'))
        

def run(server_class=HTTPServer, handler_class=Server, port=8585):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info("Starting httpd...\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt: 
        pass
    httpd.server_close()
    logging.info("Stopping httpd...\n")

if __name__ == '__main__':
    from sys import argv
    
    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
 
