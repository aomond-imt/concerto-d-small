import asyncio
import concerto_d.comp_types
from concerto_d.commands import add_comp, push_b, load_state, mem_state
from concerto_d.comp_types import *


async def main():
    add_comp("server", server)
    add_comp("client", client)
    await asyncio.gather(
        # push_b(bhv_num=0, comp_name="server"),
        # push_b(bhv_num=0, comp_name="client"),
        push_b(bhv_num=1, comp_name="server"),
        push_b(bhv_num=1, comp_name="client")
    )


if __name__ == '__main__':
    name = "server_client"
    load_state(name)
    state = concerto_d.commands.state
    print("server", state["comps"]["server"][1] if len(state["comps"]) > 0 else [])
    print("client", state["comps"]["client"][1] if len(state["comps"]) > 0 else [])
    print("deps", state["deps"])
    concerto_d.comp_types.ti = time.time()
    asyncio.run(main())
    print("server", state["comps"]["server"][1])
    print("client", state["comps"]["client"][1])
    print("deps", state["deps"])
    mem_state(name)


# TODO Checkpoint system for rollback?
# TODO Token granularity
# TODO connect prevents any non-connected port to use/provide a service
# TODO prevent incorrect reconf (unreachability, cyclic)
# TODO do a dry run and see what can be achieved or not
