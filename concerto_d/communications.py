import zenoh

z = zenoh.open()


def push_events_to_peers(event):
    port_name, port_info, timestamp, exported_values = event
    z.put(f"{port_name}", f"{port_info},{timestamp},{exported_values}")


def pull_events_from_peers(state):
    events = []
    for response in z.get("*", zenoh.Queue()):
        response = response.ok
        port_info, timestamp, exported_values = response.payload.decode('utf-8').split(",")
        print([str(response.key_expr), port_info, timestamp, exported_values])
        events.append([str(response.key_expr), int(port_info), float(timestamp), exported_values])

    for port_name, port_info, timestamp, exported_values in events:
        dep = port_name.replace("provide_", "")
        if "provide" in port_name and port_info == 0 and port_name in state["provide_deps"]:
            state["provide_deps"].remove(dep)
        if "provide" in port_name and port_info == 1 and port_name not in state["provide_deps"]:
            state["provide_deps"].append(dep)
        # if "use" in port_name and port_info == "None" and  state["using_deps"][port_name.replace("use_", "")]:
    # TODO split concerns
