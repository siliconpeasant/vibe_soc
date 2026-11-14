# IP-XACT component example

From the skill directory:

```bash
python3 scripts/soc_integrate.py ipxact-import examples/ipxact/gpio.xml
python3 scripts/soc_integrate.py integrate examples/ipxact/gpio.xml -o /tmp/gpio_top.sv
python3 scripts/soc_integrate.py ipxact-export examples/ipxact/gpio.xml \
  --ipxact-version 2022 -o /tmp/gpio_2022.xml
python3 scripts/soc_integrate.py flist /tmp/gpio_top.sv \
  --files examples/ipxact/gpio.sv -o /tmp/gpio_top.f
```

XML describes the module interface; `gpio.sv` supplies its implementation for
lint/simulation. `control` illustrates a slave interface, VLNV bus/abstraction
references and a logical DATA → physical data_i port map. Export retains those
bus groups. Import accepts both standard namespace years and all four mode names.
