interface bus_if;
    logic [7:0] data;
    modport master(output data);
    modport slave(input data);
endinterface
