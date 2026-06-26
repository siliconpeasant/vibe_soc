all: lowrisc_dv_top_earlgrey_chip_sim_0.1

lowrisc_dv_top_earlgrey_chip_sim_0.1: lowrisc_dv_top_earlgrey_chip_sim_0.1.scr
	$(EDALIZE_LAUNCHER) vcs -full64 -top tb -f lowrisc_dv_top_earlgrey_chip_sim_0.1.scr -o $@  -CFLAGS -I../../src/lowrisc_dv_crypto_prince_ref_0.1 -sverilog
run: lowrisc_dv_top_earlgrey_chip_sim_0.1
	./lowrisc_dv_top_earlgrey_chip_sim_0.1 -l vcs.log 
clean:
	$(RM) lowrisc_dv_top_earlgrey_chip_sim_0.1
