import json
import threading
import time
from threading import Thread


def print_t(msg):
    print(f"{msg}: {time.time() - ti:.2f}")


# Comp type
def install1(): time.sleep(1); print(f"install1: {time.time() - ti:.2f}")
def install2(): time.sleep(2); print(f"install2: {time.time() - ti:.2f}")
def config(): time.sleep(1); print(f"config: {time.time() - ti:.2f}")
def other_config(): time.sleep(1); print(f"other_config: {time.time() - ti:.2f}")
def run(): time.sleep(1); print(f"run: {time.time() - ti:.2f}")
def update(): time.sleep(1); print(f"update: {time.time() - ti:.2f}")
def reconfigure(): time.sleep(1); print(f"reconfigure: {time.time() - ti:.2f}")
p0 = (0, [])
p1 = (1, [])
p2 = (2, ["use_r"])
p3 = (3, ["use_r"])
p4 = (4, ["provide_r", "use_r"])
comp_type_0 = [
    (p0, [([install1, install2], p1, ["install1", "install2"]), ([config], p2, ["config"]), ([other_config], p3, ["other_config"]), ([run], p4, ["run"])]),
    (p4, [([update], p2, ["update"])]),
    (p4, [([reconfigure], p1, ["reconfigure"])]),
]

# Server
def install(): time.sleep(1); print_t("install")
def execute(): time.sleep(1); print_t("execute")
def upd1(): time.sleep(1); print_t("upd1")
def upd2(): time.sleep(1); print_t("upd2")
ps1 = (1, ["provide_ip"])
ps2 = (2, ["provide_ip", "provide_srv"])
server = [
    (p0, [(["install"], ps1, ["install"]), (["execute"], ps2, ["execute"])]),
    (ps2, [(["upd1", "upd2"], ps1, ["upd1", "upd2"])]),
]

# Client
def installc(): time.sleep(1); print_t("installc")
def biginstallc(): time.sleep(3); print_t("biginstallc")
def configc(): time.sleep(1); print_t("configc")
def runc(): time.sleep(1); print_t("runc")
def upd1c(): time.sleep(3); print_t("upd1c")
def upd2c(): time.sleep(3); print_t("upd2c")
pc1 = (1, ["use_ip"])
pc2 = (2, ["use_ip"])
pc3 = (3, ["use_ip", "use_service"])
pc4 = (4, ["use_ip", "use_service"])
client = [
    (p0, [(["installc", "biginstallc"], pc1, ["installc"]), (["configc"], pc2, ["configc", "biginstallc"]), (["runc"], pc3, ["runc"])]),
    (pc3, [(["upd1c"], pc4, ["upd1c"]), (["upd2c"], pc2, ["upd2c"])])
]


# State
comps_instances = []
state = []
push_b_threads = []


def add_comp(comp):
    state.append([comp, (0, [])])


def del_comp(comp):
    for c in state:
        if c[1] == comp[1]:
            state.remove(c)
            break


locks = [threading.Lock(), threading.Lock()]
def execute_push_b(bhv_num, comp_num):
    locks[comp_num].acquire()
    current_p = state[comp_num][1]
    start_p, steps = state[comp_num][0][bhv_num]
    threads = []
    current_step_i = 0
    if current_p != start_p:
        for i in range(len(steps)):
            if steps[i][1] == current_p:
                if i+1 < len(steps):
                    current_step_i = i+1
                else:
                    return

    for i in range(current_step_i, len(steps)):
        for t in steps[i][0]:
            th = Thread(target=globals()[t])
            th.start()
            threads.append((t, th))

        for t_name, th in threads:
            if t_name in steps[i][2]:
                th.join()
        state[comp_num][1] = steps[i][1]
    locks[comp_num].release()


def push_b(bhv_num, comp_num):
    t = Thread(target=execute_push_b, args=(bhv_num, comp_num))
    t.start()
    push_b_threads.append((comp_num, t))


def main1():
    add_comp(comp_type_0)
    push_b(0, 0)
    for _, t in push_b_threads:
        t.join()


def main2():
    add_comp(server)
    add_comp(client)
    push_b(bhv_num=0, comp_num=0)
    push_b(bhv_num=1, comp_num=0)
    push_b(bhv_num=0, comp_num=1)
    push_b(bhv_num=1, comp_num=1)
    for _, t in push_b_threads:
        t.join()


def mem_state():
    with open("/tmp/state_cdpico", "w") as f:
        json.dump(state, f)


def load_state():
    global state
    try:
        with open("/tmp/state_cdpico") as f:
            state = json.load(f)
    except FileNotFoundError:
        state = []


if __name__ == '__main__':
    load_state()
    print("server", state[0][1] if len(state) > 0 else [])
    print("client", state[1][1] if len(state) > 0 else [])
    global ti
    ti = time.time()
    main2()
    print("server", state[0][1])
    print("client", state[1][1])
    mem_state()



# Checkpoint system for rollback?
