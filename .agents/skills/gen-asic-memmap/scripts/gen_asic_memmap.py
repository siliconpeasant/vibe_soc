#!/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import re
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
        para_list = list(para_list) + [out_dir]

    excel_file = pd.ExcelFile(para_list[0])

    for i in excel_file.sheet_names :
        if "memmap" in i :
            df = pd.read_excel(para_list[0], sheet_name=i)
            note_corpus = df.values.tolist()
            note_ser = pd.Series(note_corpus)
            print("\nall data:")
            print(df)
            note_ser = pd.Series(note_corpus)
            para_list_name = [para_list[0], i]
            #gen_sysmaph(para_list_name, note_corpus, note_ser)
            #gen_sysmapsvh(para_list_name, note_corpus, note_ser)
            addrblock_yml_gen(para_list, note_corpus, out_dir)
    yml_path = out_dir+para_list[1]+"_ASIC.yml"
    print("Info: Generated "+yml_path)
    
    # 生成 C header 和 SV header（内置功能，无需外部 xreg 命令）
    # ensure para_list[2] is normalized output dir for header writers
    if len(para_list) < 3:
        para_list = list(para_list) + [out_dir]
    else:
        para_list = list(para_list)
        para_list[2] = out_dir
    gen_sysmaph(para_list, note_corpus, note_ser)
    gen_sysmapsvh(para_list, note_corpus, note_ser)
    print("## "+para_list[1]+" ASIC memmap generate successful ##")

def addrblock_yml_gen(para_list, note_corpus, out_dir="./"):#{{{
    fp = open(out_dir+para_list[1]+"_ASIC.yml", "w") 
    cnt = 0
    corder = []
    print_line = []
    print_line.append("name: "+para_list[1])
    print_line.append("blocks:")
    for addrblock_info in note_corpus :
        if pd.isna(addrblock_info[1]) == True or addrblock_info[1] == "Slave" or addrblock_info[1] == "RESERVE" or addrblock_info[1] in corder :
            print("Repeat addressblock : "+str(addrblock_info[1]))
            continue
        else :
            print_line.append("  - name: "+addrblock_info[1].upper())
            print_line.append("    offset: "+addrblock_info[5].lower())
            print_line.append("    size: "+str(addrblock_info[7]))
            if pd.isna(addrblock_info[9]) == True :
                print_line.append("    file: null")
            else :
                print_line.append("    file: "+str(addrblock_info[9]))
            #if pd.isna(addrblock_info[2]) == True :
            #    print_line.append("    protocol: null")
            #else :
            #    print_line.append("    protocol: "+addrblock_info[2])
            corder.append(addrblock_info[1])
        cnt = cnt + 1
    
    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    #fp.write('\n')
    #fp.write('endmodule')

    fp.close()
#}}}

def gen_sysmaph(para_list, note_corpus, note_ser):#{{{ 
    
    proj = para_list[1].upper()
    print_line = []
    add_header(print_line, proj+"_sysmap.h")
    print_line.append("")
   
    print_line.append("#ifndef __"+proj+"_SYSMAP_H__")
    print_line.append("#define __"+proj+"_SYSMAP_H__")
    print_line.append("#ifndef ASIC_BASEADDR")
    print_line.append("  #define ASIC_BASEADDR 0x0UL")
    print_line.append("#endif")
    print_line.append("")

    corder = []
    for note_info in note_corpus :
        if pd.isna(note_info[1]) == True or note_info[1] == "Slave" or note_info[1] == "RESERVE" or note_info[1] in corder :
            print("Repeat addressblock : "+str(note_info[1]))
            continue
        else :
            print_line.append("#ifndef ASIC_"+note_info[1].upper()+"_BASEADDR")
            print_line.append("  #define ASIC_"+note_info[1].upper()+"_BASEADDR (ASIC_BASEADDR + "+note_info[5].lower()+"UL)")
            print_line.append("#endif")
            print_line.append("")
            corder.append(note_info[1])

    print_line.append("#endif //__"+proj+"_SYSMAP_H__")

    out_dir = para_list[2] if len(para_list) >= 3 else "./"
    if not str(out_dir).endswith("/"):
        out_dir = str(out_dir) + "/"
    out_path = out_dir + proj + "_sysmap.h"
    fp = open(out_path, "w")

    for line in print_line :
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')

    fp.close()
    print("Info: Generated " + out_path)

#}}}

def gen_sysmapsvh(para_list, note_corpus, note_ser):#{{{ 
    
    proj = para_list[1].upper()
    print_line = []
    add_header(print_line, proj+"_sysmap.svh")
    print_line.append("")

    print_line.append("`ifndef __"+proj+"_SYSMAP_SVH__")
    print_line.append("`define __"+proj+"_SYSMAP_SVH__")
    print_line.append("`ifndef ASIC_BASEADDR")
    print_line.append("  `define ASIC_BASEADDR 'h0")
    print_line.append("`endif")
    print_line.append("")

    corder = []
    for note_info in note_corpus :
        if pd.isna(note_info[1]) == True or note_info[1] == "Slave" or note_info[1] == "RESERVE" or note_info[1] in corder :
            continue
        else :
            print_line.append("`ifndef ASIC_"+note_info[1].upper()+"_BASEADDR")
            print_line.append("  `define ASIC_"+note_info[1].upper()+"_BASEADDR (ASIC_BASEADDR + 'h"+note_info[5].lower().replace("0x", "")+")")
            print_line.append("`endif")
            print_line.append("")
            corder.append(note_info[1])

    print_line.append("`endif //__"+proj+"_SYSMAP_SVH__")

    out_dir = para_list[2] if len(para_list) >= 3 else "./"
    if not str(out_dir).endswith("/"):
        out_dir = str(out_dir) + "/"
    out_path = out_dir + proj + "_sysmap.svh"
    fp = open(out_path, "w")

    for line in print_line :
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')

    fp.close()
    print("Info: Generated " + out_path)

#}}}

# add_header{{{
def add_header(print_line, filename):
    today = datetime.today()
    now = datetime.now()
    user = getpass.getuser()

    date1 = today.strftime("%Y/%m/%d")
    time = now.strftime("%H:%M")

    print_line.append("// ============================================================================")
    print_line.append("// File Name    : "+filename)
    print_line.append("// Description  :")
    print_line.append("// Author       : "+user)
    print_line.append("// Created On   : "+date1+" "+time)
    print_line.append("// Last Modified: "+date1+" "+time)
    print_line.append("// ----------------------------------------------------------------------------")
    print_line.append("// Date         By           Version  Description")
    print_line.append("// ----------------------------------------------------------------------------")
    print_line.append("// "+date1+"   "+user.ljust(11)+" 1.0      Initial version")
    print_line.append("// ============================================================================")

# }}}

def gen_note(para_list, note_corpus, note_ser):#{{{ 
    
    print_line = []
   
    print_line.append("// Component")
    print_line.append("ASIC          --  v1.0")
    print_line.append("")
    print_line.append("// Block")
    print_line.append("ASIC                        --  0x0000_0000:0xffff_ffff  --   asic top block      -- ahb")
    print_line.append("")
    print_line.append("// Sub Block")

    for note_info in note_corpus :
        if "RESERVE" in str(note_info[12]) or "DEFINE NAME" in str(note_info[12]) or "Slave"  in note_info[0] :
            continue
        else :
            print_line.append(str(note_info[12]).upper()+"      --  "+note_info[4].lower()+":"+note_info[5].lower()+"  --   "+note_info[0].lower()+" address block       -- dab")

    print_line.append("// Sub Block end")
    print_line.append("")
    print_line.append("// Block end")
    print_line.append("// Component end")

    fp = open("ASIC.note", "w") 

    for line in print_line :
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')

    fp.close()

#}}}

# help{{{
def help():
    print("############## help ####################")
    print("########################################")
    print("#######regfile excel generate xml#######")
    print("gen_asic_sysmap.py excel_path project_name ")

# }}}

if __name__ == "__main__":
    main()

