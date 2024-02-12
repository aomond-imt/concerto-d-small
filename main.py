import asyncio
import json
import threading
from concurrent.futures import ThreadPoolExecutor

import comp_types
from comp_types import *


def mem_state():
    with open("/tmp/state_cdpico", "w") as f:
        json.dump(state, f)


def load_state():
    global state
    try:
        with open("/tmp/state_cdpico") as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {"comps": [], "deps": [], "using_deps": {}}


# Asyncio synchronizations
state = {}
dependencies_to_wait = {}
pushb_locks = []


def add_comp(comp):
    state["comps"].append([comp, (0, [])])
    pushb_locks.append(asyncio.Lock())


def del_comp(comp):
    for c in state["comps"]:
        if c[1] == comp[1]:
            state["comps"].remove(c)
            break


async def push_b(dependencies_to_wait, bhv_num, comp_num):
    await pushb_locks[comp_num].acquire()
    loop = asyncio.get_running_loop()
    current_place = state["comps"][comp_num][1]
    start_p, steps = state["comps"][comp_num][0][bhv_num]
    current_step_i = 0
    if current_place != start_p:
        for i in range(len(steps)):
            if steps[i][1] == current_place:
                if i + 1 < len(steps):
                    current_step_i = i + 1
                else:
                    return

    executor = ThreadPoolExecutor(max_workers=10)
    for i in range(current_step_i, len(steps)):
        current_place = state["comps"][comp_num][1]
        trans_to_launch, target_place, trans_to_wait = steps[i]

        # Wait for using deps withdrawal
        for c_p in current_place[1]:
            if "provide" in c_p and c_p not in target_place[1]:
                dep = c_p.replace("provide_", "").replace("use_", "")
                while len(state["using_deps"][dep]) > 0:
                    await dependencies_to_wait.setdefault((dep, state["using_deps"][dep][0]), asyncio.Event()).wait()

        # Start transitions
        ths = []
        for t in trans_to_launch:
            ths.append((t, loop.run_in_executor(executor, globals()[t])))

        # Withdraw usage
        for c_p in current_place[1]:
            dep = c_p.replace("provide_", "").replace("use_", "")
            if "use" in c_p and c_p not in target_place[1]:
                state["using_deps"][dep].remove(comp_num)
                if (dep, comp_num) in dependencies_to_wait.keys():
                    dependencies_to_wait[(dep, comp_num)].set()

        # Wait for required transitions (target place docks)
        for t_name, th in ths:
            if t_name in trans_to_wait:
                await th
        ports = target_place[1]

        for p in ports:
            dep = p.replace("provide_", "").replace("use_", "")

            # Provide port activation
            if "provide" in p:
                if dep not in state["deps"]:
                    state["deps"].append(dep)
                    if dep in dependencies_to_wait.keys():
                        dependencies_to_wait[dep].set()
            else:
                # Wait for provide port activation
                if dep not in state["deps"]:
                    await dependencies_to_wait.setdefault(dep, asyncio.Event()).wait()

                # Start using provide port
                if dep not in state["using_deps"].keys():
                    state["using_deps"][dep] = [comp_num]
                else:
                    if comp_num not in state["using_deps"][dep]:
                        state["using_deps"][dep].append(comp_num)
        state["comps"][comp_num][1] = target_place
    pushb_locks[comp_num].release()


async def main():
    add_comp(server)
    add_comp(client)
    await asyncio.gather(
        # push_b(dependencies_to_wait, bhv_num=0, comp_num=0),
        # push_b(dependencies_to_wait, bhv_num=0, comp_num=1),
        push_b(dependencies_to_wait, bhv_num=1, comp_num=0),
        push_b(dependencies_to_wait, bhv_num=1, comp_num=1)
    )


if __name__ == '__main__':
    load_state()
    print("server", state["comps"][0][1] if len(state["comps"]) > 0 else [])
    print("client", state["comps"][1][1] if len(state["comps"]) > 0 else [])
    print("using_deps", state["using_deps"])
    comp_types.ti = time.time()
    asyncio.run(main())
    print("server", state["comps"][0][1])
    print("client", state["comps"][1][1])
    print("using_deps", state["using_deps"])
    mem_state()


# TODO Checkpoint system for rollback?
# TODO Token granularity
