# Wrapper: delegates to parent Makefile
.PHONY: all flist lint comp sim run wave syn clean
all flist lint comp sim run wave syn clean:
	@$(MAKE) -C .. SUBDIR=$(notdir $(CURDIR)) $@
%:
	@$(MAKE) -C .. SUBDIR=$(notdir $(CURDIR)) $@
