from .const import *
from .proxies import proxies
from .console import Console
from .instagram import getProfile
from ..exceptions import CaptchaError
from bs4 import BeautifulSoup
from re import search as re_search
from urllib.parse import urlparse
from time import sleep

import threading
import queue
import typing
import requests

class Search:
    __threads:list[threading.Thread] = []
    __lock:threading.Lock = threading.Lock()
    __que:queue.Queue = queue.Queue()
    __event:threading.Event = threading.Event()
    page:int = 11 # test amaçlı 10
    # flag
    def __init__(self,query:typing.Optional[list]=None,
                     filter:typing.Optional[list]=None,
                     social_media:typing.Optional[bool]=False
                ) -> None:
        self.__filter = filter
        self.__query = ""
        self.__social_media = social_media
        for q in query:
            self.__query += q+'+'
        self.__query = self.__query[:len(self.__query)-1]
        print(self.__query)
        if isinstance(filter,list):
            self.__filter = [i.lower() for i in filter]

    def __getCookie(self,main_url:str) -> dict:
        __result = requests.get(main_url,headers=HEADER)
        __cookies = __result.cookies.get_dict()
        return __cookies

    def __linkfilter(self,response:requests.Response,attr:dict,_filter:bool=False):
        soup = BeautifulSoup(response.content,"lxml")
        if _filter:
            for i in soup.find_all("div",attrs=attr):
                try:
                    self.__lock.acquire()
                    for j in self.__filter:
                        link = i.a["href"]
                        match = re_search(r"\b{0}\b".format(j),link)
                        if match:
                            print(_filter,j)
                            self.__que.put(match.string)
                except Exception as e:
                    continue
                finally:
                    self.__lock.release()

        else:
             for i in soup.find_all("div",attrs=attr):
                try:
                    self.__lock.acquire()
                    if i.a['href'].startswith("https"):
                        if "books" not in urlparse(i.a['href']).netloc:
                            self.__que.put(i.a['href'])
                except Exception as e:
                    continue
                finally:
                    self.__lock.release()

    def __request(self,slot:int):
        try:
            self.__findCaptcha()
            print("GOOGLE")
            self.__searchEngine(slot)
        except CaptchaError as e:
            Console.display(e)
            print("BING")
            self.__searchEngine(slot,True)

    def searchQuerySet(self,slot:int):
        if isinstance(self.__filter,str):
            return self.__request(slot=slot)

        else:
            return self.__request(slot=slot)

    def getSearchedLinks(self):
        for i in range(1, 11 if self.page == 1 else (self.page * 10) + 1 ,11):
            t = threading.Thread(target=self.searchQuerySet,args=(i,))
            t.start()
            self.__threads.append(t)

        for thread in self.__threads:
            thread.join()

        count = 0
        if self.__que.qsize() != 0:
            Console.display(f"{chr(32)*7}{Console.CYAN}TIME{chr(32)*6}COUNT{chr(32)*9}LINKS")
            while not self.__que.empty():
                count += 1
                Console.display_links(count,self.__que.get())
            Console.display(f"{Console.GREEN}|")
            Console.display(f"{Console.GREEN}├───────({Console.CYAN}Search has end{Console.GREEN})")
            sleep(1)
            Console.display(f"{Console.GREEN}|\n╰───────({Console.CYAN}Scanning Popular Social media accounts.{Console.GREEN})")
            if self.__social_media:
                print("sosyal medya")
                self.social()
        else:
            Console.warn_display("No Results\n")
    
    def __searchEngine(self,slot:int,other_engine:bool=False):
        if not other_engine:
            #Google
            params = {
                "q" : self.__query,
                "start": slot
            }
            response = requests.get(GOOGLESEARCH,params=params,headers=HEADER,cookies=self.__getCookie(GOOGLEMAIN))
            attr = {"class":"yuRUbf"}
            return self.__linkfilter(response,attr,isinstance(self.__filter,list))
        else:
            #Bing
            params = {
                "q" : self.__query,
                "sp":'1',
                "first": slot
            }
            response = requests.get(BINGSEARCH,params=params,headers=HEADER,cookies=self.__getCookie(BINGMAIN))
            attr = {"class":"b_title"}
            return self.__linkfilter(response,attr,isinstance(self.__filter,list))
    
    def __findCaptcha(self) -> bool:
        params = {
            "q" : self.__query,
            "start": '1'
        }
        response = requests.get(GOOGLESEARCH,params=params,headers=HEADER,cookies=self.__getCookie(GOOGLEMAIN))
        soup = BeautifulSoup(response.content,"lxml")
        capctha = soup.find("form",attrs={"id":"captcha-form"})
        if capctha:
            raise CaptchaError()
    
    def social(self):
        for user in self.__query.split('+'):
            print(getProfile(user,userAgent()))
