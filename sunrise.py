#! /usr/bin/env python3
import sys
import requests
import uuid
import json
import datetime
import time

# TODO: Use https://api.sunrise-sunset.org/json?lat=34.034622&lng=-118.457941&tzid=America/Los_Angeles
# to determine dawn and sunrise time
DAWN_TIME    = '07:28:00'
SUNRISE_TIME = '07:55:00'

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


def clamp(i):
    if i > 255:
        i = 255
    return i

def make_orange(r):
    return (clamp(r), clamp(r//4), clamp(r//50))

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

def make_color_compat_hex(color_hex):
    return make_color_compat_int(int(f'0x{color_hex}', 0))

def rgb_to_int(rgb):
    i = 0
    i += rgb[0]
    i <<= 8
    i += rgb[1]
    i <<= 8
    i += rgb[2]
    return i

def make_color_compat_rgb(rgb):
    return make_color_compat_int(rgb_to_int(rgb))

def make_color_compat_int(color_int):
    return {
        "type": "devices.capabilities.color_setting",
        "instance": "colorRgb",
        "value": color_int
    }


def make_brightness_compat(brightness):
    return {
        "type": "devices.capabilities.range",
        "instance": "brightness",
        "value": brightness
    }


def sunrise():
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

    while now < sunrise:
        now = datetime.datetime.now()
        print(now)
        if now < dawn:
            time.sleep(1) # wait for dawn?
            print("not dawn yet, sleeping")
            continue
        rise_length = sunrise - dawn
        rise_amount = now - dawn
        percentage = rise_amount.seconds/rise_length.seconds
        if percentage <= .50:
            # make percentage from 0%->50% fit [0,1]
            percentage /= .5
            control_govee(make_color_compat_rgb(make_orange(int(300*percentage))))
        else: # percentage > .50
            # make percentage from 50%->100% fit [0,1]
            percentage -= .5
            percentage /= .5

            # brightness from 25->100
            brightness = int(25+(100-25)*percentage**2.0)
            # TODO: Better clamp?
            if brightness > 100:
                brightness = 100
            control_govee(make_brightness_compat(brightness))

        time.sleep(7) # sleep for rate limits

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        control_govee(make_brightness_compat(1))
        control_govee(make_color_compat_rgb(make_orange(0)))
        sys.exit(0)

    sunrise()

