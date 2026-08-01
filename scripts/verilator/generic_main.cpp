#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>

#include "verilated.h"

#if VM_TRACE
#include "verilated_vcd_c.h"
#endif

#define STR_HELPER(x) #x
#define STR(x) STR_HELPER(x)

#ifndef TOPLEVEL_HEADER
#error "TOPLEVEL_HEADER must be defined, for example -DTOPLEVEL_HEADER=Vtop.h"
#endif
#ifndef TOPLEVEL_NAME
#error "TOPLEVEL_NAME must be defined, for example -DTOPLEVEL_NAME=Vtop"
#endif

#include STR(TOPLEVEL_HEADER)

static vluint64_t main_time = 0;
double sc_time_stamp() { return static_cast<double>(main_time); }

static const char *plusarg_value(int argc, char **argv, const char *prefix) {
    const size_t n = std::strlen(prefix);
    for (int i = 1; i < argc; ++i) {
        if (std::strncmp(argv[i], prefix, n) == 0) {
            return argv[i] + n;
        }
    }
    return NULL;
}

static bool has_plusarg(int argc, char **argv, const char *arg) {
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], arg) == 0) {
            return true;
        }
    }
    return false;
}

int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);

    const char *max_cycles_arg = plusarg_value(argc, argv, "+max_cycles=");
    const vluint64_t max_cycles =
        max_cycles_arg ? std::strtoull(max_cycles_arg, NULL, 0) : 100000;
    if (max_cycles == 0) {
        std::cerr << "VERILATOR_FATAL: +max_cycles must be greater than zero\n";
        return 2;
    }

    TOPLEVEL_NAME *top = new TOPLEVEL_NAME;

#if VM_TRACE
    VerilatedVcdC *tfp = NULL;
    if (has_plusarg(argc, argv, "+trace")) {
        const char *wavefile = plusarg_value(argc, argv, "+wavefile=");
        if (wavefile == NULL || wavefile[0] == '\0') {
            wavefile = "wave.vcd";
        }
        Verilated::traceEverOn(true);
        tfp = new VerilatedVcdC;
        top->trace(tfp, 99);
        tfp->open(wavefile);
    }
#endif

    while (!Verilated::gotFinish() && main_time < max_cycles) {
        top->eval();
#if VM_TRACE
        if (tfp != NULL) {
            tfp->dump(main_time);
        }
#endif
        ++main_time;
    }

    top->final();
#if VM_TRACE
    if (tfp != NULL) {
        tfp->close();
        delete tfp;
    }
#endif
    delete top;
    if (!Verilated::gotFinish()) {
        std::cerr << "VERILATOR_TIMEOUT: design did not call $finish within "
                  << max_cycles << " timesteps\n";
        return 2;
    }
    return 0;
}
