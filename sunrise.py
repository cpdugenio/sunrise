#! /usr/bin/env python3
import sys
import requests
import uuid
import json
import datetime
import time

# TODO: Use https://api.sunrise-sunset.org/json?lat=34.034622&lng=-118.457941&tzid=America/Los_Angeles
# to determine dawn and sunrise time
DAWN_TIME = '06:28:00'
SUNRISE_TIME = '06:55:00'

LIGHT_SKU = 'H6003'
LIGHT_MAC_ADDRESS = None
GOVEE_API_KEY = None

with open('.secret', 'r') as secret:
    GOVEE_API_KEY = secret.read().strip()
with open('.light', 'r') as light:
    LIGHT_MAC_ADDRESS = light.read().strip()

TEMPERATURE_COMPAT_HI = {
    "type": "devices.capabilities.color_setting",
    "instance": "colorTemperatureK",
    "value": 9000
}

TEMPERATURE_COMPAT = {
    "type": "devices.capabilities.color_setting",
    "instance": "colorTemperatureK",
    "value": 2000
}

POWER_COMPAT = {
    "type": "devices.capabilities.on_off",
    "instance": "powerSwitch",
    "value": 1
}

def control_govee(compat):
    request_id = str(uuid.uuid4())
    request_body = json.dumps(
        {
            "requestId": request_id,
            "payload": {
                "sku": LIGHT_SKU,
                "device": LIGHT_MAC_ADDRESS,
                "capability": compat
            }
        }
    )
    print(">> Sending request:")
    print(request_id)
    print(request_body)
    response = requests.post(
        'https://openapi.api.govee.com/router/api/v1/device/control',
        headers={
            'Content-Type': 'application/json',
            'Govee-API-Key': GOVEE_API_KEY
        },
        data=request_body
    )
    print(">> Response:")
    print(response)
    print(response.content)

def make_brightness_compat(brightness):
    return {
        "type": "devices.capabilities.range",
        "instance": "brightness",
        "value": brightness
    }


if __name__ == '__main__':
    now = datetime.datetime.now()
    dawn = datetime.datetime.strptime(now.strftime(f"%Y-%m-%d {DAWN_TIME}"), "%Y-%m-%d %H:%M:%S")
    sunrise = datetime.datetime.strptime(now.strftime(f"%Y-%m-%d {SUNRISE_TIME}"), "%Y-%m-%d %H:%M:%S")

    if now < dawn:
        print("not dawn yet, sleeping")
        seconds_to_dawn = (dawn - now).seconds
        print(seconds_to_dawn)
        time.sleep(seconds_to_dawn)

    print(dawn)
    print(sunrise)
    bFirst_setting = True
    while now < sunrise:
        now = datetime.datetime.now()
        print(now)
        if now < dawn:
            time.sleep(1) # wait for dawn?
            print("not dawn yet, sleeping")
            continue
        rise_length = sunrise - dawn
        rise_amount = now - dawn
        brightness = (int(25+(100-25)*rise_amount.seconds/rise_length.seconds))
        if brightness < 25:
            # keep sleeping until brightness is at least 25
            # TODO: surely there's a way to math when 25 will happen, but whatever
            time.sleep(1)
            continue

        # TODO: Better clamp?
        if brightness < 1:
            brigtness = 1
        if brightness > 100:
            brigtness = 100
        print(brightness)
        control_govee(make_brightness_compat(brightness))
        if bFirst_setting:
            control_govee(TEMPERATURE_COMPAT)
            bFirst_setting = False
        time.sleep(7) # sleep for rate limits
