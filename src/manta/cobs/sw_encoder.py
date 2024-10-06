
def cobs_encode(data):
    final_zero = True
    out = []
    idx = 0
    search_start_idx = 0
    for d in data:
        if d == 0:
            final_zero = True
            out += [idx - search_start_idx + 1]
            out += data[search_start_idx:idx]
            search_start_idx = idx + 1

        else:
            if idx - search_start_idx == 0xFD:
                final_zero = False
                out += [0xFF]
                out += data[search_start_idx:idx+1]
                search_start_idx = idx + 1

        idx += 1

    if idx != search_start_idx or final_zero:
        out += [idx - search_start_idx + 1]
        out += data[search_start_idx:idx]

    return out + [0]

