# Wrapper Makefile: delegates to parent directory
.PHONY: all flist lint comp sim wave clean

all flist lint comp sim wave clean:
	@$(MAKE) -C .. SUBDIR=$(notdir $(CURDIR)) $@

%:
	@$(MAKE) -C .. SUBDIR=$(notdir $(CURDIR)) $@
