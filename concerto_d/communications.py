import zenoh

z = zenoh.open()


def push_events_to_peers(state):
    for port_name, port_info, timestamp, exported_values in state["events"]:
        z.put(f"/{port_name}", f"{port_info},{timestamp},{exported_values}")


def pull_events_from_peers(state):
    for response in z.get("/*", zenoh.Queue()):
        response = response.ok
        port_info, timestamp, exported_values = response.payload.decode('utf-8').split()
