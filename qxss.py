#!/usr/bin/python3

import enviroment, qlearning, utils, xssExploit
import sys


if __name__ == "__main__":
    
    # Print Banner
    utils.printBanner()

    # Get and check parameters 
    url,method, parameter = utils.checkParameters(sys.argv[1:]) 

    # Creates enviroment object
    env = enviroment.Enviroment(url, method, parameter)
    
    # Check the url connection and print details
    print("[*] Check connection...")
    env.checkConnection()

    # Initialize Q-Learning algorithm 
    qlearning = qlearning.QLearning(env)

    # Start executions
    print("[*] Start training...")
    print(qlearning.qLearning(10))
    