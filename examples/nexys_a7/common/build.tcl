#!/usr/bin/tclsh
# jay's build script
# pass -tclargs -d to generate diagnostics

# switches

set partNum xc7a100tcsg324-1
set outputDir output_files
set verbose 0

if { $argc > 0 } {
	if { $argc == 1 && [string compare [ lindex $argv 0 ] "-d"] == 0 } {
		set verbose 1
	} else {
		puts "usage: $argv0 \[-d\]"
		exit 1
	}
}

file mkdir $outputDir
set files [glob -nocomplain "$outputDir/*"]
if {[llength $files] != 0} {
    file delete -force {*}[glob -directory $outputDir *];
}

read_verilog -sv [ glob ./src/*.{sv,v,svh,vh} ]
read_xdc ./xdc/top_level.xdc

set_part $partNum

# synth
synth_design -top top_level -part $partNum -verbose
report_utilization -file $outputDir/post_synth_util.rpt
if { $verbose } {
	report_timing_summary -file $outputDir/post_synth_timing_summary.rpt
	report_timing -file $outputDir/post_synth_timing.rpt
}

# place
opt_design
place_design
phys_opt_design
report_utilization -file $outputDir/post_place_util.rpt

if { $verbose } {
	report_clock_utilization -file $outputDir/clock_util.rpt
	report_timing_summary -file $outputDir/post_place_timing_summary.rpt
	report_timing -file $outputDir/post_place_timing.rpt
}

# route design and generate bitstream

route_design -directive Explore
write_bitstream -force $outputDir/final.bit

if { $verbose } {
	report_route_status -file $outputDir/post_route_status.rpt
	report_timing_summary -file $outputDir/post_route_timing_summary.rpt
	report_timing -file $outputDir/post_route_timing.rpt
	report_power -file $outputDir/post_route_power.rpt
	report_drc -file $outputDir/post_imp_drc.rpt
	write_verilog -force $outputDir/cpu_impl_netlist.v -mode timesim -sdf_anno true
	# unfortunately, does nothing
	show_schematic [ get_cells ]
}

exec sh -c "rm -rf *.jou *.log"

