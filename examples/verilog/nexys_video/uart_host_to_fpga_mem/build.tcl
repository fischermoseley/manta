#!/usr/bin/tclsh

set partNum xc7a200tsbg484-1
set outputDir build

read_verilog -sv [ glob *.{sv,v,svh,vh} ]
read_xdc top_level.xdc

set_part $partNum

# synth
synth_design -top top_level -part $partNum -verbose
report_utilization -file $outputDir/post_synth_util.rpt
report_timing_summary -file $outputDir/post_synth_timing_summary.rpt
report_timing -file $outputDir/post_synth_timing.rpt

# place
opt_design
place_design
phys_opt_design
report_utilization -file $outputDir/post_place_util.rpt

report_clock_utilization -file $outputDir/clock_util.rpt
report_timing_summary -file $outputDir/post_place_timing_summary.rpt
report_timing -file $outputDir/post_place_timing.rpt

# route design and generate bitstream
route_design -directive Explore
write_bitstream -force $outputDir/out.bit

report_route_status -file $outputDir/post_route_status.rpt
report_timing_summary -file $outputDir/post_route_timing_summary.rpt
report_timing -file $outputDir/post_route_timing.rpt
report_power -file $outputDir/post_route_power.rpt
report_drc -file $outputDir/post_imp_drc.rpt
write_verilog -force $outputDir/cpu_impl_netlist.v -mode timesim -sdf_anno true
