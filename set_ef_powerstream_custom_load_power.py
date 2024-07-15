# Example Code to obtain data from API for specific sensors on an EcoFlow device
# Mark Hicks - 01/29/2024
# written by mail@sven-erbe.de - 14/02/2024

# mode VedicV - 14/07/2024

# short description
# script set powerstream - WN511_SET_PERMANENT_WATTS_PACK depend on TotalPower
# function: set_ef_powerstream_custom_load_power(SerialNumber=None,TotalPower=None,Automation=False)
# 
# 
# prerequest:
# Pyscript: Python scripting integration - https://github.com/custom-components/pyscript
# ecoflow AccessKey and SecretKey - needs to request on https://developer-eu.ecoflow.com/
# Powerstream
# please change accesskey and secret in the script

import sys
import json
import requests
import hashlib
import hmac
import random
import time
import binascii
from urllib.parse import urlencode


def hmac_sha256(data, key):
    hashed = hmac.new(key.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).digest()
    sign = binascii.hexlify(hashed).decode('utf-8')
    return sign

def get_map(json_obj, prefix=""):
  def flatten(obj, pre=""):
    result = {}
    if isinstance(obj, dict):
      for k, v in obj.items():
        result.update(flatten(v, f"{pre}.{k}" if pre else k))
    elif isinstance(obj, list):
      for i, item in enumerate(obj):
        result.update(flatten(item, f"{pre}[{i}]"))
    else: result[pre] = obj
    return result
  return flatten(json_obj, prefix)

def get_qstr(params): return '&'.join([f"{key}={params[key]}" for key in sorted(params.keys())])

def put_api(url, key, secret, params=None):
  nonce     = str(random.randint(100000, 999999))
  timestamp = str(int(time.time() * 1000))
  headers   = {'accessKey':key,'nonce':nonce,'timestamp':timestamp}
  sign_str  = (get_qstr(get_map(params)) + '&' if params else '') + get_qstr(headers)
  headers['sign'] = hmac_sha256(sign_str, secret)
  response = task.executor(requests.put, url, headers=headers, json=params)
  if response.status_code == 200: return response.json()
  else: print(f"put_api: {response.text}")

def post_api(url, key, secret, params=None):
  nonce     = str(random.randint(100000, 999999))
  timestamp = str(int(time.time() * 1000))
  headers   = {'accessKey':key,'nonce':nonce,'timestamp':timestamp}
  sign_str  = (get_qstr(get_map(params)) + '&' if params else '') + get_qstr(headers)
  headers['sign'] = hmac_sha256(sign_str, secret)
  response = task.executor(requests.post, url, headers=headers, json=params)
  #if response.status_code == 200: return response.json()
  if response.status_code == 200: return response
  else: print(f"post_api: {response.text}")


@service
def set_ef_powerstream_custom_load_power(SerialNumber=None,TotalPower=None):

    log.info(f"set_ef_powerstream_custom_load_power: got SerialNumber {SerialNumber} TotalPower {TotalPower}")

    if SerialNumber is None:
        log.info(f"SerialNumber is not provided. Exiting function.")
        print("SerialNumber is not provided. Exiting function.")
        return  # Exit the function if SerialNumber is None

    
    # Replace with valid access/secret keys
    key = '--KEY--'
    secret = ' --SECRET--'

    
    url = 'https://api.ecoflow.com/iot-open/sign/device/quota'

    # New oficial EcoFlow API Endpoint
    url2 = 'https://api-e.ecoflow.com/iot-open/sign/device/quota'
    
    cmdCode = 'WN511_SET_PERMANENT_WATTS_PACK'
    TotalPowerOffSet = 0

    # collect current permanentWatts
    quotas = ["20_1.permanentWatts"]
    params  = {"quotas":quotas}

    payload = post_api(url,key,secret,{"sn":SerialNumber,"params":params})
    if payload.status_code == 200:
        try:
            cur_permanentWatts = round(payload.json()['data']['20_1.permanentWatts'] / 10)
        except KeyError as e:
            log.info(f"Error accessing data in payload:", e)
            return  # Exit the function or handle the error appropriately
    else:
        cur_permanentWatts = 0
        return 4, "Integration was not able to collect the current permanentWatts from EcoFlow SP!"

    CalPermanentWatts = TotalPower - TotalPowerOffSet

    try:
        # allow only value between 0-600
        if 0 <= CalPermanentWatts <= 600:
            NewPermanentWatts = CalPermanentWatts * 10
        else:
            NewPermanentWatts= 0

        if CalPermanentWatts > 600:
            NewPermanentWatts = 600 * 10

        params = {"permanentWatts":NewPermanentWatts}

        payload = put_api(url,key,secret,{"sn":SerialNumber,"cmdCode":cmdCode,"params":params})
        return payload

    except Exception as e:
        print(f"Error fetching Ecoflow data: {str(e)}")
        return None
