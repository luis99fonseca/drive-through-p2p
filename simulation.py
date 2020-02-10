# coding: utf-8

import time
import pickle
import socket
import random
import logging
import argparse

from Restaurant import Restaurant
from Receptionist import Receptionist
from Chef import Chef
from Employee import Employee

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')


def main():

    restaurant = Restaurant()
    waiter = Receptionist()
    chef = Chef()
    clerk = Employee()

    restaurant.start()
    waiter.start()
    chef.start()
    clerk.start()

    restaurant.join()
    waiter.join()
    chef.join()
    clerk.join()

    return 0


if __name__ == '__main__':
    main()
