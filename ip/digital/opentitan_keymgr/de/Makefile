# Wrapper Makefile: delegates to parent directory
.PHONY: all flist lint comp sim clean

all flist lint comp sim clean:
	@$(MAKE) -C .. SUBDIR=$(notdir $(CURDIR)) $@

%:
	@$(MAKE) -C .. SUBDIR=$(notdir $(CURDIR)) $@
