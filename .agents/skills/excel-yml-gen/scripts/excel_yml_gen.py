#!/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import re
import subprocess
import pandas as pd
from datetime import datetime
import getpass
def main():
    try:
        #print(sys.argv)
        #print(len(sys.argv))

        para_list = sys.argv[1:]
        #print(para_list[0])
        #print(para_list[1])

    except Exception as e:
        print("Error parameters!!! unknown parameter")
        print(e)
        sys.exit(1)

    if(len(para_list) == 0) or para_list[0] == "-h":
        help()
        sys.exit(1)

    if len(para_list) >= 3:
        out_dir = para_list[2]
        if not out_dir.endswith("/"):
            out_dir += "/"
        os.makedirs(out_dir, exist_ok=True)
    else:
        out_dir = "./"

    sheet_base = para_list[1]
    if sheet_base.endswith('_reg'):
        sheet_base = sheet_base[:-4]
    elif sheet_base.endswith('_intp'):
        sheet_base = sheet_base[:-5]

    df = pd.read_excel(para_list[0], sheet_name = sheet_base)
    xml_corpus = df.values.tolist()

    print("\nall data:")
    print (df)
    
    df = pd.read_excel(para_list[0], sheet_name = sheet_base+'_reg')
    reg_corpus = df.values.tolist()

    print("\nall data:")
    print (df)
    reg_ser = pd.Series(reg_corpus)
    reg_empty = df.empty

    df = pd.read_excel(para_list[0], sheet_name = sheet_base+'_intp')
    intp_corpus = df.values.tolist()
    intp_ser = pd.Series(intp_corpus)
    intp_empty = df.empty

    print("\nall data:")
    print (df)
 
    gen_file_name = sheet_base

    #fp = open(gen_file_name.upper()+".xml", "w") 
    #
    #print_line = []   
    #excel_gen_xml(para_list, xml_corpus, print_line)
    #rtl_gen(para_list, xml_corpus, print_line, reg_corpus, reg_ser, reg_empty, gen_file_name)

    #if reg_empty == False:
    #    reg_xml_gen(print_line, reg_corpus, reg_ser)

    #if intp_empty == False:
    #    intp_xml_gen(print_line, intp_corpus, intp_ser)
    #
    #print_line.append("  </spirit:addressBlock>")
    #print_line.append("</spirit:component>")

    #for line in print_line:
    #    #print(line)
    #    fp.write(line)
    #    fp.write('\n')
    #
    #fp.write('\n')

    #fp.close()

    fp = open(out_dir+gen_file_name.upper()+".yml", "w") 
    
    print_line = []   

    addrblock_yml_gen(para_list, xml_corpus, print_line, out_dir)
    rtl_gen(para_list, xml_corpus, print_line, reg_corpus, reg_ser, reg_empty, gen_file_name, intp_corpus, intp_ser, intp_empty, out_dir)

    if reg_empty == False:
        excel_gen_yml(para_list, xml_corpus, print_line)
        reg_yml_gen(print_line, reg_corpus, reg_ser)

    if intp_empty == False:
        print_line.append("interrupts:")
        intp_yml_gen(print_line, intp_corpus, intp_ser)
    
    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')

    fp.close()

    plugin_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    yml2reg_py = os.path.join(plugin_root, "skills", "yml2reg", "scripts", "yml2reg.py")
    yml_file = os.path.abspath(out_dir+gen_file_name.upper()+".yml")
    protocol = xml_corpus[0][5]
    command = [sys.executable, yml2reg_py, yml_file, protocol]
    print(" ".join(command))
    subprocess.run(command, cwd=os.path.abspath(out_dir), check=True)


# excel_gen_xml{{{
def excel_gen_xml(para_list, xml_corpus, print_line):
    
    #print(xml_corpus[0])
    
    print_line.append('<?xml version="1.0" ?>')
    print_line.append('<spirit:component xmlns:spirit="http://www.siliconpeasant.com">')
    print_line.append("  <spirit:name>"+xml_corpus[0][0]+"</spirit:name>")
    print_line.append("  <spirit:version>1.0</spirit:version>")
    print_line.append("  <spirit:addressBlock>")
    print_line.append("    <spirit:name>"+xml_corpus[0][2]+"</spirit:name>")
    print_line.append("    <spirit:description>"+xml_corpus[0][6]+"</spirit:description>")
    print_line.append("    <spirit:baseAddress>"+xml_corpus[0][3]+"</spirit:baseAddress>")
    print_line.append("    <spirit:range>"+xml_corpus[0][4]+"</spirit:range>")
    print_line.append("    <spirit:width>32</spirit:width>")
    print_line.append("    <spirit:byteVisit>1</spirit:byteVisit>")
    print_line.append("    <spirit:usage>register</spirit:usage>")
    print_line.append("    <spirit:protocol>"+xml_corpus[0][5]+"</spirit:protocol>")

#}}}

def addrblock_yml_gen(para_list, xml_corpus, print_line, out_dir="./"):#{{{
    fp = open(out_dir+xml_corpus[0][0].upper()+".yml", "w") 
    cnt = 0
    for addrblock_info in xml_corpus :
        if cnt >= 2 :
            print_line.append(addrblock_info[0].upper()+":")
            print_line.append("  blocks:")
            print_line.append("    - { offset: "+addrblock_info[1]+", path: "+addrblock_info[2]+"}")
            print_line.append("  protocol: "+addrblock_info[2])
        cnt = cnt + 1
    
    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    #fp.write('\n')
    #fp.write('endmodule')

    fp.close()
#}}}

# excel_gen_yml{{{
def excel_gen_yml(para_list, xml_corpus, print_line):
    
    #print(xml_corpus[0])

    #print_line.append("blocks:")
    print_line.append("name: "+xml_corpus[0][0].upper())
    print_line.append("bytes: 4")
    print_line.append("offset: 0x000")
    print_line.append("registers:")

#}}}

#reg_yml_gen{{{
def reg_yml_gen(print_line, reg_corpus, reg_ser) :
    count = 0
    reg_sheet_cnt = 0
    for reg_info in reg_corpus:
        #print(reg_info)
        #print("max index is :", reg_ser.index.max())
        #print("count is :", count)
        #print(reg_info)
        if pd.isna(reg_info[0]) == False:
            #print(reg_info)
            print_line.append("  - name: "+reg_info[0])
            print_line.append("    description: \""+str(reg_info[6]).replace('\n', " ")+"\"")
            print_line.append("    offset: "+hex(int(reg_info[1], 16)))
            print_line.append("    fields:")
          
            count = count + 1
        else:
            #print(reg_info[3])
            bitoffset0 = str(reg_info[3]).split('[', 1)
            bitoffset_error_debug(bitoffset0, reg_info[2])
            #print(bitoffset0)
            bitoffset1 = bitoffset0[1].split(':', 1)
            bitoffset2 = bitoffset1[1].split(']', 1)
            field_msb = bitoffset1[0]
            field_lsb = bitoffset2[0]
            #print(field_msb, field_lsb)
            if pd.isna(reg_info[7]) == False :
                lock_bitoffset0 = str(reg_info[7]).split('[', 1)
                #print(bitoffset0)
                lock_bitoffset1 = lock_bitoffset0[1].split(':', 1)
                lock_bitoffset2 = lock_bitoffset1[1].split(']', 1)
                lock_field_msb = lock_bitoffset1[0]
                lock_field_lsb = lock_bitoffset2[0]
                #print(field_msb, field_lsb)
            #print(reg_info)
            if pd.isna(reg_info[7]) == False :
                print_line.append("      - { name: "+reg_info[2]+", lsb: "+field_lsb+", bits: "+str(int(field_msb) -int(field_lsb) +1)+", access: "+reg_info[4].lower()+", reset: "+reg_info[5]+", lock_lsb: "+lock_field_lsb+", lock_bits: "+str(int(lock_field_msb) - int(lock_field_lsb) + 1)+", lock_value: "+reg_info[8]+", description: \""+str(reg_info[6]).replace('\n', " ")+"\"}")
            else :
                print_line.append("      - { name: "+reg_info[2]+", lsb: "+field_lsb+", bits: "+str(int(field_msb) -int(field_lsb) +1)+", access: "+reg_info[4].lower()+", reset: "+reg_info[5]+", description: \""+str(reg_info[6]).replace('\n', " ")+"\"}")
            
#}}}

#reg_xml_gen{{{
def reg_xml_gen(print_line, reg_corpus, reg_ser):
    count = 0
    for reg_info in reg_corpus:
        #print(reg_info)
        #print("max index is :", reg_ser.index.max())
        #print("count is :", count)
        if pd.isna(reg_info[0]) == False:
            if count != 0:
                print_line.append("    </spirit:register>")
            print_line.append("    <spirit:register>")
            print_line.append("      <spirit:name>"+reg_info[0]+"</spirit:name>")
            print_line.append("      <spirit:description>"+str(reg_info[6]).replace('\n', " ")+"</spirit:description>")
            print_line.append("      <spirit:addressOffset>"+reg_info[1]+"</spirit:addressOffset>")
            print_line.append("      <spirit:size>32</spirit:size>")
            print_line.append("      <spirit:access>"+reg_info[4]+"</spirit:access>")
            print_line.append("      <spirit:reset>")
            print_line.append("        <spirit:value>"+reg_info[5]+"</spirit:value>")  
            print_line.append("      </spirit:reset>")
        else:
            #print(reg_info[3])
            bitoffset0 = str(reg_info[3]).split('[', 1)
            #print(bitoffset0)
            bitoffset1 = bitoffset0[1].split(':', 1)
            bitoffset2 = bitoffset1[1].split(']', 1)
            field_msb = bitoffset1[0]
            field_lsb = bitoffset2[0]
            #print(field_msb, field_lsb)

            #print(reg_info[3])
            if pd.isna(reg_info[7]) == False :
                lock_bitoffset0 = str(reg_info[7]).split('[', 1)
                #print(bitoffset0)
                lock_bitoffset1 = lock_bitoffset0[1].split(':', 1)
                lock_bitoffset2 = lock_bitoffset1[1].split(']', 1)
                lock_field_msb = lock_bitoffset1[0]
                lock_field_lsb = lock_bitoffset2[0]
                #print(field_msb, field_lsb)

            print_line.append("     <spirit:field>")
            print_line.append("        <spirit:name>"+reg_info[2]+"</spirit:name>")
            print_line.append("        <spirit:description>"+str(reg_info[6]).replace('\n', " ")+"</spirit:description>")
            print_line.append("        <spirit:bitOffset>"+field_lsb+"</spirit:bitOffset>")
            print_line.append("        <spirit:bitWidth>"+str(int(field_msb) - int(field_lsb) + 1)+"</spirit:bitWidth>")
            print_line.append("        <spirit:access>"+reg_info[4]+"</spirit:access>")
            if pd.isna(reg_info[7]) == False :
                print_line.append("        <spirit:lockOffset>"+lock_field_lsb+"</spirit:lockOffset>")
                print_line.append("        <spirit:lockWidth>"+str(int(lock_field_msb) - int(lock_field_lsb) + 1)+"</spirit:lockWidth>")
                print_line.append("        <spirit:lockValue>"+reg_info[8]+"</spirit:lockValue>")
            print_line.append("      </spirit:field>")
            if pd.isna(reg_info[7]) == False and "        <spirit:name>"+reg_info[2]+str(int(count)).rjust(3,'0')+"_lock_fld</spirit:name>" not in print_line :
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+reg_info[2]+str(int(count)).rjust(3,'0')+"_lock_fld</spirit:name>")
                print_line.append("        <spirit:description>"+str(reg_info[6]).replace('\n', " ")+" lock, PRTC_"+str(int(lock_field_msb))+"_"+str(int(lock_field_lsb))+"_"+str(reg_info[8])+"</spirit:description>")
                print_line.append("        <spirit:bitOffset>"+lock_field_lsb+"</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>"+str(int(lock_field_msb) - int(lock_field_lsb) + 1)+"</spirit:bitWidth>")
                print_line.append("        <spirit:access>RW</spirit:access>")
                print_line.append("      </spirit:field>")
        count = count + 1
        if count > reg_ser.index.max():
            print_line.append("    </spirit:register>")

#}}}

#intp_xml_gen{{{
def intp_xml_gen(print_line, intp_corpus, intp_ser):
    count = 0
    intp_count = 0
    for intp_info in intp_corpus:
        #print(intp_info[0])
        #if count % 14 == 0 or count % 14 == 1:
        if pd.isna(intp_info[0]) == False:
            if intp_count != 0 and intp_count % 7 == 0:
                print_line.append("    </spirit:interrupt>")
            #print(intp_info[0])
            if intp_count % 7 == 0:
                intp_name = intp_info[0].split('_')
                del(intp_name[-1])
                del(intp_name[-1])
                intp_name_str = '_'.join(intp_name)
                #print(intp_name)
                print_line.append("    <spirit:interrupt>")
                print_line.append("      <spirit:name>"+intp_name_str+"</spirit:name>")
                print_line.append("      <spirit:description>"+str(intp_info[6]).replace('\n', " ")+"</spirit:description>")
                print_line.append("      <spirit:addressOffset>"+intp_info[1]+"</spirit:addressOffset>")
                print_line.append("      <spirit:size>32</spirit:size>")
                print_line.append("      <spirit:access>"+intp_info[4]+"</spirit:access>")
                print_line.append("      <spirit:reset>")
                print_line.append("        <spirit:value>0x0</spirit:value>")
                print_line.append("      </spirit:reset>")
            intp_count = intp_count + 1
        elif (intp_count-1) % 7 == 0:
            #print(intp_count)
            #print(intp_info[3])
            bitoffset0 = str(intp_info[3]).split('[', 1)
            #print(bitoffset0)
            bitoffset1 = bitoffset0[1].split(':', 1)
            bitoffset2 = bitoffset1[1].split(']', 1)
            field_msb = bitoffset1[0]
            field_lsb = bitoffset2[0]
            #print(field_msb, field_lsb)
            
            print_line.append("      <spirit:field>")
            print_line.append("        <spirit:name>"+intp_info[2]+"</spirit:name>")
            print_line.append("        <spirit:description>"+str(intp_info[6]).replace('\n', " ")+"</spirit:description>")
            print_line.append("        <spirit:bitOffset>"+field_lsb+"</spirit:bitOffset>")
            print_line.append("        <spirit:bitWidth>"+str(int(field_msb) - int(field_lsb) + 1)+"</spirit:bitWidth>")
            print_line.append("        <spirit:access>"+intp_info[4]+"</spirit:access>")
            print_line.append("      </spirit:field>")
        count = count + 1
        if count > intp_ser.index.max():
            print_line.append("    </spirit:interrupt>")


#}}}

#intp_yml_gen{{{
def intp_yml_gen(print_line, intp_corpus, intp_ser):
    count = 0
    intp_count = 0
    for intp_info in intp_corpus:
        #print(intp_info[0])
        #if count % 14 == 0 or count % 14 == 1:
        if pd.isna(intp_info[0]) == False:
            #if intp_count != 0 and intp_count % 7 == 0:
            #    print_line.append("    </spirit:interrupt>")
            #print(intp_info[0])
            if intp_count % 7 == 0:
                intp_name = intp_info[0].split('_')
                del(intp_name[-1])
                del(intp_name[-1])
                intp_name_str = '_'.join(intp_name)
                #print(intp_name)
                #print_line.append("    <spirit:interrupt>")
                #print_line.append("      <spirit:name>"+intp_name_str+"</spirit:name>")
                #print_line.append("      <spirit:description>"+str(intp_info[6]).replace('\n', " ")+"</spirit:description>")
                #print_line.append("      <spirit:addressOffset>"+intp_info[1]+"</spirit:addressOffset>")
                #print_line.append("      <spirit:size>32</spirit:size>")
                #print_line.append("      <spirit:access>"+intp_info[4]+"</spirit:access>")
                #print_line.append("      <spirit:reset>")
                #print_line.append("        <spirit:value>0x0</spirit:value>")
                #print_line.append("      </spirit:reset>")
                print_line.append("  - name: "+intp_name_str)
                print_line.append("    description: \""+str(intp_info[6]).replace('\n', " ")+"\"")
                print_line.append("    offset: "+intp_info[1])
                print_line.append("    fields:")
            intp_count = intp_count + 1
        elif (intp_count-1) % 7 == 0:
            #print(intp_count)
            #print(intp_info[3])
            bitoffset0 = str(intp_info[3]).split('[', 1)
            #print(bitoffset0)
            bitoffset1 = bitoffset0[1].split(':', 1)
            bitoffset2 = bitoffset1[1].split(']', 1)
            field_msb = bitoffset1[0]
            field_lsb = bitoffset2[0]
            #print(field_msb, field_lsb)
            
            #print_line.append("      <spirit:field>")
            #print_line.append("        <spirit:name>"+intp_info[2]+"</spirit:name>")
            #print_line.append("        <spirit:description>"+str(intp_info[6]).replace('\n', " ")+"</spirit:description>")
            #print_line.append("        <spirit:bitOffset>"+field_lsb+"</spirit:bitOffset>")
            #print_line.append("        <spirit:bitWidth>"+str(int(field_msb) - int(field_lsb) + 1)+"</spirit:bitWidth>")
            #print_line.append("        <spirit:access>"+intp_info[4]+"</spirit:access>")
            #print_line.append("      </spirit:field>")
            print_line.append("      - { name: "+intp_info[2]+", lsb: "+field_lsb+", bits: "+str(int(field_msb) -int(field_lsb) +1)+", access: "+intp_info[4].lower()+", reset: "+intp_info[5]+", description: \""+str(intp_info[6]).replace('\n', " ")+"\"}")
        count = count + 1
        #if count > intp_ser.index.max():
        #    print_line.append("    </spirit:interrupt>")


#}}}

def rtl_gen(para_list, xml_corpus, print_line, reg_corpus, reg_ser, reg_empty, gen_file_name, intp_corpus, intp_ser, intp_empty, out_dir="./"): #{{{
    fp = open(out_dir+gen_file_name+"_reg_inst.v", "w") 
    
    print_line = []
    add_header(print_line, gen_file_name+"_reg_inst.v")
    #print_line.append('`include "sysvlog_interface_connect.h"')
    print_line.append("module "+gen_file_name+"_reg_inst(")
    #print_line.append('\tapb3_bus.slave  apb3_bus_clk_gen,')
    if xml_corpus[0][5] == "apb":
        print_line.append('\tinput           apb_clk,')        
        print_line.append('\tinput           apb_rst_n,')    
        print_line.append('\tinput           apb_sel,')       
        print_line.append('\tinput           apb_enable,')    
        print_line.append('\tinput           apb_write,')     
        print_line.append('\tinput   [31:0]  apb_addr, ')
        print_line.append('\tinput   [31:0]  apb_wdata,')
        print_line.append('\toutput          apb_ready,')     
        print_line.append('\toutput  [31:0]  apb_rdata,')
        print_line.append('\toutput          apb_slverr,')
    elif xml_corpus[0][5] == "dab":
        print_line.append('\tinput           dab_clk,')
        print_line.append('\tinput           dab_rst_n,')
        print_line.append('\tinput           dab_write,')
        print_line.append('\tinput           dab_read,')
        print_line.append('\tinput  [31:0]   dab_addr,')
        print_line.append('\tinput  [31:0]   dab_wdata,')
        print_line.append('\toutput [31:0]   dab_rdata,')
        print_line.append('\toutput          dab_ready,')
    elif xml_corpus[0][5] == "ahb":
        print_line.append('    input            ahb_clk')      
        print_line.append('    input            ahb_rst_n,') 
        print_line.append('    input            ahb_ready,') 
        print_line.append('    input            ahb_sel  ,') 
        print_line.append('    input [1:0]      ahb_trans,') 
        print_line.append('    input            ahb_write,') 
        print_line.append('    input [1:0]      ahb_burst,') 
        print_line.append('    input [1:0]      ahb_size ,') 
        print_line.append('    input [31:0]     ahb_addr ,') 
        print_line.append('    input [31:0]     ahb_wdata,') 
        print_line.append('    input            ahb_ready,')
        print_line.append('    input [1:0]      ahb_resp ,') 
        print_line.append('    input [31:0]     ahb_rdata,') 

    count = 0
    if reg_empty == False :
        for reg_info in reg_corpus:    
            if pd.isna(reg_info[0]) == False:
                rst_reg_name = reg_info[0]
            else :
                #print(reg_info[3])
                bitoffset0 = str(reg_info[3]).split('[', 1)
                #print(bitoffset0)
                bitoffset_error_debug(bitoffset0, reg_info[2])
                bitoffset1 = bitoffset0[1].split(':', 1)
                bitoffset2 = bitoffset1[1].split(']', 1)
                field_msb = bitoffset1[0]
                field_lsb = bitoffset2[0]
                if reg_info[4] == "RO" :
                    print_line.append("    input    "+"["+str(int(field_msb)-int(field_lsb))+":0]     "+reg_info[2]+",") 
                else :
                    print_line.append("    output   "+"["+str(int(field_msb)-int(field_lsb))+":0]     "+reg_info[2]+",") 
            count = count + 1           
    port_last_process(count, reg_ser, print_line)

    print_line.append(');\n')
   


    print_line.append('\t/*autodef*/\n')
  

    if xml_corpus[0][5] == "dab":
        print_line.append("    "+xml_corpus[0][2]+"_dab_reg u_"+xml_corpus[0][2]+"_dab_reg(/*autoinst*/")
        print_line.append("         .clk                                  (dab_clk             ), //input")
        print_line.append("         .reset_n                              (dab_rst_n           ), //input")
        print_line.append("         .dab_write                            (dab_write           ), //input")
        print_line.append("         .dab_read                             (dab_read            ), //input")
        print_line.append("         .dab_addr                             (dab_addr[31:0]      ), //input")
        print_line.append("         .dab_wdata                            (dab_wdata[31:0]     ), //input")
        print_line.append("         .dab_rdata                            (dab_rdata[31:0]     ), //output")
        print_line.append("         .dab_ready                            (dab_ready           ), //output")
    elif xml_corpus[0][5] == "ahb":
        print_line.append("    "+xml_corpus[0][2]+"_ahb_reg u_"+xml_corpus[0][2]+"_ahb_reg(/*autoinst*/")
        print_line.append("        .clk                                   (ahb_clk           ), //input")
        print_line.append("        .rst_n                                 (ahb_rst_n         ), //input")
        print_line.append("        .hreadyin                              (ahb_readyin      ), //input")
        print_line.append("        .hsel                                  (ahb_sel          ), //input")
        print_line.append("        .htrans                                (ahb_trans        ), //input")
        print_line.append("        .hwrite                                (ahb_write        ), //input")
        print_line.append("        .hburst                                (ahb_burst        ), //output")
        print_line.append("        .hsize                                 (ahb_size         ), //output")
        print_line.append("        .haddr                                 (ahb_addr         ), //output")
        print_line.append("        .hwdata                                (ahb_wdata        ), //output")
        print_line.append("        .hreadyout                             (ahb_readyout     ), //output")
        print_line.append("        .hresp                                 (ahb_resp         ), //output")
        print_line.append("        .hrdata                                (ahb_rdata        ), //output")
    elif xml_corpus[0][5] == "apb":
        print_line.append("    "+xml_corpus[0][2]+"_apb_reg u_"+xml_corpus[0][2]+"_apb_reg(/*autoinst*/")
        print_line.append("        .clk                                   (apb_clk              ),")
        print_line.append("        .rst_n                                 (apb_rst_n            ),")
        print_line.append("        .psel                                  (apb_sel              ),")
        print_line.append("        .penable                               (apb_enable           ),")
        print_line.append("        .pwrite                                (apb_write            ),")
        print_line.append("        .paddr                                 (apb_addr[31:0]       ),")
        print_line.append("        .pwdata                                (apb_wdata[31:0]      ),")
        print_line.append("        .pready                                (apb_ready            ),")
        print_line.append("        .prdata                                (apb_rdata[31:0]      ),")
        print_line.append("        .pslverr                               (apb_slverr           ),")
    
    tdr_buf_list = []

    if reg_empty == False :
        for reg_info in reg_corpus:    
            if pd.isna(reg_info[0]) == False:
                rst_reg_name = reg_info[0]
            else :
                #print(reg_info[3])
                bitoffset0 = str(reg_info[3]).split('[', 1)
                #print(bitoffset0)
                bitoffset1 = bitoffset0[1].split(':', 1)
                bitoffset2 = bitoffset1[1].split(']', 1)
                field_msb = bitoffset1[0]
                field_lsb = bitoffset2[0]
                #print(field_msb, field_lsb)
                #if int(field_msb) - int(field_lsb) == 0 :
                #    print_line.append("\t\t."+rst_reg_name+"_"+reg_info[2]+"\t\t("+reg_info[2]+"),")
                #else :
                #    print_line.append("\t\t."+rst_reg_name+"_"+reg_info[2]+"\t\t("+reg_info[2]+"["+str(int(field_msb)-int(field_lsb))+":0]),")
                if "mem_ctrl" in reg_info[2] :
                    #tdr_buf_list.append("u_"+gen_file_name+"/u_"+reg_info[2]+"_test_tdr_mux/dontouch_tdr/u_dontouch_tdr_buf/u_std_cell_buf 0")
                    tdr_buf_list.append("test_tdr_mux #("+str(int(field_msb)-int(field_lsb)+1)+") u_"+reg_info[2]+"_test_tdr_mux( test_mode, func_"+reg_info[2]+", "+reg_info[2]+");")
                    print_line.append("\t\t."+rst_reg_name+"_"+reg_info[2]+"\t\t(func_"+reg_info[2]+"["+str(int(field_msb)-int(field_lsb))+":0]),")
                else :
                    print_line.append("\t\t."+rst_reg_name+"_"+reg_info[2]+"\t\t("+reg_info[2]+"["+str(int(field_msb)-int(field_lsb))+":0]),")
   
        for reg_info in reg_corpus:    
            if pd.isna(reg_info[0]) == False:
                rst_reg_name = reg_info[0]
            else :
                #print(reg_info[3])
                bitoffset0 = str(reg_info[3]).split('[', 1)
                #print(bitoffset0)
                bitoffset1 = bitoffset0[1].split(':', 1)
                bitoffset2 = bitoffset1[1].split(']', 1)
                field_msb = bitoffset1[0]
                field_lsb = bitoffset2[0]
                #print(field_msb, field_lsb)
                #if int(field_msb) - int(field_lsb) == 0 :
                #    print_line.append("\t\t."+rst_reg_name+"_"+reg_info[2]+"\t\t("+reg_info[2]+"),")
                #else :
                #    print_line.append("\t\t."+rst_reg_name+"_"+reg_info[2]+"\t\t("+reg_info[2]+"["+str(int(field_msb)-int(field_lsb))+":0]),")
                if "mem_ctrl" in reg_info[2] :
                    #print(reg_info[5])
                    binary_string = list(reversed(list(bin(int(reg_info[5].replace("_", "")[2:], 16))[2:])))
                    for i in range(32) :
                        if(i >= len(binary_string)) :
                            tdr_buf_list.append("u_"+gen_file_name+"/u_"+reg_info[2]+"_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf 0")
                        else :
                            tdr_buf_list.append("u_"+gen_file_name+"/u_"+reg_info[2]+"_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf "+str(binary_string[i]))
 

    if intp_empty == False :
        intp_count = 0
        for intp_info in intp_corpus:
            if pd.isna(intp_info[0]) == False:
                if intp_count % 7 == 0:
                    intp_name = intp_info[0].split('_')
                    del(intp_name[-1])
                    del(intp_name[-1])
                    intp_name_str = '_'.join(intp_name)
                    print_line.append("\t\t."+intp_name_str+"_out\t\t("+intp_name_str+"_out),")
                intp_count = intp_count + 1

            elif (intp_count-1) % 7 == 0:
                #print(intp_count)
                #print(intp_info[3])
                bitoffset0 = str(intp_info[3]).split('[', 1)
                #print(bitoffset0)
                bitoffset1 = bitoffset0[1].split(':', 1)
                bitoffset2 = bitoffset1[1].split(']', 1)
                field_msb = bitoffset1[0]
                field_lsb = bitoffset2[0]
                #print(field_msb, field_lsb)
                print_line.append("\t\t."+intp_name_str+"_"+intp_info[2]+"\t\t("+intp_info[2]+"),")





    print_line.append(');')

    print_line.append('endmodule')
    print_line.append('//Local Variables:')
    print_line.append('//verilog-library-directories:(".")')
    print_line.append('//verilog-library-directories:("$HW/builts/xml")')
    print_line.append("")

    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    #fp.write('\n')
    #fp.write('endmodule')

    fp.close()

    fp = open(out_dir+gen_file_name+"_tdr_buf_list.txt", "w") 
    for line in tdr_buf_list :
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')
#}}}

#port_last_process{{{
def port_last_process(count, ser, print_line):
    if count > ser.index.max():
        print_line[-1] = print_line[-1].strip(',') 
#}}}

# add_header{{{
def add_header(print_line, filename):
    today = datetime.today()
    now = datetime.now()
    user = getpass.getuser()
    
    date1 = today.strftime("%Y/%m/%d")
    year = today.strftime("%Y")
    time = now.strftime("%H:%M")
    #print("date1 =", date1)
    #print("year =", year)
    #print("time =", time)
    #print(user)
    
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

# }}}

def bitoffset_error_debug(error_list, error_point):
    try:
        index = 1
        value = error_list[index]
        #print("索引 {} 的值是: {}".format(index, value))
    except IndexError:
        print(error_point)
        print("错误：列表索引超出范围！")

# help{{{
def help():
    print("############## help ####################")
    print("########################################")
    print("#######regfile excel generate xml#######")
    print("excel_xml_gen.py excel_path sheet_name ")

# }}}

if __name__ == "__main__":
    main()
