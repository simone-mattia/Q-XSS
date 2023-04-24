import sys, getopt, validators, os

USAGE=".\qxss.py -u <url> [-m <method>] - pag <pages_wordlist> -par <parameters_wordlist>"

# Check user parameters
def checkParameters(argv):
    
    # Default parameters
    url = ""
    method="GET"
    par = ""
    pag = ""

    # Get and check parameters
    try:
        opts, args = getopt.getopt(argv,"hu:m:pagw:parw:",["url=","method=", "pages_wordlist=","parameters_wordlist="])
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
        elif opt in ("-parw", "--parameters_wordlist"):
            par = arg
        elif opt in ("-pagw", "--pages_wordlist"):
            pag = arg
        
    # Required parameters
    if url == "" or par == "" or pag == "":
        print("[?] Insert url: ", end='')
        url = input()
        while not validators.url(url):
            print("[!] Not valid url")
            print("[?] Insert url: ", end='')
            url = input()
        print("[?] Insert method (GET, POST, COOKIE): ", end='')
        method = input()
        while method not in ("GET","POST","COOKIE"):
            print("[!] Method not allowed")
            print("[?] Insert method: ", end='')
            method = input()
        print("[?] Insert pages wordlist: ", end='')
        pag = input()
        while pag == "":
            print("[!] pages wordlist is required")
            print("[?] Insert pages wordlist: ", end='')
            pag = input()
        print("[?] Insert parameters wordlist: ", end='')
        par = input()
        while par == "":
            print("[!] parameters wordlist is required")
            print("[?] Insert parameters wordlist: ", end='')
            par = input()

    return url, method, pag, par

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

# Read a wordlist from a given path and return an array 
def readWordlist(path):
    output = []
    if os.path.isfile(path):
        with open(path, "r") as wordlist:
            output = [line.rstrip() for line in wordlist]
    return output