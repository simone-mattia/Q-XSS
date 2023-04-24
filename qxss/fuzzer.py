from . import utils
import random, string

class Fuzzer:

    # Initialize parameters and launch the fuzzer 
    def __init__(self, env, page_wordlist, param_wordlist):
        self.env = env
        self.page_wordlist = page_wordlist
        self.param_wordlist = param_wordlist
        self.pages = []
        self.param = []

    # Page fuzzing
    def pageFuzzer(self):
        wordlist = []
        if self.page_wordlist not in ({}, None, ""):
            wordlist = utils.readWordlist(self.page_wordlist)
        for word in wordlist:
            result = self.env.setPage(word)
            result["page"] = word
            self.pages.append(result)
        return self.pages

    # Page fuzzing
    def pageFuzzer(self):
        wordlist = []
        if self.page_wordlist not in ({}, None, ""):
            wordlist = utils.readWordlist(self.page_wordlist)
        for word in wordlist:
            result = self.env.setPage(word, checkConnection=True)
            self.pages.append({
                "page": word,
                "conn_status_code": result["conn_status_code"],
                "http_code": result["http_code"],
                "http_res_len": result["http_res_len"]
            })
        return self.pages
    
    # Parameters fuzzing
    def paramFuzzer(self):
        wordlist = []
        random_string = "".join((random.choice(string.ascii_letters) for i in range(10)))
        if self.param_wordlist not in ({}, None, ""):
            wordlist = utils.readWordlist(self.param_wordlist)
        for page in [x["page"] for x in self.pages if x["conn_status_code"]==0]:
            self.env.setParameter("")
            std = self.env.setPage(page, checkConnection=True)
            for word in wordlist:
                self.env.setParameter(word)
                result = self.env.checkConnection(value=random_string)
                result["page"] = page
                result["param"] = word
                http_res_len_difference = std["http_res_len"] - result["http_res_len"]
                reflected = False
                if http_res_len_difference == -10:
                    if random_string.lower() in result["http_res"].lower():
                        reflected=True
                self.param.append({
                "page": page,
                "param": word,
                "conn_status_code": result["conn_status_code"],
                "http_code": result["http_code"],
                "http_res_len": result["http_res_len"],
                "http_res_len_difference": http_res_len_difference,
                "inputReflected": reflected
            })
        return self.param