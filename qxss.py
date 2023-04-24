#!/usr/bin/python3

from qxss import enviroment, fuzzer, qlearning, utils
import sys


if __name__ == "__main__":
    
    # Print Banner
    utils.printBanner()

    # Get and check parameters 
    url, method, pages, params = utils.checkParameters(sys.argv[1:]) 
    url = "https://xss.challenge.training.hacq.me/"

    # Creates the object used to interact with the enviroment 
    env = enviroment.Enviroment(url)
    status = env.checkConnection(printDetails=True)
    if status["conn_status_code"] == -1:
        sys.exit(-1)

    # Parameters and page fuzzing
    fuzzer = fuzzer.Fuzzer(env, pages, params)
    pages = fuzzer.pageFuzzer()
    valid_pages = [x["page"] for x in pages if x["conn_status_code"]==0]
    param = fuzzer.paramFuzzer()
    valid_param = [(x["page"],x["param"]) for x in param if x["http_res_len_difference"]!=0]
    reflected_input = [(x["page"],x["param"]) for x in param if x["inputReflected"]]
    print("[+] Detected pages: " + str(valid_pages))
    print("[+] Detected parameters: " + str(valid_param))
    print("[+] Reflected input: " + str(reflected_input) + "\n")

    # Initialize Q-Learning algorithm 
    qlearning = qlearning.QLearning(env)

    # XSS Resolver
    for data in valid_param:
        env.setPage(data[0])
        env.setParameter(data[1])
        print("########################################")
        print(qlearning.qLearning(100))
        
    