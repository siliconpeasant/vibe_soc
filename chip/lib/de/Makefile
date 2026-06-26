# Wrapper: delegates to parent Makefile
.PHONY: all flist lint comp sim run verdi syn clean
all flist lint comp sim run verdi syn clean:
	@$(MAKE) -C .. SUBDIR=$(notdir $(CURDIR)) $@
%:
	@$(MAKE) -C .. SUBDIR=$(notdir $(CURDIR)) $@
