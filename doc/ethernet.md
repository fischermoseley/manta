ok so the way the new packets work is:

- everything uses the same ethertype - that's configured once, in manta.yaml, and is set as a parameter in each of the rx and tx stacks

- we do [addr] [data] for incoming write messages, and [addr] for incoming read messages.
- we do [data] for outgoing read responses. this means that:
    - we need to detect packet length on mac_rx
    - packets coming out of the FPGA are fixed-width, mac_tx will always send out 2 bytes of data
    - packets going into the FPGA are guarunteed to be longer than packets coming out of the FPGA

- actually this doesn't make a lot of sense - we're going to be padding anyway, so this really just introduces extra complexity for us. let's just do
    something like [rw] [addr] [data]
    - since we know that we're _always_ going to get in at least 60 bytes of content and each message only contains like
    - we could say that in the future since we're using a fixed ethertype and can detect the paket length based on the crsdv line, we could concevably
        stack a bunch of [rw] [addr] [data] things together in the same packet - and creep right up to the ethernet MTU. but we'll file that along the 'other stuff'
        and go from there. for now let's just pull 1 + 2 + 2 = 5 bytes = 40 bits into aggregate and see what happens.

    - ok so then updated mac_rx is:
        - ether, with the reset removed from it
        - bitorder, with the reset removed from it
        - firewall, but checks the destination MAC of the packet in addition to the ethertype
        - transaction, which turns the packets coming in into rw/addr/data triplets. this is then outputted to the top level of mac_rx

    - and the updated mac_tx is:
        - just the same, except we just put the busficiation logic inside it. so then instead of having start we do the logic with rw_i and valid_i ourselves,
          and buffer thee data ourselves

    - so then we just have mac_tx and mac_rx in the manta core chain. which feels good.


previous ideas:
    - how to do variable length detection? right now our current stack is not well suited for that
        - keeping in line with the existing stack, we want to progressively take out chunks as time goes on.
        - i think we should modify firewall to check ethertype in addition to mac address also get rid of the reset while we're at it
            - because it's jaycode, probably going to be easier to rewrite from scratch to preserve style and sanity. i don't have anything to prove
            - we can use the 205 checkers for this, ironcially enough
        - i think we should modify aggregate to get both the payload and length. the payload is clocked in dibit-by-dibit, so we'll want to grab the