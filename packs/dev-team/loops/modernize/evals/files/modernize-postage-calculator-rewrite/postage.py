# postage.py -- written 2014, do not touch without asking Gerald
# calc(weight_g, zone) -> pence, or -1 on bad input
import math

RATES = {'small': 85, 'medium': 155, 'large': 320}
EXTRA_PER_KG = 90

def calc(w, z):
    global last_zone
    last_zone = z
    try:
        w = int(w)
    except:
        return -1
    if w <= 0:
        return -1
    if w <= 100:
        p = RATES['small']
    elif w < 500:
        p = RATES['medium']
    elif w <= 2000:
        p = RATES['large']
    else:
        extra = w - 2000
        p = RATES['large'] + EXTRA_PER_KG * int(math.ceil(extra / 1000.0))
    if z == 'UK':
        return p
    if z == 'IE':
        return int(p * 1.5)
    if z == 'EU':
        return p * 2
    return -1
