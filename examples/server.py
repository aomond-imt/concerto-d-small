import asyncio
import concerto_d.comp_types
from concerto_d.commands import add_comp, push_b, load_state, mem_state
from concerto_d.communications import pull_events_from_peers
from concerto_d.comp_types import *


async def main():
    add_comp("server", server)
    await asyncio.gather(
        push_b(bhv_num=0, comp_name="server"),
    )


if __name__ == '__main__':
    name = "server"
    load_state(name)
    state = concerto_d.commands.state
    dependencies_to_wait = concerto_d.commands.dependencies_to_wait
    events = pull_events_from_peers(state, dependencies_to_wait)
    print("server", state["comps"]["server"][1] if len(state["comps"]) > 0 else [])
    print("deps", state["deps"])
    print("events", state["events"])
    concerto_d.comp_types.ti = time.time()
    asyncio.run(main())
    print("server", state["comps"]["server"][1])
    print("deps", state["deps"])
    print("events", state["events"])
    mem_state(name)
