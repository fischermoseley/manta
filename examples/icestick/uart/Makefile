SYN = yosys
PNR = nextpnr-ice40
GEN = icepack
PROG = iceprog

TOP = uart_demo.v
PCF = icestick.pcf
PNR_FLAGS = --hx1k

OUTPUT = $(patsubst %.v,%.bin,$(TOP))

all: $(OUTPUT)

%.bin: %.asc
	$(GEN) $< $@

%.asc: %.json
	$(PNR) $(PNR_FLAGS) --pcf $(PCF) --json $< --asc $@

%.json: %.v
	$(SYN) -p "read_verilog $<; synth_ice40 -flatten -json $@"

clean:
	rm -f *.asc *.bin *.json

flash: $(OUTPUT)
	$(PROG) $<

.PHONY: all clean flash
