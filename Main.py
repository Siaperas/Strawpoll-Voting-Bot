
try:
    from optparse import OptionParser
    import sys
    import os
    import re
    from bs4 import BeautifulSoup
    import urllib.request
    import requests
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError as msg:
    print("[!] Library not installed: " + str(msg))
    exit()



class Strawpoll_Multivote:

    # Initialization
    maxVotes = 1
    voteFor = ""
    surveyId = ""
    domainEnd = "com"
    proxyListFile = "proxies.txt"
    saveStateFile = "usedProxies.txt"
    proxyTimeout = 10 # in seconds
    currentProxyPointer = 0
    successfulVotes = 0


    def __init__(self):
        try:

            # Parse Arguments
            parser = OptionParser()
            parser.add_option("-v", "--votes", action="store", type="string", dest="votes",help="number of times to vote")
            parser.add_option("-s", "--survey", action="store", type="string", dest="survey",help="url id of the survey")
            parser.add_option("-t", "--target", action="store", type="string", dest="target", help="checkbox id to vote for")
            parser.add_option("-d", "--domain", action="store", type="string", dest="domain", help="domain name end")
            parser.add_option("-f", "--flush", action="store_true", dest="flush",help="Flushes the used proxy list")
            parser.add_option("-r", "--renew", action="store_true", dest="renew",help="Renews the proxy list")

            (options, args) = parser.parse_args()

            if len(sys.argv) > 2:
                    if options.votes is None:
                        print("[!] Times to vote not defined with: -v ")
                        exit(1)
                    if options.survey is None:
                        print("[!] Url id of the survey defined with: -s")
                        exit(1)
                    if options.target is None:
                        print("[!] Target checkbox to vote for is not defined with: -t")
                        exit(1)
                    try:
                        self.maxVotes = int(options.votes)
                    except ValueError:
                        print("[!] You incorrectly defined a non integer for -v")

                    # Save arguments into global variable
                    self.voteFor = options.target
                    self.surveyId = options.survey

                    # Flush usedProxies.txt
                    if options.flush == True:
                        print("[#] Flushing usedProxies.txt file...")
                        os.remove(self.saveStateFile)
                        open(self.saveStateFile, 'w+')
                    # Alter domain if not None.
                    if options.domain is not None:
                        self.domainEnd = options.domain
                    if options.renew == True:
                        renewlist=self.renewProxyList();
                        os.remove(self.proxyListFile)
                        with open(self.proxyListFile, "a") as myfile:
                            for i in renewlist:
                                myfile.write(i)

            # Print help
            else:
                print("[!] Not enough arguments given")
                print()
                parser.print_help()
                exit()

            # Read proxy list file
            alreadyUsedProxy = False
            proxyList = open(self.proxyListFile).read().split('\n')

            proxyList2 = None

            # Check if saveState.xml exists and read file
            if os.path.isfile(self.saveStateFile):
                proxyList2 = open(self.saveStateFile).read().split('\n')

            # Print remaining proxies
            if proxyList2 is not None:
                print("[#] Number of proxies remaining in old list: " + str(len(proxyList) - len(proxyList2)))
                print()
            else:
                print("[#] Number of proxies in new list: " + str(len(proxyList)))
                print()

            # Go through proxy list
            for proxy in proxyList:

                # Check if max votes has been reached
                if self.successfulVotes >= self.maxVotes:
                    break

                # Increase number of used proxy integer
                self.currentProxyPointer += 1



                # Read in saveState.xml if this proxy has already been used
                if proxyList2 is not None:
                    for proxy2 in proxyList2:
                        if proxy == proxy2:
                            alreadyUsedProxy = True
                            break

                # If it has been used print message and continue to next proxy
                if alreadyUsedProxy == True:
                    print("["+ str(self.currentProxyPointer) +"] Skipping proxy: " + proxy)
                    alreadyUsedProxy = False
                    continue

                # Print current proxy information
                print("["+ str(self.currentProxyPointer) +"] New proxy: " + proxy)
                print("[#] Connecting... ")

                # Connect to strawpoll and send vote
                # self.sendToWeb('http://' + proxy,'https://' + proxy)
                self.webdriverManipulation(proxy);
                # Write used proxy into saveState.xml
                self.writeUsedProxy(proxy)
                print()

            # Check if max votes has been reached
            if self.successfulVotes >= self.maxVotes:
                print("[*] Finished voting: " + str(self.successfulVotes) + ' times.')
            else:
                print("[*] Finished every proxy in the list.")

            exit()
        except IOError as ex:
            print("[!] " + ex.strerror + ": " + ex.filename)

        except KeyboardInterrupt as ex:
            print("[#] Ending procedure...")
            print("[#] Programm aborted")
            exit()





    def writeUsedProxy(self, proxyIp):
        if os.path.isfile(self.saveStateFile):
            with open(self.saveStateFile, "a") as myfile:
                myfile.write(proxyIp+"\n")




    def getIp(self, httpProxy):
        proxyDictionary = {"https": httpProxy}
        request = requests.get("https://api.ipify.org/", proxies=proxyDictionary)
        requestString = str(request.text)
        return requestString

	# Using selenium and chromedriver to run the voting process on the background
    def webdriverManipulation(self,Proxy):
        try:
            WINDOW_SIZE = "1920,1080"

            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
            chrome_options.add_argument('--proxy-server=%s' % Proxy)
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)
            chrome = webdriver.Chrome(options=chrome_options)

            if self.domainEnd == "me":
                chrome.get('https://www.strawpoll.' + self.domainEnd + '/' + self.surveyId)
                element = chrome.find_element_by_xpath('//*[@value="'+ self.voteFor +'"]')
                webdriver.ActionChains(chrome).move_to_element(element).click(element).perform()
                submit_button = chrome.find_elements_by_xpath('//*[@type="submit"]')[0]
                submit_button.click()
            else:
                chrome.get('https://strawpoll.' + self.domainEnd + '/' + self.surveyId)
                element = chrome.find_element_by_xpath('//*[@name="'+ self.voteFor +'"]')
                webdriver.ActionChains(chrome).move_to_element(element).click(element).perform()
                submit_button = chrome.find_elements_by_xpath('//*[@id="votebutton"]')[0]
                submit_button.click()

            chrome.quit()
            print("[*] Successfully voted.")
            self.successfulVotes += 1
            return True
        except Exception as exception:
            print("[!] Voting failed for the specific proxy.")
            chrome.quit()
            return False

    # Posting through requests (previous version)
    def sendToWeb(self,httpProxy, httpsProxy):
        try:
            headers = \
                {
                    'Host': 'strawpoll.'+ self.domainEnd,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0',
                    'Accept': '*/*',
                    'Accept-Language': 'en - us, en; q = 0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Charset': 'ISO - 8859 - 1, utf - 8; = 0.7, *;q = 0.7',
                    'Referer': 'https://strawpoll.'+ self.domainEnd +'/' + self.surveyId,
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Length': '29',
                    'Cookie': 'lang=en',
                    'DNT': '1',
                    'Connection': 'close'
                }
            payload = {'pid': self.surveyId, 'oids': self.voteFor}
            proxyDictionary = {"http": httpProxy,"https": httpsProxy}
            # Connect to server
            r = requests.post('https://strawpoll.' + self.domainEnd + '/vote', data=payload, headers=headers)
            json = r.json()
            # Check if the vote was successful
            if(bool(json['success'])):
                print("[*] Successfully voted.")
                self.successfulVotes += 1
                return True
            else:
                print("[!] Voting failed.")
                return False
        except requests.exceptions.Timeout:
            print("[!] Timeout")
            return False
        except requests.exceptions.ConnectionError:
            print("[!] Couldn't connect to proxy")
            return False
        except Exception as exception:
            print(str(exception))
            return False

    # Renew Proxy List
    def renewProxyList(self):
        final_list=[]
        url = "http://proxy-daily.com/"
        content = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(content,features="html5lib")
        center = soup.find_all("center")[0]
        div = center.findChildren("div", recursive=False)[0].getText();
        children= div.splitlines()
        for child in children:
            final_list.append(child+"\n")
        return (final_list)
# Execute strawpoll_multivote
Strawpoll_Multivote()
