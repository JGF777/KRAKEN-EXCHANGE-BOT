import hashlib
import json
import requests
import time
import urllib.parse
import hmac
import base64

"""Perform a market order on a specified 
symbol using the specified 
investment amount.
Reeplace API KEY and API SECRET"""

#GLOBAL VARIABLES
API_KEY = ''
API_SECRET= ''
API_URL = "https://api.kraken.com"
URI_PATH = "/0/private/AddOrder"    #As per API URL string instructions
SYMBOL = 'XXBTZEUR'                 #As per API strings instructions
INVESTMENT = 10                     #Amount in EUR to create a market order.

#Bot Class with the relevant methods to perform a correct authentication and market order.

class MyOwnKrakenBot:

    def __init__(self, API_KEY, API_SECRET, API_URL, URI_PATH, SYMBOL, INVESTMENT):
    
        self.api_key = API_KEY
        self.api_secret = API_SECRET
        self.api_url = API_URL
        self.uri_path = URI_PATH
        self.symbol = SYMBOL
        self.investment = INVESTMENT    
    
    def kraken_request(self, data):
    
        # get_kraken_signature() as defined in the 'Authentication' section
    
        headers = {}
        headers['API-Key'] = self.api_key
        headers['API-Sign'] = self.get_kraken_signature(data)  
        
        req = requests.post((self.api_url + self.uri_path), headers=headers, data=data)
        
        return req

    def get_current_price(self):
    
        #Get the current price of the specified symbol
        
        url = "https://api.kraken.com/0/public/Ticker?pair={}".format(self.symbol)
        response = requests.get(url)
        
        return response.json()['result'][self.symbol]['c'][0]
    
    def get_kraken_signature(self, data):
        
        #Get_kraken_signature() as defined in the 'Authentication' section

        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = self.uri_path.encode() + hashlib.sha256(encoded).digest()

        mac = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())
        
        return sigdigest.decode()


    def handle_retries(self, func, max_retries=3, retry_wait=5):

        #Helper function to handle connectivity issues etc. 

        retry_count = 0

        while True:
            try:
                result = func()
                return result
            except Exception as e:
                retry_count += 1
                if retry_count > max_retries:
                    print("Too many retries, giving up...")
                    return None
                print("An error occurred, retrying in {} seconds... Error:".format(retry_wait), str(e))
                time.sleep(retry_wait)

    def get_data_variable_order(self, price, volume, OrderAction , OrderType):
    
        #Function to obtain the relevant data variable (dict) with the relevant parameters 
        #Price passed is obtaind through the previous method, string.
        #volume is float, needs to be converted to string
        
        data = {
        "nonce": int(time.time()), 
        "ordertype": OrderType, 
        "pair": self.symbol,
        "price": price, #Optional 
        "type": OrderAction,
        "volume": str(volume)}                  
        
        return data
        
    def get_data_nonce(self):
    
        #Simple helper function to obtain just to pass the nonce to simple requests.
    
        data = {
        "nonce": int(time.time())
        } 
        
        return data

def main():
    
    #Initializing the BOT
    KrakenBot = MyOwnKrakenBot(API_KEY, API_SECRET, API_URL, URI_PATH, SYMBOL, INVESTMENT)
    
    #Pulling price variable from the API
    price = KrakenBot.handle_retries(KrakenBot.get_current_price)

    if price is None:
        return
    volume = KrakenBot.investment / float(price)

    #Constructing the data variable for a buy market order 
    data = KrakenBot.get_data_variable_order(price, volume, "buy" ,"market")
    
    #Getting the API Signature and print the result for feedback.
    signature = KrakenBot.get_kraken_signature(data)
    print("API-Sign: {}".format(signature))
    
    #Posting the order request
    resp = KrakenBot.handle_retries(lambda: KrakenBot.kraken_request(data))

    if resp is None:
        return
    if resp.status_code == 200:
        print(resp.json())
    else:
        print("Request failed with status code:", resp.status_code)

if __name__ == "__main__":
    
      main()
        

