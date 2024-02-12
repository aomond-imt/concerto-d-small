import asyncio
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import comp_types
from comp_types import *

# State
comps_instances = []
state = {"comps": [], "deps": []}
push_b_threads = []
dependencies_to_wait = {
    "provide_ip": asyncio.Event(),
    "provide_srv": asyncio.Event(),
}


def add_comp(comp):
    state["comps"].append([comp, (0, [])])


def del_comp(comp):
    for c in state["comps"]:
        if c[1] == comp[1]:
            state["comps"].remove(c)
            break


async def wait_dep(dependencies_to_wait, d):
    await dependencies_to_wait[d.replace("use", "provide")].wait()


locks = [threading.Lock(), threading.Lock()]
async def push_b(dependencies_to_wait, bhv_num, comp_num):
    locks[comp_num].acquire()
    loop = asyncio.get_running_loop()
    current_p = state["comps"][comp_num][1]
    start_p, steps = state["comps"][comp_num][0][bhv_num]
    current_step_i = 0
    if current_p != start_p:
        for i in range(len(steps)):
            if steps[i][1] == current_p:
                if i + 1 < len(steps):
                    current_step_i = i + 1
                else:
                    return
    executor = ThreadPoolExecutor(max_workers=10)
    for i in range(current_step_i, len(steps)):
        ths = []
        for t in steps[i][0]:
            ths.append((t, loop.run_in_executor(executor, globals()[t])))

        for t_name, th in ths:
            if t_name in steps[i][2]:
                print(f"awaiting {t_name}")
                await th
        ports = steps[i][1][1]
        for p in ports:
            if "provide" in p:
                print(f"print set {p}")
                dependencies_to_wait[p].set()
            else:
                await wait_dep(dependencies_to_wait, p)
        state["comps"][comp_num][1] = steps[i][1]
    locks[comp_num].release()


async def main():
    add_comp(server)
    add_comp(client)
    await asyncio.gather(
        push_b(dependencies_to_wait, bhv_num=0, comp_num=0),
        push_b(dependencies_to_wait, bhv_num=0, comp_num=1)
    )


def mem_state():
    with open("/tmp/state_cdpico", "w") as f:
        json.dump(state, f)


def load_state():
    global state
    try:
        with open("/tmp/state_cdpico") as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {"comps": [], "deps": []}


if __name__ == '__main__':
    load_state()
    print("server", state["comps"][0][1] if len(state["comps"]) > 0 else [])
    print("client", state["comps"][1][1] if len(state["comps"]) > 0 else [])
    comp_types.ti = time.time()
    asyncio.run(main())
    print("server", state["comps"][0][1])
    print("client", state["comps"][1][1])
    mem_state()



# Checkpoint system for rollback?
