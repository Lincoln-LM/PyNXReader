# Go to root of PyNXReader
from pprint import pprint
import signal
import sys
import json

sys.path.append('../')

from nxreader import SWSHReader
from rng import XOROSHIRO,OverworldRNG,Filter

config = json.load(open("../config.json"))
r = SWSHReader(config["IP"],usb_connection=config["USB"])

# default is for the tree in front of the meetup spot
BERRY_NAMES = ["Oran Berry", "Pecha Berry", "Cheri Berry"]
BERRY_RATES = [33, 33, 33]
POKEMON_NAMES = ["Skwovet", "Cherubi"]
POKEMON_RATES = [80, 20]
MIN_LEVEL = 7
MAX_LEVEL = 10
NPC_COUNT = 5 # -1 for non menu close
def berry_filter(result):
    return result['mark'] == "Rare" and result['pokemon'] == "Cherubi"

def signal_handler(signal, frame): #CTRL+C handler
    res = input("Exit? (y = exit, else = show path): ")
    if not res.lower().startswith("y"):
        seed = r.readRNG()
        rn = XOROSHIRO(int.from_bytes(seed[0:8],"little"),int.from_bytes(seed[8:16],"little"))
        result = generate(rn)
        print()
        print(f"{result['menu_advances']=}")
        print("Path:")
        for step in result["path"]:
            print(step)
        print()
        print(f"{result['pokemon']=}")
        print(f"{result['mark']=}")
    else:
        print("Stop request")
        r.close()


signal.signal(signal.SIGINT, signal_handler)
seed = r.readRNG()
rng = XOROSHIRO(int.from_bytes(seed[0:8],"little"),int.from_bytes(seed[8:16],"little"))
predict = XOROSHIRO(int.from_bytes(seed[0:8],"little"),int.from_bytes(seed[8:16],"little"))
advances = -1
predict_advances = 0

def generate(rng: XOROSHIRO):
    _rng = XOROSHIRO(*rng.seed.copy())
    # menu advances
    cnt = 0
    if NPC_COUNT != -1:
        for _ in range(NPC_COUNT):
            cnt += _rng.rand_count(91)[1]
        _rng.next()
        cnt += 1 + _rng.rand_count(60)[1]
    # tree
    result = []
    sum = _rng.rand(59) + 21
    while True:
        sum += _rng.rand(7) + 8
        if 99 < sum:
            # encounter
            _rng.rand(100) # lead rand
            _rng.rand(100) # dex rec(?)
            slot_rand = _rng.rand(100)
            level = _rng.rand(MAX_LEVEL - MIN_LEVEL + 1) + MIN_LEVEL
            pokemon = POKEMON_NAMES[-1]
            for i,rate in enumerate(POKEMON_RATES):
                if slot_rand < rate:
                    pokemon = POKEMON_NAMES[i]
                    break
                slot_rand -= rate
            mark = OverworldRNG.rand_mark(_rng, weather_active = False, is_fishing = False, mark_charm = True)
            result.append(f"Lv. {level} {pokemon} Mark: {mark}")
            return {"path": result, "pokemon": pokemon, "mark": mark, "level": level, "menu_advances": cnt}
        _berries = []
        for _ in range(_rng.rand(3) + 1):
            berry_rand = _rng.rand(100)
            berry_name = BERRY_NAMES[-1]
            for i,rate in enumerate(BERRY_RATES):
                if berry_rand <= rate:
                    berry_name = BERRY_NAMES[i]
                    break
                berry_rand -= rate
            _berries.append(berry_name)
        
        result.append(_berries)

print(f"Advance {advances}, State {rng.state:016X}")
result = generate(predict)
while not berry_filter(result):
    predict_advances += 1
    predict.next()
    result = generate(predict)
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

    last = advances