// OpenTitan TL-UL DE package manifest.
// TL-UL is order-sensitive in the full Earlgrey top build, so chip/top includes
// the fragment filelists under de/rtl/fragments/ at the original dependency points.
// Do not include this manifest directly for chip/top compile.

-f $SOC/ip/digital/opentitan_tlul/de/rtl/fragments/01_pkg.f
-f $SOC/ip/digital/opentitan_tlul/de/rtl/fragments/02_integrity.f
-f $SOC/ip/digital/opentitan_tlul/de/rtl/fragments/03_fifo_assert.f
-f $SOC/ip/digital/opentitan_tlul/de/rtl/fragments/04_adapters.f
-f $SOC/ip/digital/opentitan_tlul/de/rtl/fragments/05_racl.f
-f $SOC/ip/digital/opentitan_tlul/de/rtl/fragments/06_debug.f
