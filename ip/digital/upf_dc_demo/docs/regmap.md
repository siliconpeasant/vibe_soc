# UPF/DC demo register map

## Not applicable

`upf_dc_demo` has no bus slave, address decoder, software-visible control/status register, interrupt register, or memory-mapped address space. No YAML/Excel register source and no generated register RTL are required.

The 16 x 8 teaching SRAM is accessed only through direct ports `mem_cs_i`, `mem_we_i`, `mem_addr_i[3:0]`, `mem_wdata_i[7:0]`, `mem_rdata_o[7:0]`, and `mem_rvalid_o`; it has no system address range.

The four `*_power_req_i` channels, their request/response ports, PLL control/status, and pad signals are direct hardware pins. The nine-state PST, five UPF domains, supply sets, PG bindings, isolation, and level-shifter strategies are metadata and are not software-addressable.
