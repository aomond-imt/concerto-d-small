# Asyncio synchronizations
import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor

from concerto_d import comp_types, communications
from concerto_d.communications import push_events_to_peers


def mem_state(name):
    with open(f"/tmp/state_{name}", "w") as f:
        json.dump(state, f)


def load_state(name):
    global state
    try:
        with open(f"/tmp/state_{name}") as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {"comps": [], "provide_deps": [], "using_deps": {}, "events": []}


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


async def push_b(bhv_num, comp_num):
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
                push_events_to_peers([c_p, 0, time.time(), None])  # Deactive provide

        # Start transitions
        ths = []
        for t in trans_to_launch:
            ths.append((t, loop.run_in_executor(executor, getattr(comp_types, t))))

        # Withdraw usage
        for c_p in current_place[1]:
            dep = c_p.replace("provide_", "").replace("use_", "")
            if "use" in c_p and c_p not in target_place[1]:
                state["using_deps"][dep].remove(comp_num)
                if (dep, comp_num) in dependencies_to_wait.keys():
                    dependencies_to_wait[(dep, comp_num)].set()
                push_events_to_peers([c_p, None, time.time(), None])  # Deactivate use

        # Wait for required transitions (target place docks)
        for t_name, th in ths:
            if t_name in trans_to_wait:
                await th
        ports = target_place[1]

        for p in ports:
            dep = p.replace("provide_", "").replace("use_", "")

            # Provide port activation
            if "provide" in p:
                if dep not in state["provide_deps"]:
                    state["provide_deps"].append(dep)
                    if dep in dependencies_to_wait.keys():
                        dependencies_to_wait[dep].set()
                    push_events_to_peers([p, 1, time.time(), "dummy"])  # Activate provide
            else:
                # Wait for provide port activation
                if dep not in state["provide_deps"]:
                    await dependencies_to_wait.setdefault(dep, asyncio.Event()).wait()

                # Start using provide port
                if dep not in state["using_deps"].keys():
                    state["using_deps"][dep] = [comp_num]
                else:
                    if comp_num not in state["using_deps"][dep]:
                        state["using_deps"][dep].append(comp_num)
                push_events_to_peers([p, f"provide_{dep}", time.time(), None])  # Activate use
        state["comps"][comp_num][1] = target_place
    pushb_locks[comp_num].release()
