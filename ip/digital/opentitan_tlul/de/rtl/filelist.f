// OpenTitan TL-UL DE package manifest.
// Source files are copied into this native package; chip/top consumes ordered fragments through filelist.mk.

-f $SOC/ip/digital/opentitan_tlul/de/rtl/fragments/01_pkg.f
-f $SOC/ip/digital/opentitan_tlul/de/rtl/fragments/02_integrity.f
-f $SOC/ip/digital/opentitan_tlul/de/rtl/fragments/03_fifo_assert.f
-f $SOC/ip/digital/opentitan_tlul/de/rtl/fragments/04_adapters.f
-f $SOC/ip/digital/opentitan_tlul/de/rtl/fragments/05_racl.f
-f $SOC/ip/digital/opentitan_tlul/de/rtl/fragments/06_debug.f
-f $SOC/ip/digital/opentitan_tlul/de/rtl/fragments/07_optional_vh.f
