# Go to root of PyNXReader
import signal
import sys
import json

sys.path.append('../')

from nxreader import SWSHReader
from rng import XOROSHIRO,OverworldRNG,Filter

# def generate(_rng: XOROSHIRO):
#     __rng = XOROSHIRO(*_rng.seed.copy())
#     return 

config = json.load(open("../config.json"))
r = SWSHReader(config["IP"],usb_connection=config["USB"])

def signal_handler(signal, frame): #CTRL+C handler
    print("Stop request")
    r.close()

def filt(result):
    return result["isSafariSport"] and result["isBonusCount"]

signal.signal(signal.SIGINT, signal_handler)
seed = r.readRNG()
rng = XOROSHIRO(int.from_bytes(seed[0:8],"little"),int.from_bytes(seed[8:16],"little"))
predict = XOROSHIRO(int.from_bytes(seed[0:8],"little"),int.from_bytes(seed[8:16],"little"))
advances = -1
predict_advances = 0


print(f"Advance {advances}, State {rng.state:016X}")
# result = generate(predict)
# while not filt(result):
#     predict_advances += 1
#     predict.next()
#     result = generate(predict)
# print(predict_advances, result)
last = 0
while True:
    read = int.from_bytes(r.readRNG(),"little")
    while rng.state != read or advances == -1:
        if advances != -1:
            rng.next()
        advances += 1
        if rng.state == read:
            test = XOROSHIRO(*rng.seed.copy())
            print(f"Advance {advances} +{advances-last}, State {rng.state:016X}")
    last = advances