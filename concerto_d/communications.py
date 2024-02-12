import zenoh

z = zenoh.open()


def push_events_to_peers(event):
    port_name, comp_name, port_info, timestamp, exported_values = event
    z.put(f"{port_name}", f"{comp_name},{port_info},{timestamp},{exported_values}")


def pull_events_from_peers(state, dependencies_to_wait):
    for response in z.get("*", zenoh.Queue()):
        response = response.ok
        comp_name, port_info, timestamp, exported_values = response.payload.decode('utf-8').split(",")
        print([str(response.key_expr), comp_name, port_info, timestamp, exported_values])
        treat_event([str(response.key_expr), comp_name, port_info, float(timestamp), exported_values], state, dependencies_to_wait)


def treat_event(event, state, dependencies_to_wait):
    port_name, comp_name, port_info, timestamp, exported_values = event
    dep = port_name.replace("provide_", "").replace("use_", "")
    if "provide" in port_name and port_info == "0" and port_name in state["deps"]:
        state["deps"].remove(dep)
    if "provide" in port_name and port_info == "1" and port_name not in state["deps"]:
        state["deps"][dep] = []
        if dep in dependencies_to_wait.keys():
            dependencies_to_wait[dep].set()
    if "use" in port_name and port_info == "None" and comp_name in state["deps"][dep]:
        state["deps"][dep].remove(comp_name)
        if (dep, comp_name) in dependencies_to_wait.keys():
            dependencies_to_wait[(dep, comp_name)].set()
    if "use" in port_name and port_info != "None" and comp_name not in state["deps"][dep]:
        state["deps"][dep].append(comp_name)
