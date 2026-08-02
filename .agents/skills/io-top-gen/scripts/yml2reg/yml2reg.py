#!/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import re
from datetime import datetime
import getpass
import yaml

def main():
    try:
        para_list = sys.argv[1:]
    except Exception as e:
        print("Error parameters!!! unknown parameter")
        print(e)
        sys.exit(1)

    protocol = para_list[1]

    with open(para_list[0], 'r') as file:
        data = yaml.safe_load(file)

    yml2regfile(data, protocol)


def yml2regfile(data, protocol):
    fp = open(data["name"].upper()+"_"+protocol+"_regfile.v", "w")
    print_line = []

    add_header(print_line, data["name"].upper()+"_"+protocol+"_regfile.v")

    print_line.append("module "+data["name"].upper()+"_"+protocol+"_regfile(")
    if protocol == "apb":
        print_line.append('    input           apb_clk,')
        print_line.append('    input           apb_rst_n,')
        print_line.append('    input           apb_sel,')
        print_line.append('    input           apb_enable,')
        print_line.append('    input           apb_write,')
        print_line.append('    input   [31:0]  apb_addr, ')
        print_line.append('    input   [31:0]  apb_wdata,')
        print_line.append('    output          apb_ready,')
        print_line.append('    output          apb_slverr,')
        print_line.append('    output reg [31:0]  apb_rdata,')
    elif protocol == "dab":
        print_line.append('    input           dab_clk,')
        print_line.append('    input           dab_rst_n,')
        print_line.append('    input           dab_write,')
        print_line.append('    input           dab_read,')
        print_line.append('    input  [31:0]   dab_addr,')
        print_line.append('    input  [31:0]   dab_wdata,')
        print_line.append('    output reg [31:0]   dab_rdata,')
        print_line.append('    output          dab_ready,')
    elif protocol == "ahb":
        print_line.append("    input           ahb_clk,")
        print_line.append("    input           ahb_rst_n,")
        print_line.append("    input           ahb_readyin,")
        print_line.append("    input           ahb_sel,")
        print_line.append("    input  [1:0]    ahb_trans,")
        print_line.append("    input           ahb_write,")
        print_line.append("    input  [2:0]    ahb_burst,")
        print_line.append("    input  [2:0]    ahb_size,")
        print_line.append("    input  [31:0]   ahb_addr,")
        print_line.append("    input  [31:0]   ahb_wdata,")
        print_line.append("    output          ahb_readyout,")
        print_line.append("    output [1:0]    ahb_resp,")
        print_line.append("    output reg [31:0]   ahb_rdata,")

    for reg_info in data["registers"]:
        for fields_info in reg_info["fields"]:
            if fields_info["access"] in ("rw", "wo", "w1t", "wc"):
                if fields_info["bits"] == 1:
                    print_line.append("\toutput reg\t\t\t"+fields_info["name"]+",")
                else:
                    print_line.append("\toutput reg\t["+str(fields_info["bits"]-1)+":0]\t\t"+fields_info["name"]+",")
            elif fields_info["access"] == "ro":
                if fields_info["bits"] == 1:
                    print_line.append("\tinput \t\t\t\t"+fields_info["name"]+",")
                else:
                    print_line.append("\tinput \t["+str(fields_info["bits"]-1)+":0]\t\t"+fields_info["name"]+",")
    print_line[-1] = print_line[-1].strip(',')
    print_line.append(");")
    print_line.append("")

    if protocol == "apb":
        for reg_info in data["registers"]:
            for fields_info in reg_info["fields"]:
                if fields_info["access"] in ("rw", "wo", "w1t", "wc"):
                    print_line.append("wire\t"+fields_info["name"]+"_wr;")
            has_rd = any(f["access"] in ("rw", "ro") for f in reg_info["fields"])
            if has_rd:
                print_line.append("wire\t"+reg_info["name"]+"_rd;")
                print_line.append("wire\t[31:0]\t"+reg_info["name"]+"_rdata;")

        print_line.append("wire\twr_en;")
        print_line.append("wire\trd_en;")
        print_line.append("reg \t[31:0]\tapb_rdata_pre;")
        print_line.append("")
        print_line.append("assign\tapb_ready = 1'b1;")
        print_line.append("assign\tapb_slverr = 1'b0;")
        print_line.append("")
        print_line.append("assign\twr_en = apb_write & !apb_enable & apb_sel;")
        print_line.append("assign\trd_en = !apb_write & !apb_enable & apb_sel;")
        print_line.append("")

        for reg_info in data["registers"]:
            offset_hex = hex(reg_info["offset"]).replace("0x", "")
            for fields_info in reg_info["fields"]:
                if fields_info["access"] in ("rw", "wo", "w1t", "wc"):
                    print_line.append("assign\t"+fields_info["name"]+"_wr = (apb_addr[31:0] == 32'h"+offset_hex+") & wr_en;")
            has_rd = any(f["access"] in ("rw", "ro") for f in reg_info["fields"])
            if has_rd:
                print_line.append("assign\t"+reg_info["name"]+"_rd = (apb_addr[31:0] == 32'h"+offset_hex+") & rd_en;")
        print_line.append("")

        for reg_info in data["registers"]:
            for fields_info in reg_info["fields"]:
                if fields_info["access"] in ("rw", "wo", "w1t", "wc"):
                    print_line.append("always @(posedge apb_clk or negedge apb_rst_n)begin")
                    print_line.append("\tif(!apb_rst_n)")
                    print_line.append("\t\t"+fields_info["name"]+" <= "+str(fields_info["bits"])+"\'h"+str(fields_info["reset"])+";")
                    print_line.append("\telse if ("+fields_info["name"]+"_wr == 1'b1)")
                    print_line.append("\t\t"+fields_info["name"]+" <= apb_wdata["+str(fields_info["lsb"]+fields_info["bits"]-1)+":"+str(fields_info["lsb"])+"];")
                    if fields_info["access"] in ("w1t", "wc"):
                        print_line.append("\telse")
                        print_line.append("\t\t"+fields_info["name"]+" <= "+str(fields_info["bits"])+"\'h0;")
                    print_line.append("end")
                    print_line.append("")

        for reg_info in data["registers"]:
            has_rd = any(f["access"] in ("rw", "ro") for f in reg_info["fields"])
            if not has_rd:
                continue
            fields_bits_list = []
            for fields_info in reg_info["fields"]:
                fields_bits_list.append(str(fields_info["lsb"]+fields_info["bits"]-1)+":"+str(fields_info["lsb"]))
            parsed_ranges = parse_bit_ranges(fields_bits_list)
            full_range = generate_full_range(31)
            missing_bits = find_missing_bits(parsed_ranges, full_range)

            for fields_info in reg_info["fields"]:
                if fields_info["access"] in ("ro", "rw"):
                    print_line.append("assign\t"+reg_info["name"]+"_rdata["+str(fields_info["lsb"]+fields_info["bits"]-1)+":"+str(fields_info["lsb"])+"] = "+fields_info["name"]+";")
            for start, end in merge_consecutive_bits(missing_bits):
                if start == end:
                    print_line.append("assign\t"+reg_info["name"]+"_rdata["+str(start)+"] = 1'b0;")
                else:
                    print_line.append("assign\t"+reg_info["name"]+"_rdata["+str(end)+":"+str(start)+"] = "+str(end-start+1)+"'b0;")
        print_line.append("")

        print_line.append("assign apb_rdata_pre[31:0] = ")
        for reg_info in data["registers"]:
            has_rd = any(f["access"] in ("rw", "ro") for f in reg_info["fields"])
            if has_rd:
                print_line.append("\t"+reg_info["name"]+"_rd ? "+reg_info["name"]+"_rdata[31:0] :")
        print_line.append("\t32'hdeadbeef;")
        print_line.append("")

        print_line.append("always @(posedge apb_clk or negedge apb_rst_n)begin")
        print_line.append("\tif(!apb_rst_n)")
        print_line.append("\t\tapb_rdata[31:0] <= 32'h0;")
        print_line.append("\telse")
        print_line.append("\t\tapb_rdata[31:0] <= apb_rdata_pre[31:0];")
        print_line.append("end")

    elif protocol == "dab":
        print_line.append("// TODO: protocol logic not yet implemented")
        print_line.append("assign dab_rdata = 32'h0;")
        print_line.append("assign dab_ready = 1'b1;")
    elif protocol == "ahb":
        print_line.append("// TODO: AHB protocol logic not yet implemented")
        print_line.append("assign ahb_rdata = 32'h0;")
        print_line.append("assign ahb_readyout = 1'b1;")
        print_line.append("assign ahb_resp = 2'b00;")

    print_line.append("")
    print_line.append("endmodule")

    for line in print_line:
        fp.write(line)
        fp.write('\n')

    fp.close()


def parse_bit_ranges(ranges):
    parsed_ranges = set()
    for range_str in ranges:
        a, b = map(int, range_str.split(':'))
        parsed_ranges.update(range(min(a, b), max(a, b) + 1))
    return parsed_ranges

def generate_full_range(max_width):
    return set(range(max_width + 1))

def find_missing_bits(parsed_ranges, full_range):
    missing_bits = full_range - parsed_ranges
    return missing_bits

def merge_consecutive_bits(bits_set):
    if not bits_set:
        return []
    sorted_bits = sorted(bits_set)
    ranges = []
    start = sorted_bits[0]
    end = sorted_bits[0]
    for b in sorted_bits[1:]:
        if b == end + 1:
            end = b
        else:
            ranges.append((start, end))
            start = b
            end = b
    ranges.append((start, end))
    return ranges

def add_header(print_line, filename):
    today = datetime.today()
    now = datetime.now()
    user = getpass.getuser()

    date1 = today.strftime("%Y/%m/%d")
    year = today.strftime("%Y")
    time = now.strftime("%H:%M")

    print_line.append("// +FHDR----------------------------------------------------------------------------")
    print_line.append("// Copyright (c) "+year+" Silicon Peasant.")
    print_line.append("// ALL RIGHTS RESERVED Worldwide")
    print_line.append("//         ")
    print_line.append("// Author        : "+user)
    print_line.append("// Email         : "+user+"@foxmail.com")
    print_line.append("// Created On    : "+date1+" "+time)
    print_line.append("// Last Modified : "+date1+" "+time)
    print_line.append("// File Name     : "+filename)
    print_line.append("// Description   :")
    print_line.append("// ")
    print_line.append("// ---------------------------------------------------------------------------------")
    print_line.append("// Modification History:")
    print_line.append("// Date         By              Version                 Change Description")
    print_line.append("// ---------------------------------------------------------------------------------")
    print_line.append("// "+date1+"   "+user+"     1.0                     Original")
    print_line.append("// -FHDR----------------------------------------------------------------------------")

if __name__ == "__main__":
    main()
