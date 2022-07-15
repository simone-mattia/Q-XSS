#!/usr/bin/python3

import enviroment, qlearning
import sys


if __name__ == "__main__":
    
    # Banner
    print("""
  /$$$$$$         /$$   /$$  /$$$$$$   /$$$$$$ 
 /$$__  $$       | $$  / $$ /$$__  $$ /$$__  $$
| $$  \ $$       |  $$/ $$/| $$  \__/| $$  \__/
| $$  | $$ /$$$$$$\  $$$$/ |  $$$$$$ |  $$$$$$ 
| $$  | $$|______/ >$$  $$  \____  $$ \____  $$
| $$/$$ $$        /$$/\  $$ /$$  \ $$ /$$  \ $$
|  $$$$$$/       | $$  \ $$|  $$$$$$/|  $$$$$$/
 \____ $$$       |__/  |__/ \______/  \______/ 
      \__/                                     
                                                                                
 """)

    # Check parameters and creates enviroment object
    env = enviroment.Enviroment(sys.argv[1:])
    
    # Check the url connection and print details
    print("[*] Check connection...")
    env.checkConnection()

    # Initialize Q-Learning algorithm 
    qlearning = qlearning.QLearning(env)

    # Start executions
    print("[*] Start execution...")
    print(qlearning.qLearning(100))