import sys, getopt, validators, re

USAGE="main.py -u <url> [-m <method>] -p <parameter>"

# Check user parameters
def checkParameters(argv):
    
    # Default parameters
    url = ""
    method="GET"
    parameter = ""

    # Get and check parameters
    try:
        opts, args = getopt.getopt(argv,"hu:m:p:",["url=","method=","parameter="])
    except getopt.GetoptError:
        print("[!] Usage: {}".format(USAGE))
        sys.exit(1)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(USAGE)
            sys.exit()
        elif opt in ("-u", "--url"):
            if not validators.url(arg):
                print("[!] Not valid url")
                sys.exit(1)
            else:
                url = arg
        elif opt in ("-m", "--method"):
            if arg not in ("GET","POST","COOKIE"):
                print("[!] Method not allowed")
                sys.exit(1)
            else:
                method = arg
        elif opt in ("-p", "--parameter"):
            parameter = arg
        
    # Required parameters
    if url == "" and parameter == "" and method == "GET":
        print("[?] Insert url: ")
        url = input()
        while not validators.url(url):
            print("[!] Not valid url")
            print("[?] Insert url: ")
            url = input()
        print("[?] Insert method: ")
        method = input()
        while method not in ("GET","POST","COOKIE"):
            print("[!] Method not allowed")
            print("[?] Insert method: ")
            method = input()
        print("[?] Insert parameter: ")
        parameter = input()
        while parameter == "":
            print("[!] parameter is required")
            print("[?] Insert parameter: ")
            parameter = input()
    elif url == "":
        print("[!] Url is required, usage: {}".format(USAGE))
        sys.exit(1)
    elif parameter == "":
        print("[!] With {} method parameter is required, usage: main.py -u <url> -m {} -p <parameter>".format(method, method))
        sys.exit(1)

    return url, method, parameter

def printBanner():
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
