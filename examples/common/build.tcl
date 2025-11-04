#!/usr/bin/tclsh

set partNum xc7a100tcsg324-1

read_verilog -sv [ glob ../*.{sv,v,svh,vh} ]
read_xdc ../top_level.xdc

set_part $partNum

# synth
synth_design -top top_level -part $partNum -verbose
report_utilization -file post_synth_util.rpt
report_timing_summary -file post_synth_timing_summary.rpt
report_timing -file post_synth_timing.rpt

# place
opt_design
place_design
phys_opt_design
report_utilization -file post_place_util.rpt

report_clock_utilization -file clock_util.rpt
report_timing_summary -file post_place_timing_summary.rpt
report_timing -file post_place_timing.rpt

# route design and generate bitstream
route_design -directive Explore
write_bitstream -force out.bit

report_route_status -file post_route_status.rpt
report_timing_summary -file post_route_timing_summary.rpt
report_timing -file post_route_timing.rpt
report_power -file post_route_power.rpt
report_drc -file post_imp_drc.rpt
write_verilog -force cpu_impl_netlist.v -mode timesim -sdf_anno true
