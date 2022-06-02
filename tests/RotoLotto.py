# Go to root of PyNXReader
import signal
import sys
import json

sys.path.append('../')

from nxreader import SWSHReader
from rng import XOROSHIRO

npc_count = 6
target_ids = [
    69420,
    42069,
    12345,
    54321
]

def generate(_rng: XOROSHIRO, npc_count = 6):
    __rng = XOROSHIRO(*_rng.seed.copy())
    menu_advances = 0
    for _ in range(npc_count):
        menu_advances += __rng.rand_count(91)[1]
    __rng.next()
    menu_advances += 1 + __rng.rand_count(60)[1]
    return {"menu_advances": menu_advances, "lotto": __rng.rand(10) * 10000 + __rng.rand(10) * 1000 + __rng.rand(10) * 100 + __rng.rand(10) * 10 + __rng.rand(10)}

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


print(f"Advance {advances}, State {rng.state:016X}")
result = generate(predict, npc_count)
while result["lotto"] not in target_ids:
    predict_advances += 1
    predict.next()
    result = generate(predict, npc_count)
print(predict_advances, result)
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