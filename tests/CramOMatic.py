# Go to root of PyNXReader
import signal
import sys
import json

sys.path.append('../')

from nxreader import SWSHReader
from rng import XOROSHIRO

npc_count = 21
def filter_cram(result):
    return result["isSafariSport"] and result["isBonusCount"]

def generate(_rng: XOROSHIRO, npc_count = 21):
    __rng = XOROSHIRO(*_rng.seed.copy())
    # menu close advances
    menu_advances = 0
    for _ in range(npc_count):
        menu_advances += __rng.rand_count(91)[1]
    __rng.next()
    menu_advances += 1 + __rng.rand_count(60)[1]

    # scam o matic
    item_roll = __rng.rand(4)
    ball_roll = __rng.rand(100)
    is_safari_sport = __rng.rand(1000) == 0
    if is_safari_sport or ball_roll == 99:
        is_bonus_count = __rng.rand(1000) == 0
    else:
        is_bonus_count = __rng.rand(100) == 0
    return {"menuAdvances": menu_advances, "itemRoll": item_roll, "ballRoll": ball_roll, "isSafariSport": is_safari_sport, "isBonusCount": is_bonus_count}

config = json.load(open("../config.json"))
r = SWSHReader(config["IP"],usb_connection=config["USB"])

def signal_handler(signal, frame): #CTRL+C handler
    print("Stop request")
    r.close()

signal.signal(signal.SIGINT, signal_handler)
seed = r.readRNG()
rng = XOROSHIRO(int.from_bytes(seed[0:8],"little"),int.from_bytes(seed[8:16],"little"))
predict = XOROSHIRO(int.from_bytes(seed[0:8],"little"),int.from_bytes(seed[8:16],"little"))
advances = -1
predict_advances = 0

result = generate(predict, npc_count)
print(f"State {rng.state:016X}")
print("finding target...")
while not filter_cram(result):
    predict_advances += 1
    predict.next()
    result = generate(predict, npc_count)
last = 0
while True:
    read = int.from_bytes(r.readRNG(),"little")
    while rng.state != read or advances == -1:
        if advances != -1:
            rng.next()
        advances += 1
        if rng.state == read:
            print(f"Advance {advances} +{advances-last}, State {rng.state:016X}")
            print(f"Predict {advances} +{generate(rng, npc_count)['menu_advances']}")
            print(predict_advances, result)
            print()
    last = advances