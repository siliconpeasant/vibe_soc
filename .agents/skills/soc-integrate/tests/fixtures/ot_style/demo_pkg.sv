// Original minimal package exercising OpenTitan-style public headers.
package demo_pkg;
  parameter int NumRegs = 2;
  typedef logic [1:0] policy_t;
  typedef logic [NumRegs*2-1:0] enable_t;
  typedef struct packed {
    logic [6:0] address;
    logic valid;
  } h2d_t;
endpackage
