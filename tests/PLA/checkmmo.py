# Go to root of PyNXReader
import signal
import sys
import json
import struct
from math import factorial
import colorama
sys.path.append('../../')

from nxreader import NXReader
from rng import XOROSHIRO
from lookups import Util
from colorama import Fore, Back, Style


config = json.load(open("../../config.json"))
reader = NXReader(config["IP"],usb_connection=config["USB"])
colorama.init()

def signal_handler(signal, advances): #CTRL+C handler
    print("Stop request")
    reader.close()

signal.signal(signal.SIGINT, signal_handler)

def generate_from_seed(seed,rolls,guaranteed_ivs=0,set_gender=False):
    rng = XOROSHIRO(seed)
    ec = rng.rand(0xFFFFFFFF)
    sidtid = rng.rand(0xFFFFFFFF)
    for _ in range(rolls):
        pid = rng.rand(0xFFFFFFFF)
        shiny = ((pid >> 16) ^ (sidtid >> 16) \
            ^ (pid & 0xFFFF) ^ (sidtid & 0xFFFF)) < 0x10
        if shiny:
            break
    ivs = [-1,-1,-1,-1,-1,-1]
    for i in range(guaranteed_ivs):
        index = rng.rand(6)
        while ivs[index] != -1:
            index = rng.rand(6)
        ivs[index] = 31
    for i in range(6):
        if ivs[i] == -1:
            ivs[i] = rng.rand(32)
    ability = rng.rand(2) # rand(3) if ha possible
    if set_gender:
        gender = -1
    else:
        gender = rng.rand(252) + 1
    nature = rng.rand(25)
    return ec,pid,ivs,ability,gender,nature,shiny

def generate_mass_outbreak_aggressive_path(group_seed,rolls,steps,uniques,storage,spawns,true_spawns,encounters,encsum,isbonus=False,isalpha=False):
    """Generate all the pokemon of an outbreak based on a provided aggressive path"""
    # pylint: disable=too-many-locals, too-many-arguments
    # the generation is unique to each path, no use in splitting this function
    main_rng = XOROSHIRO(group_seed)
    for init_spawn in range(1,5):
        generator_seed = main_rng.next()
        main_rng.next() # spawner 1's seed, unused
        fixed_rng = XOROSHIRO(generator_seed)
        encounter_slot = (fixed_rng.next() / (2**64)) * encsum
        species,alpha = get_species(encounters,encounter_slot)
        if isbonus and alpha:
            guaranteed_ivs = 4
        elif isbonus or alpha:
            guaranteed_ivs = 3
        else:
            guaranteed_ivs = 0
        fixed_seed = fixed_rng.next()
        encryption_constant,pid,ivs,ability,gender,nature,shiny = \
            generate_from_seed(fixed_seed,rolls,guaranteed_ivs)
        if shiny and not fixed_seed in uniques:
        #if not fixed_seed in uniques and isbonus:
            uniques.add(fixed_seed)
            storage.append(
                   f"Init Spawn {init_spawn} \nShiny: "
                   f"{shiny}\n"
                   f"Species: {species}\n" \
                   f"Alpha: {Back.BLUE if alpha else Back.BLACK}" \
                   f"{alpha}  {Style.RESET_ALL}\n" \
                   f"EC: {encryption_constant:08X} PID: {pid:08X}\n"
                   f"Nature: {Util.STRINGS.natures[nature]} Ability: {ability} Gender: {gender}\n"
                   f"{'/'.join(str(iv) for iv in ivs)}")
    group_seed = main_rng.next()
    respawn_rng = XOROSHIRO(group_seed)
    for step_i,step in enumerate(steps):
        for pokemon in range(1,step+1):
            generator_seed = respawn_rng.next()
            respawn_rng.next() # spawner 1's seed, unused
            fixed_rng = XOROSHIRO(generator_seed)
            encounter_slot = (fixed_rng.next() / (2**64)) * encsum
            species,alpha = get_species(encounters,encounter_slot)
            if isbonus and alpha:
                guaranteed_ivs = 4
            elif isbonus or alpha:
                guaranteed_ivs = 3
            else:
                guaranteed_ivs = 0
            fixed_seed = fixed_rng.next()
            encryption_constant,pid,ivs,ability,gender,nature,shiny = \
                generate_from_seed(fixed_seed,rolls,guaranteed_ivs)
            if shiny and not fixed_seed in uniques and (sum(steps[:step_i]) + pokemon + 4) <= true_spawns:
            #if not fixed_seed in uniques and (sum(steps[:step_i]) + pokemon + 4) <= true_spawns and isbonus:
                uniques.add(fixed_seed)
                storage.append(
                   f"Path: {'|'.join(str(s) for s in steps[:step_i]+[pokemon])} " \
                   f"Spawns: {sum(steps[:step_i]) + pokemon + 4} Shiny: " \
                   f"{shiny}\n" \
                   f"Species: {species}\n" \
                   f"Alpha: {Back.BLUE if alpha else Back.BLACK}" \
                   f"{alpha} {Style.RESET_ALL}\n" \
                   f"EC: {encryption_constant:08X} PID: {pid:08X}\n" \
                   f"Nature: {Util.STRINGS.natures[nature]} Ability: {ability} Gender: {gender}\n" \
                   f"{'/'.join(str(iv) for iv in ivs)}"
                )
        respawn_rng = XOROSHIRO(respawn_rng.next())
        """
        if respawn_rng not in bonus_seeds and (sum(steps[:step_i]) + pokemon + 4) <= true_spawns:
            bonus_seeds.add(respawn_rng)
        """

def get_final(spawns):
    """Get the final path that will be generated to know when to stop aggressive recursion"""
    spawns -= 4
    path = [4] * (spawns // 4)
    if spawns % 4 != 0:
        path.append(spawns % 4)
    return path

def aggressive_outbreak_pathfind(group_seed,
                                 rolls,
                                 spawns,
                                 true_spawns,
                                 encounters,
                                 encsum,
                                 isbonus=False,
                                 isalpha=False,
                                 step=0,
                                 steps=None,
                                 uniques=None,
                                 storage=None):
    """Recursively pathfind to possible shinies for the current outbreak via multi battles"""
    # pylint: disable=too-many-arguments
    # can this algo be improved?
    if steps is None or uniques is None or storage is None:
        steps = []
        uniques = set()
        storage = []
    _steps = steps.copy()
    if step != 0:
        _steps.append(step)
    if sum(_steps) + step < spawns - 4:
        for _step in range(1, min(5, (spawns - 4) - sum(_steps))):
            if aggressive_outbreak_pathfind(group_seed,
                                            rolls,
                                            spawns,
                                            true_spawns,
                                            encounters,
                                            encsum,
                                            isbonus,
                                            isalpha,
                                            _step,
                                            _steps,
                                            uniques,
                                            storage) is not None:
                return storage
    else:
        _steps.append(spawns - sum(_steps) - 4)
        generate_mass_outbreak_aggressive_path(group_seed,rolls,_steps,uniques,storage,spawns,true_spawns,encounters,encsum,isbonus,isalpha)
        if _steps == get_final(spawns):
            return storage
    return None

def next_filtered_aggressive_outbreak_pathfind(group_seed,rolls,spawns,true_spawns,group_id,isbonus,isalpha=False):
    """Check the next outbreak advances until an aggressive path to a pokemon that
       passes poke_filter exists"""
    encounters,encsum = get_encounter_table(group_id,isbonus)
    main_rng = XOROSHIRO(group_seed)
    result = []
    advance = -1
    
    while len(result) == 0 and advance < 1:
        if advance != -1:
            for _ in range(4*2):
                main_rng.next()
            group_seed = main_rng.next()
            main_rng.reseed(group_seed)
        advance += 1
        result = aggressive_outbreak_pathfind(group_seed, rolls, spawns,true_spawns,encounters,encsum,isbonus,isalpha)
        if result is None:
            result = []
    if advance == 0:
        info = '\n'.join(result)
    else:
        info = '\n'
    if advance != 0:
        return f"Nothing found for this outbreak. Spawns: {true_spawns}\n{info}"
    else:
        return f"Spawns: {spawns}\n{info}"

def bonus_round(group_seed,rolls,group_id):
    max_spawns = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+i*0x90 + 0xb80 * maps+0x60:X}",4)
    print(f"Bonus Flag: {bonus_flag}")
    main_rng = XOROSHIRO(group_seed)
    encounters,encsum = get_encounter_table(group_id,True)
    for init_spawn in range(4):
        generator_seed = main_rng.next()
        main_rng.next() # spawner 1's seed, unused
        fixed_rng = XOROSHIRO(generator_seed)
        encounter_slot = (fixed_rng.next() / (2**64)) * encsum
        species,alpha = get_species(encounters,encounter_slot)
        fixed_seed = fixed_rng.next()
        ec,pid,ivs,ability,gender,nature,shiny = generate_from_seed(fixed_seed,rolls,4 if alpha else 3)
        if shiny:
            print(f"{generator_seed:X} Species: {species} Alpha: {Back.BLUE if alpha else Back.BLACK} {alpha}" + Style.RESET_ALL + f" Shiny: {shiny} BONUS ROUND Init Spawn {init_spawn} EC: {ec:08X} PID: {pid:08X} Nature: {Util.STRINGS.natures[nature]} {'/'.join(str(iv) for iv in ivs)}\n")
    group_seed = main_rng.next()
    main_rng = XOROSHIRO(group_seed)
    respawn_rng = XOROSHIRO(group_seed)
    for respawn in range(1,max_spawns-3):
        generator_seed = respawn_rng.next()
        respawn_rng.next() # spawner 1's seed, unused
        respawn_rng = XOROSHIRO(respawn_rng.next())
        fixed_rng = XOROSHIRO(generator_seed)
        encounter_slot = (fixed_rng.next() / (2**64)) * encsum
        species,alpha = get_species(encounters,encounter_slot)
        fixed_seed = fixed_rng.next()
        ec,pid,ivs,ability,gender,nature,shiny = generate_from_seed(fixed_seed,rolls,4 if alpha else 3)
        if shiny:
            print(f"{generator_seed:X} Species: {species} Alpha: {Back.BLUE if alpha else Back.BLACK} {alpha}" + Style.RESET_ALL + f" Shiny: {shiny} BONUS ROUND Respawn {respawn} EC: {ec:08X} PID: {pid:08X} Nature: {Util.STRINGS.natures[nature]} {'/'.join(str(iv) for iv in ivs)}\n")

def get_bonus_seed(group_id,rolls,mapcount,path):
    species = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * mapcount:X}",2)
    #print(f"Species Pointer: [[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * mapcount:X}")
    if species != 0:
        if species == 201:
            rolls = 19
        group_seed = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * mapcount+0x44:X}",8)
        max_spawns = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * mapcount+0x60:X}",4)
        #print(f"Max spawns: {max_spawns}")
        curr_spawns = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * mapcount+0x50:X}",4)
        main_rng = XOROSHIRO(group_seed)
        for init_spawn in range(4):
            generator_seed = main_rng.next()
            main_rng.next() # spawner 1's seed, unused
            fixed_rng = XOROSHIRO(generator_seed)
            fixed_rng.next()
            fixed_seed = fixed_rng.next()
            ec,pid,ivs,ability,gender,nature,shiny = generate_from_seed(fixed_seed,rolls)
        group_seed = main_rng.next()
        main_rng = XOROSHIRO(group_seed)
        respawn_rng = XOROSHIRO(group_seed)
        generator_seed = 0
        #for respawn in range(1,max_spawns-3):
        #print(f"Path: {path}")
        for respawn,step in enumerate(path):
            #print(f"Respawn: {respawn} Step {step}")
            for pokemon in range(0,step):
                #print(f"Pokemon {pokemon}")
                generator_seed = respawn_rng.next()
                tempseed = respawn_rng.next() # spawner 1's seed, unused
                fixed_rng = XOROSHIRO(generator_seed)
                fixed_rng.next()
                fixed_seed = fixed_rng.next()
                ec,pid,ivs,ability,gender,nature,shiny = generate_from_seed(fixed_seed,rolls)
                fixed_seed = fixed_rng.next()
            respawn_rng = XOROSHIRO(respawn_rng.next())
        bonus_seed = (respawn_rng.next() - 0x82A2B175229D6A5B) & 0xFFFFFFFFFFFFFFFF
            #bonus_seed = respawn_rng.next()
        #print(f"Bonus Seed: {bonus_seed:X}")
        return bonus_seed
    else:
        print()
        print(f"Group {group_id} not active")
        return None
    
def read_mass_outbreak_rng(group_id,rolls,mapcount,aggro,bonus_flag,initial=False):
    species = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * mapcount:X}",2)
    print()
    print(f"Pokemon Species Group: {Util.STRINGS.species[species]}")
    #print(f"Species Pointer: [[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * mapcount:X}")
    if species != 0:
        if species == 201:
            rolls = 19
        group_seed = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * mapcount+0x44:X}",8)
        if initial:
            group_seed = (group_seed - 0x82A2B175229D6A5B) & 0xFFFFFFFFFFFFFFFF
            print(f"Group Seed (initial): {group_seed:X}")
        #print(f"Group seed pointer: [[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * mapcount+0x3c:X}")
        max_spawns = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * mapcount+0x4c:X}",4)
        curr_spawns = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * mapcount+0x50:X}",4)
        #print(f"Max Spawns: {max_spawns} Curr Spawns: {curr_spawns}")
       # print(f"Max Spawns Pointer: [[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * mapcount+0x4c:X}")
        if aggro:
        # should display multiple aggressive paths like whats done with passive
            true_spawns = max_spawns
            max_spawns += 3
            display = ["",
                       f"Group Seed: {group_seed:X}\n"
                       + next_filtered_aggressive_outbreak_pathfind(group_seed,rolls,max_spawns,true_spawns,group_id,False,False)]
            return display
        else:
            print(f"Group Seed: {group_seed:X}")
            main_rng = XOROSHIRO(group_seed)
            encounters,encsum = get_encounter_table(group_id,False)
            for init_spawn in range(4):
                generator_seed = main_rng.next()
                main_rng.next() # spawner 1's seed, unused
                fixed_rng = XOROSHIRO(generator_seed)
                encounter_slot = (fixed_rng.next() / (2**64)) * encsum
                species,alpha = get_species(encounters,encounter_slot)
                fixed_seed = fixed_rng.next()
                ec,pid,ivs,ability,gender,nature,shiny = generate_from_seed(fixed_seed,rolls,3 if alpha else 0)
                if shiny:
                    print(f"{generator_seed:X} Species: {species} Alpha: {Back.BLUE if alpha else Back.BLACK} {alpha}" + Style.RESET_ALL + f" Shiny: {shiny} Init Spawn {init_spawn} EC: {ec:08X} PID: {pid:08X} Nature: {Util.STRINGS.natures[nature]} {'/'.join(str(iv) for iv in ivs)}")
            group_seed = main_rng.next()
            main_rng = XOROSHIRO(group_seed)
            respawn_rng = XOROSHIRO(group_seed)
            generator_seed = 0
            for respawn in range(1,max_spawns-3):
                generator_seed = respawn_rng.next()
                respawn_rng.next() # spawner 1's seed, unused
                respawn_rng = XOROSHIRO(respawn_rng.next())
                fixed_rng = XOROSHIRO(generator_seed)
                encounter_slot = (fixed_rng.next() / (2**64)) * encsum
                species,alpa = get_species(encounters,encounter_slot)
                fixed_seed = fixed_rng.next()
                ec,pid,ivs,ability,gender,nature,shiny = generate_from_seed(fixed_seed,rolls,3 if alpha else 0)
                if shiny:
                    print(f"{generator_seed:X} Species: {species} Alpha: {Back.BLUE if alpha else Back.BLACK} {alpha}" + Style.RESET_ALL + f" Shiny: {shiny} Respawn {respawn} EC: {ec:08X} PID: {pid:08X} Nature: {Util.STRINGS.natures[nature]} {'/'.join(str(iv) for iv in ivs)}")
            bonus_seed = (respawn_rng.next() - 0x82A2B175229D6A5B) & 0xFFFFFFFFFFFFFFFF
            if bonus_flag:
                bonus_round(bonus_seed,rolls,group_id)
            return []
    else:
        print()
        print(f"Group {group_id} not active")
        return None

def get_encounter_table(group_id,bonus):
    encounters = {}
    encsum = 0
    if bonus:
        enc_pointer = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * maps+0x2c:X}",8)
    else:
        enc_pointer = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * maps+0x24:X}",8)

    encmapurl = f"../../resources/mmo_es.json"
    encmap = open(encmapurl)
    encmap = json.load(encmap)

    enc_pointer = f"{enc_pointer:X}"
    enc_pointer = enc_pointer.upper()
    enc_pointer = "0x"+enc_pointer

    if enc_pointer not in encmap.keys():
        print(f"Enc pointer not found in encmap")
        return encounters,encsum
    else:
        encounters = encmap[enc_pointer]

    #Get encounter table sum
    for species in encounters:
        encsum += species['slot']

    return encounters,encsum

def get_species(encounters,encounter_slot):
    alpha = False
    encsum = 0

    for species in encounters:
        encsum += species['slot']
        if encounter_slot < encsum:
            alpha = species['alpha']
            slot = species['name']
            if alpha:
                slot = "Alpha-"+slot
            return slot,alpha

    return "",False

def generate_mass_outbreak_aggressive_path_seed(group_seed,rolls,steps,uniques,storage,spawns,true_spawns,encounters,encsum,true_seed,isbonus=False,isalpha=False):
    """Generate all the pokemon of an outbreak based on a provided aggressive path"""
    # pylint: disable=too-many-locals, too-many-arguments
    # the generation is unique to each path, no use in splitting this function
    #group_seed = true_seed
    #print(f"True Seed: {group_seed:X}")
    main_rng = XOROSHIRO(group_seed)
    for init_spawn in range(4):
        generator_seed = main_rng.next()
        main_rng.next() # spawner 1's seed, unused
        fixed_rng = XOROSHIRO(generator_seed)
        encounter_slot = (fixed_rng.next() / (2**64)) * encsum
        species,alpha = get_species(encounters,encounter_slot)
        if isbonus and alpha:
            guaranteed_ivs = 4
        elif isbonus or alpha:
            guaranteed_ivs = 3
        else:
            guaranteed_ivs = 0
        fixed_seed = fixed_rng.next()
    group_seed = main_rng.next()
    respawn_rng = XOROSHIRO(group_seed)
    bonus_seed = respawn_rng
    for step_i,step in enumerate(steps):
       #print(f"Respawn {step_i}")
        for pokemon in range(1,step+1):
            #print(f"Pokemon {pokemon}")
            generator_seed = respawn_rng.next()
            seed = respawn_rng.next() # spawner 1's seed, unused
            fixed_rng = XOROSHIRO(generator_seed)
            #respawn_rng = XOROSHIRO(respawn_rng.next())
            encounter_slot = (fixed_rng.next() / (2**64)) * encsum
            species,alpha = get_species(encounters,encounter_slot)
            if isbonus and alpha:
                guaranteed_ivs = 4
            elif isbonus or alpha:
                guaranteed_ivs = 3
            else:
                guaranteed_ivs = 0
            fixed_seed = fixed_rng.next()
            level = fixed_rng.next()
        respawn_rng = XOROSHIRO(respawn_rng.next())

        #seed = (bonus_seed.next() - 0x82A2B175229D6A5B) & 0xFFFFFFFFFFFFFFFF
        seed = bonus_seed.next()
        if f"{seed:X}" == "F7E141984B77E9AD":
            print("Seed {seed:X} found! At {'|'.join(str(s) for s in steps[:step_i]+[pokemon])}, step_i = {step_i}")
            break
        if ((steps[:step_i] + [pokemon]) not in uniques) and (sum(steps[:step_i]) + pokemon + 4) == true_spawns:
            #print(f"Adding seed: {seed:X}")
            #uniques.append(seed)
            #print(f"Step:[step_i] = {steps}")
            #print(f"Step[:step_i] + [pokemon] = {steps + [pokemon]}")
            add1 = steps[:step_i]
            #print(f"add1: {add1}")
            addition = add1 + [pokemon]
            #print(f"Addition: {addition}")
            uniques.append(addition)
            #print(uniques)

        #seed = (fixed_seed - 0x82A2B175229D6A5B) & 0xFFFFFFFFFFFFFFFF
        #print(f"Seed: {seed:X}")
        
        

def get_final_seed(spawns):
    """Get the final path that will be generated to know when to stop aggressive recursion"""
    spawns -= 4
    path = [4] * (spawns // 4)
    if spawns % 4 != 0:
        path.append(spawns % 4)
    return path

def aggressive_outbreak_pathfind_seed(group_seed,
                                 rolls,
                                 spawns,
                                 true_spawns,
                                 encounters,
                                 encsum,
                                 true_seed,
                                 isbonus=False,
                                 isalpha=False,
                                 step=0,
                                 steps=None,
                                 uniques=None,
                                 storage=None):
    """Recursively pathfind to possible shinies for the current outbreak via multi battles"""
    # pylint: disable=too-many-arguments
    # can this algo be improved?
    if steps is None or uniques is None or storage is None:
        steps = []
        uniques = []
        storage = []
    _steps = steps.copy()
    if step != 0:
        _steps.append(step)
    if sum(_steps) + step < spawns - 4:
        for _step in range(1, min(5, (spawns - 4) - sum(_steps))):
            if aggressive_outbreak_pathfind_seed(group_seed,
                                            rolls,
                                            spawns,
                                            true_spawns,
                                            encounters,
                                            encsum,
                                            true_seed,
                                            isbonus,
                                            isalpha,
                                            _step,
                                            _steps,
                                            uniques,
                                            storage) is not None:
                return uniques
    else:
        _steps.append(spawns - sum(_steps) -4 )
        generate_mass_outbreak_aggressive_path_seed(group_seed,rolls,_steps,uniques,storage,spawns,true_spawns,encounters,encsum,true_seed,isbonus,isalpha)
        if _steps == get_final_seed(spawns):
            return uniques
    return None

def next_filtered_aggressive_outbreak_pathfind_seed(group_seed,rolls,spawns,true_spawns,group_id,isbonus,true_seed,isalpha=False):
    """Check the next outbreak advances until an aggressive path to a pokemon that
       passes poke_filter exists"""
    encounters,encsum = get_encounter_table(group_id,isbonus)
    main_rng = XOROSHIRO(group_seed)
    result = []
    advance = -1
    
    while len(result) == 0 and advance < 1:
        if advance != -1:
            for _ in range(4*2):
                main_rng.next()
            group_seed = main_rng.next()
            main_rng.reseed(group_seed)
        advance += 1
        result = aggressive_outbreak_pathfind_seed(group_seed, rolls, spawns,true_spawns,encounters,encsum,true_seed,isbonus,isalpha)
        if result is None:
            result = []
    if advance == 0:
        info = result
    else:
        info = '\n'
    if advance != 0:
        return ""
    else:
        return info

def get_group_seed(group_id,mapcount):
    group_seed = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+group_id*0x90 + 0xb80 * mapcount+0x44:X}",8)
    return group_seed
    
if __name__ == "__main__":
    rolls = int(input("Shiny Rolls For Species: "))
    #maps = int(input("Map Count: "))
    aggro = True if input("Aggressive Pathfind? Y/N ").lower() == 'y' else False
    #initial = False if input("Are you in the map? Y/N: ").lower() == 'n' else True
    display = []

    for maps in range(0,5):
        for i in range(0,15):
            print()
            print(f"Checking group {i}, Map {maps}: ")
            print()
            bonus_flag = True if reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+i*0x90 + 0xb80 * maps+0x18:X}",1) == 1 else False
            display = read_mass_outbreak_rng(i,rolls,maps,aggro,bonus_flag)
            if display is None:
                break
            else:
                if aggro:
                    for p in range(0,len(display)):
                        print(display[p])
                    #bonus_seed = get_bonus_seed(i,rolls,maps)
                    #if bonus_seed is None:
                       # break
                    if bonus_flag:
                        print(f"Bonus Flag: {bonus_flag}")
                        isbonus = True
                        #true_spawns = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+i*0x90 + 0xb80 * maps+0x60:X}",4)
                        true_spawns = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+i*0x90 + 0xb80 * maps+0x4c:X}",4)
                        max_spawns = true_spawns+3
                        group_seed = get_group_seed(i,maps)
                        
                        bonus_seed = next_filtered_aggressive_outbreak_pathfind_seed(group_seed,rolls,max_spawns,true_spawns,i,isbonus,group_seed,False)
                        true_spawns = reader.read_pointer_int(f"[[[[[[main+42BA6B0]+2B0]+58]+18]+{0x1d4+i*0x90 + 0xb80 * maps+0x60:X}",4)
                        max_spawns = 10
                        #print(paths)
                        #print(bonus_seed)
                        #print(len(paths))
                        #print(len(bonus_seed))
                        
                        for t,value in enumerate(bonus_seed):
                            #print(f"Seed: {value}")
                            #print(f"Path {value}:")
                            seed = get_bonus_seed(i,rolls,maps,value)
                            #print(f"Seed: {seed:X}")
                            nonalpha = [next_filtered_aggressive_outbreak_pathfind(seed,rolls,max_spawns,true_spawns,i,isbonus,False)]
                            #print(nonalpha[0])
                            if "Nothing found" not in nonalpha[0]:
                                for v in range(0,len(nonalpha)):
                                    print()
                                    print(f" First Round Path: {value} + [1 | 1 | 1 | 1]\n")
                                    print(nonalpha[v])
                        """
                        print(f"Bonus Round:")
                        for q in range(0,len(nonalpha)):
                            print(nonalpha[q])
                        """
