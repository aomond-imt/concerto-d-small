import asyncio
import concerto_d.comp_types
from concerto_d.commands import add_comp, push_b, load_state, mem_state
from concerto_d.comp_types import *


async def main():
    add_comp(server)
    add_comp(client)
    await asyncio.gather(
        push_b(bhv_num=0, comp_num=0),
        push_b(bhv_num=0, comp_num=1),
        # push_b(bhv_num=1, comp_num=0),
        # push_b(bhv_num=1, comp_num=1)
    )


if __name__ == '__main__':
    load_state()
    state = concerto_d.commands.state
    print("server", state["comps"][0][1] if len(state["comps"]) > 0 else [])
    print("client", state["comps"][1][1] if len(state["comps"]) > 0 else [])
    print("using_deps", state["using_deps"])
    concerto_d.comp_types.ti = time.time()
    asyncio.run(main())
    print("server", state["comps"][0][1])
    print("client", state["comps"][1][1])
    print("using_deps", state["using_deps"])
    mem_state()


# TODO Checkpoint system for rollback?
# TODO Token granularity
# TODO connect prevents any non-connected port to use/provide a service
# TODO prevent incorrect reconf (unreachability, cyclic)
