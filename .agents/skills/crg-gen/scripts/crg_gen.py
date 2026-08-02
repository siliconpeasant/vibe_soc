#!/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import re
import pandas as pd
import numpy as np
from datetime import datetime
import getpass
import math
import copy

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
    if len(para_list) == 2 :
        gen_filepath = para_list[1]+"/"
    else :
        gen_filepath = "./"

    if len(para_list) == 2 :
        crg_option = para_list[1]
    else :
        crg_option = "crg"

    if(len(para_list) == 0) or para_list[0] == "-h":
        help()
        sys.exit(1)

    if para_list[1] != "excel_gen" :
        df = pd.read_excel(para_list[0], sheet_name = "top_info")
        top_corpus = df.values.tolist()

        #print(top_corpus)
        #print("\nall data:")
        #print (df)
        top_ser = pd.Series(top_corpus)
        top_empty = df.empty

    #design_name = top_corpus[top_info_index["design_name"]][1]
    #protocol = top_corpus[top_info_index["protocol"]][1]
    #clk_gen_addr_ofst = top_corpus[top_info_index["clk_gen_addr_ofst"]][1]
    #rst_gen_addr_ofst = top_corpus[top_info_index["rst_gen_addr_ofst"]][1]
    #user_defined_reg_addr_ofst = top_corpus[top_info_index["user_defined_reg_addr_ofst"]][1]
    #user_defined_intp_addr_ofst = top_corpus[top_info_index["user_defined_intp_addr_ofst"]][1]
    
    (filepath, filename) = os.path.split(para_list[0])
    #print("filepath is:"+filepath)
    #print("filename is:"+filename)


    top_info_index = {"design_owner":0, \
            "design_name":1, \
            "protocol":2, \
            "clk_gen_addr_ofst":3, \
            "rst_gen_addr_ofst":4, \
            "rst_status_addr_ofst":5, \
            "user_defined_reg_addr_ofst":6, \
            "user_defined_intp_addr_ofst":7, \
            "delay_beat":8, \
            "design_hier":9, \
            "clock_uncertainty_setup":10, \
            "clock_uncertainty_hold":11, \
            "clock_transition_rise_max":12, \
            "clock_transition_rise_min":13, \
            "clock_transition_fall_max":14, \
            "clock_transition_fall_min":15}




    clk_info_index = {"name":1, \
            "sel":2, \
            "src0":3, \
            "src1":4, \
            "mux_dflt":5, \
            "div":6, \
            "div_width":7, \
            "div_dflt":8, \
            "occ_scan_mux":9, \
            "icg":10, \
            "icg_dflt":11, \
            "icg_external":12, \
            "icg_internal":13, \
            "ce_en":14, \
            "attr":15, \
            "note":16, \
            "clock_group0":17, \
            "clock_source":18, \
            "divider_fadj":19, \
            "divider_fadj_val":20, \
            "divider_sync_clk":21, \
            "div_val_to_en":22, \
            "div_val_to":23}


    rst_info_index = {"name":1, \
            "reg_name":2, \
            "soft_lc":3, \
            "soft_dflt":4, \
            "glb_src":5, \
            "soft_src":6, \
            "external_src":7, \
            "internal_src":8, \
            "assert_value":9, \
            "areset_relax_en":10, \
            "sync":11, \
            "sync_clk":12, \
            "inout":13, \
            "lock_bit_offset":14, \
            "lock_value":15, \
            "note":16}
    #print(clk_info_index)
    #print(clk_info_index["name"])
    #if len(para_list) == 2 :
    if crg_option == "sdc_gen" : 
            df = pd.read_excel(para_list[0], sheet_name = "clk_gen")
            if pd.isnull(df.iloc[0, 0]) == False :
                df.insert(0, "Unnamed: 0", "NaN")
            clk_corpus = df.values.tolist()
            #print("\nall data:")
            #print (df)
            clk_ser = pd.Series(clk_corpus)
            #print(clk_ser)
            df = pd.read_excel(para_list[0], sheet_name = "rst_gen")
            if pd.isnull(df.iloc[0, 0]) == False :
                df.insert(0, "Unnamed: 0", "NaN")
            rst_corpus = df.values.tolist()
            #print("\nall data:")
            #print (df)
            rst_ser = pd.Series(rst_corpus)

            df = pd.read_excel(para_list[0], sheet_name = "user_sdc")
            sdc_corpus = df.values.tolist()

            #print("\nall data:")
            #print (df)
            sdc_ser = pd.Series(sdc_corpus)
            sdc_empty = df.empty
            clk_sdc_gen(rst_info_index, clk_info_index, top_info_index, top_corpus, clk_corpus, clk_ser, rst_corpus, rst_ser, sdc_corpus, sdc_ser, sdc_empty)
    elif crg_option == "excel_gen" :
        print("######")
        data = {"clk_gen": ["name", "sel", "src0", "src1", "div", "div_width", "div_dflt", "occ_scan_mux", "icg", "icg_dflt", "icg_external", "icg_internal", "attr", "note", "clock_gruop0", "clock_group1", "clock_source", "divider_fadj", "divider_sync_clk"]}
        writeDataIntoExcel("temp.xlsx", data)  
    else :
        df = pd.read_excel(para_list[0], sheet_name = "clk_gen")
        if pd.isnull(df.iloc[0, 0]) == False :
            df.insert(0, "Unnamed: 0", "NaN")

        clk_corpus = df.values.tolist()
        #print("\nall data:")
        #print (df)
        clk_ser = pd.Series(clk_corpus)
        
        df = pd.read_excel(para_list[0], sheet_name = "rst_gen")
        if pd.isnull(df.iloc[0, 0]) == False :
            df.insert(0, "Unnamed: 0", "NaN")
        rst_corpus = df.values.tolist()
        #print("\nall data:")
        #print (df)
        rst_ser = pd.Series(rst_corpus)

        df = pd.read_excel(para_list[0], sheet_name = "user_defined_reg")
        reg_corpus = df.values.tolist()

        #print("\nall data:")
        #print (df)
        reg_ser = pd.Series(reg_corpus)
        reg_empty = df.empty

        df = pd.read_excel(para_list[0], sheet_name = "user_code")
        code_corpus = df.values.tolist()

        #print("\nall data:")
        #print (df)
        code_ser = pd.Series(code_corpus)
        code_empty = df.empty
        
        df = pd.read_excel(para_list[0], sheet_name = "user_defined_intp")
        intp_corpus = df.values.tolist()
        intp_ser = pd.Series(intp_corpus)
        intp_empty = df.empty

        #print("\nall data:")
        #print (df)
       
        df = pd.read_excel(para_list[0], sheet_name = "user_sdc")
        sdc_corpus = df.values.tolist()

        #print("\nall data:")
        #print (df)
        sdc_ser = pd.Series(sdc_corpus)
        sdc_empty = df.empty


        clk_gen(gen_filepath, top_corpus, clk_info_index, top_info_index, clk_corpus, clk_ser)
        rst_gen(rst_info_index, top_info_index, gen_filepath, top_corpus, rst_corpus, rst_ser)
        #if para_list[1] == "csv" :
        crg_gen_top_csv(rst_info_index, gen_filepath, top_corpus, rst_corpus, rst_ser, clk_info_index, top_info_index, clk_corpus, clk_ser, reg_corpus, reg_ser, code_corpus, code_ser, code_empty, reg_empty, intp_empty, intp_corpus, intp_ser)
        #else :    
        #    crg_gen_top(top_corpus, rst_corpus, rst_ser, clk_info_index, top_info_index, clk_corpus, clk_ser, reg_corpus, reg_ser, code_corpus, code_ser, code_empty, reg_empty, intp_empty, intp_corpus, intp_ser)
        #crg_gen_xml(rst_info_index, gen_filepath, top_corpus, rst_corpus, rst_ser, clk_info_index, top_info_index, clk_corpus, clk_ser, reg_corpus, reg_ser, reg_empty, intp_empty, intp_corpus, intp_ser)
        crg_gen_yml(rst_info_index, gen_filepath, top_corpus, rst_corpus, rst_ser, clk_info_index, top_info_index, clk_corpus, clk_ser, reg_corpus, reg_ser, reg_empty, intp_empty, intp_corpus, intp_ser)
       
        #gen_xml = "gen_xml.pl "+para_list[1].upper()+".note"
        #print(gen_xml)
        add_clk_gen_inst = "soc_build add "+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.v u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen "+top_corpus[top_info_index["design_name"]][1]+"_top.csv"
        add_rst_gen_inst = "soc_build add "+top_corpus[top_info_index["design_name"]][1]+"_rst_gen.v u_"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen "+top_corpus[top_info_index["design_name"]][1]+"_top.csv"
        up_crg_top = "soc_build updateall "+top_corpus[top_info_index["design_name"]][1]+"_top.csv"
        gen_crg_top = "soc_build gen "+top_corpus[top_info_index["design_name"]][1]+"_top.csv"
        #os.system(add_clk_gen_inst) 
        #os.system(add_rst_gen_inst) 

        #os.system(gen_crg_top) 
        #os.system(up_crg_top)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        soc_build_py = os.path.join(script_dir, "soc_build.py")
        gen_rtl = "python3 "+soc_build_py+" gen "+gen_filepath+top_corpus[top_info_index["design_name"]][1]+"_top.csv"
        print(gen_rtl)
        os.system(gen_rtl)
        print("## "+top_corpus[top_info_index["design_name"]][1]+" generate successful ##")

# clk_sdc_gen{{{

def set_clk_info(clk_info_index, top_info_index, print_line, top_corpus, clk_name):

    #print_line.append("set_clock_uncertainty -setup "+str(top_corpus[top_info_index["clock_uncertainty_setup"]][1])+" [get_clocks {"+clk_name+"}]")
    #print_line.append("set_clock_uncertainty -hold "+str(top_corpus[top_info_index["clock_uncertainty_hold"]][1])+" [get_clocks {"+clk_name+"}]")
    #print_line.append("set_clock_transition -rise -max "+str(top_corpus[top_info_index["clock_transition_rise_max"]][1])+" [get_clocks {"+clk_name+"}]")
    #print_line.append("set_clock_transition -rise -min "+str(top_corpus[top_info_index["clock_transition_rise_min"]][1])+" [get_clocks {"+clk_name+"}]")
    #print_line.append("set_clock_transition -fall -max "+str(top_corpus[top_info_index["clock_transition_fall_max"]][1])+" [get_clocks {"+clk_name+"}]")
    #print_line.append("set_clock_transition -fall -min "+str(top_corpus[top_info_index["clock_transition_fall_min"]][1])+" [get_clocks {"+clk_name+"}]")
    print_line.append("")


def clk_sdc_gen(rst_info_index, clk_info_index, top_info_index, top_corpus, clk_corpus, clk_ser, rst_corpus, rst_ser, sdc_corpus, sdc_ser, sdc_empty):
    fp = open(top_corpus[top_info_index["design_name"]][1]+".sdc", "w")

    if pd.isna(top_corpus[top_info_index["design_hier"]][1]) == False :
        design_hier = top_corpus[top_info_index["design_hier"]][1]+"/"
    else :
        design_hier = ""
        
    clock_generate_list = []
    clock_source_list = []
    for clk_info in clk_corpus :
        if "source" in str(clk_info[clk_info_index["clock_source"]]) and pd.isna(clk_info[clk_info_index["div"]]) == True and pd.isna(clk_info[clk_info_index["sel"]]) == True and pd.isna(clk_info[clk_info_index["icg"]]) == True and (str(clk_info[clk_info_index["attr"]]) == "input" or str(clk_info[clk_info_index["attr"]]) == "internal"):
            clock_source_list.append(clk_info[clk_info_index["name"]]+","+clk_info[clk_info_index["clock_source"]])

    for clk_info in clk_corpus :
        if pd.isna(clk_info[clk_info_index["clock_group0"]]) == False :
            if pd.isna(clk_info[clk_info_index["sel"]]) == False :
                for clk_source_info in clock_source_list :
                    #print("#########")
                    #print(clk_source_info)
                    #print(clk_info[clk_info_index["src0"]])
                    #print("*********")
                    if clk_info[clk_info_index["src0"]] in clk_source_info :
                        clk_source_temp = clk_source_info.split(",")
                        clk_source_name = clk_source_temp[0]
                        clk_source_path = clk_source_temp[1]
                        #print("&&&&&&&&&&")
                        #print(clk_source_name)
                        #print(clk_source_path)
                        clock_generate_list.append(clk_info[clk_info_index["name"]]+", get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/u_clk_out/Z}")
                    #if clk_info[clk_info_index["src1"]] in clk_source_info :
                    #    clk_source_temp = clk_source_info.split(",")
                    #    clk_source_name = clk_source_temp[0]
                    #    clk_source_path = clk_source_temp[1]
                    #    #print("&&&&&&&&&&")
                    #    #print(clk_source_name)
                    #    #print(clk_source_path)
                    #    clock_generate_list.append(clk_info[clk_info_index["name"]]+", get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/u_clk_out/Z}")
            elif pd.isna(clk_info[clk_info_index["div"]]) == False : #and clk_info[clk_info_index["icg"]] == "N" :
                for clk_source_info in clock_source_list :
                    #print("#########")
                    #print(clk_source_info)
                    #print(clk_info[clk_info_index["src0"]])

                    if clk_info[clk_info_index["src0"]] in clk_source_info :
                        clk_source_temp = clk_source_info.split(",")
                        clk_source_name = clk_source_temp[0]
                        clk_source_path = clk_source_temp[1]
                        #print("&&&&&&&&&&")
                        #print(clk_source_name)
                        #print(clk_source_path)
                        
                        clock_generate_list.append(clk_info[clk_info_index["name"]]+", get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_divider_wrap/u_clk_divider/BYPASS0*u_std_cell_clk_buf/u_std_cell_clk_buf/Z}")

            elif clk_info[clk_info_index["icg"]] == "Y" :
                for clk_source_info in clock_source_list :
                    #print("#########")
                    #print(clk_source_info)
                    #print(clk_info[clk_info_index["src0"]])
                    #print("*********")
                    if clk_info[clk_info_index["src0"]] in clk_source_info :
                        clk_source_temp = clk_source_info.split(",")
                        clk_source_name = clk_source_temp[0]
                        clk_source_path = clk_source_temp[1]
                        #print("&&&&&&&&&&")
                        #print(clk_source_name)
                        #print(clk_source_path) 
                        clock_generate_list.append(clk_info[clk_info_index["name"]]+", get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_icg/u_dontouch_icg/Q}")

    #print("clock_source_list:")
    #for line in clock_source_list:
    #    print(line)
    #print("")
    #print("clock_generate_list:")
    #for line in clock_generate_list: 
    #    print(line)

    sdc_constrain_source = clock_source_list + clock_generate_list
    #print("")
    #print("sdc_constrain_source")
    #for line in sdc_constrain_source :
    #    print(line)
    
    sdc_all_clk_source = []
    for clk_info in clk_corpus :
        if pd.isna(clk_info[clk_info_index["clock_group0"]]) == False :
            if pd.isna(clk_info[clk_info_index["sel"]]) == False :
                for clk_source_info in sdc_constrain_source :
                    #print("#########")
                    #print(clk_source_info)
                    #print(clk_info[clk_info_index["src0"]])
                    #print("*********")
                    if clk_info[clk_info_index["src0"]] in clk_source_info :
                        clk_source_temp = clk_source_info.split(",")
                        clk_source_name = clk_source_temp[0]
                        clk_source_path = clk_source_temp[1]
                        #print("&&&&&&&&&&")
                        #print(clk_source_name)
                        #print(clk_source_path)
                        master_clock_flag = 0
                        for master_clock in clock_source_list :
                            if clk_source_name in master_clock : 
                                master_clock_flag = 1
                        if master_clock_flag == 1 :
                            sdc_all_clk_source.append(clk_info[clk_info_index["name"]]+", get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/u_clk_out/Z}")
                        else :
                            sdc_all_clk_source.append(str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]]+", get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/u_clk_out/Z}")
                    #if clk_info[clk_info_index["src1"]] in clk_source_info :
                    #    clk_source_temp = clk_source_info.split(",")
                    #    clk_source_name = clk_source_temp[0]
                    #    clk_source_path = clk_source_temp[1]
                    #    #print("&&&&&&&&&&")
                    #    #print(clk_source_name)
                    #    #print(clk_source_path)
                    #    master_clock_flag = 0
                    #    for master_clock in clock_source_list :
                    #        if clk_source_name in master_clock : 
                    #            master_clock_flag = 1
                    #    if master_clock_flag == 1 :
                    #        sdc_all_clk_source.append(clk_info[clk_info_index["name"]]+", get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/u_clk_out/Z}")
                    #    else :
                    #        sdc_all_clk_source.append(str(clk_source_name.replace(clk_info[clk_info_index["src1"]], ""))+clk_info[clk_info_index["name"]]+", get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/u_clk_out/Z}")
            elif pd.isna(clk_info[clk_info_index["div"]]) == False : #and clk_info[clk_info_index["icg"]] == "N" :
                for clk_source_info in sdc_constrain_source :
                    #print("#########")
                    #print(clk_source_info)
                    #print(clk_info[clk_info_index["src0"]])

                    if clk_info[clk_info_index["src0"]] in clk_source_info :
                        clk_source_temp = clk_source_info.split(",")
                        clk_source_name = clk_source_temp[0]
                        clk_source_path = clk_source_temp[1]
                        #print("&&&&&&&&&&")
                        #print(clk_source_name)
                        #print(clk_source_path)
                        master_clock_flag = 0
                        for master_clock in clock_source_list :
                            if clk_source_name in master_clock : 
                                master_clock_flag = 1
                        if master_clock_flag == 1 :                        
                            sdc_all_clk_source.append(clk_info[clk_info_index["name"]]+", get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_divider_wrap/u_clk_divider/BYPASS0*u_std_cell_clk_buf/u_std_cell_clk_buf/Z}")
                        else :
                            sdc_all_clk_source.append(str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]]+", get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_divider_wrap/u_clk_divider/BYPASS0*u_std_cell_clk_buf/u_std_cell_clk_buf/Z}")

            elif clk_info[clk_info_index["icg"]] == "Y" :
                for clk_source_info in sdc_constrain_source :
                    #print("#########")
                    #print(clk_source_info)
                    #print(clk_info[clk_info_index["src0"]])
                    #print("*********")
                    if clk_info[clk_info_index["src0"]] in clk_source_info :
                        clk_source_temp = clk_source_info.split(",")
                        clk_source_name = clk_source_temp[0]
                        clk_source_path = clk_source_temp[1]
                        #print("&&&&&&&&&&")
                        #print(clk_source_name)
                        #print(clk_source_path) 
                        master_clock_flag = 0
                        for master_clock in clock_source_list :
                            if clk_source_name in master_clock : 
                                master_clock_flag = 1
                        if master_clock_flag == 1 :
                            sdc_all_clk_source.append(clk_info[clk_info_index["name"]]+", get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_icg/u_dontouch_icg/Q}")
                        else :
                            sdc_all_clk_source.append(str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]]+", get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_icg/u_dontouch_icg/Q}")
    
    #print("")
    #print("sdc_all_clk_source")
    sdc_all_clk_source = clock_source_list + sdc_all_clk_source
    #sdc_all_clk_source = sdc_constrain_source
    #for line in sdc_all_clk_source :
    #    print(line)

    print_line = []
    all_clock = []
    print_line.append("# ======================================================================")
    print_line.append("# created clock define")
    print_line.append("# ======================================================================")
    for clk_info in clk_corpus :
        if "source" in str(clk_info[clk_info_index["clock_source"]]) and pd.isna(clk_info[clk_info_index["div"]]) == True and pd.isna(clk_info[clk_info_index["sel"]]) == True and pd.isna(clk_info[clk_info_index["icg"]]) == True and (str(clk_info[clk_info_index["attr"]]) == "input" or str(clk_info[clk_info_index["attr"]]) == "internal"):
            clock_source = clk_info[clk_info_index["clock_source"]].strip("source ")
            clock_freq = (1 / float(clk_info[clk_info_index["note"]].strip("MHz"))) * 1000
            #print(clock_freq)
            clock_freq_half = clock_freq / 2
            #print_line.append("create_clock -name "+clk_info[clk_info_index["name"]]+" -period "+str(format(clock_freq, ".4f"))+" -waveform {0.000 "+str(format(clock_freq_half, ".4f"))+"} ["+clock_source+"] -add")
            print_line.append("# ----------------------------------------------------------------------")
            print_line.append("# create clock for "+clk_info[clk_info_index["name"]]+" frequency: "+clk_info[clk_info_index["note"]])
            print_line.append("create_clock -name "+clk_info[clk_info_index["name"]]+" -period "+str(int(clock_freq*10000)/10000)+" -waveform {0.000 "+str(int(clock_freq_half*10000)/10000)+"} ["+clock_source+"] -add")
            all_clock.append(clk_info[clk_info_index["name"]])
            set_clk_info(clk_info_index, top_info_index, print_line, top_corpus, clk_info[clk_info_index["name"]])

    if sdc_empty == False :
        for sdc_info in sdc_corpus :
            if sdc_info[1] == "P" :
                clock_freq = (1 / float(sdc_info[6].strip("MHz"))) * 1000
                #print(clock_freq)
                clock_freq_half = clock_freq / 2
                #print_line.append("create_clock -name "+clk_info[clk_info_index["name"]]+" -period "+str(format(clock_freq, ".4f"))+" -waveform {0.000 "+str(format(clock_freq_half, ".4f"))+"} ["+clock_source+"] -add")
                print_line.append("create_clock -name "+sdc_info[0]+" -period "+str(int(clock_freq*10000)/10000)+" -waveform {0.000 "+str(int(clock_freq_half*10000)/10000)+"} ["+sdc_info[3]+"] -add")
                all_clock.append(sdc_info[0])
                set_clk_info(clk_info_index, top_info_index, print_line, top_corpus, sdc_info[0])

    print_line.append("# ======================================================================")
    print_line.append("# genetaed clock define")
    print_line.append("# ======================================================================")
    for clk_info in clk_corpus :
        if pd.isna(clk_info[clk_info_index["clock_group0"]]) == False :
            if pd.isna(clk_info[clk_info_index["sel"]]) == False :
                for clk_source_info in sdc_all_clk_source :
                    #print("#########")
                    #print(clk_source_info)
                    #print(clk_info[clk_info_index["src0"]])
                    #print("*********")
                    if clk_info[clk_info_index["src0"]] in clk_source_info :
                        clk_source_temp = clk_source_info.split(",")
                        clk_source_name = clk_source_temp[0]
                        clk_source_path = clk_source_temp[1]
                        #print("clk_source_info :"+clk_source_info)
                        #print("&&&&&&&&&&")
                        #print("clk_source_name :"+clk_source_name)
                        #print("clk_source_path :"+clk_source_path)
                        #print("generated clock for :"+str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]])
                        print_line.append("# ----------------------------------------------------------------------")
                        master_clock_flag = 0
                        for master_clock in sdc_all_clk_source :
                            if clk_source_name in master_clock : 
                                master_clock_flag = 1
                        if master_clock_flag == 1 :
                            print_line.append("# generated clock for "+clk_info[clk_info_index["name"]]+" from clk_sel frequency: "+clk_info[clk_info_index["note"]])
                            print_line.append("create_generated_clock -name "+clk_info[clk_info_index["name"]]+" -combinational \\")
                            all_clock.append(clk_info[clk_info_index["name"]])
                        else :
                            print_line.append("# generated clock for "+str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]]+" from clk_sel frequency: "+clk_info[clk_info_index["note"]])
                            print_line.append("create_generated_clock -name "+str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]]+" -combinational \\")
                            all_clock.append(str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]])
                                

                        clock_source = clk_source_path.strip("source ")
                        print_line.append("     -source ["+clock_source+"] \\")
                        print_line.append("     -edges {1 2 3} [get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/u_clk_out/Z}] \\")
                        #for master_clock in sdc_all_clk_source :
                        #    if clk_source_name in master_clock : 
                        #        master_clock_flag = 1
                        #if master_clock_flag == 1 :
                        print_line.append("     -master_clock [get_clocks {"+clk_source_name+"}] -add")
                        #else :
                        #    print_line.append("     -master_clock [get_clocks {"+str(clk_source_name)+"}] -add")

                        master_clock_flag = 0
                        for master_clock in sdc_all_clk_source :
                            if clk_source_name in master_clock : 
                                master_clock_flag = 1
                        if master_clock_flag == 1 :
                            set_clk_info(clk_info_index, top_info_index, print_line, top_corpus, clk_info[clk_info_index["name"]])
                        else :
                            set_clk_info(clk_info_index, top_info_index, print_line, top_corpus, str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]])
                        print_line.append("set_case_analysis 0 "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/sel")

                for clk_source_info in sdc_all_clk_source :
                    #print("#########")
                    #print(clk_source_info)
                    #print(clk_info[clk_info_index["src0"]])
                    #print("*********")
                    if clk_info[clk_info_index["src1"]] in clk_source_info :
                        clk_source_temp = clk_source_info.split(",")
                        clk_source_name = clk_source_temp[0]
                        clk_source_path = clk_source_temp[1]
                        #print("&&&&&&&&&&")
                        #print(clk_source_name)
                        #print(clk_source_path) 
                        print_line.append("# ----------------------------------------------------------------------")
                        master_clock_flag = 0
                        for master_clock in sdc_all_clk_source :
                            if clk_source_name in master_clock : 
                                master_clock_flag = 1
                        if master_clock_flag == 1 :
                            print_line.append("# generated clock for "+clk_info[clk_info_index["name"]]+" from clk_sel frequency: "+clk_info[clk_info_index["note"]])
                            print_line.append("create_generated_clock -name "+clk_info[clk_info_index["name"]]+" -combinational \\")
                            all_clock.append(clk_info[clk_info_index["name"]])
                        else :
                            print_line.append("# generated clock for "+str(clk_source_name.replace(clk_info[clk_info_index["src1"]], ""))+clk_info[clk_info_index["name"]]+" from clk_sel frequency: "+clk_info[clk_info_index["note"]])
                            print_line.append("create_generated_clock -name "+str(clk_source_name.replace(clk_info[clk_info_index["src1"]], ""))+clk_info[clk_info_index["name"]]+" -combinational \\")
                            all_clock.append(str(clk_source_name.replace(clk_info[clk_info_index["src1"]], ""))+clk_info[clk_info_index["name"]])

                        clock_source = clk_source_path.strip("source ")
                        print_line.append("     -source ["+clock_source+"] \\")
                        print_line.append("     -edges {1 2 3} [get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/u_clk_out/Z}] \\")
                        print_line.append("     -master_clock [get_clocks {"+clk_source_name+"}] -add")
                        master_clock_flag = 0
                        for master_clock in sdc_all_clk_source :
                            if clk_source_name in master_clock : 
                                master_clock_flag = 1
                        if master_clock_flag == 1 :
                            set_clk_info(clk_info_index, top_info_index, print_line, top_corpus, clk_info[clk_info_index["name"]])
                        else :
                            set_clk_info(clk_info_index, top_info_index, print_line, top_corpus, str(clk_source_name.replace(clk_info[clk_info_index["src1"]], ""))+clk_info[clk_info_index["name"]])
                        print_line.append("set_case_analysis 1 "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/sel")


            elif pd.isna(clk_info[clk_info_index["div"]]) == False : #and clk_info[clk_info_index["icg"]] == "N" :
                for clk_source_info in sdc_all_clk_source :
                    #print("#########")
                    #print(clk_source_info)
                    #print(clk_info[clk_info_index["src0"]])
                    #print("*********")
                    if clk_info[clk_info_index["src0"]] in clk_source_info :
                        clk_source_temp = clk_source_info.split(",")
                        clk_source_name = clk_source_temp[0]
                        clk_source_path = clk_source_temp[1]
                        #print("&&&&&&&&&&")
                        #print(clk_source_name)
                        #print(clk_source_path) 
                        print_line.append("# ----------------------------------------------------------------------")
                        master_clock_flag = 0
                        for master_clock in sdc_all_clk_source :
                            if clk_source_name in master_clock : 
                                master_clock_flag = 1
                        if master_clock_flag == 1 :
                            print_line.append("# generated clock for "+clk_info[clk_info_index["name"]]+" default: div"+str(int(clk_info[clk_info_index["div_dflt"]]))+" frequency: "+clk_info[clk_info_index["note"]])
                            print_line.append("create_generated_clock -name "+clk_info[clk_info_index["name"]]+" \\")
                            all_clock.append(clk_info[clk_info_index["name"]])
                        else :
                            print_line.append("# generated clock for "+str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]]+" default: div"+str(int(clk_info[clk_info_index["div_dflt"]]))+"frequency: "+clk_info[clk_info_index["note"]])
                            print_line.append("create_generated_clock -name "+str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]]+" \\")
                            all_clock.append(str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]])

                        clock_source = clk_source_path.strip("source ")
                        print_line.append("     -source ["+clock_source+"] \\")
                        if (int(clk_info[clk_info_index["div_dflt"]] % 2)) == 0  or clk_info[clk_info_index["div_dflt"]] == 1 :
                            print_line.append("     -edges {1 "+str(int(clk_info[clk_info_index["div_dflt"]]+1))+" "+str(int(clk_info[clk_info_index["div_dflt"]]*2+1))+"} \\")
                        else :
                            print_line.append("     -edges {1 "+str(int(clk_info[clk_info_index["div_dflt"]]))+" "+str(int(clk_info[clk_info_index["div_dflt"]]*2+1))+"} \\")
                        print_line.append("     [get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_divider_wrap/u_clk_divider/BYPASS0*u_std_cell_clk_buf/u_std_cell_clk_buf/Z}] \\")
                        print_line.append("     -master_clock [get_clocks {"+clk_source_name+"}] -add")
                        master_clock_flag = 0
                        for master_clock in sdc_all_clk_source :
                            if clk_source_name in master_clock : 
                                master_clock_flag = 1
                        if master_clock_flag == 1 :
                            set_clk_info(clk_info_index, top_info_index, print_line, top_corpus, clk_info[clk_info_index["name"]])
                        else :
                            set_clk_info(clk_info_index, top_info_index, print_line, top_corpus, str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]])

            elif clk_info[clk_info_index["icg"]] == "Y" :
                for clk_source_info in sdc_all_clk_source :
                    #print("#########")
                    #print(clk_source_info)
                    #print(clk_info[clk_info_index["src0"]])
                    #print("*********")
                    if clk_info[clk_info_index["src0"]] in clk_source_info :
                        clk_source_temp = clk_source_info.split(",")
                        clk_source_name = clk_source_temp[0]
                        clk_source_path = clk_source_temp[1]
                        #print("&&&&&&&&&&")
                        #print(clk_source_name)
                        #print(clk_source_path) 
                        print_line.append("# ----------------------------------------------------------------------")
                        master_clock_flag = 0
                        for master_clock in sdc_all_clk_source :
                            if clk_source_name in master_clock : 
                                master_clock_flag = 1
                        if master_clock_flag == 1 :
                            print_line.append("# generated clock for "+clk_info[clk_info_index["name"]]+" icg frequency: "+clk_info[clk_info_index["note"]])
                            print_line.append("create_generated_clock -name "+clk_info[clk_info_index["name"]]+" -combinational \\")
                            all_clock.append(clk_info[clk_info_index["name"]])
                        else :
                            print_line.append("# generated clock for "+str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]]+" icg frequency: "+clk_info[clk_info_index["note"]])
                            print_line.append("create_generated_clock -name "+str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]]+" -combinational \\")
                            all_clock.append(str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]])
                        clock_source = clk_source_path.strip("source ")
                        print_line.append("    -source ["+clock_source+"] \\")
                        print_line.append("    -edges {1 2 3} [get_pins {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_icg/u_dontouch_icg/Q}] \\")
                        print_line.append("     -master_clock [get_clocks {"+clk_source_name+"}] -add")
                        master_clock_flag = 0
                        for master_clock in sdc_all_clk_source :
                            if clk_source_name in master_clock : 
                                master_clock_flag = 1
                        if master_clock_flag == 1 :
                            set_clk_info(clk_info_index, top_info_index, print_line, top_corpus, clk_info[clk_info_index["name"]])
                        else :
                            set_clk_info(clk_info_index, top_info_index, print_line, top_corpus, str(clk_source_name.replace(clk_info[clk_info_index["src0"]], ""))+clk_info[clk_info_index["name"]])
   

    if sdc_empty == False :
        for sdc_info in sdc_corpus :
            if sdc_info[1] == "G" :
                print_line.append("# ----------------------------------------------------------------------")
                print_line.append("# generated clock for "+sdc_info[0]+" frequency: "+clk_info[clk_info_index["note"]])
                print_line.append("create_generated_clock -name "+sdc_info[0]+" -combinational \\")
                all_clock.append(sdc_info[0])
                print_line.append("    -source ["+sdc_info[5]+"] \\")
                print_line.append("    -edges {"+sdc_info[2]+"} ["+design_hier+sdc_info[3]+"] \\")
                print_line.append("     -master_clock [get_clocks {"+sdc_info[4]+"}] -add")
                set_clk_info(clk_info_index, top_info_index, print_line, top_corpus, sdc_info[0])

    #for line in all_clock :
    #    print(line)

    print_line.append("")
    print_line.append("#=================================")
    print_line.append("# false path for crg ctrl")
    print_line.append("#=================================")

    print_line.append("set_false_path -through [get_pins -of_objects {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_apb_reg} -filter \"direction==in && full_name=~*rst_n_status\"] ")
    print_line.append("set_false_path -through [get_pins -of_objects {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_apb_reg} -filter \"direction==in && full_name=~*clk_divider_status[*]\"]")
    print_line.append("set_false_path -through [get_pins -of_objects {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_apb_reg} -filter \"direction==out && full_name=~*clk_ea\"]") 
    print_line.append("set_false_path -through [get_pins -of_objects {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_apb_reg} -filter \"direction==in && full_name=~*clk_ea_status\"]")
    print_line.append("set_false_path -through [get_pins -of_objects {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_apb_reg} -filter \"direction==in && full_name=~*clk0_sel\"]")
    print_line.append("set_false_path -through [get_pins -of_objects {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_apb_reg} -filter \"direction==in && full_name=~*clk1_sel\"]")
    print_line.append("set_false_path -through [get_pins -of_objects {"+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_apb_reg} -filter \"direction==in && full_name=~*sel_done\"]")

#    for clk_info in clk_corpus :
#        if clk_info[clk_info_index["attr"]] == "output" or clk_info[clk_info_index["attr"]] == "na" :
#            if pd.isna(clk_info[clk_info_index["sel"]]) == False :
#                print_line.append("set_false_path -through [get_pins "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/sel]")
#                print_line.append("set_false_path -through [get_pins "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/clk0_sel]")
#                print_line.append("set_false_path -through [get_pins "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/clk1_sel]")
#                print_line.append("set_false_path -through [get_pins "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/sel_done]")
#            if pd.isna(clk_info[clk_info_index["div"]]) == False :
#                count = 0
#                while count < clk_info[clk_info_index["div_width"]] :
#                    print_line.append("set_false_path -through [get_pins "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_div_sync/data_in["+str(count)+"]]")
#                    count = count + 1
#                print_line.append("set_false_path -through [get_pins "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_div_sync/datain_en]")
#                print_line.append("")
#                count = 0
#                while count < clk_info[clk_info_index["div_width"]] :
#                    print_line.append("set_false_path -through [get_pins "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_divider/divider_status["+str(count)+"]]")
#                    count = count + 1
#                #print_line.append("set_false_path -through [get_pins "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_divider/divider_done]")
#                #print_line.append("set_false_path -through [get_pins "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_divider_req_done_sync/dst_sync_ack]")
#            if clk_info[clk_info_index["icg"]] == "Y" :
#                print_line.append("set_false_path -through [get_pins "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_icg_sync/data_s[0]]")
#            print_line.append("")

    for rst_info in rst_corpus :
        if rst_info[rst_info_index["areset_relax_en"]] == "Y" :
            print_line.append("set_multicycle_path -setup 2 -from [get_pins "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen/u_"+rst_info[rst_info_index["name"]]+"_test_mux/rstn_out]")
            print_line.append("set_multicycle_path -hold 1 -from [get_pins "+design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen/u_"+rst_info[rst_info_index["name"]]+"_test_mux/rstn_out]")
    print_line.append("")
    print_line.append("")
    print_line.append("#===================")
    print_line.append("# async clock groups")
    print_line.append("#===================")
    #print_line.append("set_clock_groups -asynchronous -group {")
    count = 0
   
    clk_corpus_group0 = copy.deepcopy(clk_corpus)
    clk_corpus_group1 = copy.deepcopy(clk_corpus)
    for clk_info in clk_corpus_group0 :
        if (pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False or "source" in str(clk_info[clk_info_index["clock_source"]]) or clk_info[clk_info_index["icg"]] == "Y") and clk_info[clk_info_index["name"]] != "nan" :
            #print("################")
            #print(clk_info[clk_info_index["name"]]+","+clk_info[clk_info_index["clock_group0"]])
            if count == 0 :
                print_line.append("set_clock_groups -name "+top_corpus[top_info_index["design_name"]][1]+"_group -asynchronous \\")
                print_line.append("                               -group {"+clk_info[clk_info_index["name"]])
            else :
                print_line.append("                               -group {"+clk_info[clk_info_index["name"]])
            clk_group = clk_info[clk_info_index["clock_group0"]]
            clk_name = clk_info[clk_info_index["name"]]
            #print(clk_group)
            for clk_info in clk_corpus_group0 :
                if pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False or "source" in str(clk_info[clk_info_index["clock_source"]]) or clk_info[clk_info_index["icg"]] == "Y" :
                    if clk_info[clk_info_index["clock_group0"]] == clk_group and clk_name != clk_info[clk_info_index["name"]] : #and clk_info[clk_info_index["name"]] not in  print_line[-1] :
                        print_line[-1] = print_line[-1]+" \\\n                                       "+clk_info[clk_info_index["name"]]
                        #print("**************************")
                        #print(clk_info[clk_info_index["name"]]+","+clk_info[clk_info_index["clock_group0"]])
                        #print_line[-1] = print_line[-1]+"} \\"
                        for i in clk_info :
                            clk_info[clk_info.index(i)] = "nan"

            print_line[-1] = print_line[-1]+"} \\"
            count = count + 1
        #print(clk_corpus_group0)

    print_line[-1] = print_line[-1].replace("\\", "")
    count = 0
    print_line.append("")

#    for group_info in clk_corpus_group1 :
#        #print(group_info)
#        #if (pd.isna(group_info[2]) == False or pd.isna(group_info[5]) == False or group_info[9] == "Y") and group_info[1] != "nan" :
#        if pd.isna(group_info[clk_info_index["div"]]) == True and pd.isna(group_info[clk_info_index["sel"]]) == True and pd.isna(group_info[clk_info_index["icg"]]) == True and pd.isna(clk_info[clk_info_index["src0"]]) == False  and pd.isna(group_info[clk_info_index["clock_group1"]]) == False :
#            #print(group_info[clk_info_index["name"]])
#            continue
#        else :
#            if pd.isna(group_info[clk_info_index["clock_group1"]]) == False :
#                #print("################")
#                #print(group_info[1]+","+group_info[clk_info_index["clock_group1"]])
#                if count == 0 :
#                    print_line.append("set_clock_groups -asynchronous -group {"+group_info[1])
#                else :
#                    print_line.append("                               -group {"+group_info[1])
#                clk_group = group_info[clk_info_index["clock_group1"]]
#                clk_name = group_info[1]
#                #print(clk_group)
#                for group_info in clk_corpus_group1 :
#                    #if pd.isna(group_info[2]) == False or pd.isna(group_info[5]) == False or group_info[9] == "Y" :
#                    if group_info[clk_info_index["clock_group1"]] == clk_group and clk_name != group_info[1] : #and group_info[1] not in  print_line[-1] :
#                        print_line[-1] = print_line[-1]+" "+group_info[1]
#                        #print("**************************")
#                        #print(group_info[1]+","+group_info[clk_info_index["clock_group1"]])
#                        #print_line[-1] = print_line[-1]+"} \\"
#                        for i in group_info :
#                            group_info[group_info.index(i)] = "nan"
#
#                print_line[-1] = print_line[-1]+"} \\"
#                count = count + 1
#            #print(clk_corpus_group1)               
#    print_line[-1] = print_line[-1].replace("\\", "")
#    print_line.append("")
#    #print_line.append("set_input_transition -rise -max 0.100 [all_inputs]")
#    #print_line.append("set_input_transition -rise -min 0.100 [all_inputs]\n")
#    #print_line.append("set_load -pin_load -max 0.5 [all_outputs]")
#    #print_line.append("set_load -pin_load -min 0.5 [all_outputs]")
#    clk_src_name = []
#    for clk_src in clock_source_list :
#        clk_source_temp = clk_src.split(",")
#        clk_source_name = clk_source_temp[0]
#        clk_source_path = clk_source_temp[1]
#        clk_src_name.append(clk_source_name.replace("_clk", ""))
#
#    #print(clk_src_name)
#    #for line in all_clock :
#    #    print(line)
#
#
#    count = 0
#    all_clock_cp = all_clock
#    for start_str in clk_src_name :
#        if count == 0 :
#            print_line.append("set_clock_groups -physically_exclusive -group {")
#            for clk in all_clock :
#                if clk.startswith(start_str) == True :
#                    print_line[-1] = print_line[-1]+" "+clk
#            #all_clock[all_clock.index(clk)] = "nan"
#        else :
#            print_line.append("                                       -group {")
#            for clk in all_clock :
#                if clk.startswith(start_str) == True :
#                    print_line[-1] = print_line[-1]+" "+clk
#            #all_clock[all_clock.index(clk)] = "nan"
#        
#        print_line[-1] = print_line[-1]+"} \\"
#        count = count + 1
#
#    print_line[-1] = print_line[-1].replace("\\", "")
#
    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')

    fp.close()

# }}}

def crg_gen_xml(rst_info_index, gen_filepath, top_corpus, rst_corpus, rst_ser, clk_info_index, top_info_index, clk_corpus, clk_ser, reg_corpus, reg_ser, reg_empty, intp_empty, intp_corpus, intp_ser): #{{{
    fp = open(gen_filepath+top_corpus[top_info_index["design_name"]][1].upper()+".xml", "w") 
    print_line = []

    print_line.append('<?xml version="1.0" ?>')
    print_line.append('<spirit:component xmlns:spirit="http://www.cygnusemi.com">')
    print_line.append("  <spirit:name>"+top_corpus[top_info_index["design_name"]][1].upper()+"</spirit:name>")
    print_line.append("  <spirit:version>1.0</spirit:version>")
    print_line.append("  <spirit:addressBlock>")
    print_line.append("    <spirit:name>"+top_corpus[top_info_index["design_name"]][1].upper()+"</spirit:name>")
    print_line.append("    <spirit:description>"+top_corpus[top_info_index["design_name"]][1].upper()+" regfile</spirit:description>")
    print_line.append("    <spirit:baseAddress>0x0000</spirit:baseAddress>")
    print_line.append("    <spirit:range>0x10000</spirit:range>")
    print_line.append("    <spirit:width>32</spirit:width>")
    print_line.append("    <spirit:byteVisit>1</spirit:byteVisit>")
    print_line.append("    <spirit:usage>register</spirit:usage>")
    if top_corpus[top_info_index["protocol"]][1] == "dab":
        print_line.append("    <spirit:protocol>dab</spirit:protocol>")
    elif top_corpus[top_info_index["protocol"]][1] == "apb":
        print_line.append("    <spirit:protocol>apb</spirit:protocol>")
    elif top_corpus[top_info_index["protocol"]][1] == "ahb":
        print_line.append("    <spirit:protocol>ahb</spirit:protocol>")

    count = 0
    clk_sheet_cnt = 0
    for clk_info in clk_corpus:
        if clk_info[clk_info_index["attr"]] == "output" or clk_info[clk_info_index["attr"]] == "na" or clk_info[clk_info_index["attr"]] == "internal" :
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False :
                if clk_info[clk_info_index["icg_dflt"]] == "Y" :
                    clk_ctrl_bit0 = "01"
                else :
                    clk_ctrl_bit0 = "00"
                clk_ctrl_bit8 = "00"
                #if pd.isna(clk_info[clk_info_index["div"]]) == False :
                #    clk_ctrl_bit_high = str(hex(int(clk_info[clk_info_index["div_dflt"]]))[2:])
                #else :
                clk_ctrl_bit_high = "00"
                reg_addr = hex(count*4)
                if count != 0:
                    print_line.append("    </spirit:register>")
                print_line.append("    <spirit:register>")
                print_line.append("      <spirit:name>"+clk_info[clk_info_index["name"]]+"_ctrl</spirit:name>")
                print_line.append("      <spirit:description>"+clk_info[clk_info_index["name"]]+" control register</spirit:description>")
                print_line.append("      <spirit:addressOffset>"+reg_addr+"</spirit:addressOffset>")
                print_line.append("      <spirit:size>32</spirit:size>")
                print_line.append("      <spirit:access>RW</spirit:access>")
                print_line.append("      <spirit:reset>")
                print_line.append("        <spirit:value>"+str(hex(int((clk_ctrl_bit_high + clk_ctrl_bit8 + clk_ctrl_bit0), 16)))+"</spirit:value>")  
                print_line.append("      </spirit:reset>")
                count += 1
            if clk_info[clk_info_index["icg"]] == "Y":
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_ea</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" icg enable, PRTC_16_16_1'h1</spirit:description>")
                print_line.append("        <spirit:bitOffset>0</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                print_line.append("        <spirit:access>RW</spirit:access>")
                print_line.append("        <spirit:lockOffset>16</spirit:lockOffset>")
                print_line.append("        <spirit:lockWidth>1</spirit:lockWidth>")
                print_line.append("        <spirit:lockValue>0x1</spirit:lockValue>")
                print_line.append("      </spirit:field>")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_divider_ea_req</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" divider enable request, PRTC_20_20_1'h1</spirit:description>")
                print_line.append("        <spirit:bitOffset>4</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                print_line.append("        <spirit:access>W1T</spirit:access>")
                print_line.append("        <spirit:lockOffset>20</spirit:lockOffset>")
                print_line.append("        <spirit:lockWidth>1</spirit:lockWidth>")
                print_line.append("        <spirit:lockValue>0x1</spirit:lockValue>")
                print_line.append("      </spirit:field>")
            if pd.isna(clk_info[clk_info_index["sel"]]) == False :
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_sel</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" select, PRTC_24_24_1'h1</spirit:description>")
                print_line.append("        <spirit:bitOffset>8</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                print_line.append("        <spirit:access>RW</spirit:access>")
                print_line.append("        <spirit:lockOffset>24</spirit:lockOffset>")
                print_line.append("        <spirit:lockWidth>1</spirit:lockWidth>")
                print_line.append("        <spirit:lockValue>0x1</spirit:lockValue>")
                print_line.append("      </spirit:field>")
            if clk_info[clk_info_index["icg"]] == "Y":
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_ea_lock_fld</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" icg enable lock, PRTC_16_16_1'h1</spirit:description>")
                print_line.append("        <spirit:bitOffset>16</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                print_line.append("        <spirit:access>W1T</spirit:access>")
                print_line.append("      </spirit:field>")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_divider_ea_req_lock_fld</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" divider enable request lock, PRTC_20_20_1'h1</spirit:description>")
                print_line.append("        <spirit:bitOffset>20</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                print_line.append("        <spirit:access>W1T</spirit:access>")
                print_line.append("      </spirit:field>")
            if pd.isna(clk_info[clk_info_index["sel"]]) == False :
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_sel_lock_fld</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" select lock, PRTC_24_24_1'h1</spirit:description>")
                print_line.append("        <spirit:bitOffset>24</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                print_line.append("        <spirit:access>W1T</spirit:access>")
                print_line.append("      </spirit:field>")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:
                reg_addr = hex(count*4)
                lock_en = 0b1111111111111111
                lock_value = lock_en >> (int(16 - clk_info[clk_info_index["div_width"]]))
                #print(str(16 - clk_info[clk_info_index["div_width"]]))
                #print("lock_value is : "+str(lock_en >> 12))
                #print("lock_value is : "+str(lock_value))
                if count != 0:
                    print_line.append("    </spirit:register>")
                print_line.append("    <spirit:register>")
                print_line.append("      <spirit:name>"+clk_info[clk_info_index["name"]]+"_divider</spirit:name>")
                print_line.append("      <spirit:description>"+clk_info[clk_info_index["name"]]+" divider</spirit:description>")
                print_line.append("      <spirit:addressOffset>"+reg_addr+"</spirit:addressOffset>")
                print_line.append("      <spirit:size>32</spirit:size>")
                print_line.append("      <spirit:access>RW</spirit:access>")
                print_line.append("      <spirit:reset>")
                print_line.append("        <spirit:value>"+str(hex(int(clk_info[clk_info_index["div_dflt"]])))+"</spirit:value>")  
                print_line.append("      </spirit:reset>")
                count += 1
            if pd.isna(clk_info[clk_info_index["div"]]) == False :
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_divider</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" divider, PRTC_"+str(int(clk_info[clk_info_index["div_width"]] + 16))+"_16_"+str(int(clk_info[clk_info_index["div_width"]]))+"'h"+str(hex(lock_value)).strip("0x")+"</spirit:description>")
                print_line.append("        <spirit:bitOffset>0</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>"+str(int(clk_info[clk_info_index["div_width"]]))+"</spirit:bitWidth>")
                print_line.append("        <spirit:access>RW</spirit:access>")
                print_line.append("        <spirit:lockOffset>16</spirit:lockOffset>")
                print_line.append("        <spirit:lockWidth>"+str(int(clk_info[clk_info_index["div_width"]]))+"</spirit:lockWidth>")
                print_line.append("        <spirit:lockValue>"+str(hex(lock_value))+"</spirit:lockValue>")
                print_line.append("      </spirit:field>")
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_divider_lock_fld</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" divider lock, PRTC_"+str(int(clk_info[clk_info_index["div_width"]] + 16))+"_16_"+str(int(clk_info[clk_info_index["div_width"]]))+"'h"+str(hex(lock_value)).strip("0x")+"</spirit:description>")
                print_line.append("        <spirit:bitOffset>16</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>"+str(int(clk_info[clk_info_index["div_width"]]))+"</spirit:bitWidth>")
                print_line.append("        <spirit:access>W1T</spirit:access>")
                print_line.append("      </spirit:field>")
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False:
                reg_addr = hex(count*4)
                if count != 0:
                    print_line.append("    </spirit:register>")
                print_line.append("    <spirit:register>")
                print_line.append("      <spirit:name>"+clk_info[clk_info_index["name"]]+"_status</spirit:name>")
                print_line.append("      <spirit:description>"+clk_info[clk_info_index["name"]]+" status</spirit:description>")
                print_line.append("      <spirit:addressOffset>"+reg_addr+"</spirit:addressOffset>")
                print_line.append("      <spirit:size>32</spirit:size>")
                print_line.append("      <spirit:access>RO</spirit:access>")
                print_line.append("      <spirit:reset>")
                print_line.append("        <spirit:value>0x0</spirit:value>")  
                print_line.append("      </spirit:reset>")
                count += 1
            if clk_info[clk_info_index["icg"]] == "Y":
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_ea_status</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" icg enable status</spirit:description>")
                print_line.append("        <spirit:bitOffset>0</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                print_line.append("        <spirit:access>RO</spirit:access>")
                print_line.append("      </spirit:field>")
            if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_sel_clk0_sel</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" select clk1 status</spirit:description>")
                print_line.append("        <spirit:bitOffset>8</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                print_line.append("        <spirit:access>RO</spirit:access>")
                print_line.append("      </spirit:field>")
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_sel_clk1_sel</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" select clk1 status</spirit:description>")
                print_line.append("        <spirit:bitOffset>9</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                print_line.append("        <spirit:access>RO</spirit:access>")
                print_line.append("      </spirit:field>")
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_sel_done</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" select done status</spirit:description>")
                print_line.append("        <spirit:bitOffset>10</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                print_line.append("        <spirit:access>RO</spirit:access>")
                print_line.append("      </spirit:field>")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:    
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_divider_done</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" divider done status</spirit:description>")
                print_line.append("        <spirit:bitOffset>12</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                print_line.append("        <spirit:access>RO</spirit:access>")
                print_line.append("      </spirit:field>")
                print_line.append("      <spirit:field>")
                print_line.append("        <spirit:name>"+clk_info[clk_info_index["name"]]+"_divider_status</spirit:name>")
                print_line.append("        <spirit:description>"+clk_info[clk_info_index["name"]]+" divider status</spirit:description>")
                print_line.append("        <spirit:bitOffset>16</spirit:bitOffset>")
                print_line.append("        <spirit:bitWidth>"+str(int(clk_info[clk_info_index["div_width"]]))+"</spirit:bitWidth>")
                print_line.append("        <spirit:access>RO</spirit:access>")
                print_line.append("      </spirit:field>")
        clk_sheet_cnt = clk_sheet_cnt + 1
        if clk_sheet_cnt > clk_ser.index.max() :
            print_line.append("    </spirit:register>")            

    #print(clk_ser.index.max())
    #print_line.append("\n")
    rst_reg_num = []
    rst_reg_bit_lc = []
    for rst_info in rst_corpus:
        if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
            continue
        elif rst_info[rst_info_index["soft_src"]] == "SOFT":
            rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
            rst_reg_num.append(rst_info_reg_lc[0])
            rst_reg_bit_lc.append(rst_info_reg_lc[1])
    
    #print(rst_reg_num)
    rst_reg_num = list(set(rst_reg_num))
    rst_reg_num = list(map(int, rst_reg_num))
    rst_reg_num.sort()
    rst_reg_num = list(map(str, rst_reg_num))
    #rst_reg_num = np.unique(rst_reg_num)
    #rst_reg_num = np.sort(rst_reg_num)
    
    #print(rst_reg_num)
    #print(type(rst_reg_num))
    #print(rst_reg_bit_lc)

    rst_reg_name = []
    for rst_info in rst_corpus:
        if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
            continue
        elif rst_info[rst_info_index["soft_src"]] == "SOFT":
            rst_reg_name.append(rst_info[rst_info_index["reg_name"]])

    reg_name = []
    for item in rst_reg_name :
        if not item in reg_name :
            reg_name.append(item)	

    #print(reg_name)

    count = 0
    idx = 0
    for idx in rst_reg_num:
        reg_addr = hex(int(idx)*4 + int(top_corpus[top_info_index["rst_gen_addr_ofst"]][1], 16))
        if count != 0:
            print_line.append("    </spirit:register>")
        print_line.append("    <spirit:register>")
        print_line.append("      <spirit:name>"+reg_name[int(count)]+"</spirit:name>")
        print_line.append("      <spirit:description>"+reg_name[int(count)]+"</spirit:description>")
        print_line.append("      <spirit:addressOffset>"+reg_addr+"</spirit:addressOffset>")
        print_line.append("      <spirit:size>32</spirit:size>")
        print_line.append("      <spirit:access>RW</spirit:access>")
        print_line.append("      <spirit:reset>")
        #if rst_info[rst_info_index["soft_dflt"]] == "N" :
        rest_value_bin = "" 
        for rst_info in rst_corpus:
            #print(rst_info[rst_info_index["name"]])
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(count)]:
                    if rst_info[rst_info_index["soft_dflt"]] == "N" :
                        rest_value_bin = "1" + rest_value_bin
                    else :
                        rest_value_bin = "0" + rest_value_bin
            else :
                rest_value_bin = "0" + rest_value_bin
        #print(rest_value_bin) 
        #print(int(rest_value_bin, 2)) 
        print_line.append("        <spirit:value>"+str(hex(int(rest_value_bin, 2)))+"</spirit:value>")  
        print_line.append("      </spirit:reset>")

        #print(count)

        for rst_info in rst_corpus:
            #print(rst_info[rst_info_index["name"]])
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(count)]:
                    if pd.isna(rst_info[rst_info_index["lock_bit_offset"]]) == False :
                        #print(str(rst_corpus.index(rst_info))+"########################################")
                        lock_bitoffset0 = str(rst_info[rst_info_index["lock_bit_offset"]]).split('[', 1)
                        #print(bitoffset0)
                        lock_bitoffset1 = lock_bitoffset0[1].split(':', 1)
                        lock_bitoffset2 = lock_bitoffset1[1].split(']', 1)
                        lock_field_msb = lock_bitoffset1[0]
                        lock_field_lsb = lock_bitoffset2[0]
                        #print(field_msb, field_lsb)
                    #if rst_info[rst_info_index["soft_dflt"]] == "N" :
                    print_line.append("      <spirit:field>")
                    print_line.append("        <spirit:name>"+rst_info[rst_info_index["name"]]+"_sftrstn</spirit:name>")
                    #if pd.isna(rst_info[rst_info_index["lock_bit_offset"]]) == False :
                    print_line.append("        <spirit:description>"+rst_info[rst_info_index["name"]]+"_sftrstn, PRTC_"+str(int(rst_info_reg_lc[1])+16)+"_"+str(int(rst_info_reg_lc[1])+16)+"_0x1</spirit:description>")
                    #else :
                    #    print_line.append("        <spirit:description>"+rst_info[rst_info_index["name"]]+"_sftrstn</spirit:description>")
                    print_line.append("        <spirit:bitOffset>"+rst_info_reg_lc[1]+"</spirit:bitOffset>")
                    print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                    print_line.append("        <spirit:access>RW</spirit:access>")
                    #if pd.isna(rst_info[rst_info_index["lock_bit_offset"]]) == False :
                    print_line.append("        <spirit:lockOffset>"+str(int(rst_info_reg_lc[1])+16)+"</spirit:lockOffset>")
                    print_line.append("        <spirit:lockWidth>1</spirit:lockWidth>")
                    print_line.append("        <spirit:lockValue>0x1</spirit:lockValue>")
                    print_line.append("      </spirit:field>")
            if rst_info[rst_info_index["soft_src"]] == "SOFT" :#and pd.isna(rst_info[rst_info_index["lock_bit_offset"]]) == False :
                if rst_info_reg_lc[0] == rst_reg_num[int(count)] and "        <spirit:name>"+rst_info[rst_info_index["name"]]+"_lock_fld</spirit:name>" not in print_line :
                    print_line.append("      <spirit:field>")
                    print_line.append("        <spirit:name>"+rst_info[rst_info_index["name"]]+"_lock_fld</spirit:name>")
                    print_line.append("        <spirit:description>"+rst_info[rst_info_index["name"]]+" lock, PRTC_"+str(int(rst_info_reg_lc[1])+16)+"_"+str(int(rst_info_reg_lc[1])+16)+"_0x1</spirit:description>")
                    print_line.append("        <spirit:bitOffset>"+str(int(rst_info_reg_lc[1])+16)+"</spirit:bitOffset>")
                    print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                    print_line.append("        <spirit:access>W1T</spirit:access>")
                    print_line.append("      </spirit:field>")

        count += 1
    print_line.append("    </spirit:register>")

    count = 0
    reg_addr_ofst = idx
    rst_status_count = 0
    for idx in rst_reg_num:
        reg_addr = hex((int(idx))*4 + int(top_corpus[top_info_index["rst_status_addr_ofst"]][1], 16)+4)
        #print("reg_addr_ofst is :" +reg_addr_ofst)
        #print("reg_addr is :" +reg_addr)
        #print("idx is :" +idx)
        if count != 0:
            print_line.append("    </spirit:register>")
        print_line.append("    <spirit:register>")
        print_line.append("      <spirit:name>"+reg_name[int(count)]+"_status</spirit:name>")
        print_line.append("      <spirit:description>"+reg_name[int(count)]+"_status</spirit:description>")
        print_line.append("      <spirit:addressOffset>"+reg_addr+"</spirit:addressOffset>")
        print_line.append("      <spirit:size>32</spirit:size>")
        print_line.append("      <spirit:access>RO</spirit:access>")
        print_line.append("      <spirit:reset>")
        print_line.append("        <spirit:value>0x0</spirit:value>")  
        print_line.append("      </spirit:reset>")
        #print(count)
        count += 1

        for rst_info in rst_corpus:
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(rst_status_count)]:
                    print_line.append("      <spirit:field>")
                    print_line.append("        <spirit:name>"+rst_info[rst_info_index["name"]]+"_status</spirit:name>")
                    print_line.append("        <spirit:description>"+rst_info[rst_info_index["name"]]+"_status</spirit:description>")
                    print_line.append("        <spirit:bitOffset>"+rst_info_reg_lc[1]+"</spirit:bitOffset>")
                    print_line.append("        <spirit:bitWidth>1</spirit:bitWidth>")
                    print_line.append("        <spirit:access>RO</spirit:access>")
                    #print_line.append("        <spirit:lockOffset>8</spirit:lockOffset>")
                    #print_line.append("        <spirit:lockWidth>1</spirit:lockWidth>")
                    #print_line.append("        <spirit:lockValue>1</spirit:lockValue>")
                    print_line.append("      </spirit:field>")
        #if rst_status_count > int(idx) :
        #    print_line.append("    </spirit:register>")
        rst_status_count += 1
    print_line.append("    </spirit:register>")
    #print(rst_ser.index.max())

    if reg_empty == False:
        reg_xml_gen(top_info_index, print_line, reg_corpus, reg_ser, top_corpus)

    if intp_empty == False:
        intp_xml_gen(top_info_index, print_line, intp_corpus, intp_ser, top_corpus)

    print_line.append("  </spirit:addressBlock>")
    print_line.append("</spirit:component>")

    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')

    fp.close()

#}}}

def crg_gen_yml(rst_info_index, gen_filepath, top_corpus, rst_corpus, rst_ser, clk_info_index, top_info_index, clk_corpus, clk_ser, reg_corpus, reg_ser, reg_empty, intp_empty, intp_corpus, intp_ser): #{{{
    fp = open(gen_filepath+top_corpus[top_info_index["design_name"]][1].upper()+".yml", "w") 
    print_line = []

#    print_line.append("blocks:")
    print_line.append("name: "+top_corpus[top_info_index["design_name"]][1].upper())
    print_line.append("bytes: 4")
    print_line.append("offset: 0x000")
    print_line.append("registers:")

    count = 0
    for clk_info in clk_corpus:
        if clk_info[clk_info_index["attr"]] == "output" or clk_info[clk_info_index["attr"]] == "na" or clk_info[clk_info_index["attr"]] == "internal" :
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False :
                if clk_info[clk_info_index["icg_dflt"]] == "Y" :
                    clk_ctrl_bit0 = "01"
                else :
                    clk_ctrl_bit0 = "00"
                clk_ctrl_bit8 = "00"
                #if pd.isna(clk_info[clk_info_index["div"]]) == False :
                #    clk_ctrl_bit_high = str(hex(int(clk_info[clk_info_index["div_dflt"]]))[2:])
                #else :
                clk_ctrl_bit_high = "00"
                reg_addr = hex(count*4)
                print_line.append("  - name: "+clk_info[clk_info_index["name"]]+"_ctrl")
                print_line.append("    description: \""+clk_info[clk_info_index["name"]]+" control register\"")
                print_line.append("    offset: "+reg_addr)
                print_line.append("    fields:")

                count += 1
            if clk_info[clk_info_index["icg"]] == "Y":
                if clk_info[clk_info_index["icg_dflt"]] == "Y" :
                    print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_ea, lsb: 0, bits: 1, access: rw, reset: 0x1, lock_lsb: 16, lock_bits: 1, lock_value: 0x1, description: \""+clk_info[clk_info_index["name"]]+" icg enable, PRTC_16_16_1'h1\"}")
                else :
                    print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_ea, lsb: 0, bits: 1, access: rw, reset: 0x0, lock_lsb: 16, lock_bits: 1, lock_value: 0x1, description: \""+clk_info[clk_info_index["name"]]+" icg enable, PRTC_16_16_1'h1\"}")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:
               print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_divider_ea_req, lsb: 4, bits: 1, access: w1t, reset: 0x0, lock_lsb: 20, lock_bits: 1, lock_value: 0x1, description: \""+clk_info[clk_info_index["name"]]+" divider enable request, PRTC_20_20_1'h1\"}")
            if pd.isna(clk_info[clk_info_index["sel"]]) == False :
                if clk_info[clk_info_index["mux_dflt"]] == 1 :
                    print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_sel, lsb: 8, bits: 1, access: rw, reset: 0x1, lock_lsb: 24, lock_bits: 1, lock_value: 0x1, description: \""+clk_info[clk_info_index["name"]]+" select, PRTC_24_24_1'h1\"}")
                else :
                    print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_sel, lsb: 8, bits: 1, access: rw, reset: 0x0, lock_lsb: 24, lock_bits: 1, lock_value: 0x1, description: \""+clk_info[clk_info_index["name"]]+" select, PRTC_24_24_1'h1\"}")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:
                reg_addr = hex(count*4)
                lock_en = 0b1111111111111111
                lock_value = lock_en >> (int(16 - clk_info[clk_info_index["div_width"]]))
                #print(str(16 - clk_info[clk_info_index["div_width"]]))
                #print("lock_value is : "+str(lock_en >> 12))
                #print("lock_value is : "+str(lock_value))
                print_line.append("  - name: "+clk_info[clk_info_index["name"]]+"_divider")
                print_line.append("    description: \""+clk_info[clk_info_index["name"]]+" divider\"")
                print_line.append("    offset: "+reg_addr)
                print_line.append("    fields:")
                count += 1
            if pd.isna(clk_info[clk_info_index["div"]]) == False :
                print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_divider, lsb: 0, bits: "+str(int(clk_info[clk_info_index["div_width"]]))+", access: rw, reset: "+str(hex(int(clk_info[clk_info_index["div_dflt"]])))+", lock_lsb: 16, lock_bits: "+str(int(clk_info[clk_info_index["div_width"]]))+", lock_value: "+str(hex(lock_value))+", description: \""+clk_info[clk_info_index["name"]]+" divider, PRTC_"+str(int(clk_info[clk_info_index["div_width"]] + 15))+"_16_"+str(int(clk_info[clk_info_index["div_width"]]))+"'h"+str(hex(lock_value)).strip("0x")+"\"}")
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False:
                reg_addr = hex(count*4)
                print_line.append("  - name: "+clk_info[clk_info_index["name"]]+"_status")
                print_line.append("    description: \""+clk_info[clk_info_index["name"]]+" status\"")
                print_line.append("    offset: "+reg_addr)
                print_line.append("    fields:")
                count += 1
            if clk_info[clk_info_index["icg"]] == "Y":
                if clk_info[clk_info_index["icg_dflt"]] == "Y" :
                    print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_ea_status, lsb: 0, bits: 1, access: ro, reset: 0x1, description: \""+clk_info[clk_info_index["name"]]+" icg enable status\"}")
                else :
                    print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_ea_status, lsb: 0, bits: 1, access: ro, reset: 0x0, description: \""+clk_info[clk_info_index["name"]]+" icg enable status\"}")
            if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                if clk_info[clk_info_index["mux_dflt"]] == 1 :
                    print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_sel_clk0_sel, lsb: 8, bits: 1, access: ro, reset: 0x0, description: \""+clk_info[clk_info_index["name"]]+" select clk1 status\"}")
                    print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_sel_clk1_sel, lsb: 9, bits: 1, access: ro, reset: 0x1, description: \""+clk_info[clk_info_index["name"]]+" select clk1 status\"}")
                else :
                    print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_sel_clk0_sel, lsb: 8, bits: 1, access: ro, reset: 0x1, description: \""+clk_info[clk_info_index["name"]]+" select clk1 status\"}")
                    print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_sel_clk1_sel, lsb: 9, bits: 1, access: ro, reset: 0x0, description: \""+clk_info[clk_info_index["name"]]+" select clk1 status\"}")
                print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_sel_done, lsb: 10, bits: 1, access: ro, reset: 0x1, description: \""+clk_info[clk_info_index["name"]]+" select done status\"}")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:    
                print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_divider_done, lsb: 12, bits: 1, access: ro, reset: 0x0, description: \""+clk_info[clk_info_index["name"]]+" divider done status\"}")
                print_line.append("      - { name: "+clk_info[clk_info_index["name"]]+"_divider_status, lsb: 16, bits: "+str(int(clk_info[clk_info_index["div_width"]]))+", access: ro, reset: "+str(hex(int(clk_info[clk_info_index["div_dflt"]])))+", description: \""+clk_info[clk_info_index["name"]]+" divider status\"}")

    #print(clk_ser.index.max())
    #print_line.append("\n")
    rst_reg_num = []
    rst_reg_bit_lc = []
    for rst_info in rst_corpus:
        if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
            continue
        elif rst_info[rst_info_index["soft_src"]] == "SOFT":
            rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
            rst_reg_num.append(rst_info_reg_lc[0])
            rst_reg_bit_lc.append(rst_info_reg_lc[1])
    
    #print(rst_reg_num)
    rst_reg_num = list(set(rst_reg_num))
    rst_reg_num = list(map(int, rst_reg_num))
    rst_reg_num.sort()
    rst_reg_num = list(map(str, rst_reg_num))
    #rst_reg_num = np.unique(rst_reg_num)
    #rst_reg_num = np.sort(rst_reg_num)
    
    #print(rst_reg_num)
    #print(type(rst_reg_num))
    #print(rst_reg_bit_lc)

    rst_reg_name = []
    for rst_info in rst_corpus:
        if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
            continue
        elif rst_info[rst_info_index["soft_src"]] == "SOFT":
            rst_reg_name.append(rst_info[rst_info_index["reg_name"]])

    reg_name = []
    for item in rst_reg_name :
        if not item in reg_name :
            reg_name.append(item)	

    #print(reg_name)

    count = 0
    idx = 0
    for idx in rst_reg_num:
        reg_addr = hex(int(idx)*4 + int(top_corpus[top_info_index["rst_gen_addr_ofst"]][1], 16))

        print_line.append("  - name: "+reg_name[int(count)])
        print_line.append("    description: \""+reg_name[int(count)]+"\"")
        print_line.append("    offset: "+reg_addr)
        print_line.append("    fields:")
        #if rst_info[rst_info_index["soft_dflt"]] == "N" :
        rest_value_bin = "" 
        for rst_info in rst_corpus:
            #print(rst_info[rst_info_index["name"]])
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(count)]:
                    if rst_info[rst_info_index["soft_dflt"]] == "N" :
                        rest_value_bin = "1" + rest_value_bin
                    else :
                        rest_value_bin = "0" + rest_value_bin
            else :
                rest_value_bin = "0" + rest_value_bin
        #print(rest_value_bin) 
        #print(int(rest_value_bin, 2)) 

        #print(count)

        for rst_info in rst_corpus:
            #print(rst_info[rst_info_index["name"]])
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(count)]:
                    if pd.isna(rst_info[rst_info_index["lock_bit_offset"]]) == False :
                        #print(str(rst_corpus.index(rst_info))+"########################################")
                        lock_bitoffset0 = str(rst_info[rst_info_index["lock_bit_offset"]]).split('[', 1)
                        #print(bitoffset0)
                        lock_bitoffset1 = lock_bitoffset0[1].split(':', 1)
                        lock_bitoffset2 = lock_bitoffset1[1].split(']', 1)
                        lock_field_msb = lock_bitoffset1[0]
                        lock_field_lsb = lock_bitoffset2[0]
                        #print(field_msb, field_lsb)
                    if rst_info[rst_info_index["soft_dflt"]] == "N" :
                        print_line.append("      - { name: "+rst_info[rst_info_index["name"]]+"_sftrstn, lsb: "+rst_info_reg_lc[1]+", bits: 1, access: rw, reset: 0x1, lock_lsb: "+str(int(rst_info_reg_lc[1])+16)+", lock_bits: 1, lock_value: 0x1, description: \""+rst_info[rst_info_index["name"]]+"_sftrstn, PRTC_"+str(int(rst_info_reg_lc[1])+16)+"_"+str(int(rst_info_reg_lc[1])+16)+"_0x1\"}")
                    else :
                        print_line.append("      - { name: "+rst_info[rst_info_index["name"]]+"_sftrstn, lsb: "+rst_info_reg_lc[1]+", bits: 1, access: rw, reset: 0x0, lock_lsb: "+str(int(rst_info_reg_lc[1])+16)+", lock_bits: 1, lock_value: 0x1, description: \""+rst_info[rst_info_index["name"]]+"_sftrstn, PRTC_"+str(int(rst_info_reg_lc[1])+16)+"_"+str(int(rst_info_reg_lc[1])+16)+"_0x1\"}")
                    
        count += 1

    count = 0
    reg_addr_ofst = idx
    rst_status_count = 0
    for idx in rst_reg_num:
        reg_addr = hex((int(idx))*4 + int(top_corpus[top_info_index["rst_status_addr_ofst"]][1], 16))
        #print("reg_addr_ofst is :" +reg_addr_ofst)
        #print("reg_addr is :" +reg_addr)
        #print("idx is :" +idx)

        print_line.append("  - name: "+reg_name[int(count)]+"_status")
        print_line.append("    description: \""+reg_name[int(count)]+"_status\"")
        print_line.append("    offset: "+reg_addr)
        print_line.append("    fields:")
        count += 1

        for rst_info in rst_corpus:
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(rst_status_count)]:
                    if rst_info[rst_info_index["soft_dflt"]] == "N" :
                        print_line.append("      - { name: "+rst_info[rst_info_index["name"]]+"_status, lsb: "+rst_info_reg_lc[1]+", bits: 1, access: ro, reset: 0x1, description: \""+rst_info[rst_info_index["name"]]+"_status\"}")
                    else :
                        print_line.append("      - { name: "+rst_info[rst_info_index["name"]]+"_status, lsb: "+rst_info_reg_lc[1]+", bits: 1, access: ro, reset: 0x0, description: \""+rst_info[rst_info_index["name"]]+"_status\"}")
        #if rst_status_count > int(idx) :
        #    print_line.append("    </spirit:register>")
        rst_status_count += 1
    #print(rst_ser.index.max())

    if reg_empty == False:
        reg_yml_gen(top_info_index, print_line, reg_corpus, reg_ser, top_corpus, top_corpus[top_info_index["user_defined_reg_addr_ofst"]][1])

    if intp_empty == False:
        #reg_yml_gen(top_info_index, print_line, intp_corpus, intp_ser, top_corpus, top_corpus[top_info_index["user_defined_intp_addr_ofst"]][1])
        print_line.append("interrupts:")
        intp_yml_gen(top_info_index, print_line, intp_corpus, intp_ser, top_corpus)

    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')

    fp.close()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    yml2reg_py = os.path.join(script_dir, "yml2reg", "yml2reg.py")
    yml_file = os.path.abspath(gen_filepath+top_corpus[top_info_index["design_name"]][1].upper()+".yml")
    protocol = top_corpus[top_info_index["protocol"]][1]
    gen_regfile = "cd "+gen_filepath+" && python3 "+yml2reg_py+" "+yml_file+" "+protocol
    print(gen_regfile)
    os.system(gen_regfile)
#}}}

def crg_gen_note(top_corpus, rst_corpus, rst_ser, clk_corpus, clk_ser, reg_corpus, reg_ser, reg_empty): #{{{
    fp = open(top_corpus[top_info_index["design_name"]][1].upper()+".note", "w") 
    print_line = []

    print_line.append('// Component')
    print_line.append(top_corpus[top_info_index["design_name"]][1]+"      --  v1.0\n")
    print_line.append('// Block')
    if top_corpus[top_info_index["protocol"]][1] == "dab":
        print_line.append(top_corpus[top_info_index["design_name"]][1].upper()+"      --  0x0000:0xffff  --  "+top_corpus[top_info_index["design_name"]][1].upper()+" regfile       -- dab")
    elif top_corpus[top_info_index["protocol"]][1] == "apb":
        print_line.append(top_corpus[top_info_index["design_name"]][1].upper()+"      --  0x0000:0xffff  --  "+top_corpus[top_info_index["design_name"]][1].upper()+" regfile       -- apb")
    elif top_corpus[top_info_index["protocol"]][1] == "ahb":
        print_line.append(top_corpus[top_info_index["design_name"]][1].upper()+"      --  0x0000:0xffff  --  "+top_corpus[top_info_index["design_name"]][1].upper()+" regfile       -- ahb")
    print_line.append('// Register')
    
    count = 0
    for clk_info in clk_corpus:
        if clk_info[clk_info_index["attr"]] == "output" or clk_info[clk_info_index["attr"]] == "na" or clk_info[clk_info_index["attr"]] == "internal" :
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False:
                reg_addr = hex(count*4)
                print_line.append("\n")
                print_line.append(reg_addr+"    			--		RW		--		"+clk_info[clk_info_index["name"]]+"_ctrl			    --		[31:0]		--	"+clk_info[clk_info_index["name"]]+" control register")	
                count += 1
                #print(count)
            if clk_info[clk_info_index["icg"]] == "Y":
                if clk_info[clk_info_index["icg_dflt"]] == "Y" :
                    print_line.append("--		'h1		--		RW		--		"+clk_info[clk_info_index["name"]]+"_ea		            --		[0]			--	"+clk_info[clk_info_index["name"]]+" icg enable")
                elif clk_info[clk_info_index["icg_dflt"]] == "N" :
                    print_line.append("--		'h0		--		RW		--		"+clk_info[clk_info_index["name"]]+"_ea		            --		[0]			--	"+clk_info[clk_info_index["name"]]+" icg enable")
            if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                print_line.append("--		'h0		--		RW		--		"+clk_info[clk_info_index["name"]]+"_sel		        --		[8]			--	"+clk_info[clk_info_index["name"]]+" select")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:
                print_line.append("--		'h"+str(hex(int(clk_info[clk_info_index["div_dflt"]]))[2:])+"		--		RW		--		"+clk_info[clk_info_index["name"]]+"_divider		    --		["+str(int(clk_info[clk_info_index["div_width"]]+15))+":16]		--	"+clk_info[clk_info_index["name"]]+" divider")
            
            #if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["div"]]) == False:
            if pd.isna(clk_info[clk_info_index["div"]]) == False:
                reg_addr = hex(count*4)
                print_line.append("\n")
                print_line.append(reg_addr+"    	       --		RW		--		"+clk_info[clk_info_index["name"]]+"_ea_req				--		[31:0]		--	"+clk_info[clk_info_index["name"]]+" enable request")
                count += 1
                #print(count)
            #if clk_info[clk_info_index["icg"]] == "Y":
                #print_line.append("--		'h0		--		RW		--		"+clk_info[clk_info_index["name"]]+"_icg_ea_req	        --		[0]			--	"+clk_info[clk_info_index["name"]]+" icg enable request")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:
                print_line.append("--		'h0		--		W1T		--		"+clk_info[clk_info_index["name"]]+"_divider_ea_req	        --		[16]		--	"+clk_info[clk_info_index["name"]]+" divider enable request")
            
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False:
                reg_addr = hex(count*4)
                print_line.append("\n")
                print_line.append(reg_addr+"    	       --		RO		--		"+clk_info[clk_info_index["name"]]+"_status				--		[31:0]		--	"+clk_info[clk_info_index["name"]]+" status")
                count += 1
            if clk_info[clk_info_index["icg"]] == "Y":
                print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_ea_status		    --		[0]	    	--  "+clk_info[clk_info_index["name"]]+" icg enable status")	
                #print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_icg_ea_ack		    --		[4]	    	--  "+clk_info[clk_info_index["name"]]+" icg enable ack")	
            if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_sel_clk0_sel	    --		[8]			--	"+clk_info[clk_info_index["name"]]+" select clk1 status")
                print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_sel_clk1_sel	    --		[9]			--	"+clk_info[clk_info_index["name"]]+" select clk1 status")
                print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_sel_done		    --		[10]		--	"+clk_info[clk_info_index["name"]]+" select done status")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:    
                print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_divider_done	    --		[12]		--  "+clk_info[clk_info_index["name"]]+" divider done status")
                #print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_divider_ea_ack	    --		[13]		--  "+clk_info[clk_info_index["name"]]+" divider enable ack")
                print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_divider_status	    --		["+str(int(clk_info[clk_info_index["div_width"]]+15))+":16]		--	"+clk_info[clk_info_index["name"]]+" divider status")

            #count += 1
            #print(count)


    print_line.append("\n")
    rst_reg_num = []
    rst_reg_bit_lc = []
    for rst_info in rst_corpus:
        if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
            continue
        elif rst_info[rst_info_index["soft_src"]] == "SOFT":
            rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
            rst_reg_num.append(rst_info_reg_lc[0])
            rst_reg_bit_lc.append(rst_info_reg_lc[1])
    
    #print(rst_reg_num)
    rst_reg_num = list(set(rst_reg_num))
    rst_reg_num = list(map(int, rst_reg_num))
    rst_reg_num.sort()
    rst_reg_num = list(map(str, rst_reg_num))
    #rst_reg_num = np.unique(rst_reg_num)
    #rst_reg_num = np.sort(rst_reg_num)
    
    #print(rst_reg_num)
    #print(type(rst_reg_num))
    #print(rst_reg_bit_lc)

    count = 0
    for idx in rst_reg_num:
        reg_addr = hex(int(count)*4 + int(top_corpus[top_info_index["user_defined_reg_addr_ofst"]][1]))
        print_line.append(reg_addr+"				--		RW		--		soft_reset_ctrl"+str(int(count)).rjust(3,'0')+"			    --		[31:0]		--	soft_reset_ctrl"+str(int(count)).rjust(3,'0')) 	
        #print(count)
        count += 1
        for rst_info in rst_corpus:
            #print(rst_info[rst_info_index["name"]])
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(idx)]:
                    if rst_info[rst_info_index["soft_dflt"]] == "N" :
                        print_line.append("--		'h1		--		RW		--		"+rst_info[rst_info_index["name"]]+"_sftrstn		                --		["+rst_info_reg_lc[1]+"]			--	"+rst_info[rst_info_index["name"]]+"_sftrstn")
                    else :
                        print_line.append("--		'h0		--		RW		--		"+rst_info[rst_info_index["name"]]+"_sftrstn		                --		["+rst_info_reg_lc[1]+"]			--	"+rst_info[rst_info_index["name"]]+"_sftrstn")
        print_line.append("\n")

    rst_status_count = 0
    for idx in rst_reg_num:
        reg_addr = hex(count*4 + int(top_corpus[top_info_index["user_defined_reg_addr_ofst"]][1]))
        print_line.append(reg_addr+"				--		RO		--		soft_reset_status"+str(int(rst_status_count)).rjust(3,'0')+"				--		[31:0]		--	soft_reset_status"+str(int(rst_status_count)).rjust(3,'0')) 
        #print(count)
        count += 1
        rst_status_count += 1
        for rst_info in rst_corpus:
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(idx)]:
                    print_line.append("--		'h0		--		RO		--		"+rst_info[rst_info_index["name"]]+"_status	                    --		["+rst_info_reg_lc[1]+"]			--	"+rst_info[rst_info_index["name"]]+"_status")
        print_line.append("\n")
    
    if reg_empty == False:
        reg_note_gen(print_line, reg_corpus, reg_ser)
    
    print_line.append("\n")
    print_line.append("// Register end\n")   
    print_line.append("// Block end")
    print_line.append("// Component end")

    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')

    fp.close()

#}}}

def crg_gen_top_csv(rst_info_index, gen_filepath, top_corpus, rst_corpus, rst_ser, clk_info_index, top_info_index, clk_corpus, clk_ser, reg_corpus, reg_ser, code_corpus, code_ser, code_empty, reg_empty, intp_empty, intp_corpus, intp_ser): #{{{
    fp = open(gen_filepath+top_corpus[top_info_index["design_name"]][1]+"_top.csv", "w") 
    
    print_line = []
    print_line.append("#author_begin")
    print_line.append(top_corpus[top_info_index["design_owner"]][1])
    print_line.append("#author_end")
    print_line.append("#order_begin")
    print_line.append("False")
    print_line.append("#order_end")
    print_line.append("#keep_begin before_module")
    print_line.append("#keep_end before_module")
    print_line.append("module,"+top_corpus[top_info_index["design_name"]][1]+"_top")
    print_line.append("#parameter_begin")
    print_line.append("#parameter_end")
    print_line.append("#keep_begin before_port")
    for code_info in code_corpus:
        if code_info[0] == "input" :
            if pd.isna(code_info[1]) == False :
                print_line.append("input,"+str(code_info[1])+","+code_info[2])
            else :
                print_line.append("input,,"+code_info[2])
        if code_info[0] == "output" :
            if pd.isna(code_info[1]) == False :
                print_line.append("output,"+str(code_info[1])+","+code_info[2]);
            else :
                print_line.append("output,,"+code_info[2]);

    #count = 0
    #for clk_info in clk_corpus:
    #    #print(clk_info)
    #    count += 1 
    #    if clk_info[clk_info_index["attr"]] == "input":
    #        print_line.append("input,,CLK_NAME")
    #    if pd.isna(clk_info[clk_info_index["icg_external"]]) == False :
    #        if "[" in clk_info[clk_info_index["icg_external"]] :
    #            other_clk_list = clk_info[clk_info_index["icg_external"]].split("[")
    #            #print(other_clk_list)
    #            print_line.append(",input,["+other_clk_list[1]+","+other_clk_list[0])
    #        else : 
    #            print_line.append("input,,"+clk_info[clk_info_index["icg_external"]])
    #    if clk_info[clk_info_index["attr"]] == "output" :
    #        #print_line.append("\t// CLK_NAME")
    #        if clk_info[clk_info_index["attr"]] == "output":
    #            print_line.append("output,,CLK_NAME")
    #    replace_CLK_NAME(clk_info, clk_info_index, top_info_index, print_line)
    #
    #count = 0
    #for rst_info in rst_corpus:
    #    count += 1
    #    #if rst_info[rst_info_index["attr"]] == "test_mode" or rst_info[rst_info_index["attr"]] == "test_rstn":
    #    if rst_info[rst_info_index["inout"]] == "input" :
    #        print_line.append("input,,"+rst_info[rst_info_index["name"]])
    #    #if rst_info[rst_info_index["sync"]] == "Y":
    #    if rst_info[rst_info_index["inout"]] == "output" :
    #        print_line.append("output,,"+rst_info[rst_info_index["name"]])
    #    if pd.isna(rst_info[rst_info_index["external_src"]]) == False :
    #        if "[" in rst_info[rst_info_index["external_src"]] :
    #            other_rst_list = rst_info[rst_info_index["external_src"]].split("[")
    #            #print(other_rst_list)
    #            print_line.append("input,["+other_rst_list[1]+","+other_rst_list[0])
    #        else : 
    #            print_line.append("input,,"+rst_info[rst_info_index["external_src"]])
    print_line.append("#keep_end before_port")
    
    for repeat_idx in range(len(print_line)-1, -1, -1) :
        if print_line.count(print_line[repeat_idx]) > 1 and "input" in print_line[repeat_idx] :
            print_line.pop(repeat_idx)
   
    print_line.append("#port_begin")
    print_line.append("#port_end")
    print_line.append("#gen_type_begin")
    print_line.append("v")
    print_line.append("#gen_type_end")
    print_line.append("#csv_begin")
    print_line.append("#csv_end")
    protocol = top_corpus[top_info_index["protocol"]][1]
    if code_empty == False :
        code_gen_csv(print_line, code_corpus, code_ser)
    print_line.append("#inst_begin===========================================================================================================")
    #if top_corpus[top_info_index["protocol"]][1] == "dab":
    #    print_line.append("inst "+top_corpus[top_info_index["design_name"]][1].upper()+"_reg u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_reg")
    #elif top_corpus[top_info_index["protocol"]][1] == "apb":
    #    print_line.append("inst "+top_corpus[top_info_index["design_name"]][1].upper()+"_cfg u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_cfg")
    #elif top_corpus[top_info_index["protocol"]][1] == "ahb":
    print_line.append("inst "+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg")
    print_line.append("#para_inst_begin")
    print_line.append("#para_inst_end")
    print_line.append("#port_inst_begin")
    if protocol == "apb" :
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.clk                 ,apb_clk            ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.rst_n               ,apb_rst_n          ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.psel                ,apb_sel            ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.penable             ,apb_enable         ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.pwrite              ,apb_write          ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.paddr               ,apb_addr[31:0]     ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.pwdata              ,apb_wdata[31:0]    ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.prdata              ,apb_rdata[31:0]    ,O         ,output,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.pready              ,apb_ready          ,O         ,output,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.pslverr             ,apb_slverr          ,O         ,output,")
    elif protocol == "dab" :
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.clk                 ,dab_clk            ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.rst_n               ,dab_rst_n          ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.dab_write           ,dab_write          ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.dab_read            ,dab_read           ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.dab_addr            ,dab_addr[31:0]     ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.dab_wdata           ,dab_wdata[31:0]    ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.dab_rdata           ,dab_rdata[31:0]    ,O         ,output,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.dab_ready           ,dab_ready          ,O         ,output,")
    elif protocol == "ahb" :
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.clk                 ,ahb_clk        ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.rst_n               ,ahb_rst_n      ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.hreadyin            ,hreadyin       ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.hsel                ,hsel           ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.htrans              ,htrans[1:0]    ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.hwrite              ,hwrite         ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.hburst              ,hburst[2:0]    ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.hsize               ,hsize[2:0]     ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.haddr               ,haddr[31:0]    ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.hwdata              ,hwdata[31:0]   ,I         ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.hreadyout           ,hreadyout      ,O         ,output,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.hresp               ,hresp[1:0]     ,O         ,output,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_reg.hrdata              ,hrdata[31:0]   ,O         ,output,")

    count = 0
    for clk_info in clk_corpus:
        count += 1 
        if clk_info[clk_info_index["attr"]] == "output" or clk_info[clk_info_index["attr"]] == "na" or clk_info[clk_info_index["attr"]] == "internal":
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False:
                count += 1
                #print(count)
                if clk_info[clk_info_index["icg"]] == "Y":
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_ea         ,"+clk_info[clk_info_index["name"]]+"_ea     ,W  ,output,")	
#                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_ea_lock_fld         ,      ,W  ,output,")	
                if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_sel        ,"+clk_info[clk_info_index["name"]]+"_sel    ,W  ,output,")	
#                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_sel_lock_fld        ,     ,W  ,output,")	
                if pd.isna(clk_info[clk_info_index["div"]]) == False:
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_divider_ea_req   ,"+clk_info[clk_info_index["name"]]+"_divider_ea_req     ,W  ,output,")
#                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_divider_ea_req_lock_fld   ,      ,W  ,output,")

            if pd.isna(clk_info[clk_info_index["div"]]) == False:
                count += 1
                #print(count)
                #if clk_info[clk_info_index["icg"]] == "Y":
                    #print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ea_req_"+clk_info[clk_info_index["name"]]+"_icg_ea_req\t\t("+clk_info[clk_info_index["name"]]+"_icg_ea_req),")	
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_divider_"+clk_info[clk_info_index["name"]]+"_divider    ,"+clk_info[clk_info_index["name"]]+"_divider["+str(int(clk_info[clk_info_index["div_width"]]-1))+":0]    ,W   ,output,")	
#                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_divider_"+clk_info[clk_info_index["name"]]+"_divider_lock_fld    ,     ,W   ,output,")	
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False:
                count += 1
                if clk_info[clk_info_index["icg"]] == "Y":
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_ea_status    ,"+clk_info[clk_info_index["name"]]+"_ea_status  ,W  ,input,")	
                    #print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_icg_ea_ack\t\t("+clk_info[clk_info_index["name"]]+"_icg_ea_ack),")	
                if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_sel_clk0_sel     ,"+clk_info[clk_info_index["name"]]+"_sel_clk0_sel   ,W  ,input,")	
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_sel_clk1_sel     ,"+clk_info[clk_info_index["name"]]+"_sel_clk1_sel   ,W  ,input,")	
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_sel_done         ,"+clk_info[clk_info_index["name"]]+"_sel_done       ,W  ,input,")	
                if pd.isna(clk_info[clk_info_index["div"]]) == False:    
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_divider_status   ,"+clk_info[clk_info_index["name"]]+"_divider_status["+str(int(clk_info[clk_info_index["div_width"]]-1))+":0]     ,W  ,input,")
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_divider_done     ,"+clk_info[clk_info_index["name"]]+"_divider_done   ,W  ,input,")
                    #print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_divider_ea_ack\t\t("+clk_info[clk_info_index["name"]]+"_divider_ea_ack),")	
                #print(count)            


    rst_reg_num = []
    rst_reg_bit_lc = []
    for rst_info in rst_corpus:
        if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
            continue    
        elif rst_info[rst_info_index["soft_src"]] == "SOFT":
            rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
            rst_reg_num.append(rst_info_reg_lc[0])
            rst_reg_bit_lc.append(rst_info_reg_lc[1]) 
    #rst_reg_num = np.unique(rst_reg_num)
    
    rst_reg_num = list(set(rst_reg_num))
    rst_reg_num = list(map(int, rst_reg_num))
    rst_reg_num.sort()
    rst_reg_num = list(map(str, rst_reg_num))
    #print(rst_reg_num)
    
    rst_reg_name = []
    for rst_info in rst_corpus:
        if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
            continue
        elif rst_info[rst_info_index["soft_src"]] == "SOFT":
            rst_reg_name.append(rst_info[rst_info_index["reg_name"]])

    reg_name = []
    for item in rst_reg_name :
        if not item in reg_name :
            reg_name.append(item)	

    #print(reg_name)
    
    count = 0
    for idx in rst_reg_num:
        reg_addr = hex(int(idx)*4)
        for rst_info in rst_corpus:
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue    
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                #print(rst_info)
                #print(rst_info_reg_lc)
                if rst_info_reg_lc[0] == rst_reg_num[int(count)]:
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+reg_name[int(count)]+"_"+rst_info[rst_info_index["name"]]+"_sftrstn     ,"+rst_info[rst_info_index["name"]]+"_sftrstn    ,W  ,output,")          
#            if rst_info[rst_info_index["soft_src"]] == "SOFT":
#                if rst_info_reg_lc[0] == rst_reg_num[int(count)] and "connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+reg_name[int(count)]+"_"+rst_info[rst_info_index["name"]]+"_lock_fld     ,     ,W  ,output," not in print_line :
#                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+reg_name[int(count)]+"_"+rst_info[rst_info_index["name"]]+"_lock_fld     ,     ,W  ,output,")          

        count += 1
    for repeat_idx in range(len(print_line)-1, -1, -1) :
        if print_line.count(print_line[repeat_idx]) > 1 and "connect" in print_line[repeat_idx] and "_lock_fld" in print_line[repeat_idx] :
            print_line.pop(repeat_idx)
    rst_status_count = 0
    count = 0
    for idx in rst_reg_num:
        reg_addr = hex(count*4)
        for rst_info in rst_corpus:
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue    
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(rst_status_count)]:
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+reg_name[int(count)]+"_status_"+rst_info[rst_info_index["name"]]+"_status     ,"+rst_info[rst_info_index["name"]]+"   ,O   ,input,")
        count += 1
        rst_status_count += 1

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
                if reg_info[4] == "RO" :
                    if int(field_msb) - int(field_lsb) == 0 :
                        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+rst_reg_name+"_"+reg_info[2]+"    ,"+reg_info[2]+"  ,W  ,input,")
                    else :
                        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+rst_reg_name+"_"+reg_info[2]+"    ,"+reg_info[2]+"["+str(int(field_msb)-int(field_lsb))+":0]  ,W  ,input,")
                elif reg_info[4] == "W1T" :
                        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+rst_reg_name+"_"+reg_info[2]+"    ,"+reg_info[2]+"  ,W  ,output,")
                else :
                    if int(field_msb) - int(field_lsb) == 0 :
                        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+rst_reg_name+"_"+reg_info[2]+"    ,"+reg_info[2]+"  ,W  ,output,")
                    else :
                        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+rst_reg_name+"_"+reg_info[2]+"    ,"+reg_info[2]+"["+str(int(field_msb)-int(field_lsb))+":0]  ,W  ,output,")
    
    if intp_empty == False :
        intp_count = 0
        for intp_info in intp_corpus :
            if pd.isna(intp_info[0]) == False :
                if intp_count % 7 == 0:
                    intp_name = intp_info[0].split('_')
                    del(intp_name[-1])
                    del(intp_name[-1])
                    intp_name_str = '_'.join(intp_name)
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+str(intp_name_str)+"_out                       ,"+str(intp_name_str)+"_out  ,W  ,output,")
                intp_count = intp_count + 1
            elif (intp_count-1) % 7 == 0:
                #print(intp_info[3])
                bitoffset0 = str(intp_info[3]).split('[', 1)
                #print(bitoffset0)
                bitoffset1 = bitoffset0[1].split(':', 1)
                bitoffset2 = bitoffset1[1].split(']', 1)
                field_msb = bitoffset1[0]
                field_lsb = bitoffset2[0]
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+str(intp_name_str)+"_"+str(intp_info[2])+"    ,"+str(intp_info[2])+"  ,W  ,input,")


#            if pd.isna(intp_info[0]) == False :
#                intp_name_str = intp_info[0]
#            else :
#                #print(intp_info[3])
#                bitoffset0 = str(intp_info[3]).split('[', 1)
#                #print(bitoffset0)
#                bitoffset1 = bitoffset0[1].split(':', 1)
#                bitoffset2 = bitoffset1[1].split(']', 1)
#                field_msb = bitoffset1[0]
#                field_lsb = bitoffset2[0]
#                #print(field_msb, field_lsb)
#                #if int(field_msb) - int(field_lsb) == 0 :
#                #    print_line.append("\t\t."+intp_reg_name+"_"+intp_info[2]+"\t\t("+intp_info[2]+"),")
#                #else :
#                #    print_line.append("\t\t."+intp_reg_name+"_"+intp_info[2]+"\t\t("+intp_info[2]+"["+str(int(field_msb)-int(field_lsb))+":0]),")
#                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+str(intp_name_str)+"_"+str(intp_info[2])+"    ,"+str(intp_info[2])+"  ,W  ,input,")
#                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+str(intp_name_str)+"_out                       ,"+str(intp_name_str)+"_out  ,W  ,output,")
#
                #if intp_info[4] == "RO" :
                #    if int(field_msb) - int(field_lsb) == 0 :
                #        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+str(intp_name_str)+"_"+intp_info[2]+"    ,"+intp_info[2]+"  ,W  ,input,")
                #    else :
                #        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+str(intp_name_str)+"_"+intp_info[2]+"    ,"+intp_info[2]+"["+str(int(field_msb)-int(field_lsb))+":0]  ,W  ,input,")
                #elif intp_info[4] == "W1T" :
                #    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+str(intp_name_str)+"_"+intp_info[2]+"    ,"+intp_info[2]+"  ,W  ,output,")
                #else :
                #    if int(field_msb) - int(field_lsb) == 0 :
                #        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+str(intp_name_str)+"_"+intp_info[2]+"    ,"+intp_info[2]+"  ,W  ,output,")
                #    else :
                #        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile."+str(intp_name_str)+"_"+intp_info[2]+"    ,"+intp_info[2]+"["+str(int(field_msb)-int(field_lsb))+":0]  ,W  ,output,")





    print_line.append("#port_inst_end")
    print_line.append("#inst_end============================================================================================================")

    print_line.append("#inst_begin===========================================================================================================")
    print_line.append("inst "+top_corpus[top_info_index["design_name"]][1]+"_clk_gen u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen")
    print_line.append("#para_inst_begin")
    print_line.append("#para_inst_end")
    print_line.append("#port_inst_begin")
    count = 0
    if top_corpus[top_info_index["protocol"]][1] == "apb" :
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.apb_clk     ,apb_clk    ,I  ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.apb_rst_n   ,apb_rst_n  ,I  ,input,")
    elif top_corpus[top_info_index["protocol"]][1] == "dab" :
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.dab_clk     ,dab_clk    ,I  ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.dab_rst_n   ,dab_rst_n  ,I  ,input,")
    elif top_corpus[top_info_index["protocol"]][1] == "ahb" :
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.ahb_clk     ,ahb_clk    ,I  ,input,")
        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.ahb_rst_n   ,ahb_rst_n  ,I  ,input,")
    
    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.dft_icg_mode_root   ,dft_icg_mode_root  ,I  ,input,")
    for clk_info in clk_corpus:
        count += 1 
        #if clk_info[clk_info_index["name"]] == "#NAME":
        #    continue
        if clk_info[clk_info_index["attr"]] == "input":
            print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME   ,CLK_NAME   ,I  ,input,")
            #print(tplt.format("input", "CLK_NAME", ","))
        #if clk_info[clk_info_index["name"]] == "#Clocks for AHB":
        #    continue
        if clk_info[clk_info_index["attr"]] == "internal" and pd.isna(clk_info[clk_info_index["src0"]]) == True :
            print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME   ,CLK_NAME   ,W  ,input,")
        if clk_info[clk_info_index["attr"]] == "output" or clk_info[clk_info_index["attr"]] == "na" or (clk_info[clk_info_index["attr"]] == "internal" and pd.isna(clk_info[clk_info_index["src0"]]) == False) :
            if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                #print(pd.isna(clk_info[clk_info_index["sel"]]))
                if "," in clk_info[clk_info_index["sel"]] :
                    clk_sel = clk_info[clk_info_index["sel"]].split(",")
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen."+clk_sel[1]+"            ,"+clk_sel[1]+"          ,W  ,input,")
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME_sel            ,CLK_NAME_sel          ,W  ,input,")
                else :
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME_sel            ,CLK_NAME_sel          ,W  ,input,")
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME_sel_clk0_sel   ,CLK_NAME_sel_clk0_sel ,W  ,output,")
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME_sel_clk1_sel   ,CLK_NAME_sel_clk1_sel ,W  ,output,")
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME_sel_done       ,CLK_NAME_sel_done     ,W  ,output,")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:
                #print(pd.isna(clk_info[clk_info_index["div"]]))
                #print_line.append("\toutput          CLK_NAME_en,")
                if pd.isna(clk_info[clk_info_index["div_val_to_en"]]) == False :
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen."+clk_info[clk_info_index["div_val_to_en"]]+"    ,"+clk_info[clk_info_index["div_val_to_en"]]+"   ,W,     input,")
                    other_clk_list = clk_info[clk_info_index["div_val_to"]].split("[")
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen."+other_clk_list[0]+"    ,"+other_clk_list[0]+"   ,W,     input,")
                if pd.isna(clk_info[clk_info_index["divider_fadj"]]) == False :
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen."+clk_info[clk_info_index["divider_fadj"]]+"    ,"+clk_info[clk_info_index["divider_fadj"]]+"   ,W,     input,")
                if pd.isna(clk_info[clk_info_index["divider_fadj_val"]]) == False :
                    other_clk_list = clk_info[clk_info_index["divider_fadj_val"]].split("[")
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen."+other_clk_list[0]+"        ,"+other_clk_list[0]+"["+str(int(int(clk_info[clk_info_index["div_width"]]-1)))+":0]   ,W  ,input,")
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME_divider        ,CLK_NAME_divider["+str(int(int(clk_info[clk_info_index["div_width"]]-1)))+":0]   ,W  ,input,")
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME_divider_ea_req ,CLK_NAME_divider_ea_req                                ,W  ,input,")
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME_divider_status ,CLK_NAME_divider_status["+str(int(clk_info[clk_info_index["div_width"]]-1))+":0] ,W  ,output,")
                #print_line.append("\toutput          CLK_NAME_divider_ea_ack,")
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME_divider_done   ,CLK_NAME_divider_done      ,W  ,output,")
            if clk_info[clk_info_index["icg"]] == "Y":
                if clk_info[clk_info_index["ce_en"]] == "Y" :
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME_ce             ,CLK_NAME_ce         ,W  ,input,")
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME_ea             ,CLK_NAME_ea                ,W  ,input,")
                #print_line.append("\tinput           CLK_NAME_icg_ea_req,") 
                #print_line.append("\toutput          CLK_NAME_icg_ea_ack,")
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME_ea_status      ,CLK_NAME_ea_status         ,W  ,output,")
            if pd.isna(clk_info[clk_info_index["icg_external"]]) == False :
                if "[" in clk_info[clk_info_index["icg_external"]] :
                    other_clk_list = clk_info[clk_info_index["icg_external"]].split("[")
                    #print(other_clk_list)
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen."+other_clk_list[0]+"   ,"+other_clk_list[0]+"["+other_clk_list[1]+"    ,I  ,input,")
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen."+clk_info[clk_info_index["name"]]+"_"+other_clk_list[0]+"   ,"+clk_info[clk_info_index["name"]]+"_"+other_clk_list[0]+"["+other_clk_list[1]+"_sync    ,W  ,output,")
                else :
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen."+clk_info[clk_info_index["icg_external"]]+"   ,"+clk_info[clk_info_index["icg_external"]]+"    ,I  ,input,")
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen."+clk_info[clk_info_index["name"]]+"_"+clk_info[clk_info_index["icg_external"]]+"_sync   ,"+clk_info[clk_info_index["name"]]+"_"+clk_info[clk_info_index["icg_external"]]+"_sync    ,W  ,output,")
            if pd.isna(clk_info[clk_info_index["icg_internal"]]) == False :
                if "[" in clk_info[clk_info_index["icg_internal"]] :
                    other_clk_list = clk_info[clk_info_index["icg_internal"]].split("[")
                    #print(other_clk_list)
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen."+other_clk_list[0]+"   ,"+other_clk_list[0]+"["+other_clk_list[1]+"    ,W  ,input,")
                else :
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen."+clk_info[clk_info_index["icg_internal"]]+"   ,"+clk_info[clk_info_index["icg_internal"]]+"    ,W  ,input,")

            if clk_info[clk_info_index["attr"]] == "output" :
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME    ,CLK_NAME   ,O  ,output,")
                #if clk_info[clk_info_index["icg"]] == "Y" :
                if clk_info[clk_info_index["ce_en"]] == "Y" :
                    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME_cg_bf          ,CLK_NAME_cg_bf             ,W  ,output,")
            elif clk_info[clk_info_index["attr"]] == "internal" :
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.CLK_NAME    ,CLK_NAME   ,W  ,output,")

        replace_CLK_NAME(clk_info, clk_info_index, top_info_index, print_line)
    print_line.append("#port_inst_end")
    print_line.append("#inst_end============================================================================================================")

    for repeat_idx in range(len(print_line)-1, -1, -1) :
        if print_line.count(print_line[repeat_idx]) > 1 and "connect" in print_line[repeat_idx] and "_clk_gen" in print_line[repeat_idx] :
            print_line.pop(repeat_idx)
    print_line.append("#inst_begin===========================================================================================================")
    print_line.append("inst "+top_corpus[top_info_index["design_name"]][1]+"_rst_gen u_"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen")
    print_line.append("#para_inst_begin")
    print_line.append("#para_inst_end")
    print_line.append("#port_inst_begin")
    count = 0
    for rst_info in rst_corpus:
        count += 1
        if rst_info[rst_info_index["inout"]] == "input":
            print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+rst_info[rst_info_index["name"]]+"     ,"+rst_info[rst_info_index["name"]]+"    ,I  ,input,")
        if rst_info[rst_info_index["inout"]] == "internal" and pd.isna(rst_info[rst_info_index["glb_src"]]) == True :
            print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+rst_info[rst_info_index["name"]]+"     ,"+rst_info[rst_info_index["name"]]+"    ,W  ,input,")
        elif rst_info[rst_info_index["inout"]] == "internal" :
            print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+rst_info[rst_info_index["name"]]+"     ,"+rst_info[rst_info_index["name"]]+"    ,W  ,output,")
        if rst_info[rst_info_index["inout"]] == "output" :
            #if pd.isna(rst_info[rst_info_index["sync_clk"]]) == False :
            #if rst_info[rst_info_index["sync"]] == "Y" :
            #    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+rst_info[rst_info_index["sync_clk"]]+"    ,"+rst_info[rst_info_index["sync_clk"]]+"   ,O  ,input,")
            #if rst_info[rst_info_index["areset_relax_en"]] == "Y" :
            #    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+str(rst_info[rst_info_index["sync_clk"]])+"_cg_bf     ,"+str(rst_info[rst_info_index["sync_clk"]])+"_cg_bf    ,W  ,input,")
            #    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+str(rst_info[rst_info_index["sync_clk"]])+"_ce     ,"+str(rst_info[rst_info_index["sync_clk"]])+"_ce    ,W  ,output,")
            if rst_info[rst_info_index["soft_src"]] == "SOFT" :
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+rst_info[rst_info_index["name"]]+"_sftrstn     ,"+rst_info[rst_info_index["name"]]+"_sftrstn    ,W  ,input,")
            print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+rst_info[rst_info_index["name"]]+"     ,"+rst_info[rst_info_index["name"]]+"    ,O  ,output,")

        #elif rst_info[rst_info_index["sync"]] == "N" :
        #    if rst_info[rst_info_index["soft_src"]] == "SOFT" :
        #        print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+rst_info[rst_info_index["name"]]+"_sftrstn     ,"+rst_info[rst_info_index["name"]]+"_sftrstn    ,W  ,input,")
        #    print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+rst_info[rst_info_index["name"]]+"   ,"+rst_info[rst_info_index["name"]]+"    ,O  ,output,")
        if pd.isna(rst_info[rst_info_index["external_src"]]) == False :
            if "[" in rst_info[rst_info_index["external_src"]] :
                other_rst_list = rst_info[rst_info_index["external_src"]].split("[")
                #print(other_rst_list)
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+other_rst_list[0]+"   ,"+other_rst_list[0]+"["+other_rst_list[1]+"   ,I  ,input,")
            else : 
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+rst_info[rst_info_index["external_src"]]+"     ,"+rst_info[rst_info_index["external_src"]]+"     ,I  ,input,")
        if pd.isna(rst_info[rst_info_index["internal_src"]]) == False :
            if "[" in rst_info[rst_info_index["internal_src"]] :
                other_rst_list = rst_info[rst_info_index["internal_src"]].split("[")
                #print(other_rst_list)
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+other_rst_list[0]+"   ,"+other_rst_list[0]+"["+other_rst_list[1]+"    ,W  ,input,")
            else : 
                print_line.append("connect,"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen."+rst_info[rst_info_index["internal_src"]]+"     ,"+rst_info[rst_info_index["internal_src"]]+"    ,W  ,input,")
    for repeat_idx in range(len(print_line)-1, -1, -1) :
        if print_line.count(print_line[repeat_idx]) > 1 and "connect" in print_line[repeat_idx] and "_rst_gen" in print_line[repeat_idx] :
            print_line.pop(repeat_idx)
    print_line.append("#port_inst_end")
    print_line.append("#inst_end============================================================================================================")

    #for repeat_idx in range(len(print_line)-1, -1, -1) :
    #    if print_line.count(print_line[repeat_idx]) > 1 and "connect" in print_line[repeat_idx] :
    #        print_line.pop(repeat_idx)
    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    #fp.write('\n')
    #fp.write('endmodule')

    fp.close()
#}}}

def crg_gen_top(top_corpus, rst_corpus, rst_ser, clk_info_index, top_info_index, clk_corpus, clk_ser, reg_corpus, reg_ser, code_corpus, code_ser, code_empty, reg_empty, intp_empty, intp_corpus, intp_ser): #{{{
    fp = open(top_corpus[top_info_index["design_name"]][1]+"_top.v", "w") 
    
    print_line = []
    add_header(print_line, top_corpus[top_info_index["design_name"]][1]+"_top.v")
    #print_line.append('`include "sysvlog_interface_connect.h"')
    print_line.append("module "+top_corpus[top_info_index["design_name"]][1]+"_top(")
    #print_line.append('\tapb3_bus.slave  apb3_bus_clk_gen,')
    if top_corpus[top_info_index["protocol"]][1] == "apb":
        print_line.append('    input           apb_clk,')        
        print_line.append('    input           apb_rst_n,')    
        print_line.append('    input           apb_sel,')       
        print_line.append('    input           apb_enable,')    
        print_line.append('    input           apb_write,')     
        print_line.append('    input   [31:0]  apb_addr, ')
        print_line.append('    input   [31:0]  apb_wdata,')
        print_line.append('    output          apb_ready,')     
        print_line.append('    output  [31:0]  apb_rdata,')
    elif top_corpus[top_info_index["protocol"]][1] == "dab":
        print_line.append('    input           dab_clk,')
        print_line.append('    input           dab_rst_n,')
        print_line.append('    input           dab_write,')
        print_line.append('    input           dab_read,')
        print_line.append('    input  [31:0]   dab_addr,')
        print_line.append('    input  [31:0]   dab_wdata,')
        print_line.append('    output [31:0]   dab_rdata,')
        print_line.append('    output          dab_ready,')
    elif top_corpus[top_info_index["protocol"]][1] == "ahb":
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
        print_line.append("    output [31:0]   ahb_rdata,")
    
    for code_info in code_corpus:
        if code_info[0] == "input" :
            if pd.isna(code_info[1]) == False :
                print_line.append("    input    "+str(code_info[1])+"    "+code_info[2]+",")
            else :
                print_line.append("    input           "+code_info[2]+",")
        if code_info[0] == "output" :
            if pd.isna(code_info[1]) == False :
                print_line.append("    output   "+str(code_info[1])+"    "+code_info[2]+",");
            else :
                print_line.append("    output          "+code_info[2]+",");

    count = 0
    for clk_info in clk_corpus:
        #print(clk_info)
        count += 1 
        if clk_info[clk_info_index["attr"]] == "input":
            print_line.append("    input           CLK_NAME,")
        if pd.isna(clk_info[clk_info_index["icg_external"]]) == False :
            if "[" in clk_info[clk_info_index["icg_external"]] :
                other_clk_list = clk_info[clk_info_index["icg_external"]].split("[")
                #print(other_clk_list)
                print_line.append("    input     ["+other_clk_list[1]+"  "+other_clk_list[0]+",")
            else :
                print_line.append("    input            "+clk_info[clk_info_index["icg_external"]]+",")
        if clk_info[clk_info_index["attr"]] == "output" :
            #print_line.append("\t// CLK_NAME")
            if clk_info[clk_info_index["attr"]] == "output":
                print_line.append("    output          CLK_NAME,")
        replace_CLK_NAME(clk_info, clk_info_index, top_info_index, print_line)
    
    count = 0
    for rst_info in rst_corpus:
        count += 1
        #if rst_info[rst_info_index["attr"]] == "test_mode" or rst_info[rst_info_index["attr"]] == "test_rstn":
        if rst_info[rst_info_index["inout"]] == "input" :
            print_line.append("    input           "+rst_info[rst_info_index["name"]]+",")
        #if rst_info[rst_info_index["sync"]] == "Y":
        if rst_info[rst_info_index["inout"]] == "output" :
            print_line.append("    output          "+rst_info[rst_info_index["name"]]+",")
        if pd.isna(rst_info[rst_info_index["external_src"]]) == False :
            if "[" in rst_info[rst_info_index["external_src"]] :
                other_rst_list = rst_info[rst_info_index["external_src"]].split("[")
                #print(other_rst_list)
                print_line.append("    input     ["+other_rst_list[1]+"  "+other_rst_list[0]+",")
            else : 
                print_line.append("    input           "+rst_info[rst_info_index["external_src"]]+",")
    
    for repeat_idx in range(len(print_line)-1, -1, -1) :
        if print_line.count(print_line[repeat_idx]) > 1 and "input" in print_line[repeat_idx] :
            print_line.pop(repeat_idx)
    
    port_last_process(count, rst_ser, print_line)

    print_line.append(');\n')
   


    print_line.append('\t/*autodef*/\n')
  
    if code_empty == False :
        code_gen(print_line, code_corpus, code_ser)

    if top_corpus[top_info_index["protocol"]][1] == "dab":
        print_line.append("\t"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile(/*autoinst*/")
        print_line.append("    .clk                                   (dab_clk             ), //input")
        print_line.append("    .reset_n                               (dab_rst_n           ), //input")
        print_line.append("    .dab_write                             (dab_write           ), //input")
        print_line.append("    .dab_read                              (dab_read            ), //input")
        print_line.append("    .dab_addr                              (dab_addr[31:0]      ), //input")
        print_line.append("    .dab_wdata                             (dab_wdata[31:0]     ), //input")
        print_line.append("    .dab_rdata                             (dab_rdata[31:0]     ), //output")
        print_line.append("    .dab_ready                             (dab_ready           ), //output")
    elif top_corpus[top_info_index["protocol"]][1] == "apb":
        print_line.append("    "+top_corpus[top_info_index["design_name"]][1].upper()+"_apb_regfile u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_apb_regfile(/*autoinst*/")
        print_line.append("        .clk                               (apb_clk             ),")
        print_line.append("        .reset_n                           (apb_rst_n           ),")
        print_line.append("        .psel                              (apb_sel             ),")
        print_line.append("        .penable                           (apb_enable          ),")
        print_line.append("        .pwrite                            (apb_write           ),")
        print_line.append("        .addr                              (apb_addr[31:0]      ),")
        print_line.append("        .wdata                             (apb_wdata[31:0]     ),")
        print_line.append("        .pready                            (apb_ready           ),")
        print_line.append("        .rdata                             (apb_rdata[31:0]     ),")
    elif protocol == "ahb" :
        print_line.append("    "+top_corpus[top_info_index["design_name"]][1].upper()+"_ahb_regfile u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_ahb_regfile(/*autoinst*/")
        print_line.append("        .clk                               (ahb_clk           ),//input")
        print_line.append("        .rst_n                             (ahb_rst_n         ),//input")
        print_line.append("        .hreadyin                          (ahb_readyin       ),//input")
        print_line.append("        .hsel                              (ahb_sel           ),//input")
        print_line.append("        .htrans                            (ahb_trans[1:0]    ),//input")
        print_line.append("        .hwrite                            (ahb_write         ),//input")
        print_line.append("        .hburst                            (ahb_burst[2:0]    ),//input")
        print_line.append("        .hsize                             (ahb_size[2:0]     ),//input")
        print_line.append("        .haddr                             (ahb_addr[31:0]    ),//input")
        print_line.append("        .hwdata                            (ahb_wdata[31:0]   ),//input")
        print_line.append("        .hreadyout                         (ahb_readyout      ),//output")
        print_line.append("        .hresp                             (ahb_resp[1:0]     ),//output")
        print_line.append("        .hrdata                            (ahb_rdata[31:0]   ),//output")

    count = 0
    for clk_info in clk_corpus:
        count += 1 
        if clk_info[clk_info_index["attr"]] == "output" or clk_info[clk_info_index["attr"]] == "na" or clk_info[clk_info_index["attr"]] == "internal":
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False:
                count += 1
                #print(count)
                if clk_info[clk_info_index["icg"]] == "Y":
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_ea\t\t("+clk_info[clk_info_index["name"]]+"_ea),")	
                    #print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_ea_lock_fld\t\t(           ),")	
                if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_sel\t\t("+clk_info[clk_info_index["name"]]+"_sel),")	
#                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_sel_lock_fld\t\t(          ),")	
                if pd.isna(clk_info[clk_info_index["div"]]) == False:
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_divider\t\t("+clk_info[clk_info_index["name"]]+"_divider["+str(int(clk_info[clk_info_index["div_width"]]-1))+":0]),")	
#                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_divider_lock_fld\t\t(          ),")	
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["div"]]) == False:
                count += 1
                #print(count)
                #if clk_info[clk_info_index["icg"]] == "Y":
                    #print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ea_req_"+clk_info[clk_info_index["name"]]+"_icg_ea_req\t\t("+clk_info[clk_info_index["name"]]+"_icg_ea_req),")	
                if pd.isna(clk_info[clk_info_index["div"]]) == False:
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ea_req_"+clk_info[clk_info_index["name"]]+"_divider_ea_req\t\t("+clk_info[clk_info_index["name"]]+"_divider_ea_req),")	
#                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ea_req_"+clk_info[clk_info_index["name"]]+"_divider_ea_req_lock_fld\t\t(             ),")	
            
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False:
                count += 1
                if clk_info[clk_info_index["icg"]] == "Y":
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_ea_status\t\t("+clk_info[clk_info_index["name"]]+"_ea_status),")	
                    #print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_icg_ea_ack\t\t("+clk_info[clk_info_index["name"]]+"_icg_ea_ack),")	
                if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_sel_clk0_sel\t\t("+clk_info[clk_info_index["name"]]+"_sel_clk0_sel),")	
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_sel_clk1_sel\t\t("+clk_info[clk_info_index["name"]]+"_sel_clk1_sel),")	
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_sel_done\t\t("+clk_info[clk_info_index["name"]]+"_sel_done),")	
                if pd.isna(clk_info[clk_info_index["div"]]) == False:    
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_divider_status\t\t("+clk_info[clk_info_index["name"]]+"_divider_status["+str(int(clk_info[clk_info_index["div_width"]]-1))+":0]),")	
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_divider_done\t\t("+clk_info[clk_info_index["name"]]+"_divider_done),")	
                    #print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_divider_ea_ack\t\t("+clk_info[clk_info_index["name"]]+"_divider_ea_ack),")	

                #print(count)            


    rst_reg_num = []
    rst_reg_bit_lc = []
    for rst_info in rst_corpus:
        if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
            continue    
        elif rst_info[rst_info_index["soft_src"]] == "SOFT":
            rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
            rst_reg_num.append(rst_info_reg_lc[0])
            rst_reg_bit_lc.append(rst_info_reg_lc[1]) 
    #rst_reg_num = np.unique(rst_reg_num)
    
    rst_reg_num = list(set(rst_reg_num))
    rst_reg_num = list(map(int, rst_reg_num))
    rst_reg_num.sort()
    rst_reg_num = list(map(str, rst_reg_num))

    #print("rst_reg_bit is :"+str(rst_reg_bit_lc))
    #print("rst_reg_num is :"+str(rst_reg_num))
    rst_reg_name = []
    for rst_info in rst_corpus:
        if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
            continue
        elif rst_info[rst_info_index["soft_src"]] == "SOFT":
            rst_reg_name.append(rst_info[rst_info_index["reg_name"]])

    reg_name = []
    for item in rst_reg_name :
        if not item in reg_name :
            reg_name.append(item)	

    #print(reg_name)
    count = 0
    for idx in rst_reg_num :
        reg_addr = hex(int(idx)*4)
        for rst_info in rst_corpus:
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue    
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                #print("rst_info is :"+str(rst_info[rst_info_index["soft_lc"]]))
                #print("rst_info_reg_lc[0] is : "+str(rst_info_reg_lc[0]))
                #print("rst_info_reg_lc[1] is : "+str(rst_info_reg_lc[1]))
                #print("rst_reg_num is : "+str(rst_reg_num[int(count)]))
                #print("idx is : "+str(idx))
                if rst_info_reg_lc[0] == rst_reg_num[int(count)]:
                    print_line.append("\t\t."+reg_name[int(count)]+"_"+rst_info[rst_info_index["name"]]+"_sftrstn\t\t("+rst_info[rst_info_index["name"]]+"_sftrstn),")
            if rst_info[rst_info_index["soft_src"]] == "SOFT":
                if rst_info_reg_lc[0] == rst_reg_num[int(count)] and "\t\t."+reg_name[int(count)]+"_"+reg_name[int(count)]+"_lock\t\t(           )," not in print_line :
                    print_line.append("\t\t."+reg_name[int(count)]+"_"+reg_name[int(count)]+"_lock\t\t(           ),")
        count += 1
    reg_addr_ofst = idx
    rst_status_count = 0
    count = 0
    for idx in rst_reg_num:
        reg_addr = hex((int(idx+reg_addr_ofst))*4)
        for rst_info in rst_corpus:
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue    
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(rst_status_count)]:
                    print_line.append("\t\t."+reg_name[int(count)]+"_status_"+rst_info[rst_info_index["name"]]+"_status\t\t("+rst_info[rst_info_index["name"]]+"),")
        count += 1
        rst_status_count += 1

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
                print_line.append("\t\t."+rst_reg_name+"_"+reg_info[2]+"\t\t("+reg_info[2]+"["+str(int(field_msb)-int(field_lsb))+":0]),")

    if intp_empty == False :
        intp_count = 0
        for intp_info in intp_corpus :
            if pd.isna(intp_info[0]) == False :
                if intp_count % 7 == 0:
                    intp_name = intp_info[0].split('_')
                    del(intp_name[-1])
                    del(intp_name[-1])
                    intp_name_str = '_'.join(intp_name)
                intp_count = intp_count + 1
            elif (intp_count-1) % 7 == 0:
                #print(intp_info[3])
                bitoffset0 = str(intp_info[3]).split('[', 1)
                #print(bitoffset0)
                bitoffset1 = bitoffset0[1].split(':', 1)
                bitoffset2 = bitoffset1[1].split(']', 1)
                field_msb = bitoffset1[0]
                field_lsb = bitoffset2[0]
                #print(field_msb, field_lsb)
                #if int(field_msb) - int(field_lsb) == 0 :
                #    print_line.append("\t\t."+intp_reg_name+"_"+intp_info[2]+"\t\t("+intp_info[2]+"),")
                #else :
                #    print_line.append("\t\t."+intp_reg_name+"_"+intp_info[2]+"\t\t("+intp_info[2]+"["+str(int(field_msb)-int(field_lsb))+":0]),")
                print_line.append("\t\t."+str(intp_name_str)+"_"+str(intp_info[2])+"\t\t("+str(intp_info[2])+"),")
                print_line.append("\t\t."+str(intp_info[2])+"_out\t\t("+str(intp_info[2])+"_out),")




    print_line[-1] = print_line[-1].strip(',')
    print_line.append('\t);\n')
    
    print_line.append("\t"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen(/*autoinst*/);\n")
    print_line.append("\t"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen u_"+top_corpus[top_info_index["design_name"]][1]+"_rst_gen(/*autoinst*/);\n")



    print_line.append('endmodule')
    print_line.append('//Local Variables:')
    print_line.append('//verilog-library-directories:(".")')
    #print_line.append('//verilog-library-directories:("$HW/ips/digital/soc_ip_common/v2/rtl/rst_gen")')
    #print_line.append('//verilog-library-directories:("$XML")')
    for code_info in code_corpus :
        if code_info[0] == "file_source" :
            print_line.append("//verilog-library-directories:(\""+code_info[1]+"\")")
    print_line.append('//verilog-library-directories-recursive:0')
    print_line.append('//End:')
    print_line.append(' ')

    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    #fp.write('\n')
    #fp.write('endmodule')

    fp.close()


#}}}

# rst_gen_top{{{
def rst_gen_top(para_list, rst_corpus, rst_ser):
    fp = open(top_corpus[top_info_index["design_name"]][1]+"_top.v", "w") 
    
    print_line = []
    add_header(print_line, top_corpus[top_info_index["design_name"]][1]+"_top.v")
    #print_line.append('`include "sysvlog_interface_connect.h"')
    print_line.append("module "+top_corpus[top_info_index["design_name"]][1]+"_top(")
    #print_line.append('\tapb3_bus.slave  apb3_bus_clk_gen,')
    if top_corpus[top_info_index["protocol"]][1] == "apb":
        print_line.append('    input          apb_clk,')        
        print_line.append('    input          apb_rst_n,')    
        print_line.append('    input          apb_sel,')       
        print_line.append('    input          apb_enable,')    
        print_line.append('    input          apb_write,')     
        print_line.append('    input   [31:0] apb_addr, ')
        print_line.append('    input   [31:0] apb_wdata,')
        print_line.append('    output         apb_ready,')     
        print_line.append('    output  [31:0] apb_rdata,')
    elif top_corpus[top_info_index["protocol"]][1] == "dab":
        print_line.append('    input          dab_clk,')
        print_line.append('    input          dab_rst_n,')
        print_line.append('    input          dab_write,')
        print_line.append('    input          dab_read,')
        print_line.append('    input  [31:0]  dab_addr,')
        print_line.append('    input  [31:0]  dab_wdata,')
        print_line.append('    output [31:0]  dab_rdata,')
        print_line.append('    output         dab_ready,')
    elif top_corpus[top_info_index["protocol"]][1] == "ahb":
        print_line.append("    input          ahb_clk,")
        print_line.append("    input          ahb_rst_n,")
        print_line.append("    input          ahb_readyin,")
        print_line.append("    input          ahb_sel,")
        print_line.append("    input  [1:0]   ahb_trans,")
        print_line.append("    input          ahb_write,")
        print_line.append("    input  [2:0]   ahb_burst,")
        print_line.append("    input  [2:0]   ahb_size,")
        print_line.append("    input  [31:0]  ahb_addr,")
        print_line.append("    input  [31:0]  ahb_wdata,")
        print_line.append("    output         ahb_readyout,")
        print_line.append("    output [1:0]   ahb_resp,")
        print_line.append("    output [31:0]  ahb_rdata,")

    count = 0
    for rst_info in rst_corpus:
        count += 1
        if rst_info[rst_info_index["attr"]] == "ori_rst" or rst_info[rst_info_index["attr"]] == "test_mode" or rst_info[rst_info_index["attr"]] == "test_rstn":
            print_line.append("\tinput           "+rst_info[rst_info_index["name"]]+",")
        if rst_info[rst_info_index["attr"]] == "core_rst":
            print_line.append("\toutput           "+rst_info[rst_info_index["name"]]+",")
        if rst_info[rst_info_index["sync"]] == "Y":
            print_line.append("\t// "+rst_info[rst_info_index["name"]])
            print_line.append("\tinput           "+rst_info[rst_info_index["sync_clk"]]+",")
            print_line.append("\toutput          "+rst_info[rst_info_index["name"]]+",")
        port_last_process(count, rst_ser, print_line)
 
    print_line.append(');\n')

    for repeat_idx in range(len(print_line)-1, -1, -1) :
        if print_line.count(print_line[repeat_idx]) > 1 and "input" in print_line[repeat_idx] :
            print_line.pop(repeat_idx)

    print_line.append('\t/*autodef*/\n')
    #print_line.append("\tassign psel          = apb3_bus_rst_gen.psel;")
    #print_line.append("\tassign penable       = apb3_bus_rst_gen.penable;")
    #print_line.append("\tassign pwrite        = apb3_bus_rst_gen.pwrite;")
    #print_line.append("\tassign paddr[31:0]   = apb3_bus_rst_gen.paddr;")
    #print_line.append("\tassign pwdata[31:0]  = apb3_bus_rst_gen.pwdata;")
    #print_line.append("\tassign apb3_bus_rst_gen.prdata  = prdata[31:0];")
    #print_line.append("\tassign apb3_bus_rst_gen.pslverr = 1'b0;")
    #print_line.append("\tassign apb3_bus_rst_gen.pready  = pready;\n")

    if top_corpus[top_info_index["protocol"]][1] == "dab":
        print_line.append("\t"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile(/*autoinst*/")
        print_line.append("    .clk                                   (dab_clk             ), //input")
        print_line.append("    .reset_n                               (dab_rst_n           ), //input")
        print_line.append("    .dab_write                             (dab_write           ), //input")
        print_line.append("    .dab_read                              (dab_read            ), //input")
        print_line.append("    .dab_addr                              (dab_addr[31:0]      ), //input")
        print_line.append("    .dab_wdata                             (dab_wdata[31:0]     ), //input")
        print_line.append("    .dab_rdata                             (dab_rdata[31:0]     ), //output")
        print_line.append("    .dab_ready                             (dab_ready           ), //output")
    elif top_corpus[top_info_index["protocol"]][1] == "apb":
        print_line.append("    "+top_corpus[top_info_index["design_name"]][1].upper()+"_apb_regfile u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_apb_regfile(/*autoinst*/")
        print_line.append("        .clk                               (apb_clk             ),")
        print_line.append("        .reset_n                           (apb_rst_n           ),")
        print_line.append("        .psel                              (apb_sel             ),")
        print_line.append("        .penable                           (apb_enable          ),")
        print_line.append("        .pwrite                            (apb_write           ),")
        print_line.append("        .addr                              (apb_addr[31:0]      ),")
        print_line.append("        .wdata                             (apb_wdata[31:0]     ),")
        print_line.append("        .pready                            (apb_ready           ),")
        print_line.append("        .rdata                             (apb_rdata[31:0]     ),")
    elif protocol == "ahb" :
        print_line.append("    "+top_corpus[top_info_index["design_name"]][1].upper()+"_ahb_regfile u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_ahb_regfile(/*autoinst*/")
        print_line.append("        .clk                               (ahb_clk           ),//input")
        print_line.append("        .rst_n                             (ahb_rst_n         ),//input")
        print_line.append("        .hreadyin                          (ahb_readyin       ),//input")
        print_line.append("        .hsel                              (ahb_sel           ),//input")
        print_line.append("        .htrans                            (ahb_trans[1:0]    ),//input")
        print_line.append("        .hwrite                            (ahb_write         ),//input")
        print_line.append("        .hburst                            (ahb_burst[2:0]    ),//input")
        print_line.append("        .hsize                             (ahb_size[2:0]     ),//input")
        print_line.append("        .haddr                             (ahb_addr[31:0]    ),//input")
        print_line.append("        .hwdata                            (ahb_wdata[31:0]   ),//input")
        print_line.append("        .hreadyout                         (ahb_readyout      ),//output")
        print_line.append("        .hresp                             (ahb_resp[1:0]     ),//output")
        print_line.append("        .hrdata                            (ahb_rdata[31:0]   ),//output")

    rst_reg_num = []
    rst_reg_bit_lc = []
    for rst_info in rst_corpus:
        if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
            continue    
        elif rst_info[rst_info_index["soft_src"]] == "SOFT":
            rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
            rst_reg_num.append(rst_info_reg_lc[0])
            rst_reg_bit_lc.append(rst_info_reg_lc[1]) 
    rst_reg_num = np.unique(rst_reg_num)
    count = 0
    for idx in rst_reg_num:
        reg_addr = hex(int(idx)*4)
        for rst_info in rst_corpus:
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue    
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(idx)]:
                    print_line.append("\t\t.soft_reset_ctrl"+str(int(count)).rjust(3,'0')+"_"+rst_info[rst_info_index["name"]]+"_sftrstn\t\t("+rst_info[rst_info_index["name"]]+"_sftrstn),")
        count += 1

    reg_addr_ofst = idx
    rst_status_count = 0
    count = 0
    for idx in rst_reg_num:
        reg_addr = hex((int(idx+reg_addr_ofst))*4)
        for rst_info in rst_corpus:
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue    
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(idx)]:
                    print_line.append("\t\t."+reg_name[int(count)]+"_status_"+rst_info[rst_info_index["name"]]+"_status\t\t("+rst_info[rst_info_index["name"]]+"),")
        count += 1
        rst_status_count += 1

    print_line[-1] = print_line[-1].strip(',')
    print_line.append('\t);\n')

    print_line.append("\t"+top_corpus[top_info_index["design_name"]][1]+" u_"+top_corpus[top_info_index["design_name"]][1]+"(/*autoinst*/);\n")
    print_line.append('endmodule')
    print_line.append('//Local Variables:')
    print_line.append('//verilog-library-directories:(".")')
    print_line.append('//verilog-library-directories:("$XML/")')
    print_line.append('//verilog-library-directories-recursive:0')
    print_line.append('//End:')
    print_line.append(' ')

    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    #fp.write('\n')
    #fp.write('endmodule')

    fp.close()
# }}}

# clk_gen_top{{{
def clk_gen_top(para_list, clk_corpus, clk_ser):
    fp = open(top_corpus[top_info_index["design_name"]][1]+"_top.v", "w") 
    
    print_line = []
    add_header(print_line, top_corpus[top_info_index["design_name"]][1]+"_top.v")
    #print_line.append('`include "sysvlog_interface_connect.h"')
    print_line.append("module "+top_corpus[top_info_index["design_name"]][1]+"_top(")
    #print_line.append('\tapb3_bus.slave  apb3_bus_clk_gen,')
    if top_corpus[top_info_index["protocol"]][1] == "apb":
        print_line.append('\tinput          apb_clk,')        
        print_line.append('\tinput          apb_rst_n,')    
        print_line.append('\tinput          apb_sel,')       
        print_line.append('\tinput          apb_enable,')    
        print_line.append('\tinput          apb_write,')     
        print_line.append('\tinput   [31:0] apb_addr, ')
        print_line.append('\tinput   [31:0] apb_wdata,')
        print_line.append('\toutput         apb_ready,')     
        print_line.append('\toutput  [31:0] apb_rdata,')
    elif top_corpus[top_info_index["protocol"]][1] == "dab":
        print_line.append('\tinput              dab_clk,')
        print_line.append('\tinput              dab_rst_n,')
        print_line.append('\tinput              dab_write,')
        print_line.append('\tinput              dab_read,')
        print_line.append('\tinput  [31:0]      dab_addr,')
        print_line.append('\tinput  [31:0]      dab_wdata,')
        print_line.append('\toutput [31:0]      dab_rdata,')
        print_line.append('\toutput             dab_ready,')
    elif top_corpus[top_info_index["protocol"]][1] == "ahb":
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
        print_line.append("    output [31:0]   ahb_rdata,")

    count = 0
    for clk_info in clk_corpus:
        #print(clk_info)
        count += 1 
        #if clk_info[clk_info_index["name"]] == "#NAME":
        #    continue
        if clk_info[clk_info_index["attr"]] == "input":
            #print("##################")
            print_line.append("\tinput           CLK_NAME,")
            #print(tplt.format("input", "CLK_NAME", ","))

        #if clk_info[clk_info_index["name"]] == "#Clocks for AHB":
        #    continue
        if clk_info[clk_info_index["attr"]] == "output":
            #print_line.append("\t// CLK_NAME")
            print_line.append("\toutput          CLK_NAME,")
        replace_CLK_NAME(clk_info, clk_info_index, top_info_index, print_line)
        port_last_process(count, clk_ser, print_line) 
    print_line.append(');\n')
   

    print_line.append('\t/*autodef*/\n')

    #print_line.append("\tassign psel          = apb3_bus_clk_gen.psel;")
    #print_line.append("\tassign penable       = apb3_bus_clk_gen.penable;")
    #print_line.append("\tassign pwrite        = apb3_bus_clk_gen.pwrite;")
    #print_line.append("\tassign paddr[31:0]   = apb3_bus_clk_gen.paddr;")
    #print_line.append("\tassign pwdata[31:0]  = apb3_bus_clk_gen.pwdata;")
    #print_line.append("\tassign apb3_bus_clk_gen.prdata  = prdata[31:0];")
    #print_line.append("\tassign apb3_bus_clk_gen.pslverr = 1'b0;")
    #print_line.append("\tassign apb3_bus_clk_gen.pready  = pready;\n")
    
    if top_corpus[top_info_index["protocol"]][1] == "dab":
        print_line.append("    "+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_"+protocol+"_regfile(/*autoinst*/")
        print_line.append("    .clk                                   (dab_clk             ), //input")
        print_line.append("    .reset_n                               (dab_rst_n           ), //input")
        print_line.append("    .dab_write                             (dab_write           ), //input")
        print_line.append("    .dab_read                              (dab_read            ), //input")
        print_line.append("    .dab_addr                              (dab_addr[31:0]      ), //input")
        print_line.append("    .dab_wdata                             (dab_wdata[31:0]     ), //input")
        print_line.append("    .dab_rdata                             (dab_rdata[31:0]     ), //output")
        print_line.append("    .dab_ready                             (dab_ready           ), //output")
    elif top_corpus[top_info_index["protocol"]][1] == "apb":
        print_line.append("    "+top_corpus[top_info_index["design_name"]][1].upper()+"_apb_regfile u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_apb_regfile(/*autoinst*/")
        print_line.append("        .clk                             (apb_clk                ),")
        print_line.append("        .reset_n                         (apb_rst_n              ),")
        print_line.append("        .psel                            (apb_sel                ),")
        print_line.append("        .penable                         (apb_enable             ),")
        print_line.append("        .pwrite                          (apb_write              ),")
        print_line.append("        .addr                            (apb_addr[31:0]         ),")
        print_line.append("        .wdata                           (apb_wdata[31:0]        ),")
        print_line.append("        .pready                          (apb_ready              ),")
        print_line.append("        .rdata                           (apb_rdata[31:0]        ),")
    elif protocol == "ahb" :
        print_line.append("    "+top_corpus[top_info_index["design_name"]][1].upper()+"_ahb_regfile u_"+top_corpus[top_info_index["design_name"]][1].upper()+"_ahb_regfile(/*autoinst*/")
        print_line.append("        .clk                               (ahb_clk           ),//input")
        print_line.append("        .rst_n                             (ahb_rst_n         ),//input")
        print_line.append("        .hreadyin                          (ahb_readyin       ),//input")
        print_line.append("        .hsel                              (ahb_sel           ),//input")
        print_line.append("        .htrans                            (ahb_trans[1:0]    ),//input")
        print_line.append("        .hwrite                            (ahb_write         ),//input")
        print_line.append("        .hburst                            (ahb_burst[2:0]    ),//input")
        print_line.append("        .hsize                             (ahb_size[2:0]     ),//input")
        print_line.append("        .haddr                             (ahb_addr[31:0]    ),//input")
        print_line.append("        .hwdata                            (ahb_wdata[31:0]   ),//input")
        print_line.append("        .hreadyout                         (ahb_readyout      ),//output")
        print_line.append("        .hresp                             (ahb_resp[1:0]     ),//output")
        print_line.append("        .hrdata                            (ahb_rdata[31:0]   ),//output")
    count = 0
    for clk_info in clk_corpus:
        count += 1 
        if clk_info[clk_info_index["attr"]] == "output" or clk_info[clk_info_index["attr"]] == "na":
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False:
                count += 1
                #print(count)
                if clk_info[clk_info_index["icg"]] == "Y":
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_ea\t\t("+clk_info[clk_info_index["name"]]+"_ea),")	
                if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_sel\t\t("+clk_info[clk_info_index["name"]]+"_sel),")	
                if pd.isna(clk_info[clk_info_index["div"]]) == False:
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ctrl_"+clk_info[clk_info_index["name"]]+"_divider\t\t("+clk_info[clk_info_index["name"]]+"_divider["+str(int(clk_info[clk_info_index["div_width"]]-1))+":0]),")	
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["div"]]) == False:
                count += 1
                #print(count)
                #if clk_info[clk_info_index["icg"]] == "Y":
                    #print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ea_req_"+clk_info[clk_info_index["name"]]+"_icg_ea_req\t\t("+clk_info[clk_info_index["name"]]+"_icg_ea_req),")	
                if pd.isna(clk_info[clk_info_index["div"]]) == False:
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_ea_req_"+clk_info[clk_info_index["name"]]+"_divider_ea_req\t\t("+clk_info[clk_info_index["name"]]+"_divider_ea_req),")	
            
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False:
                count += 1
                if clk_info[clk_info_index["icg"]] == "Y":
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_ea_status\t\t("+clk_info[clk_info_index["name"]]+"_ea_status),")	
                if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_sel_clk0_sel\t\t("+clk_info[clk_info_index["name"]]+"_sel_clk0_sel),")	
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_sel_clk1_sel\t\t("+clk_info[clk_info_index["name"]]+"_sel_clk1_sel),")	
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_sel_done\t\t("+clk_info[clk_info_index["name"]]+"_sel_done),")	
                if pd.isna(clk_info[clk_info_index["div"]]) == False:    
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_divider_status\t\t("+clk_info[clk_info_index["name"]]+"_divider_status["+str(int(clk_info[clk_info_index["div_width"]]-1))+":0]),")	
                    print_line.append("\t\t."+clk_info[clk_info_index["name"]]+"_status_"+clk_info[clk_info_index["name"]]+"_divider_done\t\t("+clk_info[clk_info_index["name"]]+"_divider_done),")	

                #print(count)            


    print_line[-1] = print_line[-1].strip(',')
    print_line.append('\t);\n')

    print_line.append("\t"+top_corpus[top_info_index["design_name"]][1]+" u_"+top_corpus[top_info_index["design_name"]][1]+"(/*autoinst*/);\n")
    print_line.append('endmodule')
    print_line.append('//Local Variables:')
    print_line.append('//verilog-library-directories:(".")')
    print_line.append('//verilog-library-directories:("$XML")')
    print_line.append('//verilog-library-directories-recursive:0')
    print_line.append('//End:')
    print_line.append(' ')

    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    #fp.write('\n')
    #fp.write('endmodule')

    fp.close()
# }}}

# rst_gen_note{{{
def rst_gen_note(para_list, rst_corpus, rst_ser):
    fp = open(top_corpus[top_info_index["design_name"]][1].upper()+".note", "w") 
    print_line = []

    print_line.append('// Component')
    print_line.append(top_corpus[top_info_index["design_name"]][1]+"      --  v1.0\n")
    print_line.append('// Block')
    if top_corpus[top_info_index["protocol"]][1] == "dab":
        print_line.append(top_corpus[top_info_index["design_name"]][1].upper()+"      --  0x0000:0x0fff  --  "+top_corpus[top_info_index["design_name"]][1]+" regfile       -- dab")
    elif top_corpus[top_info_index["protocol"]][1] == "apb":
        print_line.append(top_corpus[top_info_index["design_name"]][1].upper()+"      --  0x0000:0x0fff  --  "+top_corpus[top_info_index["design_name"]][1]+" regfile       -- apb")
    elif top_corpus[top_info_index["protocol"]][1] == "ahb":
        print_line.append(top_corpus[top_info_index["design_name"]][1].upper()+"      --  0x0000:0x0fff  --  "+top_corpus[top_info_index["design_name"]][1]+" regfile       -- ahb")
    print_line.append('// Register')
    rst_reg_num = []
    rst_reg_bit_lc = []
    for rst_info in rst_corpus:
        if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
            continue
        elif rst_info[rst_info_index["soft_src"]] == "SOFT":
            rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
            rst_reg_num.append(rst_info_reg_lc[0])
            rst_reg_bit_lc.append(rst_info_reg_lc[1])
    
    rst_reg_num = np.unique(rst_reg_num)

    #print(rst_reg_num)
    #print(rst_reg_bit_lc)


    count = 0
    for idx in rst_reg_num:
        reg_addr = hex(int(idx)*4)
        print_line.append(reg_addr+"				--		RW		--		soft_reset_ctrl"+str(int(count)).rjust(3,'0')+"			    --		[31:0]		--	soft_reset_ctrl"+str(int(count)).rjust(3,'0')) 	
        #print(count)
        count += 1
        for rst_info in rst_corpus:
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(idx)]:
                    if rst_info[rst_info_index["soft_dflt"]] == "N" :
                        print_line.append("--		'h1		--		RW		--		"+rst_info[rst_info_index["name"]]+"_sftrstn		                --		["+rst_info_reg_lc[1]+"]			--	"+rst_info[rst_info_index["name"]]+"_sftrstn")
                    else :
                        print_line.append("--		'h0		--		RW		--		"+rst_info[rst_info_index["name"]]+"_sftrstn		                --		["+rst_info_reg_lc[1]+"]			--	"+rst_info[rst_info_index["name"]]+"_sftrstn")
        print_line.append("\n")

    reg_addr_ofst = idx
    rst_status_count = 0
    for idx in rst_reg_num:
        reg_addr = hex(count*4)
        print_line.append(reg_addr+"				--		RO		--		soft_reset_status"+str(int(rst_status_count)).rjust(3,'0')+"				--		[31:0]		--	soft_reset_status"+str(int(rst_status_count)).rjust(3,'0')) 
        #print(count)
        count += 1
        rst_status_count += 1
        for rst_info in rst_corpus:
            if pd.isna(rst_info[rst_info_index["soft_lc"]]) == True or pd.isna(rst_info[rst_info_index["soft_src"]]) == True :
                continue
            elif rst_info[rst_info_index["soft_src"]] == "SOFT":
                rst_info_reg_lc  = rst_info[rst_info_index["soft_lc"]].split('-', 1)
                if rst_info_reg_lc[0] == rst_reg_num[int(idx)]:
                    print_line.append("--		'h0		--		RO		--		"+rst_info[rst_info_index["name"]]+"_status	                    --		["+rst_info_reg_lc[1]+"]			--	"+rst_info[rst_info_index["name"]]+"_status")
        print_line.append("\n")


    print_line.append("// Register end\n")   
    print_line.append("// Block end")
    print_line.append("// Component end")

    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')

    fp.close()
#}}}

# clk_gen_note{{{
def clk_gen_note(para_list, clk_corpus, clk_ser):
    fp = open(top_corpus[top_info_index["design_name"]][1].upper()+".note", "w") 
    print_line = []

    print_line.append('// Component')
    print_line.append(top_corpus[top_info_index["design_name"]][1]+"      --  v1.0\n")
    print_line.append('// Block')
    if top_corpus[top_info_index["protocol"]][1] == "dab":
        print_line.append(top_corpus[top_info_index["design_name"]][1].upper()+"      --  0x0000:0x0fff  --  "+top_corpus[top_info_index["design_name"]][1].upper()+" regfile       -- dab")
    elif top_corpus[top_info_index["protocol"]][1] == "apb":
        print_line.append(top_corpus[top_info_index["design_name"]][1].upper()+"      --  0x0000:0x0fff  --  "+top_corpus[top_info_index["design_name"]][1].upper()+" regfile       -- apb")
    elif top_corpus[top_info_index["protocol"]][1] == "ahb":
        print_line.append(top_corpus[top_info_index["design_name"]][1].upper()+"      --  0x0000:0x0fff  --  "+top_corpus[top_info_index["design_name"]][1].upper()+" regfile       -- ahb")
    print_line.append('// Register')
    
    count = 0
    for clk_info in clk_corpus:
        if clk_info[clk_info_index["attr"]] == "output" or clk_info[clk_info_index["attr"]] == "na":
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False:
                reg_addr = hex(count*4)
                print_line.append("\n")
                print_line.append(reg_addr+"    			--		RW		--		"+clk_info[clk_info_index["name"]]+"_ctrl			    --		[31:0]		--	"+clk_info[clk_info_index["name"]]+" control register")	
                count += 1
                #print(count)
            if clk_info[clk_info_index["icg"]] == "Y":
                print_line.append("--		'h0		--		RW		--		"+clk_info[clk_info_index["name"]]+"_ea		            --		[0]			--	"+clk_info[clk_info_index["name"]]+" icg enable")
            if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                print_line.append("--		'h0		--		RW		--		"+clk_info[clk_info_index["name"]]+"_sel		        --		[8]			--	"+clk_info[clk_info_index["name"]]+" select")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:
                print_line.append("--		'h0		--		RW		--		"+clk_info[clk_info_index["name"]]+"_divider		    --		["+str(int(clk_info[clk_info_index["div_width"]]+15))+":16]		--	"+clk_info[clk_info_index["name"]]+" divider")
            
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["div"]]) == False:
                reg_addr = hex(count*4)
                print_line.append("\n")
                print_line.append(reg_addr+"    	       --		RW		--		"+clk_info[clk_info_index["name"]]+"_ea_req				--		[31:0]		--	"+clk_info[clk_info_index["name"]]+" enable request")
                count += 1
                #print(count)
            #if clk_info[clk_info_index["icg"]] == "Y":
            #    print_line.append("--		'h0		--		RW		--		"+clk_info[clk_info_index["name"]]+"_icg_ea_req	        --		[0]			--	"+clk_info[clk_info_index["name"]]+" icg enable request")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:
                print_line.append("--		'h0		--		RW		--		"+clk_info[clk_info_index["name"]]+"_divider_ea_req	        --		[16]		--	"+clk_info[clk_info_index["name"]]+" divider enable request")
            
            if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["sel"]]) == False or pd.isna(clk_info[clk_info_index["div"]]) == False:
                reg_addr = hex(count*4)
                print_line.append("\n")
                print_line.append(reg_addr+"    	       --		RO		--		"+clk_info[clk_info_index["name"]]+"_status				--		[31:0]		--	"+clk_info[clk_info_index["name"]]+" status")
            if clk_info[clk_info_index["icg"]] == "Y":
                print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_ea_status		    --		[0]	    	--  "+clk_info[clk_info_index["name"]]+" icg enable status")	
            if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_sel_clk0_sel	    --		[8]			--	"+clk_info[clk_info_index["name"]]+" select clk1 status")
                print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_sel_clk1_sel	    --		[9]			--	"+clk_info[clk_info_index["name"]]+" select clk1 status")
                print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_sel_done		    --		[10]		--	"+clk_info[clk_info_index["name"]]+" select done status")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:    
                print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_divider_status	    --		["+str(int(clk_info[clk_info_index["div_width"]]+15))+":16]		--	"+clk_info[clk_info_index["name"]]+" divider status")
                print_line.append("--		'h0		--		RO		--		"+clk_info[clk_info_index["name"]]+"_divider_done	    --		[24]		--  "+clk_info[clk_info_index["name"]]+" divider done status")
            count += 1
            #print(count)

    print_line.append("\n")
    print_line.append("// Register end\n")   
    print_line.append("// Block end")
    print_line.append("// Component end")

    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')

    fp.close()
#}}}

#clk_gen{{{
def clk_gen(gen_filepath, top_corpus, clk_info_index, top_info_index, clk_corpus, clk_ser):
    fp = open(gen_filepath+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.v", "w") 
    if pd.isna(top_corpus[top_info_index["design_hier"]][1]) == False :
        design_hier = top_corpus[top_info_index["design_hier"]][1]+"/"
    else :
        design_hier = ""
    if pd.isna(top_corpus[top_info_index["design_hier"]][1]) == False :
        occ_design_hier = top_corpus[top_info_index["design_hier"]][1]+"."
    else :
        occ_design_hier = ""
    #print(top_corpus)
    #print(top_info_index)
    print_line = []
    add_header(print_line, top_corpus[top_info_index["design_name"]][1]+"_clk_gen.v")
    print_line.append("module "+top_corpus[top_info_index["design_name"]][1]+"_clk_gen(")

    count = 0
    if top_corpus[top_info_index["protocol"]][1] == "apb" :
        print_line.append("\tinput           apb_clk,")
        print_line.append("\tinput           apb_rst_n,")
    elif top_corpus[top_info_index["protocol"]][1] == "dab" :
        print_line.append("\tinput           dab_clk,")
        print_line.append("\tinput           dab_rst_n,")
    elif top_corpus[top_info_index["protocol"]][1] == "ahb" :
        print_line.append("\tinput           ahb_clk,")
        print_line.append("\tinput           ahb_rst_n,")
    print_line.append("    input           dft_icg_mode_root,")
    for clk_info in clk_corpus:
        count += 1 
        #if clk_info[clk_info_index["name"]] == "#NAME":
        #    continue
        if clk_info[clk_info_index["attr"]] == "input":
            print_line.append("\tinput           CLK_NAME,")
            #print(tplt.format("input", "CLK_NAME", ","))
        #if clk_info[clk_info_index["name"]] == "#Clocks for AHB":
        #    continue
        if clk_info[clk_info_index["attr"]] == "internal" and pd.isna(clk_info[clk_info_index["src0"]]) == True :
            print_line.append("\tinput           CLK_NAME,")
        if clk_info[clk_info_index["attr"]] == "output" or clk_info[clk_info_index["attr"]] == "na" or (clk_info[clk_info_index["attr"]] == "internal" and pd.isna(clk_info[clk_info_index["src0"]]) == False) :
            print_line.append("\t// CLK_NAME")
            if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                #print(pd.isna(clk_info[clk_info_index["sel"]]))
                if "," in clk_info[clk_info_index["sel"]] :
                    clk_sel = clk_info[clk_info_index["sel"]].split(",")
                    print_line.append("\tinput           "+clk_sel[1]+",")
                    print_line.append("\tinput           CLK_NAME_sel,")
                else :
                    print_line.append("\tinput           CLK_NAME_sel,")
                print_line.append("\toutput          CLK_NAME_sel_clk0_sel,")
                print_line.append("\toutput          CLK_NAME_sel_clk1_sel,")
                print_line.append("\toutput          CLK_NAME_sel_done,")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:
                #print(pd.isna(clk_info[clk_info_index["div"]]))
                #print_line.append("\toutput          CLK_NAME_en,")
                if pd.isna(clk_info[clk_info_index["div_val_to_en"]]) == False :
                    print_line.append("\tinput           "+clk_info[clk_info_index["div_val_to_en"]]+",")
                    other_clk_list = clk_info[clk_info_index["div_val_to"]].split("[")
                    print_line.append("\tinput [ "+str(int(int(clk_info[clk_info_index["div_width"]]-1)))+":0]    "+other_clk_list[0]+",")
                if pd.isna(clk_info[clk_info_index["divider_fadj"]]) == False :
                    print_line.append("\tinput           "+clk_info[clk_info_index["divider_fadj"]]+",")
                if pd.isna(clk_info[clk_info_index["divider_fadj_val"]]) == False :
                    other_clk_list = clk_info[clk_info_index["divider_fadj_val"]].split("[")
                    print_line.append("\tinput [ "+str(int(int(clk_info[clk_info_index["div_width"]]-1)))+":0]    "+other_clk_list[0]+",")
                print_line.append("\tinput [ "+str(int(int(clk_info[clk_info_index["div_width"]]-1)))+":0]    CLK_NAME_divider,")
                print_line.append("\tinput           CLK_NAME_divider_ea_req,")
                print_line.append("\toutput[ "+str(int(clk_info[clk_info_index["div_width"]]-1))+":0]    CLK_NAME_divider_status,")
                #print_line.append("\toutput          CLK_NAME_divider_ea_ack,")
                print_line.append("\toutput          CLK_NAME_divider_done,")
            if clk_info[clk_info_index["icg"]] == "Y":
                #if clk_info[clk_info_index["attr"]] == "output" :
                if clk_info[clk_info_index["ce_en"]] == "Y" : 
                    print_line.append("\tinput           CLK_NAME_ce,")
                print_line.append("\tinput           CLK_NAME_ea,")
                #print_line.append("\tinput           CLK_NAME_icg_ea_req,") 
                #print_line.append("\toutput          CLK_NAME_icg_ea_ack,")
                print_line.append("\toutput          CLK_NAME_ea_status,")
            if pd.isna(clk_info[clk_info_index["icg_external"]]) == False :
                if "[" in clk_info[clk_info_index["icg_external"]] :
                    other_clk_list = clk_info[clk_info_index["icg_external"]].split("[")
                    #print(other_clk_list)
                    print_line.append("\tinput     ["+other_clk_list[1]+"  "+other_clk_list[0]+",")
                    print_line.append("\toutput    ["+other_clk_list[1]+"  "+clk_info[clk_info_index["name"]]+"_"+other_clk_list[0]+"_sync,")
                else :
                    print_line.append("\tinput              "+clk_info[clk_info_index["icg_external"]]+",")
                    #print_line.append("\toutput             "+clk_info[clk_info_index["icg_external"]]+"_sync,")
                    print_line.append("\toutput             "+clk_info[clk_info_index["name"]]+"_"+clk_info[clk_info_index["icg_external"]]+"_sync,")
            if pd.isna(clk_info[clk_info_index["icg_internal"]]) == False :
                if "[" in clk_info[clk_info_index["icg_internal"]] :
                    other_clk_list = clk_info[clk_info_index["icg_internal"]].split("[")
                    #print(other_clk_list)
                    print_line.append("\tinput     ["+other_clk_list[1]+"  "+other_clk_list[0]+",")
                else :
                    print_line.append("\tinput              "+clk_info[clk_info_index["icg_internal"]]+",")
            if clk_info[clk_info_index["attr"]] == "output" or (clk_info[clk_info_index["attr"]] == "internal" and pd.isna(clk_info[clk_info_index["src0"]]) == False) :
                print_line.append("\toutput          CLK_NAME,")
                if clk_info[clk_info_index["attr"]] == "output" and clk_info[clk_info_index["ce_en"]] == "Y" :
                    print_line.append("\toutput          CLK_NAME_cg_bf,")
        replace_CLK_NAME(clk_info, clk_info_index, top_info_index, print_line)
        #print("count is :", count)
        port_last_process(count, clk_ser, print_line)
    print_line.append(');\n')

    count = 0
    for clk_info in clk_corpus :
        count += 1 
        if pd.isna(clk_info[clk_info_index["sel"]]) == False :
            print_line.append("wire         CLK_NAME_sel_clk0_sel_bf_sync;")
            print_line.append("wire         CLK_NAME_sel_clk1_sel_bf_sync;")
            print_line.append("wire         CLK_NAME_sel_done_bf_sync;")
            print_line.append("wire         CLK_NAME_muxed;")
        if clk_info[clk_info_index["attr"]] == "output" or clk_info[clk_info_index["attr"]] == "na" or clk_info[clk_info_index["attr"]] == "internal":
            if clk_info[clk_info_index["attr"]] == "na" and pd.isna(clk_info[clk_info_index["src0"]]) == False :
                print_line.append("wire        "+clk_info[clk_info_index["name"]]+";")
            if pd.isna(clk_info[clk_info_index["div"]]) == False :
                #print_line.append("wire [ "+str(int(clk_info[clk_info_index["div_width"]]-1))+":0] CLK_NAME_divider_sync;")
                #print_line.append("wire [ "+str(int(clk_info[clk_info_index["div_width"]]-1))+":0] CLK_NAME_divider_sync_func;")
                #print_line.append("wire [ "+str(int(clk_info[clk_info_index["div_width"]]-1))+":0] CLK_NAME_divider_to;")
                ##print_line.append("wire         CLK_NAME_divider_en;")
                #print_line.append("wire         CLK_NAME_divider_ea_req_sync;")
                #print_line.append("wire         CLK_NAME_divider_ea_req_done;")
                #if clk_info[clk_info_index["icg"]] == "Y" or pd.isna(clk_info[clk_info_index["occ_scan_mux"]]) == False :
                print_line.append("wire        CLK_NAME_dived;")

                if pd.isna(clk_info[clk_info_index["divider_fadj_val"]]) == False :
                    print_line.append("wire ["+str(int(int(clk_info[clk_info_index["div_width"]]-1)))+":0]    CLK_NAME_divider_fadj_val;")
            #if "," in str(clk_info[clk_info_index["clock_group0"]]) :    
            #    print_line.append("wire         CLK_NAME_divider_bf_en;")
            if clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX":
                print_line.append("wire        CLK_NAME_scan_mux;")
            elif clk_info[clk_info_index["occ_scan_mux"]] == "OCC":
                #print_line.append("wire        CLK_NAME_buf_in;")
                print_line.append("wire        CLK_NAME_buf_out;")
            if clk_info[clk_info_index["icg"]] == "Y":
                print_line.append("wire        CLK_NAME_ea_sync;")
                print_line.append("wire        CLK_NAME_ea_multi;")
        if pd.isna(clk_info[clk_info_index["icg_external"]]) == False :
            if "[" in clk_info[clk_info_index["icg_external"]] :
        #        other_clk_list = clk_info[clk_info_index["icg_external"]].split("[")
                print_line.append("genvar   i;")
        #        print_line.append("wire     ["+other_clk_list[1]+"      "+other_clk_list[0]+"_sync;")
        #    else :
        #        print_line.append("wire     "+clk_info[clk_info_index["name"]]+"_"+clk_info[clk_info_index["icg_external"]]+"_sync;")
        if pd.isna(clk_info[clk_info_index["icg_internal"]]) == False :
            if "[" in clk_info[clk_info_index["icg_internal"]] :
                other_clk_list = clk_info[clk_info_index["icg_internal"]].split("[")
                print_line.append("genvar   i;")
                print_line.append("wire     ["+other_clk_list[1]+"      "+other_clk_list[0]+"_sync;")
            else :
                print_line.append("wire     "+clk_info[clk_info_index["name"]]+"_"+clk_info[clk_info_index["icg_internal"]]+"_sync;")



        replace_CLK_NAME(clk_info, clk_info_index, top_info_index, print_line)

    for repeat_idx in range(len(print_line)-1, -1, -1) :
        if print_line.count(print_line[repeat_idx]) > 1 and "wire" in print_line[repeat_idx] :
            print_line.pop(repeat_idx)
        if print_line.count(print_line[repeat_idx]) > 1 and "genvar" in print_line[repeat_idx] :
            print_line.pop(repeat_idx)
        if print_line.count(print_line[repeat_idx]) > 1 and "input" in print_line[repeat_idx] :
            print_line.pop(repeat_idx)
        if print_line.count(print_line[repeat_idx]) > 1 and "output" in print_line[repeat_idx] :
            print_line.pop(repeat_idx)

    count = 0
    tdr_buf_list = []
    occ_buf_list = []
    div_list = []
    for clk_info in clk_corpus:
        count += 1 
        #print(clk_info[clk_info_index["attr"]])
        if clk_info[clk_info_index["attr"]] == "output" or clk_info[clk_info_index["attr"]] == "na" or (clk_info[clk_info_index["attr"]] == "internal" and pd.isna(clk_info[clk_info_index["src0"]]) == False) :
            print_line.append("//===============")
            print_line.append("// CLK_NAME ctrl")
            print_line.append("//===============")
            if pd.isna(clk_info[clk_info_index["sel"]]) == False:
                if clk_info[clk_info_index["mux_dflt"]] == 1 :
                    tdr_buf_list.append(design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/u_dontouch_tdr_buf/u_std_cell_buf 1")
                else :
                    tdr_buf_list.append(design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_clk_glitch_free_switch/u_dontouch_tdr_buf/u_std_cell_buf 0")
                print_line.append("// clk sel")
                print_line.append("clk_glitch_free_switch u_CLK_NAME_clk_glitch_free_switch(")
                print_line.append("    .test_mode  (test_mode              ),")
                print_line.append("    .rst0_n     (clk_gen_rst_n          ),")
                print_line.append("    .rst1_n     (clk_gen_rst_n          ),")
                print_line.append("    .clk0       ("+clk_info[clk_info_index["src0"]]+"        ),")
                print_line.append("    .clk1       ("+clk_info[clk_info_index["src1"]]+"        ),")
                if "," in clk_info[clk_info_index["sel"]] :
                    clk_sel = clk_info[clk_info_index["sel"]].split(",")
                    if clk_info[clk_info_index["mux_dflt"]] == 1 :
                        print_line.append("    .sel        (CLK_NAME_sel & "+clk_sel[1]+"       ),")
                    else :
                        print_line.append("    .sel        (CLK_NAME_sel | "+clk_sel[1]+"       ),")
                else :
                    print_line.append("    .sel        (CLK_NAME_sel           ),")
                print_line.append("    .clk0_sel   (CLK_NAME_sel_clk0_sel_bf_sync  ),")
                print_line.append("    .clk1_sel   (CLK_NAME_sel_clk1_sel_bf_sync  ),")
                print_line.append("    .sel_done   (CLK_NAME_sel_done_bf_sync      ),")
                #print_line.append("    .clk_out    ("+clk_info[clk_info_index["name"]]+"         )")
                print_line.append("    .clk_out    (CLK_NAME_muxed         )")
                print_line.append(");")
                print_line.append("")
                print_line.append("sync")
                print_line.append("#(")
                print_line.append("    .D_WIDTH        (1        ),")
                if top_corpus[top_info_index["delay_beat"]][1] == 3 :
                    print_line.append("    .DELAY_2        (1'b0      ),")
                if clk_info[clk_info_index["mux_dflt"]] == 1 :
                    print_line.append("    .DATA_DEFAULT   (1'b0      )")
                else :
                    print_line.append("    .DATA_DEFAULT   (1'b1      )")
                print_line.append(")")
                print_line.append("u_CLK_NAME_sel_clk0_sel_sync(")
                if top_corpus[top_info_index["protocol"]][1] == "apb":
                    print_line.append("    .clk_d      (apb_clk                ),")
                    print_line.append("    .rst_d_n    (apb_rst_n              ),")
                elif top_corpus[top_info_index["protocol"]][1] == "dab":
                    print_line.append("    .clk_d      (dab_clk                ),")
                    print_line.append("    .rst_d_n    (dab_rst_n        ),")
                elif top_corpus[top_info_index["protocol"]][1] == "ahb":
                    print_line.append("    .clk_d      (ahb_clk                ),")
                    print_line.append("    .rst_d_n    (ahb_rst_n        ),")
                print_line.append("    .data_s     (CLK_NAME_sel_clk0_sel_bf_sync),")
                print_line.append("    .data_d     (CLK_NAME_sel_clk0_sel)")
                print_line.append(");")
                print_line.append("")
                print_line.append("sync")
                print_line.append("#(")
                print_line.append("    .D_WIDTH        (1        ),")
                if top_corpus[top_info_index["delay_beat"]][1] == 3 :
                    print_line.append("    .DELAY_2        (1'b0      ),")
                if clk_info[clk_info_index["mux_dflt"]] == 1 :
                    print_line.append("    .DATA_DEFAULT   (1'b1      )")
                else :
                    print_line.append("    .DATA_DEFAULT   (1'b0      )")

                print_line.append(")")
                print_line.append("u_CLK_NAME_sel_clk1_sel_sync(")
                if top_corpus[top_info_index["protocol"]][1] == "apb":
                    print_line.append("    .clk_d      (apb_clk                ),")
                    print_line.append("    .rst_d_n    (apb_rst_n              ),")
                elif top_corpus[top_info_index["protocol"]][1] == "dab":
                    print_line.append("    .clk_d      (dab_clk                ),")
                    print_line.append("    .rst_d_n    (dab_rst_n              ),")
                elif top_corpus[top_info_index["protocol"]][1] == "ahb":
                    print_line.append("    .clk_d      (ahb_clk                ),")
                    print_line.append("    .rst_d_n    (ahb_rst_n              ),")
                print_line.append("    .data_s     (CLK_NAME_sel_clk1_sel_bf_sync),")
                print_line.append("    .data_d     (CLK_NAME_sel_clk1_sel)")
                print_line.append(");")
                print_line.append("")
                print_line.append("sync")
                print_line.append("#(")
                print_line.append("    .D_WIDTH        (1        ),")
                if top_corpus[top_info_index["delay_beat"]][1] == 3 :
                    print_line.append("    .DELAY_2        (1'b0      ),")
                print_line.append("    .DATA_DEFAULT   (1'b1      )")
                print_line.append(")")
                print_line.append("u_CLK_NAME_sel_done_sync(")
                if top_corpus[top_info_index["protocol"]][1] == "apb":
                    print_line.append("    .clk_d      (apb_clk                ),")
                    print_line.append("    .rst_d_n    (apb_rst_n              ),")
                elif top_corpus[top_info_index["protocol"]][1] == "dab":
                    print_line.append("    .clk_d      (dab_clk                ),")
                    print_line.append("    .rst_d_n    (dab_rst_n              ),")
                elif top_corpus[top_info_index["protocol"]][1] == "ahb":
                    print_line.append("    .clk_d      (ahb_clk                ),")
                    print_line.append("    .rst_d_n    (ahb_rst_n              ),")
                print_line.append("    .data_s     (CLK_NAME_sel_done_bf_sync),")
                print_line.append("    .data_d     (CLK_NAME_sel_done)")
                print_line.append(");")
                print_line.append("")
            if pd.isna(clk_info[clk_info_index["div"]]) == False:
                div_list.append(design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_divider_wrap/  #divider_width "+str(int(clk_info[clk_info_index["div_width"]])))
                binary_string = list(reversed(list(bin(int(clk_info[clk_info_index["div_dflt"]]))[2:])))
                #print(binary_string)
                for tdr_buf_index in range(int(clk_info[clk_info_index["div_width"]])) :
                    #print(tdr_buf_index)
                    #print(len(binary_string))
                    if(tdr_buf_index >= len(binary_string)) :
                        tdr_buf_list.append(design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_divider_wrap/u_clk_divider_test_tdr_mux/dontouch_tdr_"+str(tdr_buf_index)+"__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    else :
                        tdr_buf_list.append(design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen/u_"+clk_info[clk_info_index["name"]]+"_divider_wrap/u_clk_divider_test_tdr_mux/dontouch_tdr_"+str(tdr_buf_index)+"__u_dontouch_tdr_buf/u_std_cell_buf "+str(binary_string[int(tdr_buf_index)]))

                #if pd.isna(clk_info[clk_info_index["div_val_to_en"]]) == False :
                #    print_line.append("assign CLK_NAME_divider_to = "+clk_info[clk_info_index["div_val_to_en"]]+" ? (("+clk_info[clk_info_index["div_val_to"]]+" > CLK_NAME_divider) ? "+clk_info[clk_info_index["div_val_to"]]+" : CLK_NAME_divider) : CLK_NAME_divider;")
                #else :
                #    print_line.append("assign CLK_NAME_divider_to = CLK_NAME_divider;")
                print_line.append("clk_divider_wrap")
                print_line.append("        #(")
                print_line.append("    .PRRWIDTH        ("+str(int(clk_info[clk_info_index["div_width"]]))+"),")
                if "bypass" in clk_info[clk_info_index["div"]] :
                    print_line.append("    .BYPASS          (1'b1),")
                else :
                    print_line.append("    .BYPASS          (1'b0),")
                if top_corpus[top_info_index["delay_beat"]][1] == 3 :
                    print_line.append("    .DELAY_2          (1'b0),")
                else :
                    print_line.append("    .DELAY_2          (1'b1),")
                if pd.isna(clk_info[clk_info_index["div_val_to_en"]]) == False :
                    print_line.append("    .DIV_VAL_TO_EN          (1'b1),")
                else :
                    print_line.append("    .DIV_VAL_TO_EN          (1'b0),")
                print_line.append("    .DEFAULT_VALUE   ("+str(int(clk_info[clk_info_index["div_dflt"]]))+")")
                print_line.append("    )")
                print_line.append("u_CLK_NAME_divider_wrap(/*autoinst*/")
                print_line.append("    .test_mode              (test_mode               ), //input")
                if top_corpus[top_info_index["protocol"]][1] == "apb":
                    print_line.append("    .cfg_clk                (apb_clk                 ), //input")
                    print_line.append("    .cfg_rst_n              (apb_rst_n               ), //input")
                elif top_corpus[top_info_index["protocol"]][1] == "dab":
                    print_line.append("    .cfg_clk                (dab_clk                 ), //input")
                    print_line.append("    .cfg_rst_n              (dab_rst_n               ), //input")
                elif top_corpus[top_info_index["protocol"]][1] == "ahb":
                    print_line.append("    .cfg_clk                (ahb_clk                 ), //input")
                    print_line.append("    .cfg_rst_n              (ahb_rst_n               ), //input")
                if pd.isna(clk_info[clk_info_index["divider_sync_clk"]]) == False :
                    print_line.append("    .clk_div_sync_clk       ("+clk_info[clk_info_index["divider_sync_clk"]]+" ), //input")
                    print_line.append("    .clk_in                 ("+clk_info[clk_info_index["src0"]]+" ), //input")
                elif pd.isna(clk_info[clk_info_index["sel"]]) == False :
                    print_line.append("    .clk_div_sync_clk       (CLK_NAME_muxed          ), //input")
                    print_line.append("    .clk_in                 (CLK_NAME_muxed          ), //input")
                else :
                    print_line.append("    .clk_div_sync_clk       ("+clk_info[clk_info_index["src0"]]+"), //input")
                    print_line.append("    .clk_in                 ("+clk_info[clk_info_index["src0"]]+"), //input")
                print_line.append("    .clk_gen_rst_n          (clk_gen_rst_n                       ), //input")
                if pd.isna(clk_info[clk_info_index["div_val_to_en"]]) == False :
                    print_line.append("    .clk_div_to_en          ("+clk_info[clk_info_index["div_val_to_en"]]+" ), //input")
                    print_line.append("    .clk_to_divider         ("+clk_info[clk_info_index["div_val_to"]]+"    ), //input")
                else :
                    print_line.append("    .clk_div_to_en          (1'b0                  ), //input")
                    print_line.append("    .clk_to_divider         ("+str(int(clk_info[clk_info_index["div_width"]]))+"'b0 ), //input")
                if pd.isna(clk_info[clk_info_index["divider_fadj"]]) == False :
                    print_line.append("    .clk_divider_ea_req     (CLK_NAME_divider_ea_req  | "+clk_info[clk_info_index["divider_fadj"]]+"), //input")
                else :
                    print_line.append("    .clk_divider_ea_req     (CLK_NAME_divider_ea_req ), //input")

                if pd.isna(clk_info[clk_info_index["divider_fadj_val"]]) == False :
                    print_line.append("    .clk_divider            (CLK_NAME_divider_fadj_val  ), //input")
                else :
                    print_line.append("    .clk_divider            (CLK_NAME_divider           ), //input")
                print_line.append("    .clk_divider_status     (CLK_NAME_divider_status    ), //output")
                print_line.append("    .clk_divider_done       (CLK_NAME_divider_done      ), //output")
                print_line.append("    .clk_dived              (CLK_NAME_dived             )  //output")
                print_line.append("    );")
                if pd.isna(clk_info[clk_info_index["divider_fadj_val"]]) == False :
                    print_line.append("assign CLK_NAME_divider_fadj_val = "+clk_info[clk_info_index["divider_fadj"]]+" ? "+clk_info[clk_info_index["divider_fadj_val"]]+" : CLK_NAME_divider;")
                #if top_corpus[top_info_index["protocol"]][1] == "apb":
                #    print_line.append("always @(posedge apb_clk or negedge apb_rst_n)begin")
                #    print_line.append("    if(!apb_rst_n)begin")
                #elif top_corpus[top_info_index["protocol"]][1] == "dab":
                #    print_line.append("always @(posedge dab_clk or negedge dab_rst_n)begin")
                #    print_line.append("    if(!dab_rst_n)begin")
                #elif top_corpus[top_info_index["protocol"]][1] == "ahb":
                #    print_line.append("always @(posedge ahb_clk or negedge ahb_rst_n)begin")
                #    print_line.append("    if(!ahb_rst_n)begin")
                #print_line.append("        CLK_NAME_divider_done <= 1'b0;")
                #print_line.append("    end")
                #print_line.append("    else if(CLK_NAME_divider_ea_req == 1'b1)begin")
                #print_line.append("        CLK_NAME_divider_done <= 1'b0;")
                #print_line.append("    end")
                #print_line.append("    else if(CLK_NAME_divider_ea_req_done == 1'b1)begin")
                #print_line.append("        CLK_NAME_divider_done <= 1'b1;")
                #print_line.append("    end")
                #print_line.append("end")
                #print_line.append("")
                ##print(top_corpus[top_info_index["delay_beat"]][1])
                #if top_corpus[top_info_index["delay_beat"]][1] == 3 :
                #    #print(top_corpus[top_info_index["delay_beat"]][1])
                #    print_line.append("pulse_sync")
                #    print_line.append("#(")
                #    print_line.append("    .DELAY_2        (1'b0      )")
                #    print_line.append(")")
                #    print_line.append("u_CLK_NAME_divider_req_done_sync(")
                #else :
                #    #print(top_corpus[top_info_index["delay_beat"]][1])
                #    print_line.append("pulse_sync u_CLK_NAME_divider_req_done_sync(")
                #if pd.isna(clk_info[clk_info_index["divider_sync_clk"]]) == False :
                #    print_line.append("    .src_clk                ("+clk_info[clk_info_index["divider_sync_clk"]]+"            ), //input")
                #elif pd.isna(clk_info[clk_info_index["sel"]]) == False :
                #    print_line.append("    .src_clk                (CLK_NAME_muxed              ), //input")
                #else :
                #    print_line.append("    .src_clk                ("+clk_info[clk_info_index["src0"]]+"             ), //input")
                #print_line.append("    .src_rst_n              (clk_gen_rst_n               ), //input")
                #print_line.append("    .src_pulse              (CLK_NAME_divider_ea_req_sync), //input")
                #if top_corpus[top_info_index["protocol"]][1] == "apb":
                #    print_line.append("    .dst_clk                (apb_clk                 ), //input")
                #    print_line.append("    .dst_rst_n              (apb_rst_n               ), //input")
                #elif top_corpus[top_info_index["protocol"]][1] == "dab":
                #    print_line.append("    .dst_clk                (dab_clk                 ), //input")
                #    print_line.append("    .dst_rst_n              (dab_rst_n               ), //input")
                #elif top_corpus[top_info_index["protocol"]][1] == "ahb":
                #    print_line.append("    .dst_clk                (ahb_clk                 ), //input")
                #    print_line.append("    .dst_rst_n              (ahb_rst_n               ), //input")
                #print_line.append("    .src_sync_fail          (                            ), //output")
                #print_line.append("    .dst_pulse              (CLK_NAME_divider_ea_req_done)  //output")
                #print_line.append(");           ")
                #print_line.append("")
                #print_line.append("// clk div sync")
                #print_line.append("dmux_sync ")
                #print_line.append("#(")
                #if top_corpus[top_info_index["delay_beat"]][1] == 3 :
                #    print_line.append("    .DELAY_2        (1'b0      ),")
                #print_line.append("    .DATA_WIDTH     ("+str(int(clk_info[clk_info_index["div_width"]]))+"),")
                #print_line.append("    .DEFAULT_VALUE  ("+str(int(clk_info[clk_info_index["div_dflt"]]))+")")
                #print_line.append(")")
                #print_line.append("u_CLK_NAME_div_sync(")
                #if top_corpus[top_info_index["protocol"]][1] == "apb":
                #    print_line.append("    .clk_src                (apb_clk                         ), //input")
                #    print_line.append("    .rstn_src               (apb_rst_n                       ), //input")
                #elif top_corpus[top_info_index["protocol"]][1] == "dab":
                #    print_line.append("    .clk_src                (dab_clk                         ), //input")
                #    print_line.append("    .rstn_src               (dab_rst_n                       ), //input")
                #elif top_corpus[top_info_index["protocol"]][1] == "ahb":
                #    print_line.append("    .clk_src                (ahb_clk                         ), //input")
                #    print_line.append("    .rstn_src               (ahb_rst_n                       ), //input")
                #print_line.append("    .data_in                (CLK_NAME_divider                ), //input")
                ##if "," in str(clk_info[clk_info_index["clock_group0"]]) :
                ##    print_line.append("    .datain_en              (CLK_NAME_divider_bf_en          ), //input")
                ##else :
                #if pd.isna(clk_info[clk_info_index["divider_fadj"]]) == False :
                #    print_line.append("    .datain_en              (CLK_NAME_divider_ea_req | "+clk_info[clk_info_index["divider_fadj"]]+"), //input")
                #else :
                #    print_line.append("    .datain_en              (CLK_NAME_divider_ea_req         ), //input")
                #if pd.isna(clk_info[clk_info_index["divider_sync_clk"]]) == False :
                #    print_line.append("    .clk_dst                ("+clk_info[clk_info_index["divider_sync_clk"]]+"            ), //input")
                #elif pd.isna(clk_info[clk_info_index["sel"]]) == False :
                #    print_line.append("    .clk_dst                (CLK_NAME_muxed              ), //input")
                #else :
                #    print_line.append("    .clk_dst                ("+clk_info[clk_info_index["src0"]]+"             ), //input")

                #print_line.append("    .rstn_dst               (clk_gen_rst_n                   ), //input")
                #print_line.append("    .data_out               (CLK_NAME_divider_sync           ), //output")
                #print_line.append("    .dataout_en             (CLK_NAME_divider_ea_req_sync    )  //output")
                #print_line.append(");")
                #print_line.append("")
            
                #if pd.isna(clk_info[clk_info_index["div_val_to_en"]]) == False :
                #    print_line.append("assign CLK_NAME_divider_to = "+clk_info[clk_info_index["div_val_to_en"]]+"? "+clk_info[clk_info_index["div_val_to"]]+": CLK_NAME_divider_sync;")
                #else :
                #    print_line.append("assign CLK_NAME_divider_to = CLK_NAME_divider_sync;")
               
                #print_line.append("test_tdr_mux ")
                #print_line.append("#(")
                #print_line.append("    .D_WIDTH    ("+str(int(clk_info[clk_info_index["div_width"]]))+")")
                #print_line.append(")")
                #print_line.append("u_CLK_NAME_divider_test_tdr_mux(")
                #print_line.append("        .test_mode              (test_mode                      ), //input")
                #print_line.append("        .func_in                (CLK_NAME_divider_to            ), //input")
                #print_line.append("        .func_out               (CLK_NAME_divider_sync_func     )  //output")
                #print_line.append(");")


 
                #if "bypass" in clk_info[clk_info_index["div"]] :
                #    print_line.append(clk_info[clk_info_index["div"]].replace("_bypass", ""))
                #else :
                #    print_line.append(clk_info[clk_info_index["div"]])
                #print_line.append("    #(")
                #if "bypass" in clk_info[clk_info_index["div"]] :
                #    print_line.append("        .BYPASS                 (1'b1        ),") 
                #print_line.append("        .PRRWIDTH               ("+str(int(clk_info[clk_info_index["div_width"]]))+"           )") 
                #print_line.append("    )")
                #print_line.append("u_CLK_NAME_divider(")
                #if pd.isna(clk_info[clk_info_index["sel"]]) == False :
                #    print_line.append("    .clk_in                 (CLK_NAME_muxed             ), //input")
                #else :
                #    print_line.append("    .clk_in                 ("+clk_info[clk_info_index["src0"]]+"                ), //input")
                #print_line.append("    .test_mode              (test_mode                      ),")
                #print_line.append("    .rst_n                  (clk_gen_rst_n                  ), //input")
                #print_line.append("    .divisor                (CLK_NAME_divider_sync_func     ), //input")
                ##if clk_info[clk_info_index["icg"]] == "Y" or clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX" or clk_info[clk_info_index["occ_scan_mux"]] == "OCC":
                #print_line.append("    .clk_out                (CLK_NAME_dived                 ), //output")
                ##else :
                ##    print_line.append("    .clk_out                ("+clk_info[clk_info_index["name"]]+"            ), //output")
                #print_line.append("    .divider_status         (CLK_NAME_divider_status        ), //output")
                #print_line.append("    .divider_done           (                               )  //output")
                #print_line.append(");")
            #else :
            #    if clk_info[clk_info_index["icg"]] == "Y":
            #        print_line.append("assign CLK_NAME_dived = "+clk_info[clk_info_index["name"]]+";")

            #print(clk_info[clk_info_index["occ_scan_mux"]])
            if clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX":
                #print("####################################################")
                print_line.append("// clk scan mux")
                print_line.append("scan_clk_mux u_CLK_NAME_scan_clk_mux(")
                if pd.isna(clk_info[clk_info_index["div"]]) == False :
                    print_line.append("    .clkin0       (CLK_NAME_dived         ),")
                elif pd.isna(clk_info[clk_info_index["sel"]]) == False :
                    print_line.append("    .clkin0       (CLK_NAME_muxed         ),")
                else :
                    print_line.append("    .clkin0       ("+clk_info[clk_info_index["src0"]]+"        ),")
                print_line.append("    .clkin1       (scan_clk                ),")
                print_line.append("    .sel          (test_mode               ),")
                print_line.append("    .clkout       (CLK_NAME_scan_mux       )")
                print_line.append(");")
            elif clk_info[clk_info_index["occ_scan_mux"]] == "OCC":
                clock_freq = (1 / float(clk_info[clk_info_index["note"]].strip("MHz"))) * 1000
                clock_freq_half = clock_freq / 2
                occ_buf_list.append("clock -name sdr_asic_top."+occ_design_hier+"u_"+top_corpus[top_info_index["design_name"]][1]+"_clk_gen.u_"+clk_info[clk_info_index["name"]]+"_buf_for_occ.u_clk_buf_for_occ.Z -domain "+clk_info[clk_info_index["name"]]+"_domain -atspeed -testclock -period "+str(int(clock_freq*10000)/10000)+" -edge {0 1}")

                print_line.append("clk_buf_for_occ u_CLK_NAME_buf_for_occ(/*autoinst*/")
                if pd.isna(clk_info[clk_info_index["div"]]) == False :
                    print_line.append("    .clkin                  (CLK_NAME_dived     ), //input")
                elif pd.isna(clk_info[clk_info_index["sel"]]) == False :
                    print_line.append("    .clkin                  (CLK_NAME_muxed     ), //input")
                else :
                    print_line.append("    .clkin                  ("+clk_info[clk_info_index["src0"]]+"     ), //input")
                print_line.append("    .clkout                 (CLK_NAME_buf_out    )  //output")
                print_line.append(");")
            if clk_info[clk_info_index["icg"]] == "Y": 
                #print_line.append("// clk icg sync")
                #print_line.append("clk_icg_sync")
                #print_line.append("#(")
                #print_line.append("    .D_WIDTH        (1       ),")
                #print_line.append("    .DATA_DEFAULT   (1'b1    )")
                #print_line.append(")")
                #print_line.append("u_CLK_NAME_icg_sync(")
                #if clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX":
                #    print_line.append("    .clk_d      (CLK_NAME_scan_mux       ),")
                #else:
                #    print_line.append("    .clk_d      ("+clk_info[clk_info_index["src0"]]+"         ),")
                #print_line.append("    .rst_d_n    (clk_gen_rst_n            ),")
                #print_line.append("    .data_s     (CLK_NAME_ea             ),")
                #print_line.append("    .data_d     (CLK_NAME_ea_sync        ),")
                #print_line.append("    .ea_req     (CLK_NAME_icg_ea_req     ),")
                #print_line.append("    .ea_ack     (CLK_NAME_icg_ea_ack     )")
                #print_line.append(");")
                if pd.isna(clk_info[clk_info_index["icg_external"]]) == False :
                    if "[" in clk_info[clk_info_index["icg_external"]] :
                        other_clk_list = clk_info[clk_info_index["icg_external"]].split("[")
                        #print(other_clk_list)
                        #print_line.append("\tinput     ["+other_clk_list[1]+"  "+other_clk_list[0]+",")
                        width = other_clk_list[1].split(":")
                        print_line.append("generate ")
                        print_line.append("    for (i = 0; i <= "+width[0]+"; i = i+1)begin:gen_"+other_clk_list[0]+"_sync")
                        print_line.append("sync ")
                        print_line.append("    #(")
                        print_line.append("    .D_WIDTH                (1                              ),")
                        if top_corpus[top_info_index["delay_beat"]][1] == 3 :
                            print_line.append("    .DELAY_2                (1'b0      ),")
                        #if clk_info[clk_info_index["icg_dflt"]] == "Y" :
                        #    print_line.append("    .DATA_DEFAULT           (1'b1                           ) ")
                        #elif clk_info[clk_info_index["icg_dflt"]] == "N" :
                        print_line.append("    .DATA_DEFAULT           (1'b0                           ) ")
                        print_line.append(")")
                        print_line.append("    u_"+other_clk_list[0]+"_sync(")
                        if clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX":
                            print_line.append("            .clk_d                  (CLK_NAME_scan_mux   ), //input")
                        elif clk_info[clk_info_index["occ_scan_mux"]] == "OCC":
                            print_line.append("            .clk_d                  (CLK_NAME_buf_out    ), //input")
                        elif pd.isna(clk_info[clk_info_index["div"]]) == False:
                            print_line.append("            .clk_d                  (CLK_NAME_dived      ), //input")
                        else :
                            print_line.append("            .clk_d                  ("+clk_info[clk_info_index["src0"]]+"     ), //input")
                        print_line.append("            .rst_d_n                (clk_gen_rst_n         ), //input")
                        print_line.append("            .data_s                 ("+other_clk_list[0]+"[i]          ), //input")
                        print_line.append("            .data_d                 ("+other_clk_list[0]+"_sync[i]     )  //output")
                        print_line.append("        );")
                        print_line.append("     end")
                        print_line.append("endgenerate")
                    else :
                        print_line.append("sync ")
                        print_line.append("#(")
                        print_line.append("    .D_WIDTH                (1                              ),")
                        if top_corpus[top_info_index["delay_beat"]][1] == 3 :
                            print_line.append("    .DELAY_2                (1'b0      ),")
                        #if clk_info[clk_info_index["icg_dflt"]] == "Y" :
                        #    print_line.append("    .DATA_DEFAULT           (1'b1                           ) ")
                        #elif clk_info[clk_info_index["icg_dflt"]] == "N" :
                        print_line.append("    .DATA_DEFAULT           (1'b0                           ) ")
                        print_line.append(")")
                        print_line.append("u_"+clk_info[clk_info_index["name"]]+"_"+clk_info[clk_info_index["icg_external"]]+"_sync(")
                        if clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX":
                            print_line.append("            .clk_d                  (CLK_NAME_scan_mux   ), //input")
                        elif clk_info[clk_info_index["occ_scan_mux"]] == "OCC":
                            print_line.append("            .clk_d                  (CLK_NAME_buf_out    ), //input")
                        elif pd.isna(clk_info[clk_info_index["div"]]) == False:
                            print_line.append("            .clk_d                  (CLK_NAME_dived      ), //input")
                        else :
                            print_line.append("            .clk_d                  ("+clk_info[clk_info_index["src0"]]+"     ), //input")
                        print_line.append("            .rst_d_n                (clk_gen_rst_n         ), //input")
                        print_line.append("            .data_s                 ("+clk_info[clk_info_index["icg_external"]]+"          ), //input")
                        print_line.append("            .data_d                 ("+clk_info[clk_info_index["name"]]+"_"+clk_info[clk_info_index["icg_external"]]+"_sync     )  //output")
                        print_line.append("        );")                
                if pd.isna(clk_info[clk_info_index["icg_internal"]]) == False :
                    if "[" in clk_info[clk_info_index["icg_internal"]] :
                        other_clk_list = clk_info[clk_info_index["icg_internal"]].split("[")
                        #print(other_clk_list)
                        #print_line.append("\tinput     ["+other_clk_list[1]+"  "+other_clk_list[0]+",")
                        width = other_clk_list[1].split(":")
                        print_line.append("generate ")
                        print_line.append("    for (i = 0; i <= "+width[0]+"; i = i+1)begin:gen_"+other_clk_list[0]+"_sync")
                        print_line.append("    sync ")
                        print_line.append("    #(")
                        print_line.append("        .D_WIDTH                (1                              ),")
                        if top_corpus[top_info_index["delay_beat"]][1] == 3 :
                            print_line.append("    .DELAY_2                (1'b0      ),")
                        #if clk_info[clk_info_index["icg_dflt"]] == "Y" :
                        #    print_line.append("        .DATA_DEFAULT           (1'b1                           ) ")
                        #elif clk_info[clk_info_index["icg_dflt"]] == "N" :
                        print_line.append("        .DATA_DEFAULT           (1'b0                           ) ")
                        print_line.append(")")
                        print_line.append("    u_"+other_clk_list[0]+"_sync(")
                        if clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX":
                            print_line.append("            .clk_d                  (CLK_NAME_scan_mux   ), //input")
                        elif clk_info[clk_info_index["occ_scan_mux"]] == "OCC":
                            print_line.append("            .clk_d                  (CLK_NAME_buf_out    ), //input")
                        elif pd.isna(clk_info[clk_info_index["div"]]) == False:
                            print_line.append("            .clk_d                  (CLK_NAME_dived      ), //input")
                        else :
                            print_line.append("            .clk_d                  ("+clk_info[clk_info_index["src0"]]+"     ), //input")
                        print_line.append("            .rst_d_n                (clk_gen_rst_n         ), //input")
                        print_line.append("            .data_s                 ("+other_clk_list[0]+"[i]          ), //input")
                        print_line.append("            .data_d                 ("+other_clk_list[0]+"_sync[i]     )  //output")
                        print_line.append("        );")
                        print_line.append("     end")
                        print_line.append("endgenerate")
                    else :
                        print_line.append("    sync ")
                        print_line.append("    #(")
                        print_line.append("        .D_WIDTH                (1                              ),")
                        if top_corpus[top_info_index["delay_beat"]][1] == 3 :
                            print_line.append("    .DELAY_2                (1'b0      ),")
                        #if clk_info[clk_info_index["icg_dflt"]] == "Y" :
                        #    print_line.append("        .DATA_DEFAULT           (1'b1                           ) ")
                        #elif clk_info[clk_info_index["icg_dflt"]] == "N" :
                        print_line.append("        .DATA_DEFAULT           (1'b0                           ) ")
                        print_line.append(")")
                        print_line.append("    u_"+clk_info[clk_info_index["name"]]+"_"+clk_info[clk_info_index["icg_internal"]]+"_sync(")
                        if clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX":
                            print_line.append("            .clk_d                  (CLK_NAME_scan_mux   ), //input")
                        elif clk_info[clk_info_index["occ_scan_mux"]] == "OCC":
                            print_line.append("            .clk_d                  (CLK_NAME_buf_out    ), //input")
                        elif pd.isna(clk_info[clk_info_index["div"]]) == False:
                            print_line.append("            .clk_d                  (CLK_NAME_dived      ), //input")
                        else :
                            print_line.append("            .clk_d                  ("+clk_info[clk_info_index["src0"]]+"     ), //input")
                        print_line.append("            .rst_d_n                (clk_gen_rst_n         ), //input")
                        print_line.append("            .data_s                 ("+clk_info[clk_info_index["icg_internal"]]+"          ), //input")
                        print_line.append("            .data_d                 ("+clk_info[clk_info_index["name"]]+"_"+clk_info[clk_info_index["icg_internal"]]+"_sync     )  //output")
                        print_line.append("        );")
                print_line.append("")
                print_line.append("sync ")
                print_line.append("#(")
                print_line.append("    .D_WIDTH                (1                              ),")
                #print(top_corpus[top_info_index["delay_beat"]][1])
                if top_corpus[top_info_index["delay_beat"]][1] == 3 :
                    print_line.append("    .DELAY_2                (1'b0      ),")
                if clk_info[clk_info_index["icg_dflt"]] == "Y" :
                    print_line.append("    .DATA_DEFAULT           (1'b1                           ) ")
                elif clk_info[clk_info_index["icg_dflt"]] == "N" :
                    print_line.append("    .DATA_DEFAULT           (1'b0                           ) ")
                print_line.append(")")
                print_line.append("u_CLK_NAME_icg_sync(")
                if clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX":
                    print_line.append("    .clk_d                  (CLK_NAME_scan_mux   ), //input")
                elif clk_info[clk_info_index["occ_scan_mux"]] == "OCC":
                    print_line.append("    .clk_d                  (CLK_NAME_buf_out    ), //input")
                elif pd.isna(clk_info[clk_info_index["div"]]) == False :
                    print_line.append("    .clk_d                  (CLK_NAME_dived     ), //input")
                elif pd.isna(clk_info[clk_info_index["sel"]]) == False :
                    print_line.append("    .clk_d                  (CLK_NAME_muxed     ), //input")
                else :
                    print_line.append("    .clk_d                  ("+clk_info[clk_info_index["src0"]]+"     ), //input")
                print_line.append("    .rst_d_n                (clk_gen_rst_n         ), //input")
                print_line.append("    .data_s                 (CLK_NAME_ea          ), //input")
                print_line.append("    .data_d                 (CLK_NAME_ea_sync     )  //output")
                print_line.append(");")
                print_line.append("")
                if pd.isna(clk_info[clk_info_index["icg_external"]]) == False :
                    if "[" in clk_info[clk_info_index["icg_external"]] :
                        if clk_info[clk_info_index["ce_en"]] == "Y" :
                            print_line.append("assign CLK_NAME_ea_multi = CLK_NAME_ea_sync | CLK_NAME_ce & (&"+other_clk_list[0]+"_sync["+other_clk_list[1]+");")
                        else :
                            print_line.append("assign CLK_NAME_ea_multi = CLK_NAME_ea_sync & (&"+other_clk_list[0]+"_sync["+other_clk_list[1]+");")
                    else :
                        if clk_info[clk_info_index["ce_en"]] == "Y" :
                            print_line.append("assign CLK_NAME_ea_multi = CLK_NAME_ea_sync | CLK_NAME_ce & "+clk_info[clk_info_index["name"]]+"_"+clk_info[clk_info_index["icg_external"]]+"_sync;")
                        else :
                            print_line.append("assign CLK_NAME_ea_multi = CLK_NAME_ea_sync & "+clk_info[clk_info_index["name"]]+"_"+clk_info[clk_info_index["icg_external"]]+"_sync;")
                #else :
                #    print_line.append("    .enable                 (CLK_NAME_ea_sync                ), //input")
                elif pd.isna(clk_info[clk_info_index["icg_internal"]]) == False :
                    if "[" in clk_info[clk_info_index["icg_internal"]] :
                        if clk_info[clk_info_index["ce_en"]] == "Y" :
                            print_line.append("assign CLK_NAME_ea_multi = CLK_NAME_ea_sync | CLK_NAME_ce & (&"+other_clk_list[0]+"_sync["+other_clk_list[1]+");")
                        else :
                            print_line.append("assign CLK_NAME_ea_multi = CLK_NAME_ea_sync & (&"+other_clk_list[0]+"_sync["+other_clk_list[1]+");")
                    else :
                        if clk_info[clk_info_index["ce_en"]] == "Y" :
                            print_line.append("assign CLK_NAME_ea_multi = CLK_NAME_ea_sync | CLK_NAME_ce & "+clk_info[clk_info_index["name"]]+"_"+clk_info[clk_info_index["icg_internal"]]+"_sync;")
                        else :
                            print_line.append("assign CLK_NAME_ea_multi = CLK_NAME_ea_sync & "+clk_info[clk_info_index["name"]]+"_"+clk_info[clk_info_index["icg_internal"]]+"_sync;")
                else :
                    if clk_info[clk_info_index["ce_en"]] == "Y" :
                        print_line.append("assign CLK_NAME_ea_multi = CLK_NAME_ea_sync | CLK_NAME_ce;")
                    else :
                        print_line.append("assign CLK_NAME_ea_multi = CLK_NAME_ea_sync;")

                #print_line.append("assign CLK_NAME_ea_status = CLK_NAME_ea_multi;")
                print_line.append("")
                print_line.append("sync")
                print_line.append("#(")
                print_line.append("    .D_WIDTH        (1        ),")
                if top_corpus[top_info_index["delay_beat"]][1] == 3 :
                    print_line.append("    .DELAY_2        (1'b0      ),")
                if clk_info[clk_info_index["mux_dflt"]] == 1 :
                    print_line.append("    .DATA_DEFAULT   (1'b0      )")
                else :
                    print_line.append("    .DATA_DEFAULT   (1'b1      )")
                print_line.append(")")
                print_line.append("u_CLK_NAME_ea_status_sync(")
                if top_corpus[top_info_index["protocol"]][1] == "apb":
                    print_line.append("    .clk_d      (apb_clk                ),")
                    print_line.append("    .rst_d_n    (apb_rst_n              ),")
                elif top_corpus[top_info_index["protocol"]][1] == "dab":
                    print_line.append("    .clk_d      (dab_clk                ),")
                    print_line.append("    .rst_d_n    (dab_rst_n        ),")
                elif top_corpus[top_info_index["protocol"]][1] == "ahb":
                    print_line.append("    .clk_d      (ahb_clk                ),")
                    print_line.append("    .rst_d_n    (ahb_rst_n        ),")
                print_line.append("    .data_s     (CLK_NAME_ea_multi),")
                print_line.append("    .data_d     (CLK_NAME_ea_status)")
                print_line.append(");")
                print_line.append("")
                if clk_info[clk_info_index["attr"]] == "output" and clk_info[clk_info_index["ce_en"]] == "Y" :
                    if clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX":
                        print_line.append("assign   CLK_NAME_cg_bf = CLK_NAME_scan_mux;")
                    elif clk_info[clk_info_index["occ_scan_mux"]] == "OCC":
                        print_line.append("assign   CLK_NAME_cg_bf = CLK_NAME_buf_out;")
                    elif pd.isna(clk_info[clk_info_index["div"]]) == False :
                        print_line.append("assign   CLK_NAME_cg_bf = CLK_NAME_dived;")
                    elif pd.isna(clk_info[clk_info_index["sel"]]) == False :
                        print_line.append("assign   CLK_NAME_cg_bf = CLK_NAME_muxed;")
                    else :
                        print_line.append("assign   CLK_NAME_cg_bf = "+clk_info[clk_info_index["src0"]]+";")
                
                print_line.append("icg u_CLK_NAME_icg(")
                if clk_info[clk_info_index["attr"]] == "output" and clk_info[clk_info_index["ce_en"]] == "Y" :
                    print_line.append("    .clkin                  (CLK_NAME_cg_bf      ), //input")
                else :
                    if clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX":
                        print_line.append("    .clkin      (CLK_NAME_scan_mux       ),")
                    elif clk_info[clk_info_index["occ_scan_mux"]] == "OCC":
                        print_line.append("    .clkin                  (CLK_NAME_buf_out    ), //input")
                    elif pd.isna(clk_info[clk_info_index["div"]]) == False :
                        print_line.append("    .clkin                  (CLK_NAME_dived      ), //input")
                    elif pd.isna(clk_info[clk_info_index["sel"]]) == False :
                        print_line.append("    .clkin                  (CLK_NAME_muxed      ), //input")
                    else :
                        print_line.append("    .clkin                  ("+clk_info[clk_info_index["src0"]]+"     ), //input")
                print_line.append("    .enable                 (CLK_NAME_ea_multi            ), //input")
                print_line.append("    .icg_test_mode          (dft_icg_mode_root            ), //input")
                print_line.append("    .clkout                 (CLK_NAME                     )  //output")
                print_line.append(");")
            else :
                #if clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX":
                #    print_line.append("assign CLK_NAME = CLK_NAME_scan_mux;")
                #elif clk_info[clk_info_index["occ_scan_mux"]] == "OCC":
                #    print_line.append("assign CLK_NAME = CLK_NAME_buf_out;")
                #elif pd.isna(clk_info[clk_info_index["div"]]) == False :
                #    print_line.append("assign CLK_NAME = CLK_NAME_dived;")
                #elif pd.isna(clk_info[clk_info_index["sel"]]) == False :
                #    print_line.append("assign CLK_NAME = CLK_NAME_muxed;")
                #else :
                #    print_line.append("assign CLK_NAME = "+str(clk_info[clk_info_index["src0"]])+";")
                if clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX":
                    print_line.append("assign CLK_NAME = CLK_NAME_scan_mux;")
                elif clk_info[clk_info_index["occ_scan_mux"]] == "OCC":
                    print_line.append("assign CLK_NAME = CLK_NAME_buf_out;")
                elif pd.isna(clk_info[clk_info_index["div"]]) == False :
                    print_line.append("assign CLK_NAME = CLK_NAME_dived;")
                elif pd.isna(clk_info[clk_info_index["sel"]]) == False :
                    print_line.append("assign CLK_NAME = CLK_NAME_muxed;")
                else :
                    print_line.append("assign CLK_NAME = "+str(clk_info[clk_info_index["src0"]])+";")
                if clk_info[clk_info_index["attr"]] == "output" and clk_info[clk_info_index["ce_en"]] == "Y" :
                    if clk_info[clk_info_index["occ_scan_mux"]] == "SCAN_MUX":
                        print_line.append("assign CLK_NAME_cg_bf = CLK_NAME_scan_mux;")
                    elif clk_info[clk_info_index["occ_scan_mux"]] == "OCC":
                        print_line.append("assign CLK_NAME_cg_bf = CLK_NAME_buf_out;")
                    elif pd.isna(clk_info[clk_info_index["div"]]) == False :
                        print_line.append("assign CLK_NAME_cg_bf = CLK_NAME_dived;")
                    elif pd.isna(clk_info[clk_info_index["sel"]]) == False :
                        print_line.append("assign CLK_NAME_cg_bf = CLK_NAME_muxed;")
                    else :
                        print_line.append("assign CLK_NAME_cg_bf = "+str(clk_info[clk_info_index["src0"]])+";")

        replace_CLK_NAME(clk_info, clk_info_index, top_info_index, print_line)


    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')
    fp.write('endmodule')

    fp.close()

    fp = open(gen_filepath+top_corpus[top_info_index["design_name"]][1]+"_tdr_buf_list.txt", "w") 
    for line in tdr_buf_list :
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')
    fp.close()

    fp = open(gen_filepath+top_corpus[top_info_index["design_name"]][1]+"_occ_buf_list.txt", "w") 
    for line in occ_buf_list :
        #print(line)
        fp.write(line)
        fp.write('\n')
   
    fp = open(gen_filepath+top_corpus[top_info_index["design_name"]][1]+"_div_list.txt", "w") 
    for line in div_list :
        #print(line)
        fp.write(line)
        fp.write('\n')

    fp.write('\n')

    fp.close()

#}}}

# rst_gen{{{
def rst_gen(rst_info_index, top_info_index, gen_filepath, top_corpus, rst_corpus, rst_ser):
    #print(top_corpus)
    fp = open(gen_filepath+top_corpus[top_info_index["design_name"]][1]+"_rst_gen.v", "w") 
    
    print_line = []
    add_header(print_line, top_corpus[top_info_index["design_name"]][1]+"_rst_gen.v")
    print_line.append("module "+top_corpus[top_info_index["design_name"]][1]+"_rst_gen(")
    
    #count = 0
    #for rst_info in rst_corpus:
    #    count += 1 
    #    if rst_info[rst_info_index["inout"]] == "input":
    #        print_line.append("\tinput           "+rst_info[rst_info_index["name"]]+",")
    #    if rst_info[rst_info_index["inout"]] == "internal" and pd.isna(rst_info[rst_info_index["attr"]]) == True :
    #        print_line.append("\tinput           "+rst_info[rst_info_index["name"]]+",")

    count = 0
    for rst_info in rst_corpus:
        count += 1
        if rst_info[rst_info_index["inout"]] == "input":
            print_line.append("\tinput           "+rst_info[rst_info_index["name"]]+",")
        if rst_info[rst_info_index["inout"]] == "internal" and pd.isna(rst_info[rst_info_index["glb_src"]]) == True :
            print_line.append("\tinput           "+rst_info[rst_info_index["name"]]+",")
        elif rst_info[rst_info_index["inout"]] == "internal" :
            print_line.append("\toutput          "+rst_info[rst_info_index["name"]]+",")
        if rst_info[rst_info_index["inout"]] == "output" :
            print_line.append("\t// "+rst_info[rst_info_index["name"]])
            #if pd.isna(rst_info[rst_info_index["sync_clk"]]) == False :
            #if rst_info[rst_info_index["sync"]] == "Y" :
            #    print_line.append("\tinput           "+rst_info[rst_info_index["sync_clk"]]+",")
            #if rst_info[rst_info_index["areset_relax_en"]] == "Y" :
            #    print_line.append("\tinput           "+rst_info[rst_info_index["sync_clk"]]+"_cg_bf,")
            #    if rst_info[rst_info_index["areset_relax_en"]] == "Y" :
            #        print_line.append("\toutput          "+str(rst_info[rst_info_index["sync_clk"]])+"_ce,")
            if rst_info[rst_info_index["soft_src"]] == "SOFT" :
                print_line.append("\tinput           "+rst_info[rst_info_index["name"]]+"_sftrstn,")
            print_line.append("\toutput          "+rst_info[rst_info_index["name"]]+",")

            #elif rst_info[rst_info_index["sync"]] == "N" :
            #    #print_line.append("\t// "+rst_info[rst_info_index["name"]])
            #    if rst_info[rst_info_index["soft_src"]] == "SOFT" :
            #        print_line.append("\tinput           "+rst_info[rst_info_index["name"]]+"_sftrstn,")
            #    print_line.append("\toutput          "+rst_info[rst_info_index["name"]]+",")
            #    print_line.append("    output          "+rst_info[rst_info_index["name"]]+"_ce,")
        if pd.isna(rst_info[rst_info_index["external_src"]]) == False :
            if "[" in rst_info[rst_info_index["external_src"]] :
                other_rst_list = rst_info[rst_info_index["external_src"]].split("[")
                #print(other_rst_list)
                print_line.append("\tinput     ["+other_rst_list[1]+"  "+other_rst_list[0]+",")
            else : 
                print_line.append("\tinput           "+rst_info[rst_info_index["external_src"]]+",")
        if pd.isna(rst_info[rst_info_index["internal_src"]]) == False :
            if "[" in rst_info[rst_info_index["internal_src"]] :
                other_rst_list = rst_info[rst_info_index["internal_src"]].split("[")
                #print(other_rst_list)
                print_line.append("\tinput     ["+other_rst_list[1]+"  "+other_rst_list[0]+",")
            else : 
                print_line.append("\tinput           "+rst_info[rst_info_index["internal_src"]]+",")


    for repeat_idx in range(len(print_line)-1, -1, -1) :
        if print_line.count(print_line[repeat_idx]) > 1 and "input" in print_line[repeat_idx] :
            print_line.pop(repeat_idx)    
    port_last_process(count, rst_ser, print_line)
    print_line.append(');\n')



    for rst_info in rst_corpus:
        count += 1 
        #if rst_info[rst_info_index["sync"]] == "Y":
        #    print_line.append("wire        "+rst_info[rst_info_index["name"]]+"_bf_sync;")
            #print_line.append("wire        "+rst_info[rst_info_index["name"]]+"_bf_test;")
        #elif rst_info[rst_info_index["sync"]] == "N":
        #if rst_info[rst_info_index["inout"]] == "output" or rst_info[rst_info_index["inout"]] == "na" or (rst_info[rst_info_index["inout"]] == "internal" and pd.isna(rst_info[rst_info_index["glb_src"]]) == False) :
        #    print_line.append("wire        "+rst_info[rst_info_index["name"]]+"_bf_test;")

    for rst_info in rst_corpus:
        count += 1 
        if rst_info[rst_info_index["inout"]] == "output" or rst_info[rst_info_index["inout"]] == "na" or (rst_info[rst_info_index["inout"]] == "internal" and pd.isna(rst_info[rst_info_index["glb_src"]]) == False) :
            print_line.append("//===============")
            print_line.append("// "+rst_info[rst_info_index["name"]]+" ctrl")
            #print_line.append("//===============")
            #print_line.append("// "+rst_info[rst_info_index["name"]]+" src")
            #if rst_info[rst_info_index["sync"]] == "Y" :
            #    print_line.append("assign "+rst_info[rst_info_index["name"]]+"_bf_sync = "+rst_info[rst_info_index["glb_src"]])
            #else :
            #    print_line.append("assign "+rst_info[rst_info_index["name"]]+"_bf_test = "+rst_info[rst_info_index["glb_src"]])
            print_line.append("assign "+rst_info[rst_info_index["name"]]+" = "+rst_info[rst_info_index["glb_src"]])
            if rst_info[rst_info_index["soft_src"]] == "SOFT":
                print_line[-1] = print_line[-1] + " & "+rst_info[rst_info_index["name"]]+"_sftrstn"
            if pd.isna(rst_info[rst_info_index["external_src"]]) == False :
                if "[" in rst_info[rst_info_index["external_src"]] :
                    print_line[-1] = print_line[-1] + " & (&"+rst_info[rst_info_index["external_src"]]+")"
                else :
                    print_line[-1] = print_line[-1] + " & "+rst_info[rst_info_index["external_src"]]+""
            if pd.isna(rst_info[rst_info_index["internal_src"]]) == False :
                if "[" in rst_info[rst_info_index["internal_src"]] :
                    print_line[-1] = print_line[-1] + " & (&"+rst_info[rst_info_index["internal_src"]]+")"
                else :
                    print_line[-1] = print_line[-1] + " & "+rst_info[rst_info_index["internal_src"]]+""
            print_line[-1] = print_line[-1] + ";"

            print_line.append("")
            #if rst_info[rst_info_index["sync"]] == "Y" :
            #    print_line.append("// "+rst_info[rst_info_index["name"]]+" sync")
            #    if rst_info[rst_info_index["areset_relax_en"]] == "Y" :
            #        print_line.append("areset_relax u_"+rst_info[rst_info_index["name"]]+"_sync(")
            #        #print_line.append("#(")

            #        #    print_line.append("    .BYPASS         (0)")
            #        #else :
            #        #    print_line.append("    .BYPASS         (1)")
            #        #print_line.append(")")
            #        #print_line.append("u_"+rst_info[rst_info_index["name"]]+"_sync(")
            #        print_line.append("    .rstn_n         ("+rst_info[rst_info_index["name"]]+"_bf_sync        ),")
            #        print_line.append("    .sync_clock     ("+rst_info[rst_info_index["sync_clk"]]+"_cg_bf      ),")
            #        print_line.append("    .async_rstn_n   ("+rst_info[rst_info_index["name"]]+"_bf_test        ),")
            #        print_line.append("    .ce             ("+str(rst_info[rst_info_index["sync_clk"]])+"_ce             )")
            #        print_line.append(");")
            #    else : 
            #        print_line.append("rstn_sync u_"+rst_info[rst_info_index["name"]]+"_sync(")
            #        print_line.append("    .rstn_n         ("+rst_info[rst_info_index["name"]]+"_bf_sync        ),")
            #        print_line.append("    .sync_clock     ("+rst_info[rst_info_index["sync_clk"]]+"               ),")
            #        print_line.append("    .async_rstn_n   ("+rst_info[rst_info_index["name"]]+"_bf_test        ),")
            #        print_line.append("    .sync_rstn_n    (                               )")
            #        print_line.append(");")
            #print_line.append("// "+rst_info[rst_info_index["name"]]+" test mux")
            #print_line.append("rstn_test_mux u_"+rst_info[rst_info_index["name"]]+"_test_mux(")
            ##if rst_info[rst_info_index["sync"]] == "Y" :
            #print_line.append("    .rstn_in        ("+rst_info[rst_info_index["name"]]+"_bf_test        ),")
            ##elif rst_info[rst_info_index["sync"]] == "N"  :
            ##    print_line.append("    .rstn_in        ("+rst_info[rst_info_index["name"]]+"_bf_sync        ),")
            #print_line.append("    .test_rstn      (test_rstn              ),")
            #print_line.append("    .test_md        (test_mode                ),")
            #print_line.append("    .rstn_out       ("+rst_info[rst_info_index["name"]]+"                )")
            #print_line.append(");")
    
    

    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')
    fp.write('endmodule')

    fp.close()
#}}}

#replace_CLK_NAME{{{

def replace_CLK_NAME(clk_info, clk_info_index, top_info_index, print_line):
    for element in print_line:
        if 'CLK_NAME' in element:
            print_line[print_line.index(element)] = print_line[print_line.index(element)].replace("CLK_NAME", clk_info[clk_info_index["name"]])
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

#reg_yml_gen{{{
def reg_yml_gen(top_info_index, print_line, reg_corpus, reg_ser, top_corpus, reg_addr_ofst) :
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
            print_line.append("    offset: "+hex(int(reg_info[1], 16) + int(reg_addr_ofst, 16)))
            print_line.append("    fields:")
          
            count = count + 1
        else:
            #print(reg_info[3])
            bitoffset0 = str(reg_info[3]).split('[', 1)
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
def reg_xml_gen(top_info_index, print_line, reg_corpus, reg_ser, top_corpus) :
    count = 0
    reg_sheet_cnt = 0
    for reg_info in reg_corpus:
        #print(reg_info)
        #print("max index is :", reg_ser.index.max())
        #print("count is :", count)
        #print(reg_info)
        if pd.isna(reg_info[0]) == False:
            #print(reg_info)
            if count != 0:
                print_line.append("    </spirit:register>")
            print_line.append("    <spirit:register>")
            print_line.append("      <spirit:name>"+reg_info[0]+"</spirit:name>")
            print_line.append("      <spirit:description>"+str(reg_info[6]).replace('\n', " ")+"</spirit:description>")
            print_line.append("      <spirit:addressOffset>"+hex(int(reg_info[1], 16) + int(top_corpus[top_info_index["user_defined_reg_addr_ofst"]][1], 16))+"</spirit:addressOffset>")
            print_line.append("      <spirit:size>32</spirit:size>")
            print_line.append("      <spirit:access>"+reg_info[4]+"</spirit:access>")
            print_line.append("      <spirit:reset>")
            print_line.append("        <spirit:value>"+reg_info[5]+"</spirit:value>")  
            print_line.append("      </spirit:reset>")
            count = count + 1
        else:
            #print(reg_info[3])
            bitoffset0 = str(reg_info[3]).split('[', 1)
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
            print_line.append("      <spirit:field>")
            print_line.append("        <spirit:name>"+reg_info[2]+"</spirit:name>")
            print_line.append("        <spirit:description>"+str(reg_info[6]).replace('\n', " ")+"</spirit:description>")
            print_line.append("        <spirit:bitOffset>"+field_lsb+"</spirit:bitOffset>")
            print_line.append("        <spirit:bitWidth>"+str(int(field_msb) -int(field_lsb) +1)+"</spirit:bitWidth>")
            print_line.append("        <spirit:access>"+reg_info[4]+"</spirit:access>")
            if pd.isna(reg_info[7]) == False :
                print_line.append("        <spirit:lockOffset>"+lock_field_lsb+"</spirit:lockOffset>")
                print_line.append("        <spirit:lockWidth>"+str(int(lock_field_msb) - int(lock_field_lsb) + 1)+"</spirit:lockWidth>")
                print_line.append("        <spirit:lockValue>"+reg_info[8]+"</spirit:lockValue>")
            print_line.append("      </spirit:field>")
        reg_sheet_cnt = reg_sheet_cnt + 1
        if reg_sheet_cnt > reg_ser.index.max() :
            print_line.append("    </spirit:register>")
#}}}

#reg_note_gen{{{
def reg_note_gen(print_line, reg_corpus, reg_ser) :
    count = 0
    for reg_info in reg_corpus:
        #print(reg_info)
        #print("max index is :", reg_ser.index.max())
        #print("count is :", count)
        #print(reg_info)
        if pd.isna(reg_info[0]) == False:
            #print(reg_info)
            print_line.append("")
            print_line.append(reg_info[1]+"    			--		"+reg_info[4]+"		--		"+reg_info[0]+"			    --		[31:0]		--	"+str(reg_info[6]).replace('\n', " "))
        else:
            #print(reg_info[3])
            bitoffset0 = str(reg_info[3]).split('[', 1)
            #print(bitoffset0)
            bitoffset1 = bitoffset0[1].split(':', 1)
            bitoffset2 = bitoffset1[1].split(']', 1)
            field_msb = bitoffset1[0]
            field_lsb = bitoffset2[0]
            #print(field_msb, field_lsb)

            #print(reg_info)
            if field_msb ==  field_lsb :
                print_line.append("--		'h"+reg_info[5][2:]+"		--		"+reg_info[4]+"		--		"+reg_info[2]+"		            --		["+field_msb+"]			--	"+str(reg_info[6]).replace('\n', " "))
            else :
                print_line.append("--		'h"+reg_info[5][2:]+"		--		"+reg_info[4]+"		--		"+reg_info[2]+"		            --		["+field_msb+":"+field_lsb+"]			--	"+str(reg_info[6]).replace('\n', " "))

#}}}

#code_gen_csv{{{
def code_gen_csv(print_line, code_corpus, code_ser) :
    for code_info in code_corpus:
        #print("code_info[0] is code_info[1]:"+str(code_info[0])+"  "+str(code_info[1]))
        #print("code_info[1] is :"+str(code_info[1]))
        if code_info[0] == "assign" :
            print_line.append("#keep_begin after_wire_reg")
            print_line.append("assign "+code_info[1]+" = "+code_info[2]+";")
            print_line.append("#keep_end after_wire_reg")
        elif pd.isna(code_info[0]) == True and pd.isna(code_info[1]) == True and pd.isna(code_info[2]) == True :
            #print("############")
            continue
        elif code_info[0] == "inst_begin" :
            print_line.append("#inst_begin===========================================================================================================")
            #if pd.isna(code_info[2]) == True :
            #    print_line.append("inst "+code_info[1])
            #else :
            print_line.append("inst "+code_info[1]+" "+code_info[2])
            inst_module = code_info[1]
            print_line.append("#para_inst_begin")
        elif code_info[0] == "para_begin" :
            print_line.append("connect,"+inst_module+"."+str(code_info[1])+"     ,"+str(code_info[2]))
        elif pd.isna(code_info[0]) == True and pd.isna(code_info[3]) == True :
            print_line.append("connect,"+inst_module+"."+str(code_info[1])+"     ,"+str(code_info[2]))
        elif code_info[0] == "para_end" :
            print_line.append("connect,"+inst_module+"."+str(code_info[1])+"     ,"+str(code_info[2]))
        elif code_info[0] == "port_begin" :
            print_line.append("#para_inst_end")
            print_line.append("#port_inst_begin")
            print_line.append("connect,"+inst_module+"."+code_info[1]+"     ,"+code_info[2]+"   ,"+str(code_info[3])+"  ,"+str(code_info[4])+",")
        elif code_info[0] == "port_end" :
            print_line.append("connect,"+inst_module+"."+code_info[1]+"     ,"+code_info[2]+"   ,"+str(code_info[3])+"  ,"+str(code_info[4])+",")
        elif code_info[0] == "inst_end" :
            print_line.append("connect,"+inst_module+"."+code_info[1]+"     ,"+code_info[2]+"   ,"+str(code_info[3])+"  ,"+str(code_info[4])+",")
            print_line.append("#port_inst_end")
            print_line.append("#inst_end============================================================================================================")
        elif pd.isna(code_info[0]) == True and pd.isna(code_info[3]) == False :
            #print("11111111111111111111111111"+code_info[1])
            print_line.append("connect,"+inst_module+"."+code_info[1]+"     ,"+code_info[2]+"   ,"+str(code_info[3])+"  ,"+str(code_info[4])+",")
            #print("###### connect,"+inst_module+"."+code_info[1]+"     ,"+code_info[2]+"   ,"+str(code_info[3])+"  ,"+str(code_info[4])+",")


#}}}

#code_gen{{{
def code_gen(print_line, code_corpus, code_ser) :
    for code_info in code_corpus:
        if code_info[0] == "assign" :
            print_line.append("    assign "+code_info[1]+" = "+code_info[2]+";")
        elif code_info[0] == "inst_begin" :
            print_line.append("    "+code_info[1]+" "+code_info[2]+"(/*autoinst*/");
        elif pd.isna(code_info[0]) == True and pd.isna(code_info[1]) == True and pd.isna(code_info[2]) == True :
            print_line.append("")
        elif pd.isna(code_info[0]) == True :
            print_line.append("        ."+code_info[1]+"     ("+code_info[2]+"),")
        elif code_info[0] == "inst_end" :
            print_line.append("        ."+code_info[1]+"     ("+code_info[2]+"),")
            print_line[-1] = print_line[-1].strip(',')
            print_line.append('\t);\n')
#}}}

def intp_yml_gen(top_info_index, print_line, intp_corpus, intp_ser, top_corpus):#{{{

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
                print_line.append("  - name: "+intp_name_str)
                print_line.append("    description: \""+str(intp_info[6]).replace('\n', " ")+"\"")
                print_line.append("    offset: "+hex(int(intp_info[1], 16) + int(top_corpus[top_info_index["user_defined_intp_addr_ofst"]][1], 16)))
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

def intp_xml_gen(top_info_index, print_line, intp_corpus, intp_ser, top_corpus):#{{{

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
                print_line.append("      <spirit:addressOffset>"+hex(int(intp_info[1], 16) + int(top_corpus[top_info_index["user_defined_intp_addr_ofst"]][1], 16))+"</spirit:addressOffset>")
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

def writeDataIntoExcel(xlsPath: str, data: dict):#{{{
	writer = pd.ExcelWriter(xlsPath)
	sheetNames = data.keys()  # 获取所有sheet的名称
	# sheets是要写入的excel工作簿名称列表
	data = pd.DataFrame(data)
	for sheetName in sheetNames:
		data.to_excel(writer, sheet_name=sheetName)
	# 保存writer中的数据至excel
	# 如果省略该语句，则数据不会写入到上边创建的excel文件中
	writer.save()

#}}}

# help{{{
def help():
    print("############## help ####################")
    print("########################################")
    print("##generate clk_gen, rst_gen, crg_top, clk & rst xml##")
    print("crg_gen excel_path")
    #print("crg_gen excel_path ip_name_crg clk_gen_sheet_name rst_gen_sheet_name crg_gen dab/apb top")
    #print("crg_gen excel_path ip_name_crg clk_gen_sheet_name rst_gen_sheet_name crg_gen dab/apb clk")
    #print("crg_gen excel_path ip_name_crg clk_gen_sheet_name rst_gen_sheet_name crg_gen dab/apb rst")
    #print("crg_gen excel_path ip_name_crg clk_gen_sheet_name rst_gen_sheet_name crg_gen dab/apb note rst_ofst_addr")
    print("########################################")
    print("##generate sdc##")
    print("crg_gen excel_path sdc_gen")
# }}}

if __name__ == "__main__":
    main()


