# Comp type
import time

ti = 0


def print_t(msg):
    print(f"{msg}: {time.time() - ti:.2f}")


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
def install(): time.sleep(5); print_t("install")
def execute(): time.sleep(2); print_t("execute")
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
def runc(): time.sleep(2); print_t("runc")
def upd1c(): time.sleep(3); print_t("upd1c")
def upd2c(): time.sleep(3); print_t("upd2c")
pc1 = (1, ["use_ip"])
pc2 = (2, ["use_ip"])
pc3 = (3, ["use_ip", "use_srv"])
pc4 = (4, ["use_ip", "use_srv"])
client = [
    (p0, [(["installc", "biginstallc"], pc1, ["installc"]), (["configc"], pc2, ["configc", "biginstallc"]), (["runc"], pc3, ["runc"])]),
    (pc3, [(["upd1c"], pc4, ["upd1c"]), (["upd2c"], pc2, ["upd2c"])])
]
