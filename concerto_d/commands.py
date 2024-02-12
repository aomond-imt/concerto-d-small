# Asyncio synchronizations
import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor

from concerto_d import comp_types
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
        state = {"comps": {}, "deps": {}, "events": []}


state = {}
dependencies_to_wait = {}
pushb_locks = {}


def add_comp(comp_name, comp_type):
    state["comps"][comp_name] = [comp_type, (0, [])]
    pushb_locks[comp_name] = asyncio.Lock()


def del_comp(comp_name):
    del state["comps"][comp_name]


async def push_b(bhv_num, comp_name):
    await pushb_locks[comp_name].acquire()
    loop = asyncio.get_running_loop()
    current_place = state["comps"][comp_name][1]
    start_p, steps = state["comps"][comp_name][0][bhv_num]
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
        current_place = state["comps"][comp_name][1]
        trans_to_launch, target_place, trans_to_wait = steps[i]

        # Wait for using deps withdrawal
        for c_p in current_place[1]:
            if "provide" in c_p and c_p not in target_place[1]:
                dep = c_p.replace("provide_", "")
                while len(state["deps"][dep]) > 0:
                    await dependencies_to_wait.setdefault((dep, state["deps"][dep][0]), asyncio.Event()).wait()
                push_events_to_peers([c_p, comp_name, 0, time.time(), None])  # Deactive provide

        # Start transitions
        ths = []
        for t in trans_to_launch:
            ths.append((t, loop.run_in_executor(executor, getattr(comp_types, t))))

        # Withdraw usage
        for c_p in current_place[1]:
            dep = c_p.replace("provide_", "").replace("use_", "")
            if "use" in c_p and c_p not in target_place[1]:
                state["deps"][dep].remove(comp_name)
                if (dep, comp_name) in dependencies_to_wait.keys():
                    dependencies_to_wait[(dep, comp_name)].set()
                push_events_to_peers([c_p, comp_name, None, time.time(), None])  # Deactivate use

        # Wait for required transitions (target place docks)
        for t_name, th in ths:
            if t_name in trans_to_wait:
                await th
        ports = target_place[1]

        for p in ports:
            dep = p.replace("provide_", "").replace("use_", "")

            # Provide port activation
            if "provide" in p:
                if dep not in state["deps"].keys():
                    state["deps"][dep] = []
                    if dep in dependencies_to_wait.keys():
                        dependencies_to_wait[dep].set()
                    push_events_to_peers([p, comp_name, 1, time.time(), "dummy"])  # Activate provide
            else:
                # Wait for provide port activation
                if dep not in state["deps"].keys():
                    await dependencies_to_wait.setdefault(dep, asyncio.Event()).wait()

                # Start using provide port
                if comp_name not in state["deps"][dep]:
                    state["deps"][dep].append(comp_name)
                push_events_to_peers([p, comp_name, f"provide_{dep}", time.time(), None])  # Activate use
        state["comps"][comp_name][1] = target_place
    pushb_locks[comp_name].release()
