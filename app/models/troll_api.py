# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime
from time import time

class FindTrollApi:
    def __init__(self, key_api, url_to_server='http://127.0.0.1:5000', treshold=0.5):
        self._headers = {
            'Content-type': 'application/json',
            'Accept': 'text/plain',
            'Content-Encoding': 'utf-8',
            }
        self._key_api = key_api
        self._url_to_server = url_to_server
        self._treshold = treshold
    
    def _save_to_json(self, response, path_to_save):
        with open(path_to_save, "w", encoding="utf-8") as write_file:
            json.dump(response, write_file, indent=2, ensure_ascii=False)

    def set_treshold(self, treshold):
        self._treshold = treshold

    def funcname(self, parameter_list):
        """
        docstring
        """
        pass

    def get_count_available_requests(self,
                                     save_to_json=False, 
                                     path_to_save="available_requests_{}.json".format(datetime.today().strftime("%Y-%m-%d_%H.%M.%S")),
                                     timeout=300):
        answer = requests.post(
            self._url_to_server + "/get_query_left", 
            data=json.dumps({"key_api":self._key_api}), 
            headers=self._headers,
        )
        response = answer.json()
        if save_to_json: self._save_to_json(response, path_to_save)
        return response
        
    def get_available_type_parsers(self,):
        answer = requests.post(
            self._url_to_server + "/get_proba", 
            data=json.dumps({
                "question":question,
                "answer":answer,
                "treshold":self._treshold
            }), 
            headers=self._headers,
        )
        response = answer.json()

    def get_proba(self, 
                  question,
                  answer, 
                  save_to_json=False, 
                  path_to_save="request_proba_{}.json".format(datetime.today().strftime("%Y-%m-%d_%H.%M.%S")),
                  timeout=300):
        answer = requests.post(
            self._url_to_server + "/get_proba", 
            data=json.dumps({
                "question":question,
                "answer":answer,
                "treshold":self._treshold,
                "key_api":self._key_api
            }), 
            headers=self._headers,
            timeout=timeout
        )
        response = answer.json()
        if save_to_json: self._save_to_json(response, path_to_save)
        return response

    def get_proba_from_link(self, 
                            link,
                            type_parser="answers_mail.ru", 
                            save_to_json=False, 
                            path_to_save="request_proba_from_link_{}.json".format(datetime.today().strftime("%Y-%m-%d_%H.%M.%S")),
                            timeout=300):
        answer = requests.post(
            self._url_to_server + "/get_link", 
            data=json.dumps({
                "link":link,
                "parser":type_parser,
                "treshold":self._treshold,
                "key_api":self._key_api
            }), 
            headers=self._headers,
            timeout=timeout
        )
        response = answer.json()
        if save_to_json: self._save_to_json(response, path_to_save)
        return response

if __name__ == "__main__":
    api = FindTrollApi(key_api="qwerty")
    N = 7
    question = ["questionquestion"] * N
    answer = "answer"
    link = "1234567"
    t1 = time()
    data_ = api.get_proba(question, answer, save_to_json=True)
    print(time()-t1)
    """
    data1 = {
        "question":["questionquestion"]*N,
        "answer":"answer",
        "link":"1234567"
    }
    with open("path_to_save.json", "w", encoding="utf-8") as write_file:
                json.dump(data1, write_file, indent=2, ensure_ascii=False)
    """