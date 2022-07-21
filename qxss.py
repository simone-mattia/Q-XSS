#!/usr/bin/python3

import enviroment, qlearning, utils, xssExploit
import sys


if __name__ == "__main__":
    
    # Print Banner
    utils.printBanner()

    # Check parameters and creates enviroment object
    env = enviroment.Enviroment(sys.argv[1:])
    
    # Check the url connection and print details
    print("[*] Check connection...")
    env.checkConnection()

    # Initialize Q-Learning algorithm 
    qlearning = qlearning.QLearning(env)

    # Start executions
    print("[*] Start training...")
    #print(qlearning.qLearning(10))
    xssExploit = xssExploit.XssExploit()
    