from js import workerReadSerial, workerWriteSerial

def capture(foo):
    print(f"(Python): capture() has been called with args: {foo}")
    workerWriteSerial("W00000001\r\n")
    workerWriteSerial("W00010001\r\n")
    workerWriteSerial("R0000\r\n")
    foo = workerReadSerial()
    print(f"(Python): capture() has completed and returned value: ", {foo})
    return foo

print("(Python) Load Complete!")