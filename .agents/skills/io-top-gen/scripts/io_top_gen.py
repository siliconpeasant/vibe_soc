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
        #print(para_list[0].rstrip(".csv"))

    except Exception as e:
        print("Error parameters!!! unknown parameter")
        print(e)
        sys.exit(1)

    if(len(para_list) == 0) or para_list[0] == "-h":
        help()
        sys.exit(1)

    if len(para_list) == 3 :
        io_option = para_list[2]
    else :
        io_option = "io"

    df = pd.read_excel(para_list[0], sheet_name = "pad_cfg", header=None)
    pad_cfg_corpus = df.values.tolist()

    #print("\nall data:")
    #print (df)
    pad_cfg_ser = pd.Series(pad_cfg_corpus)
    pad_cfg_empty = df.empty

    df = pd.read_excel(para_list[0], sheet_name = "pin_mux")
    pad_corpus = df.values.tolist()

    #print("\nall data:")
    #print (df)
    pad_ser = pd.Series(pad_corpus)
    pad_empty = df.empty

    #df = pd.read_csv(para_list[0])
    #df = pd.read_excel("/remote/share/ninghechuan/io_tool_dev.xlsx")
    #df = pd.read_excel(para_list[0], sheet_name = para_list[0].rstrip(".csv"))
    
    (filepath, filename) = os.path.split(para_list[0])
    #print("filepath is:"+filepath)
    #print("filename is:"+filename)
    filename = pad_cfg_corpus[1][1]
    design_owner = pad_cfg_corpus[0][1]
    design_hier = pad_cfg_corpus[2][1]
    protocol = pad_cfg_corpus[3][1]
    gen_filepath = para_list[1]+"/"
    #gen_filepath = para_list[1]+"/"+filename+"/"
    #isExists=os.path.exists(gen_filepath)
    #if not isExists:
    #    os.makedirs(gen_filepath) 

    #print(gen_filepath)
    
    pad_info_index = {"pad_name":0, \
                      "pad_cell_type":1, \
                      "io_domain":2, \
                      "type":3, \
                      "drv":4, \
                      "rx_smit":5, \
                      "pu":6, \
                      "pd":7, \
                      "normal_mode":8, \
                      "normal_attr":9, \
                      "normal_dflt":10, \
                      "func1":11, \
                      "func1_attr":12, \
                      "func1_dflt":13, \
                      "func2":14, \
                      "func2_attr":15, \
                      "func2_dflt":16, \
                      "func3":17, \
                      "func3_attr":18, \
                      "func3_dflt":19, \
                      "dft_mode":20, \
                      "nomal_input_clock":21, \
                      "nomal_output_clock":22, \
                      "func1_input_clock":23, \
                      "func1_output_clock":24, \
                      "func2_input_clock":25, \
                      "func2_output_clock":26, \
                      "func3_input_clock":27, \
                      "func3_output_clock":28}

    pad_cell_index = {"pad_name":0, "ds":1, "st":2, "sl":3, "msc":4, "ps":5, "he":6, "pe":7}
    pad_cell = []
    for cfg_info in pad_cfg_corpus :
        if "pad_cell_type" == pad_cfg_corpus[pad_cfg_corpus.index(cfg_info)][0] :
            pad_cell.append(pad_cfg_corpus[pad_cfg_corpus.index(cfg_info)][1]\
                    +","+str(pad_cfg_corpus[pad_cfg_corpus.index(cfg_info)][2])\
                    +","+str(pad_cfg_corpus[pad_cfg_corpus.index(cfg_info)][3])\
                    +","+str(pad_cfg_corpus[pad_cfg_corpus.index(cfg_info)][4])\
                    +","+str(pad_cfg_corpus[pad_cfg_corpus.index(cfg_info)][5])\
                    +","+str(pad_cfg_corpus[pad_cfg_corpus.index(cfg_info)][6])\
                    +","+str(pad_cfg_corpus[pad_cfg_corpus.index(cfg_info)][7])\
                    +","+str(pad_cfg_corpus[pad_cfg_corpus.index(cfg_info)][8]))
    #print(pad_cell)
    #print(pad_cfg_corpus)

# io_top{{{
    #if io_option == "sdc_gen" :
    #    io_sdc_gen(gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index, pad_info_index)
    #else :
    gen_io_yml(gen_filepath, filename, pad_corpus, pad_info_index, pad_cell, pad_cell_index, protocol)
    io_top_gen_csv(protocol, design_owner, pad_cell, pad_info_index, gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index, design_hier)
#	add in 12011 zhengzhiqiang
    io_connet_check_csv(protocol, design_owner, pad_cell, pad_info_index, gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index, design_hier)
    io_top_gen_model_csv(protocol, design_owner, pad_cell, pad_info_index, gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index)
    io_ring_gen(protocol, design_owner, pad_cell, pad_info_index, gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index, design_hier)
    io_pin_mux_gen(protocol, design_owner, pad_cell, pad_info_index, gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index)
    io_pin_mux_model_gen(protocol, design_owner, pad_cell, pad_info_index, gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index)
    print_dont_touch_list(gen_filepath, pad_corpus, pad_info_index, filename)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    soc_build_py = os.path.join(script_dir, "soc_build.py")
    gen_rtl = "python3 "+soc_build_py+" gen "+gen_filepath+filename+"_top.csv"
    gen_rtl_model = "python3 "+soc_build_py+" gen "+gen_filepath+filename+"_top_model.csv"
    print(gen_rtl)
    os.system(gen_rtl)
    print(gen_rtl_model)
    os.system(gen_rtl_model)
    io_sdc_gen(gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index, pad_info_index)
    gen_io_sdc = "soc_build gen "+gen_filepath+filename+".sdc"
    print(gen_io_sdc)

# }}}

## pin_mux_note{{{
#    #print("note name is :"+filename)
#    fp = open(gen_filepath+filename.upper()+".note", "w")
#    print_line = []
#
#    print_line.append('// Component')
#    print_line.append(filename.upper()+"      --  v1.0\n")
#    print_line.append('// Block')
#    print_line.append(filename.upper()+"      --  0x0000:0xffff  --  "+filename.upper()+" regfile       -- "+protocol)
#    print_line.append('// Register')
#    
#    count = 0
#
#    for pad_info in pad_corpus :
#
#        if 'PINMUX' == pad_info[pad_info_index["type"]] or "GPIO" == pad_info[pad_info_index["type"]] :
#            #reg_addr = hex(count * 2)
#            reg_addr = hex(count)
#            #print(reg_addr)
#            #if (count % 2) == 0:
#                #print(count)
#            print_line.append(reg_addr+"\t\t\t\t--\t\tRW\t\t--\t\tpad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"\t\t\t\t--\t\t[31:0]\t\t--\t\tpad control register "+pad_info[pad_info_index["pad_name"]].lower())
#            #cell_ds_msb = 0
#            #cell_st_msb = 0
#            #cell_st = 0
#            #cell_sl = 0
#            #cell_msc = 0
#            #cell_ps = 0
#            #cell_he = 0
#            #cell_pe = 0
#            for cell_info in pad_cell :
#                #print(cell_info)
#                cell_info_list = cell_info.split(",")
#                #print(cell_info_list)
#                cell_name = cell_info_list[0]
#                if pad_info[pad_info_index["pad_cell_type"]] == cell_name :
#                    cell_ds = str(cell_info_list[pad_cell_index["ds"]])
#                    cell_st = str(cell_info_list[pad_cell_index["st"]])
#                    cell_sl = str(cell_info_list[pad_cell_index["sl"]])
#                    cell_msc= str(cell_info_list[pad_cell_index["msc"]])
#                    cell_ps = str(cell_info_list[pad_cell_index["ps"]])
#                    cell_he = str(cell_info_list[pad_cell_index["he"]])
#                    cell_pe = str(cell_info_list[pad_cell_index["pe"]])
#                    if "[" in cell_ds :
#                        cell_ds_list = cell_ds.split("[", 1)
#                        cell_ds_width_list = cell_ds_list[1].split(":", 1)
#                        #print(cell_ds_width_list[0])
#                        cell_ds_msb = cell_ds_width_list[0]
#                    if "[" in cell_st :
#                        cell_st_list = cell_st.split("[", 1)
#                        cell_st_width_list = cell_st_list[1].split(":", 1)
#                        cell_st_msb = cell_st_width_list[0]
#            
#            print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_pu\t\t\t\t--\t\t[0]\t\t\t--\t\tpad control pull up")
#            print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_pd\t\t\t\t--\t\t[1]\t\t\t--\t\tpad control pull down")
#            #if 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]] :
#            print_line.append("--\t\t'h1\t\t--\t\tRW\t\t--\t\tpad_name0_ie\t\t\t\t--\t\t[2]\t\t\t--\t\tpad control input enable")
#
#            #else :
#            #    print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_ie\t\t\t\t--\t\t[2]\t\t\t--\t\tpad control input enable")
#            #print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_ds\t\t\t\t--\t\t[5:4]\t\t--\t\tpad control driver strength") 
#            print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_ds\t\t\t\t--\t\t["+str(4+int(cell_ds_msb))+":4]\t\t--\t\tpad control driver strength") 
#            if 'PINMUX' == pad_info[pad_info_index["type"]] :
#                print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_func_sel\t\t\t--\t\t[9:8]\t\t--\t\tpad control function select")
#            #if pd.isna(cell_st) == False  :
#            if cell_st != "nan" :
#                print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_st\t\t\t\t--\t\t["+str(12+int(cell_st_msb))+":12]\t\t\t--\t\tpad control Schmitt trigger enable. ST=1 enables Schmitt trigger input function")
#            
#            #if pd.isna(cell_sl) == False  :
#            if cell_sl != "nan" :
#                print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_sl\t\t\t\t--\t\t[16]\t\t\t--\t\tpad control Slew-rate-control enable，SL=1 enables Slew-rate-control function")
#            #if pd.isna(cell_msc) == False  :
#            if cell_msc != "nan" :
#                print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_msc\t\t\t\t--\t\t[17]\t\t\t--\t\tpad control mode selector")
#            #if pd.isna(cell_ps) == False  :
#            if cell_ps != "nan" :
#                print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_ps\t\t\t\t--\t\t[18]\t\t\t--\t\tpad control pull selector")
#            #if pd.isna(cell_he) == False  :
#            if cell_he != "nan" :
#                print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_he\t\t\t\t--\t\t[19]\t\t\t--\t\tpad control Hold enable")
#            #if pd.isna(cell_pe) == False  :
#            if cell_pe != "nan" :
#                print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_pe\t\t\t\t--\t\t[20]\t\t\t--\t\tpad control pull enable")
#            
#            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name0')
#            print_line.append("")
#            #else: 
#            #    print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name1_pu\t\t\t\t--\t\t[16]\t\t--\t\tpad control pull up")
#            #    print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name1_pd\t\t\t\t--\t\t[17]\t\t--\t\tpad control pull down")
#            #    #if 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]] :
#            #    print_line.append("--\t\t'h1\t\t--\t\tRW\t\t--\t\tpad_name1_ie\t\t\t\t--\t\t[18]\t\t--\t\tpad control input enable")
#            #    #else :
#            #    #    print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name1_ie\t\t\t\t--\t\t[18]\t\t--\t\tpad control input enable")
#            #    print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name1_ds\t\t\t\t--\t\t["+str(20+int(cell_ds_msb))+":20]\t\t--\t\tpad control driver strength")
#            #    if 'PINMUX' == pad_info[pad_info_index["type"]] :
#            #        print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name1_func_sel\t\t\t--\t\t[25:24]\t\t--\t\tpad control function select")
#            #    print_line.append("")
#            #replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name1')
#
#            count += 4
#
#    
#    print_line.append("")
#    print_line.append("// Register end\n")   
#    print_line.append("// Block end")
#    print_line.append("// Component end")
#
#
#    for line in print_line:
#        #print(line)
#        fp.write(line)
#        fp.write('\n')
#
#    fp.close()
#
#    gen_xml = "gen_xml.pl "+gen_filepath+filename.upper()+".note"
#    print(gen_xml)
##}}}

def io_ring_gen(protocol, design_owner, pad_cell, pad_info_index, gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index, design_hier) :#{{{
    fp = open(gen_filepath+filename+"_ring.v", "w") 
    
    print_line = []
    tdr_buf_list = []
    add_header(print_line, filename+"_ring.v")
    print_line.append('module '+filename+'_ring(')

    count = 0
    print_line.append("\tinput               test_mode,")
    for pad_info in pad_corpus:
        count += 1  
        if 'ANALOG' == pad_info[pad_info_index["type"]]:
            print_line.append('\t//pad PAD_NAME')
            #print(pad_ser.index.max())
            #print(count)
            print_line.append('\tinout        PAD_NAME,')
            #port_last_process(count, pad_ser, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif "POC" == pad_info[pad_info_index["type"]]:
            continue
        elif "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
            continue
        #    print_line.append('\t//pad PAD_NAME')
        #    print_line.append("\tinput   [7:0]       pad_name_reg_vref_sel,")
        #    print_line.append("\tinput               pad_name_reg_vref_pd,")
        #    print_line.append("\tinput               pad_name_pwrokb_h,")
        #    print_line.append("\toutput              vref,")
        #    replace_pad_name(pad_info_index, pad_info, print_line)
        #    replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif "INNO_GPIO" == pad_info[pad_info_index["pad_cell_type"]]:
            print_line.append('\t//pad PAD_NAME')
            print_line.append('\tinout        PAD_NAME,')
            print_line.append('\tinput        pad_name_oe_n,')
            print_line.append('\tinput        pad_name_i,')
            print_line.append("\tinput  [4:0] pad_name_drvpd  ,")
            print_line.append("\tinput  [4:0] pad_name_drvpu  ,")     
            print_line.append("\tinput  [5:0] pad_name_idelay ,")   
            print_line.append("\tinput  [5:0] pad_name_odelay ,")  
            print_line.append("\tinput        pad_name_ie     ,")    
            print_line.append("\tinput        pad_name_fben   ,")      
            print_line.append("\tinput        pad_name_fbsel  ,")     
            print_line.append("\tinput        pad_name_odten  ,")   
            print_line.append("\tinput  [3:0] pad_name_odtpd  ,")   
            print_line.append("\tinput  [3:0] pad_name_odtpu  ,")   
            print_line.append("\tinput  [4:0] pad_name_slew ,")     
            print_line.append("\tinput        pad_name_smit_rxmode ,")
            print_line.append("\tinput        pad_name_weakpd      ,")   
            print_line.append("\tinput        pad_name_weakpu      ,")
            print_line.append("\tinput        pad_name_pwrokb_h      ,")
            print_line.append("\tinput        pad_name_vref      ,")
            print_line.append('\toutput       pad_name_c,')
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        else :
            for cell_info in pad_cell :
                cell_info_list = cell_info.split(",")
                cell_name = cell_info_list[0]
                cell_ds_msb = 0
                cell_st_msb = 0
                cell_st = 0
                cell_sl = 0
                cell_msc = 0
                cell_ps = 0
                cell_he = 0
                cell_pe = 0
                if pad_info[pad_info_index["pad_cell_type"]] == cell_name :
                    cell_ds = str(cell_info_list[pad_cell_index["ds"]])
                    cell_st = str(cell_info_list[pad_cell_index["st"]])
                    cell_sl = str(cell_info_list[pad_cell_index["sl"]])
                    cell_msc= str(cell_info_list[pad_cell_index["msc"]])
                    cell_ps = str(cell_info_list[pad_cell_index["ps"]])
                    cell_he = str(cell_info_list[pad_cell_index["he"]])
                    cell_pe = str(cell_info_list[pad_cell_index["pe"]])
                    #print(cell_ds)
                    #print(cell_st)
                    #print(cell_sl)
                    #print(cell_msc)
                    #print(cell_ps)
                    #print(cell_he)
                    #print(cell_pe)
                    if "[" in cell_ds :
                        cell_ds_list = cell_ds.split("[", 1)
                        cell_ds_width_list = cell_ds_list[1].split(":", 1)
                        cell_ds_msb = cell_ds_width_list[0]
                    if "[" in cell_st :
                        cell_st_list = cell_st.split("[", 1)
                        cell_st_width_list = cell_st_list[1].split(":", 1)
                        cell_st_msb = cell_st_width_list[0]
            #print(pad_info)
            print_line.append('\t//pad PAD_NAME')
            print_line.append('\tinout        PAD_NAME,')
            print_line.append('\tinput        pad_name_oe_n,')
            print_line.append('\tinput        pad_name_i,')
            print_line.append('\tinput        pad_name_ie,')
#   241106
#            print_line.append('\tinput        pad_name_pu,')
#            print_line.append('\tinput        pad_name_pd,')
            print_line.append("\tinput  ["+str(cell_ds_msb)+":0] pad_name_ds,")
            #print(cell_st)
            #print(pd.isna(cell_st))
            #if pd.isna(cell_st) == False :
            if cell_st != "nan" :
                print_line.append("\tinput  ["+str(cell_st_msb)+":0] pad_name_st,")
            #if pd.isna(cell_sl) == False :
            if cell_sl != "nan" :
                print_line.append('\tinput        pad_name_sl,')
            #if pd.isna(cell_msc) == False :
            if cell_msc != "nan" :
                print_line.append('\tinput        pad_name_msc,')
            #print(cell_ps)
            #print(pd.isna(cell_ps))
            #if pd.isna(cell_ps) == False :
            if cell_ps != "nan" :
                print_line.append('\tinput        pad_name_ps,')
            else : 
                print_line.append('\tinput        pad_name_pu,')
                print_line.append('\tinput        pad_name_pd,')
            #if pd.isna(cell_he) == False :
            if cell_he != "nan" :
                print_line.append('\tinput        pad_name_he,')
            #if pd.isna(cell_pe) == False :
            if cell_pe != "nan" :
                print_line.append('\tinput        pad_name_pe,')
            print_line.append('\toutput       pad_name_c,')
            #port_last_process(count, pad_ser, print_line)
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        for repeat_idx in range(len(print_line)-1, -1, -1) :
            if print_line.count(print_line[repeat_idx]) > 1 and "input" in print_line[repeat_idx] :
                print_line.pop(repeat_idx)    
    port_last_process(count, pad_ser, print_line)
    print_line.append(');\n')


    for pad_info in pad_corpus:
        if  "INNO_GPIO" == pad_info[pad_info_index["pad_cell_type"]]:
            if False == pd.isna(pad_info[pad_info_index["dft_mode"]]) or "JT" in pad_info[pad_info_index["pad_name"]] :
                print_line.append("wire       dft_pad_name_oe_n;")
                print_line.append("wire [4:0] dft_pad_name_drvpd  ;")
                print_line.append("wire [4:0] dft_pad_name_drvpu  ;")
                print_line.append("wire [5:0] dft_pad_name_idelay ;")
                print_line.append("wire [5:0] dft_pad_name_odelay ;")
                print_line.append("wire       dft_pad_name_ie     ;")
                print_line.append("wire       dft_pad_name_fben   ;")
                print_line.append("wire       dft_pad_name_fbsel  ;")
                print_line.append("wire       dft_pad_name_odten  ;")
                print_line.append("wire [3:0] dft_pad_name_odtpd  ;")
                print_line.append("wire [3:0] dft_pad_name_odtpu  ;")
                print_line.append("wire [4:0] dft_pad_name_slew ;")
                print_line.append("wire       dft_pad_name_smit_rxmode ;")
                print_line.append("wire       dft_pad_name_weakpd      ;")
                print_line.append("wire       dft_pad_name_weakpu      ;")
                print_line.append("wire       dft_pad_name_c;")
                print_line.append("wire       dft_pad_name_i;")
        else :
            for cell_info in pad_cell :
                cell_info_list = cell_info.split(",")
                cell_name = cell_info_list[0]
                if pad_info[pad_info_index["pad_cell_type"]] == cell_name :
                    cell_ds = str(cell_info_list[pad_cell_index["ds"]])
                    cell_st = str(cell_info_list[pad_cell_index["st"]])
                    cell_sl = str(cell_info_list[pad_cell_index["sl"]])
                    cell_msc= str(cell_info_list[pad_cell_index["msc"]])
                    cell_ps = str(cell_info_list[pad_cell_index["ps"]])
                    cell_he = str(cell_info_list[pad_cell_index["he"]])
                    cell_pe = str(cell_info_list[pad_cell_index["pe"]])
                    if "[" in cell_ds :
                        cell_ds_list = cell_ds.split("[", 1)
                        cell_ds_width_list = cell_ds_list[1].split(":", 1)
                        cell_ds_msb = cell_ds_width_list[0]
                    if "[" in cell_st :
                        cell_st_list = cell_st.split("[", 1)
                        cell_st_width_list = cell_st_list[1].split(":", 1)
                        cell_st_msb = cell_st_width_list[0]
            if False == pd.isna(pad_info[pad_info_index["dft_mode"]]) or "JT" in pad_info[pad_info_index["pad_name"]] :
                #print_line.append("wire         pad_name_buf;")
                #print_line.append("wire         pad_name_en_buf;")
                print_line.append("wire         dft_pad_name_i;")
                print_line.append("wire         dft_pad_name_c;")
#   241106 ZZQ
#                print_line.append("wire         dft_pad_name_en;")
                print_line.append("wire         dft_pad_name_oe_n;")
                print_line.append("wire         dft_pad_name_ie;")
#                print_line.append("wire         dft_pad_name_pu;")
#                print_line.append("wire         dft_pad_name_pd;")
                print_line.append("wire    ["+str(cell_ds_msb)+":0] dft_pad_name_ds;")
                if cell_st != "nan" :
                    print_line.append("wire    ["+str(cell_st_msb)+":0] dft_pad_name_st;")
                if cell_sl != "nan" :
                    print_line.append("wire         dft_pad_name_sl;")
#   241106
#                if cell_msc != "nan" :
#                    print_line.append("wire         dft_pad_name_msc;")
                if cell_ps != "nan" :
                    print_line.append("wire         dft_pad_name_ps;")
#   241106 ZZQ
                else :
                    print_line.append("wire         dft_pad_name_pu;")
                    print_line.append("wire         dft_pad_name_pd;")
                if cell_he != "nan" :
                    print_line.append("wire         dft_pad_name_he;")
                if cell_pe != "nan" :
                    print_line.append("wire         dft_pad_name_pe;")
        
        replace_pad_name(pad_info_index, pad_info, print_line)
    
    for pad_info in pad_corpus:
        if 'ANALOG' == pad_info[pad_info_index["type"]]:
            print_line.append('\tanalog_base_cell u_pad_name_pad (.pad(PAD_NAME));\n')
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
            continue
        #    print_line.append("\t"+pad_info[pad_info_index["pad_cell_type"]].lower()+"_model u_pad_name_pad (")
        #    print_line.append("\t           .reg_vref_sel    (pad_name_reg_vref_sel  ),")
        #    print_line.append("\t           .reg_vref_pd     (pad_name_reg_vref_pd   ),")
        #    print_line.append("\t           .pwrokb_h        (pad_name_pwrokb_h      ),")
        #    print_line.append("\t           .vref            (vref          )")
        #    print_line.append("\t);")
        #    print_line.append("")
        #    replace_pad_name(pad_info_index, pad_info, print_line)
        #    replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif "POC" == pad_info[pad_info_index["type"]]:
            continue
        elif  "INNO_GPIO" == pad_info[pad_info_index["pad_cell_type"]]:
            if "JT" in pad_info[pad_info_index["pad_name"]] :
                if pad_info[pad_info_index["normal_attr"]] == "INPUT" :
                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_i_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    print_line.append("    assign  dft_pad_name_oe_n        = test_mode ?  1'b0     : pad_name_oe_n       ;")
                    print_line.append("    test_tdr_mux #(1) u_pad_name_i_test_tdr_mux( test_mode, pad_name_i      , dft_pad_name_i      );")
                    print_line.append("    assign  dft_pad_name_drvpd       = test_mode ?  "+pad_info[pad_info_index["drv"]]+" : pad_name_drvpd      ;")
                    print_line.append("    assign  dft_pad_name_drvpu       = test_mode ?  "+pad_info[pad_info_index["drv"]]+" : pad_name_drvpu      ;")
                    print_line.append("    assign  dft_pad_name_idelay      = test_mode ?  6'b0     : pad_name_idelay     ;")
                    print_line.append("    assign  dft_pad_name_odelay      = test_mode ?  6'b0     : pad_name_odelay     ;")
                    print_line.append("    assign  dft_pad_name_ie          = test_mode ?  1'b1     : pad_name_ie         ;")
                    print_line.append("    assign  dft_pad_name_fben        = test_mode ?  1'b0     : pad_name_fben       ;")
                    print_line.append("    assign  dft_pad_name_fbsel       = test_mode ?  1'b0     : pad_name_fbsel      ;")
                    print_line.append("    assign  dft_pad_name_odten       = test_mode ?  1'b0     : pad_name_odten      ;")
                    print_line.append("    assign  dft_pad_name_odtpd       = test_mode ?  4'b0  : pad_name_odtpd      ;")
                    print_line.append("    assign  dft_pad_name_odtpu       = test_mode ?  4'b0  : pad_name_odtpu      ;")
                    print_line.append("    assign  dft_pad_name_slew        = test_mode ?  5'b0     : pad_name_slew       ;")
                    print_line.append("    assign  dft_pad_name_smit_rxmode = test_mode ?  "+pad_info[pad_info_index["rx_smit"]]+"     : pad_name_smit_rxmode;")
#                    print_line.append("    assign  dft_pad_name_weakpd      = test_mode ?  1'b0     : pad_name_weakpd     ;")
#                    print_line.append("    assign  dft_pad_name_weakpu      = test_mode ?  1'b0     : pad_name_weakpu     ;")
                    print_line.append("    assign  dft_pad_name_weakpd      = test_mode ?  "+pad_info[pad_info_index["pd"]]+" : pad_name_weakpd     ;")
                    print_line.append("    assign  dft_pad_name_weakpu      = test_mode ?  "+pad_info[pad_info_index["pu"]]+" : pad_name_weakpu     ;")
                elif pad_info[pad_info_index["normal_attr"]] == "OUTPUT" :
                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_i_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    print_line.append("    assign  dft_pad_name_oe_n        = test_mode ?  1'b1     : pad_name_oe_n       ;")
                    print_line.append("    test_tdr_mux #(1) u_pad_name_i_test_tdr_mux( test_mode, pad_name_i      , dft_pad_name_i      );")
                    print_line.append("    assign  dft_pad_name_drvpd       = test_mode ?  "+pad_info[pad_info_index["drv"]]+" : pad_name_drvpd      ;")
                    print_line.append("    assign  dft_pad_name_drvpu       = test_mode ?  "+pad_info[pad_info_index["drv"]]+" : pad_name_drvpu      ;")
                    print_line.append("    assign  dft_pad_name_idelay      = test_mode ?  6'b0     : pad_name_idelay     ;")
                    print_line.append("    assign  dft_pad_name_odelay      = test_mode ?  6'b0     : pad_name_odelay     ;")
                    print_line.append("    assign  dft_pad_name_ie          = test_mode ?  1'b1     : pad_name_ie         ;")
                    print_line.append("    assign  dft_pad_name_fben        = test_mode ?  1'b0     : pad_name_fben       ;")
                    print_line.append("    assign  dft_pad_name_fbsel       = test_mode ?  1'b0     : pad_name_fbsel      ;")
                    print_line.append("    assign  dft_pad_name_odten       = test_mode ?  1'b0     : pad_name_odten      ;")
                    print_line.append("    assign  dft_pad_name_odtpd       = test_mode ?  4'b0     : pad_name_odtpd      ;")
                    print_line.append("    assign  dft_pad_name_odtpu       = test_mode ?  4'b0     : pad_name_odtpu      ;")
                    print_line.append("    assign  dft_pad_name_slew        = test_mode ?  5'b0     : pad_name_slew       ;")
                    print_line.append("    assign  dft_pad_name_smit_rxmode = test_mode ?  "+pad_info[pad_info_index["rx_smit"]]+"     : pad_name_smit_rxmode;")
                    print_line.append("    assign  dft_pad_name_weakpd      = test_mode ?  "+pad_info[pad_info_index["pd"]]+" : pad_name_weakpd     ;")
                    print_line.append("    assign  dft_pad_name_weakpu      = test_mode ?  "+pad_info[pad_info_index["pu"]]+" : pad_name_weakpu     ;")
                    #print_line.append("    assign  dft_pad_name_weakpd      = test_mode ?  1'b0     : pad_name_weakpd     ;")
                    #print_line.append("    assign  dft_pad_name_weakpu      = test_mode ?  1'b0     : pad_name_weakpu     ;")

                print_line.append("`ifdef TSMC22")
                print_line.append("    assign dft_pad_name_c = test_mode ? pad_name_c : 1'b0;")
                print_line.append("    `STD_CLK_BUF_CELL u_buf_pad_name(")
                print_line.append("         .Z          (   ),")
                print_line.append("         .I          (dft_pad_name_c)")
                print_line.append("     );")
                print_line.append("`else")
                print_line.append("    assign dft_pad_name_c = 1'b0;")
                print_line.append("`endif") 

                print_line.append("    "+pad_info[pad_info_index["pad_cell_type"]].lower()+"_model u_pad_name_pad (")
                print_line.append("        .pad        (PAD_NAME            ),")
                print_line.append("        .c          (pad_name_c          ),")
                print_line.append("        .oe         (dft_pad_name_oe_n      ),")
                print_line.append("        .i          (dft_pad_name_i         ),")
                print_line.append("        .drvpd      (dft_pad_name_drvpd      ),")
                print_line.append("        .drvpu      (dft_pad_name_drvpu      ),")
                print_line.append("        .idelay     (dft_pad_name_idelay     ),")
                print_line.append("        .odelay     (dft_pad_name_odelay     ),")
                print_line.append("        .ie         (dft_pad_name_ie         ),")
                print_line.append("        .fben       (dft_pad_name_fben       ),")
                print_line.append("        .fbsel      (dft_pad_name_fbsel      ),")
                print_line.append("        .odten      (dft_pad_name_odten      ),")
                print_line.append("        .odtpd      (dft_pad_name_odtpd      ),")
                print_line.append("        .odtpu      (dft_pad_name_odtpu      ),")
                print_line.append("        .slew       (dft_pad_name_slew       ),")
                print_line.append("        .smit_rxmode(dft_pad_name_smit_rxmode),")
                print_line.append("        .weakpd     (dft_pad_name_weakpd     ),")
                print_line.append("        .weakpu     (dft_pad_name_weakpu     ),")
                print_line.append("        .pwrokb_h   (pad_name_pwrokb_h       ),")
                print_line.append("        .vref       (pad_name_vref           )")
                print_line.append("    );")
            elif False == pd.isna(pad_info[pad_info_index["dft_mode"]]) :
                #elif pad_info[pad_info_index["normal_attr"]] == "INOUT" :
                tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_oe_n_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_i_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                binary_string = list(reversed(list(bin(int(pad_info[pad_info_index["drv"]][3:], 2))[2:])))
                #print(int(pad_info[pad_info_index["drv"]][3:]))
                #print(int(pad_info[pad_info_index["drv"]][3:], 2))
                #print(bin(int(pad_info[pad_info_index["drv"]][3:], 2))[2:])
                for i in range(5) :
                    if(i >= len(binary_string)) :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_drvpd_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    else :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_drvpd_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf "+str(binary_string[i]))
                for i in range(5) :
                    if(i >= len(binary_string)) :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_drvpu_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    else :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_drvpu_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf "+str(binary_string[i]))
                for i in range(6) :
                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_idelay_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf 0")
                for i in range(6) :
                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_odelay_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf 0")
                tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_ie_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 1")
                tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_fben_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_fbsel_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_odten_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                binary_string = list(reversed(list(bin(0)[3:])))
                for i in range(4) :
                    if(i >= len(binary_string)) :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_odtpd_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    else :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_odtpd_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf "+str(binary_string[i]))
                for i in range(4) :
                    if(i >= len(binary_string)) :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_odtpu_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    else :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_odtpu_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf "+str(binary_string[i]))
                for i in range(5) :
                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_slew_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf 0")
                tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_smit_rxmode_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf "+str(pad_info[pad_info_index["rx_smit"]][3:])+"")

                if pad_info[pad_info_index["pu"]] == "1'b1" :
                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_weakpd_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 1")
                else :
                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_weakpd_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                if pad_info[pad_info_index["pd"]] == "1'b1" :
                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_weakpu_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 1")
                else :
                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_weakpu_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                print_line.append("    test_tdr_mux #(1) u_pad_name_oe_n_test_tdr_mux( test_mode, pad_name_oe_n       , dft_pad_name_oe_n       );")
                print_line.append("    test_tdr_mux #(1) u_pad_name_i_test_tdr_mux( test_mode, pad_name_i      , dft_pad_name_i      );")
                print_line.append("    test_tdr_mux #(5) u_pad_name_drvpd_test_tdr_mux( test_mode, pad_name_drvpd      , dft_pad_name_drvpd      );")
                print_line.append("    test_tdr_mux #(5) u_pad_name_drvpu_test_tdr_mux( test_mode, pad_name_drvpu      , dft_pad_name_drvpu      );")
                print_line.append("    test_tdr_mux #(6) u_pad_name_idelay_test_tdr_mux( test_mode, pad_name_idelay     , dft_pad_name_idelay     );")
                print_line.append("    test_tdr_mux #(6) u_pad_name_odelay_test_tdr_mux( test_mode, pad_name_odelay     , dft_pad_name_odelay     );")
                print_line.append("    test_tdr_mux #(1) u_pad_name_ie_test_tdr_mux( test_mode, pad_name_ie         , dft_pad_name_ie         );")
                print_line.append("    test_tdr_mux #(1) u_pad_name_fben_test_tdr_mux( test_mode, pad_name_fben       , dft_pad_name_fben       );")
                print_line.append("    test_tdr_mux #(1) u_pad_name_fbsel_test_tdr_mux( test_mode, pad_name_fbsel      , dft_pad_name_fbsel      );")
                print_line.append("    test_tdr_mux #(1) u_pad_name_odten_test_tdr_mux( test_mode, pad_name_odten      , dft_pad_name_odten      );")
                print_line.append("    test_tdr_mux #(4) u_pad_name_odtpd_test_tdr_mux( test_mode, pad_name_odtpd      , dft_pad_name_odtpd      );")
                print_line.append("    test_tdr_mux #(4) u_pad_name_odtpu_test_tdr_mux( test_mode, pad_name_odtpu      , dft_pad_name_odtpu      );")
                print_line.append("    test_tdr_mux #(5) u_pad_name_slew_test_tdr_mux( test_mode, pad_name_slew       , dft_pad_name_slew       );")
                print_line.append("    test_tdr_mux #(1) u_pad_name_smit_rxmode_test_tdr_mux( test_mode, pad_name_smit_rxmode, dft_pad_name_smit_rxmode);")
                print_line.append("    test_tdr_mux #(1) u_pad_name_weakpd_test_tdr_mux( test_mode, pad_name_weakpd     , dft_pad_name_weakpd     );")
                print_line.append("    test_tdr_mux #(1) u_pad_name_weakpu_test_tdr_mux( test_mode, pad_name_weakpu     , dft_pad_name_weakpu     );")
                
                print_line.append("`ifdef TSMC22")
                print_line.append("    assign dft_pad_name_c = test_mode ? pad_name_c : 1'b0;")
                print_line.append("    `STD_CLK_BUF_CELL u_buf_pad_name(")
                print_line.append("         .Z          (   ),")
                print_line.append("         .I          (dft_pad_name_c)")
                print_line.append("     );")
                print_line.append("`else")
                print_line.append("    assign dft_pad_name_c = 1'b0;")
                print_line.append("`endif") 

                print_line.append("    "+pad_info[pad_info_index["pad_cell_type"]].lower()+"_model u_pad_name_pad (")
                print_line.append("        .pad        (PAD_NAME            ),")
                print_line.append("        .c          (pad_name_c          ),")
                print_line.append("        .oe         (dft_pad_name_oe_n      ),")
                print_line.append("        .i          (dft_pad_name_i         ),")
                print_line.append("        .drvpd      (dft_pad_name_drvpd      ),")
                print_line.append("        .drvpu      (dft_pad_name_drvpu      ),")
                print_line.append("        .idelay     (dft_pad_name_idelay     ),")
                print_line.append("        .odelay     (dft_pad_name_odelay     ),")
                print_line.append("        .ie         (dft_pad_name_ie         ),")
                print_line.append("        .fben       (dft_pad_name_fben       ),")
                print_line.append("        .fbsel      (dft_pad_name_fbsel      ),")
                print_line.append("        .odten      (dft_pad_name_odten      ),")
                print_line.append("        .odtpd      (dft_pad_name_odtpd      ),")
                print_line.append("        .odtpu      (dft_pad_name_odtpu      ),")
                print_line.append("        .slew       (dft_pad_name_slew       ),")
                print_line.append("        .smit_rxmode(dft_pad_name_smit_rxmode),")
                print_line.append("        .weakpd     (dft_pad_name_weakpd     ),")
                print_line.append("        .weakpu     (dft_pad_name_weakpu     ),")
                print_line.append("        .pwrokb_h   (pad_name_pwrokb_h       ),")
                print_line.append("        .vref       (pad_name_vref           )")
                print_line.append("    );")
            else :
                print_line.append("    "+pad_info[pad_info_index["pad_cell_type"]].lower()+"_model u_pad_name_pad (")
                print_line.append("        .pad        (PAD_NAME            ),")
                print_line.append("        .c          (pad_name_c          ),")
                print_line.append("        .oe         (pad_name_oe_n      ),")
                print_line.append("        .i          (pad_name_i          ),")
                print_line.append("        .drvpd      (pad_name_drvpd      ),")
                print_line.append("        .drvpu      (pad_name_drvpu      ),")
                print_line.append("        .idelay     (pad_name_idelay     ),")
                print_line.append("        .odelay     (pad_name_odelay     ),")
                print_line.append("        .ie         (pad_name_ie         ),")
                print_line.append("        .fben       (pad_name_fben       ),")
                print_line.append("        .fbsel      (pad_name_fbsel      ),")
                print_line.append("        .odten      (pad_name_odten      ),")
                print_line.append("        .odtpd      (pad_name_odtpd      ),")
                print_line.append("        .odtpu      (pad_name_odtpu      ),")
                print_line.append("        .slew       (pad_name_slew       ),")
                print_line.append("        .smit_rxmode(pad_name_smit_rxmode),")
                print_line.append("        .weakpd     (pad_name_weakpd     ),")
                print_line.append("        .weakpu     (pad_name_weakpu     ),")
                print_line.append("        .pwrokb_h   (pad_name_pwrokb_h   ),")
                print_line.append("        .vref       (pad_name_vref       )")
                print_line.append("    );")
            print_line.append("")
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
            replace_pad_name(pad_info_index, pad_info, tdr_buf_list)
            replace_PAD_NAME(pad_info_index, pad_info, tdr_buf_list)
        else :
            #cell_ds_msb = 0
            #cell_st_msb = 0
            #cell_st = 0
            #cell_sl = 0
            #cell_msc = 0
            #cell_ps = 0
            #cell_he = 0
            #cell_pe = 0
            for cell_info in pad_cell :
                cell_info_list = cell_info.split(",")
                cell_name = cell_info_list[0]
                if pad_info[pad_info_index["pad_cell_type"]] == cell_name :
                    cell_ds = str(cell_info_list[pad_cell_index["ds"]])
                    cell_st = str(cell_info_list[pad_cell_index["st"]])
                    cell_sl = str(cell_info_list[pad_cell_index["sl"]])
                    cell_msc= str(cell_info_list[pad_cell_index["msc"]])
                    cell_ps = str(cell_info_list[pad_cell_index["ps"]])
                    cell_he = str(cell_info_list[pad_cell_index["he"]])
                    cell_pe = str(cell_info_list[pad_cell_index["pe"]])
                    #print(cell_ds)
                    #print(cell_st)
                    #print(cell_sl)
                    #print(cell_msc)
                    #print(cell_ps)
                    #print(cell_he)
                    #print(cell_pe)
                    if "[" in cell_ds :
                        cell_ds_list = cell_ds.split("[", 1)
                        cell_ds_width_list = cell_ds_list[1].split(":", 1)
                        cell_ds_msb = cell_ds_width_list[0]
                    if "[" in cell_st :
                        cell_st_list = cell_st.split("[", 1)
                        cell_st_width_list = cell_st_list[1].split(":", 1)
                        cell_st_msb = cell_st_width_list[0]
            if "JT" in pad_info[pad_info_index["pad_name"]] :
                if pad_info[pad_info_index["normal_attr"]] == "INPUT" :
                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_i_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    print_line.append("    assign dft_pad_name_oe_n  = test_mode ? 1'b0 : pad_name_oe_n;")
                    print_line.append("    test_tdr_mux #(1) u_pad_name_i_test_tdr_mux( test_mode, pad_name_i      , dft_pad_name_i      );")
                    print_line.append("    assign dft_pad_name_ie  = test_mode ? 1'b0 : pad_name_ie;")
#   241106  ZZQ
#                    print_line.append("    assign dft_pad_name_pu  = test_mode ? 1'b0 : pad_name_pu;")
#                    print_line.append("    assign dft_pad_name_pd  = test_mode ? 1'b0 : pad_name_pd;")
                    if cell_sl != "nan" :
                        print_line.append("    assign dft_pad_name_sl  = test_mode ? 1'b0 : pad_name_sl;")
                    #if cell_msc != "nan" :
                    #    print_line.append("    assign dft_pad_name_msc = test_mode ? 1'b0 : pad_name_msc;")
                    if cell_ps != "nan" :
                        if pad_info[pad_info_index["pu"]] == "1'b1" :
                            print_line.append("    assign dft_pad_name_ps  = test_mode ? 1'b1 : pad_name_ps;")
                    else :
                            print_line.append("    assign dft_pad_name_ps  = test_mode ? 1'b0 : pad_name_ps;")
                    if cell_he != "nan" :
                        print_line.append("    assign dft_pad_name_he  = test_mode ? 1'b0 : pad_name_he;")
                    if cell_pe != "nan" :
                        if pad_info[pad_info_index["pu"]] == "1'b1" or pad_info[pad_info_index["pd"]] == "1'b1" :
                            print_line.append("    assign dft_pad_name_pe  = test_mode ? 1'b1 : pad_name_pe;")
                        else :
                            print_line.append("    assign dft_pad_name_pe  = test_mode ? 1'b0 : pad_name_pe;")
                    print_line.append("    assign dft_pad_name_ds  = test_mode ? "+pad_info[pad_info_index["drv"]]+" : pad_name_ds;")
                    if cell_st != "nan" :
                        print_line.append("    assign dft_pad_name_st  = test_mode ? {"+str(1+int(cell_st_msb))+"{1'b0}} : pad_name_st;")
                elif pad_info[pad_info_index["normal_attr"]] == "OUTPUT" :
                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_i_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    print_line.append("    assign dft_pad_name_oe_n  = test_mode ? 1'b0 : pad_name_oe_n;")
                    print_line.append("    test_tdr_mux #(1) u_pad_name_i_test_tdr_mux( test_mode, pad_name_i      , dft_pad_name_i      );")
                    print_line.append("    assign dft_pad_name_ie  = test_mode ? 1'b0 : pad_name_ie;")
#   241106 ZZQ
#                    print_line.append("    assign dft_pad_name_pu  = test_mode ? 1'b0 : pad_name_pu;")
#                    print_line.append("    assign dft_pad_name_pd  = test_mode ? 1'b0 : pad_name_pd;")
                    if cell_sl != "nan" :
                        print_line.append("    assign dft_pad_name_sl  = test_mode ? 1'b0 : pad_name_sl;")
                    #if cell_msc != "nan" :
                    #    print_line.append("    assign dft_pad_name_msc = test_mode ? 1'b0 : pad_name_msc;")
                    if cell_ps != "nan" :
                        if pad_info[pad_info_index["pu"]] == "1'b1" :
                            print_line.append("    assign dft_pad_name_ps  = test_mode ? 1'b1 : pad_name_ps;")
                        else :
                            print_line.append("    assign dft_pad_name_ps  = test_mode ? 1'b0 : pad_name_ps;")
		            #else :
                    if cell_ps == "nan" :
                        print_line.append("    assign dft_pad_name_pu  = test_mode ? "+pad_info[pad_info_index["pu"]]+" : pad_name_pu;")
                        print_line.append("    assign dft_pad_name_pd  = test_mode ? "+pad_info[pad_info_index["pd"]]+" : pad_name_pd;")
                    if cell_he != "nan" :
                        print_line.append("    assign dft_pad_name_he  = test_mode ? 1'b0 : pad_name_he;")
                    if cell_pe != "nan" :
                        if pad_info[pad_info_index["pu"]] == "1'b1" or pad_info[pad_info_index["pd"]] == "1'b1" :
                            print_line.append("    assign dft_pad_name_pe  = test_mode ? 1'b1 : pad_name_pe;")
                        else :
                            print_line.append("    assign dft_pad_name_pe  = test_mode ? 1'b0 : pad_name_pe;")
                    print_line.append("    assign dft_pad_name_ds  = test_mode ? "+pad_info[pad_info_index["drv"]]+" : pad_name_ds;")
                    if cell_st != "nan" :
                        print_line.append("    assign dft_pad_name_st  = test_mode ? {"+str(1+int(cell_st_msb))+"{1'b0}} : pad_name_st;")
                print_line.append("`ifdef TSMC22")
                print_line.append("    assign dft_pad_name_c = test_mode ? pad_name_c : 1'b0;")
                print_line.append("    `STD_CLK_BUF_CELL u_buf_pad_name(")
                print_line.append("         .Z          (   ),")
                print_line.append("         .I          (dft_pad_name_c)")
                print_line.append("     );")
                print_line.append("`else")
                print_line.append("    assign dft_pad_name_c = 1'b0;")
                print_line.append("`endif") 
                print_line.append("    "+pad_info[pad_info_index["pad_cell_type"]].lower()+"_model u_pad_name_pad (")
                print_line.append("        .oen(dft_pad_name_oe_n),")
                print_line.append("        .i  (dft_pad_name_i  ),")
                print_line.append("        .ie (dft_pad_name_ie ),")
#                print_line.append("        .pu (dft_pad_name_pu ),")
#                print_line.append("        .pd (dft_pad_name_pd ),")
                print_line.append("        .ds (dft_pad_name_ds ),")
                if cell_st != "nan" :
                    print_line.append("        .st (dft_pad_name_st ),")
                if cell_sl != "nan" :
                    print_line.append("        .sl (dft_pad_name_sl ),")
                if cell_msc != "nan" :
                    print_line.append("        .msc (pad_name_msc ),")
                if cell_ps != "nan" :
                    print_line.append("        .ps (dft_pad_name_ps ),")
#   241106  ZZQ
                else :
                    print_line.append("        .pu (dft_pad_name_pu ),")
                    print_line.append("        .pd (dft_pad_name_pd ),")
                if cell_he != "nan" :
                    print_line.append("        .he (dft_pad_name_he ),")
                if cell_pe != "nan" :
                    print_line.append("        .pe (dft_pad_name_pe ),")
                print_line.append("        .c  (pad_name_c  ),")
                print_line.append("        .pad(PAD_NAME    )")
                print_line.append("        );\n")

            elif False == pd.isna(pad_info[pad_info_index["dft_mode"]]) :

                #elif pad_info[pad_info_index["normal_attr"]] == "INOUT" :
                tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_oe_n_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_i_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_ie_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
#                if pad_info[pad_info_index["pu"]] == "1'b1" :
#                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_pu_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 1")
#                else :
#                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_pu_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
#                if pad_info[pad_info_index["pd"]] == "1'b1" :
#                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_pd_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 1")
#                else :
#                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_pd_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                print_line.append("    test_tdr_mux #(1) u_pad_name_oe_n_test_tdr_mux( test_mode, pad_name_oe_n      , dft_pad_name_oe_n      );")
                print_line.append("    test_tdr_mux #(1) u_pad_name_i_test_tdr_mux( test_mode, pad_name_i      , dft_pad_name_i      );")
                print_line.append("    test_tdr_mux #(1) u_pad_name_ie_test_tdr_mux( test_mode, pad_name_ie      , dft_pad_name_ie      );")
                #print_line.append("    test_tdr_mux #(1) u_pad_name_pu_test_tdr_mux( test_mode, pad_name_pu      , dft_pad_name_pu      );")
                #print_line.append("    test_tdr_mux #(1) u_pad_name_pd_test_tdr_mux( test_mode, pad_name_pd      , dft_pad_name_pd      );")
                if cell_sl != "nan" :
                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_sl_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    print_line.append("    test_tdr_mux #(1) u_pad_name_sl_test_tdr_mux( test_mode, pad_name_sl      , dft_pad_name_sl      );")
                #if cell_msc != "nan" :
                #    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_msc_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                #    print_line.append("    test_tdr_mux #(1) u_pad_name_msc_test_tdr_mux( test_mode, pad_name_msc      , dft_pad_name_msc      );")
                if cell_ps != "nan" :
                    if pad_info[pad_info_index["pu"]] == "1'b1" :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_ps_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 1")
                    else :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_ps_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    print_line.append("    test_tdr_mux #(1) u_pad_name_ps_test_tdr_mux( test_mode, pad_name_ps      , dft_pad_name_ps      );")
#   241106 ZZQ
                else :
                    print_line.append("    test_tdr_mux #(1) u_pad_name_pu_test_tdr_mux( test_mode, pad_name_pu      , dft_pad_name_pu      );")
                    print_line.append("    test_tdr_mux #(1) u_pad_name_pd_test_tdr_mux( test_mode, pad_name_pd      , dft_pad_name_pd      );")
                    if pad_info[pad_info_index["pu"]] == "1'b1" :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_pu_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 1")
                    else :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_pu_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    if pad_info[pad_info_index["pd"]] == "1'b1" :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_pd_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 1")
                    else :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_pd_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                if cell_he != "nan" :
                    tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_he_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    print_line.append("    test_tdr_mux #(1) u_pad_name_he_test_tdr_mux( test_mode, pad_name_he      , dft_pad_name_he      );")
                if cell_pe != "nan" :
                    if pad_info[pad_info_index["pu"]] == "1'b1" or pad_info[pad_info_index["pd"]] == "1'b1" :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_pe_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 1")
                    else :
                    	tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_pe_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    print_line.append("    test_tdr_mux #(1) u_pad_name_pe_test_tdr_mux( test_mode, pad_name_pe      , dft_pad_name_pe      );")
                
                #print(pad_info[pad_info_index["drv"]])
                #print(int(pad_info[pad_info_index["drv"]][3:]))
                #print(int(pad_info[pad_info_index["drv"]][3:], 2))
                #print(bin(int(pad_info[pad_info_index["drv"]][3:], 2)))
                #print(list(reversed(list(bin(0)[3:]))))
                binary_string = list(reversed(list(bin(int(pad_info[pad_info_index["drv"]][3:], 2))[2:])))
                for i in range(1+int(cell_ds_msb)) :
                    if(i >= len(binary_string)) :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_ds_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    else :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_ds_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf "+binary_string[i])
                print_line.append("    test_tdr_mux #("+str(1+int(cell_ds_msb))+") u_pad_name_ds_test_tdr_mux( test_mode, pad_name_ds      , dft_pad_name_ds      );")
                if cell_st != "nan" :
                    binary_string = list(reversed(list(bin(1+int(cell_st_msb))[3:])))
                    for i in range(1+int(cell_st_msb)) :
                        tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_"+filename+"_ring/u_pad_name_st_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf 0")
                    print_line.append("    test_tdr_mux #("+str(1+int(cell_st_msb))+") u_pad_name_st_test_tdr_mux( test_mode, pad_name_st      , dft_pad_name_st      );")
                print_line.append("`ifdef TSMC22")
                print_line.append("    assign dft_pad_name_c = test_mode ? pad_name_c : 1'b0;")
                print_line.append("    `STD_CLK_BUF_CELL u_buf_pad_name(")
                print_line.append("         .Z          (   ),")
                print_line.append("         .I          (dft_pad_name_c)")
                print_line.append("     );")
                print_line.append("`else")
                print_line.append("    assign dft_pad_name_c = 1'b0;")
                print_line.append("`endif") 
                print_line.append("    "+pad_info[pad_info_index["pad_cell_type"]].lower()+"_model u_pad_name_pad (")
                print_line.append("        .oen(dft_pad_name_oe_n),")
                print_line.append("        .i  (dft_pad_name_i  ),")
                print_line.append("        .ie (dft_pad_name_ie ),")
#   241106  ZZQ
#                print_line.append("        .pu (dft_pad_name_pu ),")
#                print_line.append("        .pd (dft_pad_name_pd ),")
                print_line.append("        .ds (dft_pad_name_ds ),")
                if cell_st != "nan" :
                    print_line.append("        .st (dft_pad_name_st ),")
                if cell_sl != "nan" :
                    print_line.append("        .sl (dft_pad_name_sl ),")
                if cell_msc != "nan" :
                    print_line.append("        .msc (pad_name_msc ),")
                if cell_ps != "nan" :
                    print_line.append("        .ps (dft_pad_name_ps ),")
#   241106 ZZQ
                else :
                    print_line.append("        .pu (dft_pad_name_pu ),")
                    print_line.append("        .pd (dft_pad_name_pd ),")
                if cell_he != "nan" :
                    print_line.append("        .he (dft_pad_name_he ),")
                if cell_pe != "nan" :
                    print_line.append("        .pe (dft_pad_name_pe ),")
                print_line.append("        .c  (pad_name_c  ),")
                print_line.append("        .pad(PAD_NAME    )")
                print_line.append("        );\n")
            else :
                print_line.append("    "+pad_info[pad_info_index["pad_cell_type"]].lower()+"_model u_pad_name_pad (")
                print_line.append("        .oen(pad_name_oe_n),")
                print_line.append("        .i  (pad_name_i  ),")
                print_line.append("        .ie (pad_name_ie ),")
#   241106 ZZQ
#                print_line.append("        .pu (pad_name_pu ),")
#                print_line.append("        .pd (pad_name_pd ),")
                print_line.append("        .ds (pad_name_ds ),")
                if cell_st != "nan" :
                    print_line.append("        .st (pad_name_st ),")
                if cell_sl != "nan" :
                    print_line.append("        .sl (pad_name_sl ),")
                if cell_msc != "nan" :
                    print_line.append("        .msc (pad_name_msc ),")
                if cell_ps != "nan" :
                    print_line.append("        .ps (pad_name_ps ),")
#   241106 ZZQ
                else :
                    print_line.append("        .pu (pad_name_pu ),")
                    print_line.append("        .pd (pad_name_pd ),")
                if cell_he != "nan" :
                    print_line.append("        .he (pad_name_he ),")
                if cell_pe != "nan" :
                    print_line.append("        .pe (pad_name_pe ),")
                print_line.append("        .c  (pad_name_c  ),")
                print_line.append("        .pad(PAD_NAME    )")
                print_line.append("        );\n")
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
            replace_pad_name(pad_info_index, pad_info, tdr_buf_list)
            replace_PAD_NAME(pad_info_index, pad_info, tdr_buf_list)
    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')
    fp.write('endmodule')

    fp.close()

    fp = open(gen_filepath+filename+"_tdr_buf_list.txt", "w") 
    for line in tdr_buf_list :
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')

    fp.close()

#}}}

def io_pin_mux_gen(protocol, design_owner, pad_cell, pad_info_index, gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index) :#{{{
    fp = open(gen_filepath+filename+"_pin_mux.v", "w") 
    
    print_line = []
    add_header(print_line, filename+"_pin_mux.v")
    print_line.append('`include "std_cell_def.h"')
    print_line.append('module '+filename+'_pin_mux(')

    print_line.append("\tinput               test_mode,")

# pin_mux port{{{
    count = 0
    for pad_info in pad_corpus:
        count += 1
        if "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
            replace_pad_name(pad_info_index, pad_info, print_line)
        elif 'GPIO' == pad_info[pad_info_index["type"]]:
            #print(pad_info)
            print_line.append('\t//pad PAD_NAME')
            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tinput          pad_name_c,')
                print_line.append('\toutput         pad_name_i,')
                print_line.append('\toutput         pad_name_oe_n,'),
                print_line.append('\tinput          pad_name_out,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            elif 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tinput          pad_name_c,')
                print_line.append('\toutput         pad_name_i,')
                print_line.append('\toutput         pad_name_oe_n,'),
                print_line.append('\toutput         pad_name_in,') 
                replace_pad_name(pad_info_index, pad_info, print_line)
            elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tinput          pad_name_c,')
                print_line.append('\toutput         pad_name_i,')
                print_line.append('\toutput         pad_name_oe_n,')
                print_line.append('\tinput          pad_name_out,')
                print_line.append('\tinput          pad_name_oen,')
                print_line.append('\toutput         pad_name_in,') 
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'GPI' == pad_info[pad_info_index["type"]] :
            print_line.append('\t//pad PAD_NAME')
            if 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tinput          pad_name_c,')
                print_line.append('\toutput         pad_name_in,') 
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'GPO' == pad_info[pad_info_index["type"]] :
            print_line.append('\t//pad PAD_NAME')
            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\toutput         pad_name_i,')
                print_line.append('\toutput         pad_name_oe_n,'),
                print_line.append('\tinput          pad_name_out,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'PINMUX' == pad_info[pad_info_index["type"]]: 
            print_line.append('\t//pad PAD_NAME')
            print_line.append('\tinput          pad_name_c,')
            print_line.append('\toutput reg     pad_name_i,')
            print_line.append('\toutput reg     pad_name_oe_n,')
            print_line.append('\tinput  [1:0]   pad_name_func_sel,')
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
            replace_pad_name(pad_info_index, pad_info, print_line)
            # function 0
            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tinput          pad_name_out,')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line)
            elif 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\toutput         pad_name_in,')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line)
            elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tinput          pad_name_out,')
                print_line.append('\tinput          pad_name_oen,')
                print_line.append('\toutput         pad_name_in,')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line) 
           # function 1
            pin_mux_port_gen(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["func1_attr"]], pad_info[pad_info_index["func1"]:])
            # function 2
            pin_mux_port_gen(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["func2_attr"]], pad_info[pad_info_index["func2"]:])
            # function 3
            pin_mux_port_gen(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["func3_attr"]], pad_info[pad_info_index["func3"]:])
        #print(count)
        port_last_process(count, pad_ser, print_line)
    print_line.append(');\n')

# }}}

# define {{{
    count = 0
    for pad_info in pad_corpus:
        count += 1
        if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
            print_line.append('\twire pad_name_dft_in;')
        if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
            print_line.append('\twire pad_name_dft_out;')
        replace_pad_name(pad_info_index, pad_info, print_line)
        if "GPI" == pad_info[pad_info_index["type"]] :
            print_line.append('\twire pad_name_in_pre;')
            replace_pad_name(pad_info_index, pad_info, print_line)

        if 'PINMUX' == pad_info[pad_info_index["type"]] or "GPIO" == pad_info[pad_info_index["type"]] :
            # function 0
            if 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\twire func0_pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            # function 1
            if 'INPUT' == pad_info[pad_info_index["func1_attr"]] or 'INOUT' == pad_info[pad_info_index["func1_attr"]]:
                print_line.append('\twire func1_pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["func1"]:], print_line, 'func1_pad_name')
            # function 2
            if 'INPUT' == pad_info[pad_info_index["func2_attr"]] or 'INOUT' == pad_info[pad_info_index["func2_attr"]]:
                print_line.append('\twire func2_pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["func2"]:], print_line, 'func2_pad_name')
            # function 3
            if 'INPUT' == pad_info[pad_info_index["func3_attr"]] or 'INOUT' == pad_info[pad_info_index["func3_attr"]]:
                print_line.append('\twire func3_pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["func3"]:], print_line, 'func3_pad_name')

    print_line.append("\n")
#}}}

# pin_mux always assign {{{
    count = 0
    for pad_info in pad_corpus:
        count += 1
        if 'PINMUX' == pad_info[pad_info_index["type"]]:
            print_line.append('\t//pad PAD_NAME')
            print_line.append('\talways @ (*)')
            #if False == pd.isna(pad_info[pad_info_index["dft_mode"]]) :
            #    print_line.append("    if (test_mode == 1'b1)begin")
            #    if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
            #        print_line.append("        pad_name_oe_n = 1'b0;")
            #    elif 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
            #        print_line.append("        pad_name_oe_n = 1'b1;")
            #    print_line.append("    end")
            #    print_line.append("    else begin")
            print_line.append('\t    case (pad_name_func_sel)')
            # function 0
            if 'INPUT' == pad_info[pad_info_index["normal_attr"]] :
                print_line.append("\t        2'h0:    pad_name_oe_n = 1'b1;")
            elif 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append("\t        2'h0:    pad_name_oe_n = 1'b0;")
            elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append("\t        2'h0:    pad_name_oe_n = ~func0_pad_name_oen;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            # function 1
            if 1 == pd.isna(pad_info[pad_info_index["func1"]]) :
                if 'INPUT' == pad_info[pad_info_index["normal_attr"]] :
                    print_line.append("\t        2'h1:    pad_name_oe_n = 1'b1;")
                elif'OUTPUT' == pad_info[pad_info_index["normal_attr"]] :
                    print_line.append("\t        2'h1:    pad_name_oe_n = 1'b0;")
                elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                    print_line.append("\t        2'h1:    pad_name_oe_n = ~func0_pad_name_oen;")
            else :
                if 'INPUT' == pad_info[pad_info_index["func1_attr"]] :
                    print_line.append("\t        2'h1:    pad_name_oe_n = 1'b1;")
                elif'OUTPUT' == pad_info[pad_info_index["func1_attr"]] :
                    print_line.append("\t        2'h1:    pad_name_oe_n = 1'b0;")
                elif 'INOUT' == pad_info[pad_info_index["func1_attr"]]:
                    print_line.append("\t        2'h1:    pad_name_oe_n = ~func1_pad_name_oen;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["func1"]:], print_line, 'func1_pad_name')
            # function 2
            if 1 == pd.isna(pad_info[pad_info_index["func2"]]) :
                if 'INPUT' == pad_info[pad_info_index["normal_attr"]] :
                    print_line.append("\t        2'h2:    pad_name_oe_n = 1'b1;")
                elif'OUTPUT' == pad_info[pad_info_index["normal_attr"]] :
                    print_line.append("\t        2'h2:    pad_name_oe_n = 1'b0;")
                elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                    print_line.append("\t        2'h2:    pad_name_oe_n = ~func0_pad_name_oen;")
            else :
                if 'INPUT' == pad_info[pad_info_index["func2_attr"]] :
                    print_line.append("\t        2'h2:    pad_name_oe_n = 1'b1;")
                elif 'OUTPUT' == pad_info[pad_info_index["func2_attr"]] :
                    print_line.append("\t        2'h2:    pad_name_oe_n = 1'b0;")
                elif 'INOUT' == pad_info[pad_info_index["func2_attr"]]:
                    print_line.append("\t        2'h2:    pad_name_oe_n = ~func2_pad_name_oen;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["func2"]:], print_line, 'func2_pad_name')
            # function 3
            if 1 == pd.isna(pad_info[pad_info_index["func3"]]) :
                if 'INPUT' == pad_info[pad_info_index["normal_attr"]] :
                    print_line.append("\t        default: pad_name_oe_n = 1'b1;")
                elif'OUTPUT' == pad_info[pad_info_index["normal_attr"]] :
                    print_line.append("\t        default: pad_name_oe_n = 1'b0;")
                elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                    print_line.append("\t        default: pad_name_oe_n = ~func0_pad_name_oen;")
            else :
                if 'INPUT' == pad_info[pad_info_index["func3_attr"]] :
                    print_line.append("\t        default: pad_name_oe_n = 1'b1;")
                elif 'OUTPUT' == pad_info[pad_info_index["func3_attr"]] :
                    print_line.append("\t        default: pad_name_oe_n = 1'b0;")
                elif 'INOUT' == pad_info[pad_info_index["func3_attr"]]:
                    print_line.append('\t        default: pad_name_oe_n = ~func3_pad_name_oen;')
            replace_pad_name(pad_info_index, pad_info[pad_info_index["func3"]:], print_line, 'func3_pad_name')
            print_line.append('\t    endcase')
            #if False == pd.isna(pad_info[pad_info_index["dft_mode"]]) :
            ##if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
            #    print_line.append('\tend')

            print_line.append('\talways @ (*)')
            #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
            #    print_line.append("    if (test_mode == 1'b1)begin")
            #    print_line.append("        pad_name_i = pad_name_dft_out;")
            #    print_line.append("    end")
            #    print_line.append("    else begin")
            print_line.append('\t    case (pad_name_func_sel)')
            # function 0
            if 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append("\t        2'h0:    pad_name_i = 1'b0;")
            elif 'OUTPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append("\t        2'h0:    pad_name_i = func0_pad_name_out;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            # function 1
            if 1 == pd.isna(pad_info[pad_info_index["func1"]]):
                if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                    print_line.append("\t        2'h1:    pad_name_i = func0_pad_name_out;")
                else :
                    print_line.append("\t        2'h1:    pad_name_i = 1'b0;")
            elif 'INPUT' == pad_info[pad_info_index["func1_attr"]]:
                print_line.append("\t        2'h1:    pad_name_i = 1'b0;")
            elif 'OUTPUT' == pad_info[pad_info_index["func1_attr"]] or 'INOUT' == pad_info[pad_info_index["func1_attr"]]:
                print_line.append("\t        2'h1:    pad_name_i = func1_pad_name_out;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            replace_pad_name(pad_info_index, pad_info[pad_info_index["func1"]:], print_line, 'func1_pad_name')
            # function 2
            if 1 == pd.isna(pad_info[pad_info_index["func2"]]):
                if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                    print_line.append("\t        2'h2:    pad_name_i = func0_pad_name_out;")
                else :
                    print_line.append("\t        2'h2:    pad_name_i = 1'b0;")
            elif 'INPUT' == pad_info[pad_info_index["func2_attr"]]:
                print_line.append("\t        2'h2:    pad_name_i = 1'b0;")
            elif 'OUTPUT' == pad_info[pad_info_index["func2_attr"]] or 'INOUT' == pad_info[pad_info_index["func2_attr"]]:
                print_line.append("\t        2'h2:    pad_name_i = func2_pad_name_out;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            replace_pad_name(pad_info_index, pad_info[pad_info_index["func2"]:], print_line, 'func2_pad_name')
            # function 3
            if 1 == pd.isna(pad_info[pad_info_index["func3"]]):
                if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                    print_line.append("\t        default: pad_name_i = func0_pad_name_out;")
                else :
                    print_line.append("\t        default: pad_name_i = 1'b0;")
            elif 'INPUT' == pad_info[pad_info_index["func3_attr"]]:
                print_line.append("\t        default: pad_name_i = 1'b0;")
            elif 'OUTPUT' == pad_info[pad_info_index["func3_attr"]] or 'INOUT' == pad_info[pad_info_index["func3_attr"]]:
                print_line.append("\t        default: pad_name_i = func3_pad_name_out;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            replace_pad_name(pad_info_index, pad_info[pad_info_index["func3"]:], print_line, 'func3_pad_name')
            print_line.append('\t    endcase')
            #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
            #    print_line.append('\tend')
            #if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
            #    print_line.append("")
            #    print_line.append("\tassign pad_name_dft_in = (test_mode == 1'b1)? pad_name_c : 1'b0;")

            # function 0
            if 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                if False == pd.isna(pad_info[pad_info_index["dft_mode"]])  :
                    print_line.append("\tassign func0_pad_name_in_pre = (test_mode==1'b1)? 1'b0: ((pad_name_func_sel == 2'h0)") 
                else :
                    print_line.append("\tassign func0_pad_name_in_pre = ((pad_name_func_sel == 2'h0)") 

                if pad_info[pad_info_index["normal_mode"]] == pad_info[pad_info_index["func1"]] or True == pd.isna(pad_info[pad_info_index["func1"]]) :
                    print_line.append("\t                             || (pad_name_func_sel == 2'h1)")
                if pad_info[pad_info_index["normal_mode"]] == pad_info[pad_info_index["func2"]] or True == pd.isna(pad_info[pad_info_index["func2"]]) :
                    print_line.append("\t                             || (pad_name_func_sel == 2'h2)")
                if pad_info[pad_info_index["normal_mode"]] == pad_info[pad_info_index["func3"]] or True == pd.isna(pad_info[pad_info_index["func3"]]) :
                    print_line.append("\t                             || (pad_name_func_sel == 2'h3)")
                if pad_info[pad_info_index["normal_dflt"]] == "1'b0" or pad_info[pad_info_index["normal_dflt"]] ==  "1’b0": 
                    print_line.append("\t                             ) ? pad_name_c : 1'b0;")
                elif pad_info[pad_info_index["normal_dflt"]] == "1'b1" or pad_info[pad_info_index["normal_dflt"]] ==  "1’b1":
                    print_line.append("\t                             ) ? pad_name_c : 1'b1;")
                #print_line.append("\tassign func0_pad_name_in_pre = (pad_name_func_sel == 2'h0) ? pad_name_c : 1'b0;")
                replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            if 'INPUT' == pad_info[pad_info_index["func1_attr"]] or 'INOUT' == pad_info[pad_info_index["func1_attr"]]:
                if False == pd.isna(pad_info[pad_info_index["dft_mode"]])  :
                    print_line.append("\tassign func1_pad_name_in_pre = (test_mode==1'b1)? 1'b0: ((pad_name_func_sel == 2'h1)") 
                else :
                    print_line.append("\tassign func1_pad_name_in_pre = ((pad_name_func_sel == 2'h1)") 
                if pad_info[pad_info_index["func1"]] == pad_info[pad_info_index["func2"]] :
                    print_line.append("\t                             || (pad_name_func_sel == 2'h2)")
                if pad_info[pad_info_index["func1"]] == pad_info[pad_info_index["func3"]] :
                    print_line.append("\t                             || (pad_name_func_sel == 2'h3)")
                if pad_info[pad_info_index["func1_dflt"]] == "1'b0" or pad_info[pad_info_index["func1_dflt"]] ==  "1’b0":
                    print_line.append("\t                             ) ? pad_name_c : 1'b0;")
                elif pad_info[pad_info_index["func1_dflt"]] == "1'b1" or pad_info[pad_info_index["func1_dflt"]] ==  "1’b1":
                    print_line.append("\t                             ) ? pad_name_c : 1'b1;")
                #print_line.append("\tassign func1_pad_name_in_pre = (pad_name_func_sel == 2'h1) ? pad_name_c : 1'b0;")
                replace_pad_name(pad_info_index, pad_info[pad_info_index["func1"]:], print_line, 'func1_pad_name')
            if 'INPUT' == pad_info[pad_info_index["func2_attr"]] or 'INOUT' == pad_info[pad_info_index["func2_attr"]]:
                if False == pd.isna(pad_info[pad_info_index["dft_mode"]])  :
                    print_line.append("\tassign func2_pad_name_in_pre = (test_mode==1'b1)? 1'b0: ((pad_name_func_sel == 2'h2)") 
                else :
                    print_line.append("\tassign func2_pad_name_in_pre = ((pad_name_func_sel == 2'h2)") 
                if pad_info[pad_info_index["func2"]] == pad_info[pad_info_index["func3"]] :
                    print_line.append("\t                             || (pad_name_func_sel == 2'h3)")
                if pad_info[pad_info_index["func2_dflt"]] == "1'b0" or pad_info[pad_info_index["func2_dflt"]] ==  "1’b0":
                    print_line.append("\t                             ) ? pad_name_c : 1'b0;")
                elif pad_info[pad_info_index["func2_dflt"]] == "1'b1" or pad_info[pad_info_index["func2_dflt"]] ==  "1’b1":
                    print_line.append("\t                             ) ? pad_name_c : 1'b1;")
                #print_line.append("\tassign func2_pad_name_in_pre = (pad_name_func_sel == 2'h2) ? pad_name_c : 1'b0;")
                replace_pad_name(pad_info_index, pad_info[pad_info_index["func2"]:], print_line, 'func2_pad_name')
            if 'INPUT' == pad_info[pad_info_index["func3_attr"]] or 'INOUT' == pad_info[pad_info_index["func3_attr"]]:
                if False == pd.isna(pad_info[pad_info_index["dft_mode"]])  :
                    print_line.append("\tassign func3_pad_name_in_pre = (test_mode==1'b1)? 1'b0: ((pad_name_func_sel == 2'h3)") 
                else :
                    print_line.append("\tassign func3_pad_name_in_pre = ((pad_name_func_sel == 2'h3)") 
                if pad_info[pad_info_index["func3_dflt"]] == "1'b0" or pad_info[pad_info_index["func3_dflt"]] ==  "1’b0":
                    print_line.append("\t                             ) ? pad_name_c : 1'b0;")
                elif pad_info[pad_info_index["func3_dflt"]] == "1'b1" or pad_info[pad_info_index["func3_dflt"]] ==  "1’b1":
                    print_line.append("\t                             ) ? pad_name_c : 1'b1;")
                #print_line.append("\tassign func3_pad_name_in_pre = (pad_name_func_sel == 2'h3) ? pad_name_c : 1'b0;")
                replace_pad_name(pad_info_index, pad_info[pad_info_index["func3"]:], print_line, 'func3_pad_name')

            replace_PAD_NAME(pad_info_index, pad_info, print_line)
            replace_pad_name(pad_info_index, pad_info, print_line)
            print_line.append("\n")
# }}}

# pad assign{{{

    print_line.append("\t//---------------")
    print_line.append("\t// input buffers")
    print_line.append("\t//---------------")
    # asic
    for pad_info in pad_corpus:
        if 'GPIO' == pad_info[pad_info_index["type"]]:
            print_line.append('\t//pad PAD_NAME')
            #if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
            #   print_line.append("")
            #   print_line.append("\tassign pad_name_dft_in = (test_mode == 1'b1)? pad_name_c : 1'b0;")

            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                #if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_oe_n = (test_mode == 1'b1)? 1'b1: 1'b0;")
                #else :
                print_line.append("\tassign pad_name_oe_n = 1'b0;")
                #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_i = (test_mode == 1'b1)? pad_name_dft_out : pad_name_out;")
                #else :
                print_line.append('\tassign pad_name_i    = pad_name_out;')
                replace_pad_name(pad_info_index, pad_info, print_line)
            elif 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_oe_n   = (test_mode == 1'b1)? 1'b0: 1'b1;")
                #else :
                print_line.append("\tassign pad_name_oe_n   = 1'b1;")
                #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_i = (test_mode == 1'b1)? pad_name_dft_out : 1'b0;")
                #else :
                print_line.append("\tassign pad_name_i      = 1'b0;")
                print_line.append('\tassign pad_name_in_pre = pad_name_c;')
                replace_pad_name(pad_info_index, pad_info, print_line)
            elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_oe_n   = (test_mode == 1'b1)? 1'b0: ~pad_name_oen;")
                #else :
                print_line.append("\tassign pad_name_oe_n   = (test_mode == 1'b1)? 1'b1: ~pad_name_oen;")
                #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_i = (test_mode == 1'b1)? pad_name_dft_out : pad_name_out;")
                #else :
                print_line.append("\tassign pad_name_i    = pad_name_out;")
                print_line.append('\tassign pad_name_in_pre = pad_name_c;')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'GPI' == pad_info[pad_info_index["type"]] :
            print_line.append('\t//pad PAD_NAME')
            if 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tassign pad_name_in_pre = pad_name_c;')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'GPO' == pad_info[pad_info_index["type"]] :
            print_line.append('\t//pad PAD_NAME')
            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                #if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_oe_n = (test_mode == 1'b1)? 1'b1: 1'b0;")
                #else :
                print_line.append("\tassign pad_name_oe_n = 1'b0;")
                print_line.append('\tassign pad_name_i    = pad_name_out;')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)

    print_line.append("\n")
    
    # no asic
    print_line.append('\t`ifdef NO_ASIC')
    for pad_info in pad_corpus:
        if 'GPIO' == pad_info[pad_info_index["type"]]:
            if 'OUTPUT' != pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tassign pad_name_in = pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info, print_line)
        if 'GPI' == pad_info[pad_info_index["type"]]:
            if 'OUTPUT' != pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tassign pad_name_in = pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info, print_line)
        elif 'PINMUX' == pad_info[pad_info_index["type"]]:
            # function 0
            pad_noasic_input_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["normal_attr"]],  pad_info[pad_info_index["normal_mode"]:],   'func0_pad_name')
            # function 1
            pad_noasic_input_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func1_attr"]],  pad_info[pad_info_index["func1"]:],   'func1_pad_name')
            # function 2
            pad_noasic_input_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func2_attr"]],  pad_info[pad_info_index["func2"]:],   'func2_pad_name')
            # function 3
            pad_noasic_input_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func3_attr"]], pad_info[pad_info_index["func3"]:],  'func3_pad_name')
            # function 0
            #if 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
            #    print_line.append('\tassign func0_pad_name_in = func0_pad_name_in_pre;')
            #    replace_pad_name(pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
    # fpga
    print_line.append('\t`elsif FPGA')
    for pad_info in pad_corpus:
        if 'GPIO' == pad_info[pad_info_index["type"]]:
            if 'OUTPUT' != pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tassign pad_name_in = pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info, print_line)
        if 'GPI' == pad_info[pad_info_index["type"]]:
            if 'OUTPUT' != pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tassign pad_name_in = pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info, print_line)
        elif 'PINMUX' == pad_info[pad_info_index["type"]]:
            # function 0
            pad_noasic_input_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["normal_attr"]],  pad_info[pad_info_index["normal_mode"]:],   'func0_pad_name')
            # function 1
            pad_noasic_input_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func1_attr"]],  pad_info[pad_info_index["func1"]:],   'func1_pad_name')
            # function 2
            pad_noasic_input_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func2_attr"]],  pad_info[pad_info_index["func2"]:],   'func2_pad_name')
            # function 3
            pad_noasic_input_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func3_attr"]], pad_info[pad_info_index["func3"]:],  'func3_pad_name')
            #if 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
            #    print_line.append('\tassign func0_pad_name_in = func0_pad_name_in_pre;')
            #    replace_pad_name(pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
    # pad sta cell
    print_line.append('\t`else')
    for pad_info in pad_corpus:
        #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]]:
        #    print_line.append('\tstd_cell_clk_buf pad_name_dft_out_dontouch_buf (.clk_buf_in(), .clk_buf_out(pad_name_dft_out));')
        #if 'INPUT' == pad_info[pad_info_index["dft_mode"]]:
        #    print_line.append('\tstd_cell_clk_buf pad_name_dft_in_dontouch_buf (.clk_buf_in(pad_name_dft_in), .clk_buf_out());')
        replace_pad_name(pad_info_index, pad_info, print_line)
        
        if 'GPIO' == pad_info[pad_info_index["type"]]:
            if 'OUTPUT' != pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tstd_cell_clk_buf pad_name_in_dontouch_buf (.clk_buf_in(pad_name_in_pre), .clk_buf_out(pad_name_in));')
                replace_pad_name(pad_info_index, pad_info, print_line)
        if 'GPI' == pad_info[pad_info_index["type"]]:
            if 'OUTPUT' != pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tstd_cell_clk_buf pad_name_in_dontouch_buf (.clk_buf_in(pad_name_in_pre), .clk_buf_out(pad_name_in));')
                replace_pad_name(pad_info_index, pad_info, print_line)
        elif 'PINMUX' == pad_info[pad_info_index["type"]]:
            # function 0
            pad_input_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["normal_attr"]],  pad_info[pad_info_index["normal_mode"]:],  'func0_pad_name')
            # function 1
            pad_input_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func1_attr"]],  pad_info[pad_info_index["func1"]:],  'func1_pad_name')
            # function 2
            pad_input_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func2_attr"]],  pad_info[pad_info_index["func2"]:],  'func2_pad_name')
            # function 3
            pad_input_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func3_attr"]], pad_info[pad_info_index["func3"]:], 'func3_pad_name')
            #if 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
            #    print_line.append('\tstd_cell_clk_buf func0_pad_name_in_dontouch_buf (.buf_in(func0_pad_name_in_pre),.buf_out(func0_pad_name_in));')
            #    replace_pad_name(pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            # function 1
    print_line.append('\t`endif')
   
#}}}

    # write file
    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')
    fp.write('endmodule')

    fp.close()

#}}}

def io_pin_mux_model_gen(protocol, design_owner, pad_cell, pad_info_index, gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index) :#{{{
    fp = open(gen_filepath+filename+"_pin_mux_model.v", "w") 
    
    print_line = []
    add_header(print_line, filename+"_pin_mux_model.v")
    print_line.append('`include "std_cell_def.h"')
    print_line.append('module '+filename+'_pin_mux_model(')

# pin_mux port{{{
    count = 0
    print_line.append('\tinput          test_mode,')
    for pad_info in pad_corpus:
        count += 1
        if "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
            replace_pad_name(pad_info_index, pad_info, print_line)
        elif 'GPIO' == pad_info[pad_info_index["type"]]:
            print_line.append('\t//pad PAD_NAME')
            if 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tinput          pad_name_c,')
                print_line.append('\toutput         pad_name_i,')
                print_line.append('\toutput         pad_name_oe_n,'),
                print_line.append('\tinput          pad_name_out,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            elif 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tinput          pad_name_c,')
                print_line.append('\toutput         pad_name_i,')
                print_line.append('\toutput         pad_name_oe_n,'),
                print_line.append('\toutput         pad_name_in,') 
                replace_pad_name(pad_info_index, pad_info, print_line)
            elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tinput          pad_name_c,')
                print_line.append('\toutput         pad_name_i,')
                print_line.append('\toutput         pad_name_oe_n,')
                print_line.append('\tinput          pad_name_out,')
                print_line.append('\tinput          pad_name_oen,')
                print_line.append('\toutput         pad_name_in,') 
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'GPI' == pad_info[pad_info_index["type"]] :
            print_line.append('\t//pad PAD_NAME')
            if 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\toutput         pad_name_i,')
                print_line.append('\toutput         pad_name_oe_n,'),
                print_line.append('\tinput          pad_name_out,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'GPO' == pad_info[pad_info_index["type"]] :
            print_line.append('\t//pad PAD_NAME')
            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tinput          pad_name_c,')
                print_line.append('\toutput         pad_name_in,') 
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'PINMUX' == pad_info[pad_info_index["type"]]: 
            print_line.append('\t//pad PAD_NAME')
            print_line.append('\tinput          pad_name_c,')
            print_line.append('\toutput reg     pad_name_i,')
            print_line.append('\toutput reg     pad_name_oe_n,')
            print_line.append('\tinput  [1:0]   pad_name_func_sel,')
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
            replace_pad_name(pad_info_index, pad_info, print_line)
            # function 0
            if 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tinput          pad_name_out,')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line)
            elif 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\toutput         pad_name_in,')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line)
            elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tinput          pad_name_out,')
                print_line.append('\tinput          pad_name_oen,')
                print_line.append('\toutput         pad_name_in,')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line) 
           # function 1
            pin_mux_port_gen_model(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["func1_attr"]], pad_info[pad_info_index["func1"]:])
            # function 2
            pin_mux_port_gen_model(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["func2_attr"]], pad_info[pad_info_index["func2"]:])
            # function 3
            pin_mux_port_gen_model(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["func3_attr"]], pad_info[pad_info_index["func3"]:])
        #print(count)
        port_last_process(count, pad_ser, print_line)
    print_line.append(');\n')

# }}}

# define {{{
    count = 0
    for pad_info in pad_corpus:
        count += 1
        if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
            print_line.append('\twire pad_name_dft_in;')
        if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
            print_line.append('\twire pad_name_dft_out;')
        replace_pad_name(pad_info_index, pad_info, print_line)

        if 'PINMUX' == pad_info[pad_info_index["type"]] or "GPIO" == pad_info[pad_info_index["type"]] or "GPO" == pad_info[pad_info_index["type"]]:
            # function 0
            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\twire func0_pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            # function 1
            if 'OUTPUT' == pad_info[pad_info_index["func1_attr"]] or 'INOUT' == pad_info[pad_info_index["func1_attr"]]:
                print_line.append('\twire func1_pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["func1"]:], print_line, 'func1_pad_name')
            # function 2
            if 'OUTPUT' == pad_info[pad_info_index["func2_attr"]] or 'INOUT' == pad_info[pad_info_index["func2_attr"]]:
                print_line.append('\twire func2_pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["func2"]:], print_line, 'func2_pad_name')
            # function 3
            if 'OUTPUT' == pad_info[pad_info_index["func3_attr"]] or 'INOUT' == pad_info[pad_info_index["func3_attr"]]:
                print_line.append('\twire func3_pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info[pad_info_index["func3"]:], print_line, 'func3_pad_name')

    print_line.append("\n")
#}}}

# pin_mux always assign {{{
    count = 0
    for pad_info in pad_corpus:
        count += 1
        if 'PINMUX' == pad_info[pad_info_index["type"]]:
            print_line.append('\t//pad PAD_NAME')
            print_line.append('\talways @ (*)')
            #if False == pd.isna(pad_info[pad_info_index["dft_mode"]]) :
            #    print_line.append("    if (test_mode == 1'b1)begin")
            #    if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
            #        print_line.append("        pad_name_oe_n = 1'b0;")
            #    elif 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
            #        print_line.append("        pad_name_oe_n = 1'b1;")
            #    print_line.append("    end")
            #    print_line.append("    else begin")
            print_line.append('\t    case (pad_name_func_sel)')
            # function 0
            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]] :
                print_line.append("\t        2'h0:    pad_name_oe_n = 1'b1;")
            elif 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append("\t        2'h0:    pad_name_oe_n = 1'b0;")
            elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append("\t        2'h0:    pad_name_oe_n = func0_pad_name_oen;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            # function 1
            if 1 == pd.isna(pad_info[pad_info_index["func1"]]) :
                if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]] :
                    print_line.append("\t        2'h1:    pad_name_oe_n = 1'b1;")
                elif'INPUT' == pad_info[pad_info_index["normal_attr"]] :
                    print_line.append("\t        2'h1:    pad_name_oe_n = 1'b0;")
                elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                    print_line.append("\t        2'h1:    pad_name_oe_n = func0_pad_name_oen;")
            else :
                if 'OUTPUT' == pad_info[pad_info_index["func1_attr"]] :
                    print_line.append("\t        2'h1:    pad_name_oe_n = 1'b1;")
                elif'INPUT' == pad_info[pad_info_index["func1_attr"]] :
                    print_line.append("\t        2'h1:    pad_name_oe_n = 1'b0;")
                elif 'INOUT' == pad_info[pad_info_index["func1_attr"]]:
                    print_line.append("\t        2'h1:    pad_name_oe_n = func1_pad_name_oen;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["func1"]:], print_line, 'func1_pad_name')
            # function 2
            if 1 == pd.isna(pad_info[pad_info_index["func2"]]) :
                if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]] :
                    print_line.append("\t        2'h2:    pad_name_oe_n = 1'b1;")
                elif'INPUT' == pad_info[pad_info_index["normal_attr"]] :
                    print_line.append("\t        2'h2:    pad_name_oe_n = 1'b0;")
                elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                    print_line.append("\t        2'h2:    pad_name_oe_n = func0_pad_name_oen;")
            else :
                if 'OUTPUT' == pad_info[pad_info_index["func2_attr"]] :
                    print_line.append("\t        2'h2:    pad_name_oe_n = 1'b1;")
                elif 'INPUT' == pad_info[pad_info_index["func2_attr"]] :
                    print_line.append("\t        2'h2:    pad_name_oe_n = 1'b0;")
                elif 'INOUT' == pad_info[pad_info_index["func2_attr"]]:
                    print_line.append("\t        2'h2:    pad_name_oe_n = func2_pad_name_oen;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["func2"]:], print_line, 'func2_pad_name')
            # function 3
            if 1 == pd.isna(pad_info[pad_info_index["func3"]]) :
                if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]] :
                    print_line.append("\t        default: pad_name_oe_n = 1'b1;")
                elif'INPUT' == pad_info[pad_info_index["normal_attr"]] :
                    print_line.append("\t        default: pad_name_oe_n = 1'b0;")
                elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                    print_line.append("\t        default: pad_name_oe_n = func0_pad_name_oen;")
            else :
                if 'OUTPUT' == pad_info[pad_info_index["func3_attr"]] :
                    print_line.append("\t        default: pad_name_oe_n = 1'b1;")
                elif 'INPUT' == pad_info[pad_info_index["func3_attr"]] :
                    print_line.append("\t        default: pad_name_oe_n = 1'b0;")
                elif 'INOUT' == pad_info[pad_info_index["func3_attr"]]:
                    print_line.append('\t        default: pad_name_oe_n = func3_pad_name_oen;')
            replace_pad_name(pad_info_index, pad_info[pad_info_index["func3"]:], print_line, 'func3_pad_name')
            print_line.append('\t    endcase')
            #if False == pd.isna(pad_info[pad_info_index["dft_mode"]]) :
            ##if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
            #    print_line.append('\tend')

            print_line.append('\talways @ (*)')
            #if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
            #    print_line.append("    if (test_mode == 1'b1)begin")
            #    print_line.append("        pad_name_i = pad_name_dft_out;")
            #    print_line.append("    end")
            #    print_line.append("    else begin")
            print_line.append('\t    case (pad_name_func_sel)')
            # function 0
            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append("\t        2'h0:    pad_name_i = 1'b0;")
            elif 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append("\t        2'h0:    pad_name_i = func0_pad_name_out;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            # function 1
            if 1 == pd.isna(pad_info[pad_info_index["func1"]]):
                if 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                    print_line.append("\t        2'h1:    pad_name_i = func0_pad_name_out;")
                else :
                    print_line.append("\t        2'h1:    pad_name_i = 1'b0;")
            elif 'OUTPUT' == pad_info[pad_info_index["func1_attr"]]:
                print_line.append("\t        2'h1:    pad_name_i = 1'b0;")
            elif 'INPUT' == pad_info[pad_info_index["func1_attr"]] or 'INOUT' == pad_info[pad_info_index["func1_attr"]]:
                print_line.append("\t        2'h1:    pad_name_i = func1_pad_name_out;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            replace_pad_name(pad_info_index, pad_info[pad_info_index["func1"]:], print_line, 'func1_pad_name')
            # function 2
            if 1 == pd.isna(pad_info[pad_info_index["func2"]]):
                if 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                    print_line.append("\t        2'h2:    pad_name_i = func0_pad_name_out;")
                else :
                    print_line.append("\t        2'h2:    pad_name_i = 1'b0;")
            elif 'OUTPUT' == pad_info[pad_info_index["func2_attr"]]:
                print_line.append("\t        2'h2:    pad_name_i = 1'b0;")
            elif 'INPUT' == pad_info[pad_info_index["func2_attr"]] or 'INOUT' == pad_info[pad_info_index["func2_attr"]]:
                print_line.append("\t        2'h2:    pad_name_i = func2_pad_name_out;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            replace_pad_name(pad_info_index, pad_info[pad_info_index["func2"]:], print_line, 'func2_pad_name')
            # function 3
            if 1 == pd.isna(pad_info[pad_info_index["func3"]]):
                if 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                    print_line.append("\t        default: pad_name_i = func0_pad_name_out;")
                else :
                    print_line.append("\t        default: pad_name_i = 1'b0;")
            elif 'OUTPUT' == pad_info[pad_info_index["func3_attr"]]:
                print_line.append("\t        default: pad_name_i = 1'b0;")
            elif 'INPUT' == pad_info[pad_info_index["func3_attr"]] or 'INOUT' == pad_info[pad_info_index["func3_attr"]]:
                print_line.append("\t        default: pad_name_i = func3_pad_name_out;")
            replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            replace_pad_name(pad_info_index, pad_info[pad_info_index["func3"]:], print_line, 'func3_pad_name')
            print_line.append('\t    endcase')
            #if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
            #    print_line.append('\tend')
            #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
            #    print_line.append("")
            #    print_line.append("\tassign pad_name_dft_in = (test_mode == 1'b1)? pad_name_c : 1'b0;")

            # function 0
            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign func0_pad_name_in_pre = (test_mode==1'b1)? 1'b0: ((pad_name_func_sel == 2'h0)") 
                #else :
                print_line.append("\tassign func0_pad_name_in_pre = ((pad_name_func_sel == 2'h0)") 

                if pad_info[pad_info_index["normal_mode"]] == pad_info[pad_info_index["func1"]] or True == pd.isna(pad_info[pad_info_index["func1"]]) :
                    print_line.append("\t                             || (pad_name_func_sel == 2'h1)")
                if pad_info[pad_info_index["normal_mode"]] == pad_info[pad_info_index["func2"]] or True == pd.isna(pad_info[pad_info_index["func2"]]) :
                    print_line.append("\t                             || (pad_name_func_sel == 2'h2)")
                if pad_info[pad_info_index["normal_mode"]] == pad_info[pad_info_index["func3"]] or True == pd.isna(pad_info[pad_info_index["func3"]]) :
                    print_line.append("\t                             || (pad_name_func_sel == 2'h3)")
                #print(pad_info[pad_info_index["normal_mode"]])
                if pad_info[pad_info_index["normal_dflt"]] == "1'b0" or pad_info[pad_info_index["normal_dflt"]] ==  "1’b0": 
                    print_line.append("\t                             ) ? pad_name_c : 1'b0;")
                elif pad_info[pad_info_index["normal_dflt"]] == "1'b1" or pad_info[pad_info_index["normal_dflt"]] ==  "1’b1":
                    print_line.append("\t                             ) ? pad_name_c : 1'b1;")
                #print_line.append("\tassign func0_pad_name_in_pre = (pad_name_func_sel == 2'h0) ? pad_name_c : 1'b0;")
                replace_pad_name(pad_info_index, pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            if 'OUTPUT' == pad_info[pad_info_index["func1_attr"]] or 'INOUT' == pad_info[pad_info_index["func1_attr"]]:
                #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign func1_pad_name_in_pre = (test_mode==1'b1)? 1'b0: ((pad_name_func_sel == 2'h1)") 
                #else :
                print_line.append("\tassign func1_pad_name_in_pre = ((pad_name_func_sel == 2'h1)") 
                if pad_info[pad_info_index["func1"]] == pad_info[pad_info_index["func2"]] :
                    print_line.append("\t                             || (pad_name_func_sel == 2'h2)")
                if pad_info[pad_info_index["func1"]] == pad_info[pad_info_index["func3"]] :
                    print_line.append("\t                             || (pad_name_func_sel == 2'h3)")
                if pad_info[pad_info_index["func1_dflt"]] == "1'b0" or pad_info[pad_info_index["func1_dflt"]] ==  "1’b0":
                    print_line.append("\t                             ) ? pad_name_c : 1'b0;")
                elif pad_info[pad_info_index["func1_dflt"]] == "1'b1" or pad_info[pad_info_index["func1_dflt"]] ==  "1’b1":
                    print_line.append("\t                             ) ? pad_name_c : 1'b1;")
                #print_line.append("\tassign func1_pad_name_in_pre = (pad_name_func_sel == 2'h1) ? pad_name_c : 1'b0;")
                replace_pad_name(pad_info_index, pad_info[pad_info_index["func1"]:], print_line, 'func1_pad_name')
            if 'OUTPUT' == pad_info[pad_info_index["func2_attr"]] or 'INOUT' == pad_info[pad_info_index["func2_attr"]]:
                #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign func2_pad_name_in_pre = (test_mode==1'b1)? 1'b0: ((pad_name_func_sel == 2'h2)") 
                #else :
                print_line.append("\tassign func2_pad_name_in_pre = ((pad_name_func_sel == 2'h2)") 
                if pad_info[pad_info_index["func2"]] == pad_info[pad_info_index["func3"]] :
                    print_line.append("\t                             || (pad_name_func_sel == 2'h3)")
                if pad_info[pad_info_index["func2_dflt"]] == "1'b0" or pad_info[pad_info_index["func2_dflt"]] ==  "1’b0":
                    print_line.append("\t                             ) ? pad_name_c : 1'b0;")
                elif pad_info[pad_info_index["func2_dflt"]] == "1'b1" or pad_info[pad_info_index["func2_dflt"]] ==  "1’b1":
                    print_line.append("\t                             ) ? pad_name_c : 1'b1;")
                #print_line.append("\tassign func2_pad_name_in_pre = (pad_name_func_sel == 2'h2) ? pad_name_c : 1'b0;")
                replace_pad_name(pad_info_index, pad_info[pad_info_index["func2"]:], print_line, 'func2_pad_name')
            if 'OUTPUT' == pad_info[pad_info_index["func3_attr"]] or 'INOUT' == pad_info[pad_info_index["func3_attr"]]:
                #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign func3_pad_name_in_pre = (test_mode==1'b1)? 1'b0: ((pad_name_func_sel == 2'h3)") 
                #else :
                print_line.append("\tassign func3_pad_name_in_pre = ((pad_name_func_sel == 2'h3)") 
                if pad_info[pad_info_index["func3_dflt"]] == "1'b0" or pad_info[pad_info_index["func3_dflt"]] ==  "1’b0":
                    print_line.append("\t                             ) ? pad_name_c : 1'b0;")
                elif pad_info[pad_info_index["func3_dflt"]] == "1'b1" or pad_info[pad_info_index["func3_dflt"]] ==  "1’b1":
                    print_line.append("\t                             ) ? pad_name_c : 1'b1;")
                #print_line.append("\tassign func3_pad_name_in_pre = (pad_name_func_sel == 2'h3) ? pad_name_c : 1'b0;")
                replace_pad_name(pad_info_index, pad_info[pad_info_index["func3"]:], print_line, 'func3_pad_name')

            replace_PAD_NAME(pad_info_index, pad_info, print_line)
            replace_pad_name(pad_info_index, pad_info, print_line)
            print_line.append("\n")
# }}}

# pad assign{{{

    print_line.append("\t//---------------")
    print_line.append("\t// input buffers")
    print_line.append("\t//---------------")
    # asic
    for pad_info in pad_corpus:
        if 'GPIO' == pad_info[pad_info_index["type"]]:
            print_line.append('\t//pad PAD_NAME')
            #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
            #    print_line.append("")
            #    print_line.append("\tassign pad_name_dft_in = (test_mode == 1'b1)? pad_name_c : 1'b0;")

            if 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_oe_n = (test_mode == 1'b1)? 1'b1: 1'b0;")
                #else :
                print_line.append("\tassign pad_name_oe_n = 1'b0;")
                #if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_i = (test_mode == 1'b1)? pad_name_dft_out : pad_name_out;")
                #else :
                print_line.append('\tassign pad_name_i    = pad_name_out;')
                replace_pad_name(pad_info_index, pad_info, print_line)
            elif 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                #if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_oe_n   = (test_mode == 1'b1)? 1'b0: 1'b1;")
                #else :
                print_line.append("\tassign pad_name_oe_n   = 1'b1;")
                #if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_i = (test_mode == 1'b1)? pad_name_dft_out : 1'b0;")
                #else :
                print_line.append("\tassign pad_name_i      = 1'b0;")
                print_line.append('\tassign pad_name_in_pre = pad_name_c;')
                replace_pad_name(pad_info_index, pad_info, print_line)
            elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                #if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_oe_n   = (test_mode == 1'b1)? 1'b0: ~pad_name_oen;")
                #else :
                print_line.append("\tassign pad_name_oe_n   =  ~pad_name_oen;")
                #if 'INPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_i = (test_mode == 1'b1)? pad_name_dft_out : pad_name_out;")
                #else :
                print_line.append("\tassign pad_name_i    = pad_name_out;")
                print_line.append('\tassign pad_name_in_pre = pad_name_c;')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'GPI' == pad_info[pad_info_index["type"]] :
            if 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]] :
                #    print_line.append("\tassign pad_name_oe_n = (test_mode == 1'b1)? 1'b1: 1'b0;")
                #else :
                print_line.append("\tassign pad_name_oe_n = 1'b0;")
                print_line.append('\tassign pad_name_i    = pad_name_out;')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'GPO' == pad_info[pad_info_index["type"]] :
            print_line.append('\t//pad PAD_NAME')
            print_line.append('\t//pad PAD_NAME')
            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tassign pad_name_in_pre = pad_name_c;')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)

    print_line.append("\n")
    
    # no asic
    print_line.append('\t`ifdef NO_ASIC')
    for pad_info in pad_corpus:
        if 'GPIO' == pad_info[pad_info_index["type"]]:
            if 'INPUT' != pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tassign pad_name_in = pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info, print_line)
        if 'GPI' == pad_info[pad_info_index["type"]]:
            if 'INPUT' != pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tassign pad_name_in = pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info, print_line)
        elif 'PINMUX' == pad_info[pad_info_index["type"]]:
            # function 0
            pad_noasic_output_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["normal_attr"]],  pad_info[pad_info_index["normal_mode"]:],   'func0_pad_name')
            # function 1
            pad_noasic_output_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func1_attr"]],  pad_info[pad_info_index["func1"]:],   'func1_pad_name')
            # function 2
            pad_noasic_output_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func2_attr"]],  pad_info[pad_info_index["func2"]:],   'func2_pad_name')
            # function 3
            pad_noasic_output_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func3_attr"]], pad_info[pad_info_index["func3"]:],  'func3_pad_name')
            # function 0
            #if 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
            #    print_line.append('\tassign func0_pad_name_in = func0_pad_name_in_pre;')
            #    replace_pad_name(pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
    # fpga
    print_line.append('\t`elsif FPGA')
    for pad_info in pad_corpus:
        if 'GPIO' == pad_info[pad_info_index["type"]]:
            if 'INPUT' != pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tassign pad_name_in = pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info, print_line)
        if 'GPI' == pad_info[pad_info_index["type"]]:
            if 'INPUT' != pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tassign pad_name_in = pad_name_in_pre;')
                replace_pad_name(pad_info_index, pad_info, print_line)
        elif 'PINMUX' == pad_info[pad_info_index["type"]]:
            # function 0
            pad_noasic_output_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["normal_attr"]],  pad_info[pad_info_index["normal_mode"]:],   'func0_pad_name')
            # function 1
            pad_noasic_output_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func1_attr"]],  pad_info[pad_info_index["func1"]:],   'func1_pad_name')
            # function 2
            pad_noasic_output_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func2_attr"]],  pad_info[pad_info_index["func2"]:],   'func2_pad_name')
            # function 3
            pad_noasic_output_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func3_attr"]], pad_info[pad_info_index["func3"]:],  'func3_pad_name')
            #if 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
            #    print_line.append('\tassign func0_pad_name_in = func0_pad_name_in_pre;')
            #    replace_pad_name(pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
    # pad sta cell
    print_line.append('\t`else')
    for pad_info in pad_corpus:
        #if 'INPUT' == pad_info[pad_info_index["dft_mode"]]:
        #    print_line.append('\tstd_cell_clk_buf pad_name_dft_out_dontouch_buf (.clk_buf_in(), .clk_buf_out(pad_name_dft_out));')
        #if 'OUTPUT' == pad_info[pad_info_index["dft_mode"]]:
        #    print_line.append('\tstd_cell_clk_buf pad_name_dft_in_dontouch_buf (.clk_buf_in(pad_name_dft_in), .clk_buf_out());')
        replace_pad_name(pad_info_index, pad_info, print_line)
        
        if 'GPIO' == pad_info[pad_info_index["type"]]:
            if 'INPUT' != pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tstd_cell_clk_buf pad_name_in_dontouch_buf (.clk_buf_in(pad_name_in_pre), .clk_buf_out(pad_name_in));')
                replace_pad_name(pad_info_index, pad_info, print_line)
        if 'GPI' == pad_info[pad_info_index["type"]]:
            if 'INPUT' != pad_info[pad_info_index["normal_attr"]]:
                print_line.append('\tstd_cell_clk_buf pad_name_in_dontouch_buf (.clk_buf_in(pad_name_in_pre), .clk_buf_out(pad_name_in));')
                replace_pad_name(pad_info_index, pad_info, print_line)
        elif 'PINMUX' == pad_info[pad_info_index["type"]]:
            # function 0
            pad_output_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["normal_attr"]],  pad_info[pad_info_index["normal_mode"]:],  'func0_pad_name')
            # function 1
            pad_output_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func1_attr"]],  pad_info[pad_info_index["func1"]:],  'func1_pad_name')
            # function 2
            pad_output_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func2_attr"]],  pad_info[pad_info_index["func2"]:],  'func2_pad_name')
            # function 3
            pad_output_buffer_gen(pad_info_index, pad_info, print_line, pad_info[pad_info_index["func3_attr"]], pad_info[pad_info_index["func3"]:], 'func3_pad_name')
            #if 'INPUT' == pad_info[pad_info_index["normal_attr"]] or 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
            #    print_line.append('\tstd_cell_clk_buf func0_pad_name_in_dontouch_buf (.buf_in(func0_pad_name_in_pre),.buf_out(func0_pad_name_in));')
            #    replace_pad_name(pad_info[pad_info_index["normal_mode"]:], print_line, 'func0_pad_name')
            # function 1
    print_line.append('\t`endif')
   
#}}}

    # write file
    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')
    fp.write('endmodule')

    fp.close()

#}}}

def gen_io_yml(gen_filepath, filename, pad_corpus, pad_info_index, pad_cell, pad_cell_index, protocol) :#{{{

    #print("note name is :"+filename)
    fp = open(gen_filepath+filename.upper()+".yml", "w")
    print_line = []

#    print_line.append("blocks:")
    print_line.append("name: "+filename.upper())
    print_line.append("bytes: 4")
    print_line.append("offset: 0x000")
    print_line.append("registers:")

    count = 0

    for pad_info in pad_corpus :


        if 'PINMUX' == pad_info[pad_info_index["type"]] or "GPIO" == pad_info[pad_info_index["type"]] or 'VREF' == pad_info[pad_info_index["type"]] or 'POC' == pad_info[pad_info_index["type"]]:
            #reg_addr = hex(count * 2)
            reg_addr = hex(count)
            #print(reg_addr)
            #if (count % 2) == 0:
                #print(count)
            if  "INNO_GPIO" == pad_info[pad_info_index["pad_cell_type"]]:
                print_line.append("  - name: pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"0")
                print_line.append("    description: \"pad control register "+pad_info[pad_info_index["pad_name"]].lower()+"0\"")
                print_line.append("    offset: "+reg_addr)
                print_line.append("    fields:")
                print_line.append("      - { name: pad_name0_drvpd,  lsb: 0,  bits: 5, access: rw, reset: "+str(hex(int(pad_info[pad_info_index["drv"]][3:], 2)))+", description: \"pad control, driver pull-down strength control-bit \"}")
                print_line.append("      - { name: pad_name0_drvpu,  lsb: 8,  bits: 5, access: rw, reset: "+str(hex(int(pad_info[pad_info_index["drv"]][3:], 2)))+", description: \"pad control, driver pull-up strength control-bit \"}")     
                print_line.append("      - { name: pad_name0_idelay, lsb: 16, bits: 6, access: rw, reset: 0x0, description: \"pad control, delay control for Rx direction \"}")   
                print_line.append("      - { name: pad_name0_odelay, lsb: 24, bits: 6, access: rw, reset: 0x0, description: \"pad control, delay control for Tx direction \"}")
                count += 4
                reg_addr = hex(count)
                print_line.append("  - name: pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1")
                print_line.append("    description: \"pad control register "+pad_info[pad_info_index["pad_name"]].lower()+"1\"")
                print_line.append("    offset: "+reg_addr)
                print_line.append("    fields:")
#   add ZZQ 241111
                if "OUTPUT" == pad_info[pad_info_index["normal_attr"]] :
                    print_line.append("      - { name: pad_name0_ie,     lsb: 0, bits: 1, access: rw, reset: 0x0, description: \"pad control, input enable \"}")
                else :
                    print_line.append("      - { name: pad_name0_ie,     lsb: 0, bits: 1, access: rw, reset: 0x1, description: \"pad control, input enable \"}")    
                print_line.append("      - { name: pad_name0_fben,   lsb: 1, bits: 1, access: rw, reset: 0x0, description: \"pad control, Outer ring loopback enable signal \"}")      
                print_line.append("      - { name: pad_name0_fbsel,  lsb: 2, bits: 1, access: rw, reset: 0x0, description: \"pad control, Inner ring loopback enable signal \"}")     
                print_line.append("      - { name: pad_name0_odten,  lsb: 3, bits: 1, access: rw, reset: 0x0, description: \"pad control, ODT enbale for data when in read mode \"}")   
                #if "INPUT" == pad_info[pad_info_index["normal_attr"]] :
                #    print_line.append("      - { name: pad_name0_odtpd,  lsb: 4, bits: 4, access: rw, reset: 0x0, description: \"pad control \"}")   
                #    print_line.append("      - { name: pad_name0_odtpu,  lsb: 8, bits: 4, access: rw, reset: 0x0, description: \"pad control \"}")   
                #elif "OUTPUT" == pad_info[pad_info_index["normal_attr"]] :
                #    print_line.append("      - { name: pad_name0_odtpd,  lsb: 4, bits: 4, access: rw, reset: 0x0, description: \"pad control \"}")   
                #    print_line.append("      - { name: pad_name0_odtpu,  lsb: 8, bits: 4, access: rw, reset: 0x0, description: \"pad control \"}")
                #else :
                print_line.append("      - { name: pad_name0_odtpd,  lsb: 4, bits: 4, access: rw, reset: 0x0, description: \"pad control, ODT pull-down strength control-bit \"}")   
                print_line.append("      - { name: pad_name0_odtpu,  lsb: 8, bits: 4, access: rw, reset: 0x0, description: \"pad control, ODT pull-up stength control-bit \"}")   
                print_line.append("      - { name: pad_name0_slew, lsb: 12, bits: 5, access: rw, reset: 0x0, description: \"pad control, slewrate control bit when in tx mode, 5'b00000:fast , 5'b1111:slow, 5;b*:medium \"}")     
                print_line.append("      - { name: pad_name0_smit_rxmode, lsb: 21, bits: 1, access: rw, reset: "+str(hex(int(pad_info[pad_info_index["rx_smit"]][3:])))+", description: \"pad control The rx receiver select control bit, 1;b1 : Schmitt trigger when low speed ,1'b0 high speed comparator when high speed \"}")
                print_line.append("      - { name: pad_name0_weakpd,  lsb: 22, bits: 1, access: rw, reset: "+str(hex(int(pad_info[pad_info_index["pd"]][3:])))+", description: \"pad control, weak pull-down control bit \"}")   
                print_line.append("      - { name: pad_name0_weakpu,   lsb: 23, bits: 1, access: rw, reset: "+str(hex(int(pad_info[pad_info_index["pu"]][3:])))+", description: \"pad control, weak pull-up control bit \"}") 
                if 'PINMUX' == pad_info[pad_info_index["type"]] :
                    print_line.append("      - { name: pad_name0_func_sel, lsb: 28, bits: 2, access: rw, reset: 0x0, description: \"pad control function select\"}")
                replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name0')
                count += 4
            elif "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
                print_line.append("  - name: pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower())
                print_line.append("    description: \"pad control register "+pad_info[pad_info_index["pad_name"]].lower()+"\"")
                print_line.append("    offset: "+reg_addr)
                print_line.append("    fields:")
                print_line.append("      - { name: pad_name_reg_vref_sel, lsb: 0, bits: 8, access: rw, reset: 0x80, description: \"pad control, Reference voltage control code \"}")
                print_line.append("      - { name: pad_name_reg_vref_pd,  lsb: 8, bits: 1, access: rw, reset: 0x0, description: \"pad control, VREF reset signal, when high, VREF CELL in power down mode, when low speed mode, VREF may not used , VREF_PD can set high \"}")
                count += 4
                
                if pd.isna(pad_info[pad_info_index["io_domain"]]) == True :
                    reg_addr = hex(count)
                    print_line.append("  - name: pad_name_inno_poc_cell")
                    print_line.append("    description: \"pad control register pad_name_inno_poc_cell\"")
                    print_line.append("    offset: "+reg_addr)
                    print_line.append("    fields:")
                    print_line.append("      - { name: pad_name_inno_poc_cell_pwrok, lsb: 0, bits: 1, access: rw, reset: 0x1, description: \"When low, IO PAD is in high-Z state. High: VDD Low: 0V\"}")

                    count += 4
                replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            elif "POC" == pad_info[pad_info_index["type"]]:
                reg_addr = hex(count+4)
                print_line.append("  - name: pad_name0_"+pad_info[pad_info_index["pad_cell_type"]])
                print_line.append("    description: \"pad control register pad_name0_"+pad_info[pad_info_index["pad_cell_type"]]+"\"")
                print_line.append("    offset: "+reg_addr)
                print_line.append("    fields:")
                print_line.append("      - { name: pad_name0_ms, lsb: 0, bits: 1, access: rw, reset: 0x0, description: \"Mode selector\"}")
                replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name0')
                count += 4
            else :
                print_line.append("  - name: pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower())
                print_line.append("    description: \"pad control register "+pad_info[pad_info_index["pad_name"]].lower()+"\"")
                print_line.append("    offset: "+reg_addr)
                print_line.append("    fields:")
                for cell_info in pad_cell :
                    #print(cell_info)
                    cell_info_list = cell_info.split(",")
                    #print(cell_info_list)
                    cell_name = cell_info_list[0]
                    if pad_info[pad_info_index["pad_cell_type"]] == cell_name :
                        cell_ds = str(cell_info_list[pad_cell_index["ds"]])
                        cell_st = str(cell_info_list[pad_cell_index["st"]])
                        cell_sl = str(cell_info_list[pad_cell_index["sl"]])
                        cell_msc= str(cell_info_list[pad_cell_index["msc"]])
                        cell_ps = str(cell_info_list[pad_cell_index["ps"]])
                        cell_he = str(cell_info_list[pad_cell_index["he"]])
                        cell_pe = str(cell_info_list[pad_cell_index["pe"]])
                        if "[" in cell_ds :
                            cell_ds_list = cell_ds.split("[", 1)
                            cell_ds_width_list = cell_ds_list[1].split(":", 1)
                            #print(cell_ds_width_list[0])
                            cell_ds_msb = cell_ds_width_list[0]
                        if "[" in cell_st :
                            cell_st_list = cell_st.split("[", 1)
                            cell_st_width_list = cell_st_list[1].split(":", 1)
                            cell_st_msb = cell_st_width_list[0]
                
                if "PINMUX" == pad_info[pad_info_index["type"]] or "GPIO" == pad_info[pad_info_index["type"]]:
#   241106 ZZQ
#                    print_line.append("      - { name: pad_name0_pu, lsb: 0, bits: 1, access: rw, reset: 0x0, description: \"pad control pull up\"}")
#                    print_line.append("      - { name: pad_name0_pd, lsb: 1, bits: 1, access: rw, reset: 0x0, description: \"pad control pull down\"}")
#                    print_line.append("      - { name: pad_name0_ds, lsb: 4, bits: "+str(1+int(cell_ds_msb))+", access: rw, reset: "+str(hex(int(pad_info[pad_info_index["drv"]][3:], 2)))+", description: \"pad control driver strength\"}")
#   241116 ZZQ 
                    if "OUTPUT" == pad_info[pad_info_index["normal_attr"]] :
                        print_line.append("      - { name: pad_name0_ie, lsb: 2, bits: 1, access: rw, reset: 0x0, description: \"pad control input enable\"}")
                    else :
                        print_line.append("      - { name: pad_name0_ie, lsb: 2, bits: 1, access: rw, reset: 0x1, description: \"pad control input enable\"}")
                    print_line.append("      - { name: pad_name0_ds, lsb: 4, bits: "+str(1+int(cell_ds_msb))+", access: rw, reset: "+str(hex(int(pad_info[pad_info_index["drv"]][3:], 2)))+", description: \"pad control driver strength\"}")
                if 'PINMUX' == pad_info[pad_info_index["type"]] :
                    #print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_func_sel\t\t\t--\t\t[9:8]\t\t--\t\tpad control function select")
                    print_line.append("      - { name: pad_name0_func_sel, lsb: 8, bits: 2, access: rw, reset: 0x0, description: \"pad control function select\"}")
                #if pd.isna(cell_st) == False  :
                if cell_st != "nan" :
                    #print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_st\t\t\t\t--\t\t["+str(12+int(cell_st_msb))+":12]\t\t\t--\t\tpad control Schmitt trigger enable. ST=1 enables Schmitt trigger input function")
                    print_line.append("      - { name: pad_name0_st, lsb: 12, bits: "+str(1+int(cell_st_msb))+", access: rw, reset: 0x0, description: \"pad control Schmitt trigger enable. ST=1 enables Schmitt trigger input function\"}")
                
                #if pd.isna(cell_sl) == False  :
                if cell_sl != "nan" :
                    #print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_sl\t\t\t\t--\t\t[16]\t\t\t--\t\tpad control Slew-rate-control enable，SL=1 enables Slew-rate-control function")
                    print_line.append("      - { name: pad_name0_sl, lsb: 16, bits: 1, access: rw, reset: 0x0, description: \"pad control Slew-rate-control enable，SL=1 enables Slew-rate-control function\"}")
                #if pd.isna(cell_msc) == False  :
                #if cell_msc != "nan" :
                    #print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_msc\t\t\t\t--\t\t[17]\t\t\t--\t\tpad control mode selector")
                    #print_line.append("          - { name: pad_name0_msc, lsb: 17, bits: 1, access: rw, reset: 0x0, description: \"pad control mode selector\"}")
                #if pd.isna(cell_ps) == False  :
                if cell_ps != "nan" :
                    #print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_ps\t\t\t\t--\t\t[18]\t\t\t--\t\tpad control pull selector")
                    if pad_info[pad_info_index["pu"]] == "1'b1" :
                        print_line.append("      - { name: pad_name0_ps, lsb: 18, bits: 1, access: rw, reset: 0x1, description: \"pad control pull selector\"}")
                    else :
                        print_line.append("      - { name: pad_name0_ps, lsb: 18, bits: 1, access: rw, reset: 0x0, description: \"pad control pull selector\"}")
#   241106 ZZQ
                else :
                    print_line.append("      - { name: pad_name0_pu, lsb: 0, bits: 1, access: rw, reset: "+str(hex(int(pad_info[pad_info_index["pu"]][3:])))+", description: \"pad control pull up\"}")
                    print_line.append("      - { name: pad_name0_pd, lsb: 1, bits: 1, access: rw, reset: "+str(hex(int(pad_info[pad_info_index["pd"]][3:])))+", description: \"pad control pull down\"}")
                #if pd.isna(cell_he) == False  :
                if cell_he != "nan" :
                    #print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_he\t\t\t\t--\t\t[19]\t\t\t--\t\tpad control Hold enable")
                    print_line.append("      - { name: pad_name0_he, lsb: 19, bits: 1, access: rw, reset: 0x0, description: \"pad control Hold enable\"}")
                #if pd.isna(cell_pe) == False  :
                if cell_pe != "nan" :
                    #print_line.append("--\t\t'h0\t\t--\t\tRW\t\t--\t\tpad_name0_pe\t\t\t\t--\t\t[20]\t\t\t--\t\tpad control pull enable")
                    if pad_info[pad_info_index["pu"]] == "1'b1" or pad_info[pad_info_index["pd"]] == "1'b1" :
                        print_line.append("      - { name: pad_name0_pe, lsb: 20, bits: 1, access: rw, reset: 0x1, description: \"pad control pull enable\"}")
                    else :
                    	print_line.append("      - { name: pad_name0_pe, lsb: 20, bits: 1, access: rw, reset: 0x0, description: \"pad control pull enable\"}")

                replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name0')
                #print_line.append("")

                count += 4
        





    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')

    fp.close()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    yml2reg_py = os.path.join(script_dir, "yml2reg", "yml2reg.py")
    yml_file = os.path.abspath(gen_filepath+filename.upper()+".yml")
    gen_regfile = "cd "+gen_filepath+" && python3 "+yml2reg_py+" "+yml_file+" "+protocol
    print(gen_regfile)
    os.system(gen_regfile)

# }}}

#replace_pad_name{{{
def replace_pad_name(pad_info_index, pad_info, print_line, pad_name = 'pad_name'):
    for element in print_line:
        if pad_name in element:
            print_line[print_line.index(element)] = print_line[print_line.index(element)].replace(pad_name, pad_info[pad_info_index["pad_name"]].lower())
#}}}

#replace_PAD_NAME{{{

def replace_PAD_NAME(pad_info_index, pad_info, print_line):
    for element in print_line:
        if 'PAD_NAME' in element:
            print_line[print_line.index(element)] = print_line[print_line.index(element)].replace("PAD_NAME", pad_info[pad_info_index["pad_name"]])
#}}}

#replace_slash_with_dot{{{
def replace_slash_with_dot(input_list):
    """
    Replace all occurrences of '/' with '.' in the elements of the input list.
    Parameters:
    input_list (list): The list of strings to search and replace.
    search_string (str): The string to be replaced.

    Returns:
    list: The modified list with all '/' replaced by '.'.
    """
    # 遍历 input_list 列表中的每个元素
    for i in range(len(input_list)):
        # 检查当前元素是否包含 '/' 字符串
        if '/' in input_list[i]:
            # 替换元素中的 '/' 为 '.'
            input_list[i] = input_list[i].replace('/', '.')
    return input_list
#}}}

#   replace_char_in_strings{{{
def replace_char_in_strings(input_list, search_char, replacement_char):
    """
    Replace all occurrences of a specified character with another character in the elements of the input list.

    Parameters:
    input_list (list): The list of strings to search and replace.
    search_char (str): The character to search for in the strings.
    replacement_char (str): The character to replace search_char with.

    Returns:
    list: The modified list with all occurrences of search_char replaced by replacement_char.
    """
    # 遍历 input_list 列表中的每个元素
    for i in range(len(input_list)):
        # 替换元素中的 search_char 为 replacement_char
        input_list[i] = input_list[i].replace(search_char, replacement_char)
    return input_list
#}}}
#port_last_process{{{
def port_last_process(count, pad_ser, print_line):
    if count > pad_ser.index.max():
        print_line[-1] = print_line[-1].strip(',') 
#}}}

# pad_input_buffer_gen{{{
def pad_input_buffer_gen(pad_info_index, pad_info, print_line, pad_name_idx, pad_direct_idx, pad_name = 'func0_pad_name'):
    if 'INPUT' == pad_name_idx or 'INOUT' == pad_name_idx:
        print_line.append('\tstd_cell_clk_buf '+ pad_name + '_in_dontouch_buf (.clk_buf_in(' + pad_name + '_in_pre), .clk_buf_out(' + pad_name + '_in));')
        replace_pad_name(pad_info_index, pad_direct_idx, print_line, pad_name)
#}}}

# pad_output_buffer_gen{{{
def pad_output_buffer_gen(pad_info_index, pad_info, print_line, pad_name_idx, pad_direct_idx, pad_name = 'func0_pad_name'):
    if 'OUTPUT' == pad_name_idx or 'INOUT' == pad_name_idx:
        print_line.append('\tstd_cell_clk_buf '+ pad_name + '_in_dontouch_buf (.clk_buf_in(' + pad_name + '_in_pre), .clk_buf_out(' + pad_name + '_in));')
        replace_pad_name(pad_info_index, pad_direct_idx, print_line, pad_name)
#}}}

# pad_dontouch_buffer_gen{{{
def pad_dontouch_buffer_gen(filename, pad_info_index, pad_info, print_line, pad_name_idx, pad_direct_idx, pad_name = 'func0_pad_name'):
    if 'INPUT' == pad_name_idx or 'INOUT' == pad_name_idx:
        #print_line.append("u_"+filename+"_top.u_"+filename+"_pin_mux."+pad_name+"_in_dontouch_buf")
        print_line.append("u_"+filename+"_top/u_"+filename+"_pin_mux/"+pad_name+"_in_dontouch_buf")
        replace_pad_name(pad_info_index, pad_direct_idx, print_line, pad_name)
#}}}

# pad_noasic_input_buffer_gen{{{
def pad_noasic_input_buffer_gen(pad_info_index, pad_info, print_line, pad_name_idx, pad_direct_idx, pad_name = 'func0_pad_name'):
    if 'INPUT' == pad_name_idx or 'INOUT' == pad_name_idx:
        print_line.append('\tassign ' + pad_name + '_in = ' + pad_name + '_in_pre;')
        #print_line.append('\tassign func0_pad_name_in = func0_pad_name_in_pre;')
        replace_pad_name(pad_info_index, pad_direct_idx, print_line, pad_name)
#}}}

# pad_noasic_output_buffer_gen{{{
def pad_noasic_output_buffer_gen(pad_info_index, pad_info, print_line, pad_name_idx, pad_direct_idx, pad_name = 'func0_pad_name'):
    if 'OUTPUT' == pad_name_idx or 'INOUT' == pad_name_idx:
        print_line.append('\tassign ' + pad_name + '_in = ' + pad_name + '_in_pre;')
        #print_line.append('\tassign func0_pad_name_in = func0_pad_name_in_pre;')
        replace_pad_name(pad_info_index, pad_direct_idx, print_line, pad_name)
#}}}

def io_top_gen_csv(protocol, design_owner, pad_cell, pad_info_index, gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index, design_hier) :#{{{
    fp = open(gen_filepath+filename+"_top.csv", "w") 

    print_line = []

    print_line.append("#author_begin")
    print_line.append(design_owner)
    print_line.append("#author_end")
    print_line.append("#order_begin")
    print_line.append("False")
    print_line.append("#order_end")
    print_line.append("#keep_begin before_module")
    print_line.append("#keep_end before_module")
    print_line.append("module,"+filename+"_top")
    print_line.append("#parameter_begin")
    print_line.append("#parameter_end")
   
    print_line.append("#port_begin")
    print_line.append("#port_end")
    print_line.append("#gen_type_begin")
    print_line.append("v")
    print_line.append("#gen_type_end")
    print_line.append("#csv_begin")
    print_line.append("#csv_end")

    print_line.append("#inst_begin===========================================================================================================")
    #if protocol == "apb" :
    #    print_line.append("inst "+filename.upper()+"_"+protocol+"_reg u_"+filename.upper()+"_"+protocol+"_reg")
    #elif protocol == "ahb" :
    #    print_line.append("inst "+filename.upper()+"_"+protocol+"_reg u_"+filename.upper()+"_"+protocol+"_reg")
    #elif protocol == "dab" :
    print_line.append("inst "+filename.upper()+"_"+protocol+"_reg u_"+filename.upper()+"_"+protocol+"_reg")
    print_line.append("#para_inst_begin")
    print_line.append("#para_inst_end")
    print_line.append("#port_inst_begin")
    if protocol == "apb" :
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.clk                 ,apb_clk            ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.rst_n               ,apb_rst_n          ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.psel                ,apb_sel            ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.penable             ,apb_enable         ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pwrite              ,apb_write          ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.paddr               ,apb_addr[31:0]     ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pwdata              ,apb_wdata[31:0]    ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.prdata              ,apb_rdata[31:0]    ,O         ,output,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pready              ,apb_pready         ,O         ,output,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pslverr              ,apb_slverr         ,O         ,output,")
    elif protocol == "dab" :
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.clk                 ,dab_clk            ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.rst_n               ,dab_rst_n          ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.dab_write           ,dab_write          ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.dab_read            ,dab_read           ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.dab_addr            ,dab_addr[31:0]     ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.dab_wdata           ,dab_wdata[31:0]    ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.dab_rdata           ,dab_rdata[31:0]    ,O         ,output,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.dab_ready           ,dab_ready          ,O         ,output,")
    elif protocol == "ahb" :
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.clk                 ,ahb_clk        ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.rst_n               ,ahb_rst_n      ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hreadyin            ,hreadyin       ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hsel                ,hsel           ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.htrans              ,htrans[1:0]    ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hwrite              ,hwrite         ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hburst              ,hburst[2:0]    ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hsize               ,hsize[2:0]     ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.haddr               ,haddr[31:0]    ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hwdata              ,hwdata[31:0]   ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hreadyout           ,hreadyout      ,O         ,output,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hresp               ,hresp[1:0]     ,O         ,output,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hrdata              ,hrdata[31:0]   ,O         ,output,")


    count = 0
    for pad_info in pad_corpus:
        if 'PINMUX' == pad_info[pad_info_index["type"]] or 'GPIO' == pad_info[pad_info_index["type"]] or 'VREF' == pad_info[pad_info_index["type"]] or 'POC' == pad_info[pad_info_index["type"]]:
            #cell_ds_msb = 0
            #cell_st_msb = 0
            #cell_st = 0
            #cell_sl = 0
            #cell_msc = 0
            #cell_ps = 0
            #cell_he = 0
            #cell_pe = 0
            if  "INNO_GPIO" == pad_info[pad_info_index["pad_cell_type"]]:
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"0_pad_name0_drvpd      ,pad_name0_drvpd[4:0]                     ,W      ,output, ")
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"0_pad_name0_drvpu      ,pad_name0_drvpu[4:0]                     ,W      ,output, ")     
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"0_pad_name0_idelay     ,pad_name0_idelay[5:0]                    ,W      ,output,  ")   
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"0_pad_name0_odelay     ,pad_name0_odelay[5:0]                    ,W      ,output,  ")  
                if 'PINMUX' == pad_info[pad_info_index["type"]]:
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_func_sel  ,pad_name0_func_sel[1:0]     ,W      ,output,")
                                                                                                                                                                                       
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_ie         ,pad_name0_ie                        ,W      ,output,  ")    
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_fben       ,pad_name0_fben                      ,W      ,output,  ")      
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_fbsel      ,pad_name0_fbsel                     ,W      ,output,  ")     
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_odten      ,pad_name0_odten                     ,W      ,output,  ")   
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_odtpd      ,pad_name0_odtpd[3:0]                     ,W      ,output,  ")   
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_odtpu      ,pad_name0_odtpu[3:0]                     ,W      ,output,  ")   
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_slew      ,pad_name0_slew[4:0]                     ,W      ,output,  ")     
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_smit_rxmode,pad_name0_smit_rxmode               ,W      ,output,  ")
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_weakpd     ,pad_name0_weakpd                    ,W      ,output,  ")   
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_weakpu     ,pad_name0_weakpu                     ,W      ,output, ") 
                replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name0')
            elif "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_reg_vref_sel       ,pad_name0_reg_vref_sel[7:0]                ,W      ,output,  ")   
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_reg_vref_pd        ,pad_name0_reg_vref_pd                     ,W      ,output, ") 
                if pd.isna(pad_info[pad_info_index["io_domain"]]) == True :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_name0_inno_poc_cell_pad_name0_inno_poc_cell_pwrok      ,pad_name0_inno_poc_cell_pwrok                     ,W      ,output, ")
                replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name0')
            elif "POC" == pad_info[pad_info_index["type"]]:
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_pad_name_ms                       ,pad_name_ms                     ,W      ,output, ")
                replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            else :
                for cell_info in pad_cell :
                    cell_info_list = cell_info.split(",")
                    cell_name = cell_info_list[0]
                    if pad_info[pad_info_index["pad_cell_type"]] == cell_name :
                        cell_ds = str(cell_info_list[pad_cell_index["ds"]])
                        cell_st = str(cell_info_list[pad_cell_index["st"]])
                        cell_sl = str(cell_info_list[pad_cell_index["sl"]])
                        cell_msc= str(cell_info_list[pad_cell_index["msc"]])
                        cell_ps = str(cell_info_list[pad_cell_index["ps"]])
                        cell_he = str(cell_info_list[pad_cell_index["he"]])
                        cell_pe = str(cell_info_list[pad_cell_index["pe"]])
                        if "[" in cell_ds :
                            cell_ds_list = cell_ds.split("[", 1)
                            cell_ds_width_list = cell_ds_list[1].split(":", 1)
                            cell_ds_msb = cell_ds_width_list[0]
                        if "[" in cell_st :
                            cell_st_list = cell_st.split("[", 1)
                            cell_st_width_list = cell_st_list[1].split(":", 1)
                            cell_st_msb = cell_st_width_list[0]
                if "PINMUX" == pad_info[pad_info_index["type"]] or "GPIO" == pad_info[pad_info_index["type"]] :
#   241106 ZZQ
#                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_pu        ,pad_name0_pu                ,W      ,output,")
#                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_pd        ,pad_name0_pd                ,W      ,output,")
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_ie        ,pad_name0_ie                ,W      ,output,")
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_ds        ,pad_name0_ds["+str(cell_ds_msb)+":0]           ,W      ,output,")
                if 'PINMUX' == pad_info[pad_info_index["type"]]:
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_func_sel  ,pad_name0_func_sel[1:0]     ,W      ,output,")
                #if pd.isna(cell_st) == False :
                if cell_st != "nan" :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_st        ,pad_name0_st["+str(cell_st_msb)+":0]           ,W      ,output,")
                #if pd.isna(cell_sl) == False :
                if cell_sl != "nan" :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_sl        ,pad_name0_sl                ,W      ,output,")
                #if pd.isna(cell_msc) == False :
                #if cell_msc != "nan" :
                #    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_msc        ,pad_name0_msc                ,W      ,output,")
                #if pd.isna(cell_ps) == False :
                if cell_ps != "nan" :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_ps        ,pad_name0_ps                ,W      ,output,")
#   241106
                else :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_pu        ,pad_name0_pu                ,W      ,output,")
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_pd        ,pad_name0_pd                ,W      ,output,")
                    
                #if pd.isna(cell_he) == False :
                if cell_he != "nan" :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_he        ,pad_name0_he                ,W      ,output,")
                #if pd.isna(cell_pe) == False :
                if cell_pe != "nan" :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_pe        ,pad_name0_pe                ,W      ,output,")
                replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name0')


    replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
    print_line.append("#port_inst_end")
    print_line.append("#inst_end============================================================================================================")
    tdr_buf_list = []
    for pad_info in pad_corpus:
        if "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
            tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_pad_name_inno_poc_cell_pwrok_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 1")
            print_line.append("#inst_begin===========================================================================================================")
            print_line.append('inst test_tdr_mux u_pad_name_inno_poc_cell_pwrok_test_tdr_mux')
            print_line.append("#para_inst_begin")
            print_line.append("#para_inst_end")
            print_line.append("#port_inst_begin")
            print_line.append("connect,u_pad_name_inno_poc_cell_pwrok_test_tdr_mux.test_mode      ,test_mode                        ,I       ,input,")
            if pd.isna(pad_info[pad_info_index["io_domain"]]) == False :
                print_line.append("connect,u_pad_name_inno_poc_cell_pwrok_test_tdr_mux.func_in        ,"+pad_info[pad_info_index["io_domain"]]+"     ,W       ,input,")
            else :
                print_line.append("connect,u_pad_name_inno_poc_cell_pwrok_test_tdr_mux.func_in    ,pad_name_inno_poc_cell_pwrok     ,W       ,input,")
            print_line.append("connect,u_pad_name_inno_poc_cell_pwrok_test_tdr_mux.func_out       ,dft_pad_name_inno_poc_cell_pwrok ,W       ,output,")
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#port_inst_end")
            print_line.append("#inst_end============================================================================================================")

            print_line.append("#inst_begin===========================================================================================================")
            print_line.append('inst INNO_POC_CELL u_pad_name_inno_poc_cell')
            print_line.append("#para_inst_begin")
            print_line.append("#para_inst_end")
            print_line.append("#port_inst_begin")
            print_line.append('connect,u_inno_poc_cell.PWROK     ,dft_pad_name_inno_poc_cell_pwrok       ,W       ,input,')
            print_line.append('connect,u_inno_poc_cell.PWROKB_H  ,pad_name_pwrokb_h    ,W       ,output,')
            print_line.append('connect,u_inno_poc_cell.VREF      ,pad_name_vref        ,W       ,input,')
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#port_inst_end")
            print_line.append("#inst_end============================================================================================================")
            binary_string = list(reversed(list(bin(128)[2:])))
            for i in range(8) :
                tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_pad_name_reg_vref_sel_test_tdr_mux/dontouch_tdr_"+str(i)+"__u_dontouch_tdr_buf/u_std_cell_buf "+str(binary_string[i]))
            tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_pad_name_reg_vref_pd_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")

            print_line.append("#inst_begin===========================================================================================================")
            print_line.append('inst test_tdr_mux u_pad_name_reg_vref_sel_test_tdr_mux')
            print_line.append("#para_inst_begin")
            print_line.append('connect,u_pad_name_reg_vref_sel_test_tdr_mux.D_WIDTH      ,8 ')
            print_line.append("#para_inst_end")
            print_line.append("#port_inst_begin")
            print_line.append('connect,u_pad_name_reg_vref_sel_test_tdr_mux.test_mode      ,test_mode                 ,I       ,input,')
            print_line.append('connect,u_pad_name_reg_vref_sel_test_tdr_mux.func_in        ,pad_name_reg_vref_sel     ,W       ,input,')
            print_line.append('connect,u_pad_name_reg_vref_sel_test_tdr_mux.func_out       ,dft_pad_name_reg_vref_sel[7:0] ,W       ,output,')
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#port_inst_end")
            print_line.append("#inst_end============================================================================================================")


            print_line.append("#inst_begin===========================================================================================================")
            print_line.append('inst test_tdr_mux u_pad_name_reg_vref_pd_test_tdr_mux')
            print_line.append("#para_inst_begin")
            print_line.append("#para_inst_end")
            print_line.append("#port_inst_begin")
            print_line.append('connect,u_pad_name_reg_vref_pd_test_tdr_mux.test_mode      ,test_mode                ,I       ,input,')
            print_line.append('connect,u_pad_name_reg_vref_pd_test_tdr_mux.func_in        ,pad_name_reg_vref_pd     ,W       ,input,')
            print_line.append('connect,u_pad_name_reg_vref_pd_test_tdr_mux.func_out       ,dft_pad_name_reg_vref_pd ,W       ,output,')
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#port_inst_end")
            print_line.append("#inst_end============================================================================================================")

            print_line.append("#inst_begin===========================================================================================================")
            print_line.append("inst "+pad_info[pad_info_index["pad_cell_type"]].lower()+"_model u_pad_name_vref")
            print_line.append("#para_inst_begin")
            print_line.append("#para_inst_end")
            print_line.append("#port_inst_begin")
            print_line.append("connect,u_inno_poc_cell.reg_vref_sel    ,dft_pad_name_reg_vref_sel[7:0]   ,W       ,input,")
            print_line.append("connect,u_inno_poc_cell.reg_vref_pd     ,dft_pad_name_reg_vref_pd    ,W       ,input,")
            print_line.append("connect,u_inno_poc_cell.pwrokb_h        ,pad_name_pwrokb_h       ,W       ,input,")
            print_line.append("connect,u_inno_poc_cell.vref            ,pad_name_vref           ,W       ,output,")
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)   
            print_line.append("#port_inst_end")
            print_line.append("#inst_end============================================================================================================")
    

        if "POC" == pad_info[pad_info_index["type"]]:
            tdr_buf_list.append(design_hier+"/u_"+filename+"_top/u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_test_tdr_mux/dontouch_tdr_0__u_dontouch_tdr_buf/u_std_cell_buf 0")
            print_line.append("#inst_begin===========================================================================================================")
            print_line.append("inst test_tdr_mux u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_test_tdr_mux")
            print_line.append("#para_inst_begin")
            print_line.append("#para_inst_end")
            print_line.append("#port_inst_begin")
            print_line.append("connect,u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+".test_mode      ,test_mode       ,I       ,input,")
            print_line.append("connect,u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+".func_in        ,pad_name_ms     ,W       ,input,")
            print_line.append("connect,u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+".func_out       ,dft_pad_name_ms ,W       ,output,")

            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#port_inst_end")
            print_line.append("#inst_end============================================================================================================")

            print_line.append("#inst_begin===========================================================================================================")
            print_line.append("inst "+pad_info[pad_info_index["pad_cell_type"]]+" u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]])
            print_line.append("#para_inst_begin")
            print_line.append("#para_inst_end")
            print_line.append("#port_inst_begin")
            print_line.append("connect,u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+".MS       ,dft_pad_name_ms     ,W       ,input,")
            print_line.append("connect,u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+".MSC      ,pad_name_msc        ,W       ,output,")
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#port_inst_end")
            print_line.append("#inst_end============================================================================================================")

        replace_pad_name(pad_info_index, pad_info, tdr_buf_list)
        replace_PAD_NAME(pad_info_index, pad_info, tdr_buf_list)
    print_line.append("#inst_begin===========================================================================================================")
    print_line.append('inst '+filename+'_pin_mux u_'+filename+'_pin_mux')
    print_line.append("#para_inst_begin")
    print_line.append("#para_inst_end")
    print_line.append("#port_inst_begin")




    count = 0
    module_inst = filename+'_pin_mux'
    print_line.append('connect,'+module_inst+'.test_mode     ,test_mode       ,I       ,input,')
    for pad_info in pad_corpus:
        count += 1
        if "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
            replace_pad_name(pad_info_index, pad_info, print_line)
        elif 'GPIO' == pad_info[pad_info_index["type"]]:
            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('connect,'+module_inst+'.pad_name_c     ,pad_name_c       ,W       ,input,')
                print_line.append('connect,'+module_inst+'.pad_name_i     ,pad_name_i       ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_oe_n  ,pad_name_oe_n    ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_out   ,pad_name_out     ,I       ,input,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            elif 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('connect,'+module_inst+'.pad_name_c     ,pad_name_c       ,W       ,input,')
                print_line.append('connect,'+module_inst+'.pad_name_i     ,pad_name_i       ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_oe_n  ,pad_name_oe_n    ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_in    ,pad_name_in      ,O       ,output,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('connect,'+module_inst+'.pad_name_c     ,pad_name_c       ,W       ,input,')
                print_line.append('connect,'+module_inst+'.pad_name_i     ,pad_name_i       ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_oe_n  ,pad_name_oe_n    ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_out   ,pad_name_out     ,I       ,input,')
                print_line.append('connect,'+module_inst+'.pad_name_oen   ,pad_name_oen     ,I       ,input,')
                print_line.append('connect,'+module_inst+'.pad_name_in    ,pad_name_in      ,O       ,output,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'GPI' == pad_info[pad_info_index["type"]]:
            if 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('connect,'+module_inst+'.pad_name_c     ,pad_name_c       ,W       ,input,')
                print_line.append('connect,'+module_inst+'.pad_name_in    ,pad_name_in      ,O       ,output,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'GPO' == pad_info[pad_info_index["type"]]:
            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('connect,'+module_inst+'.pad_name_i     ,pad_name_i       ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_oe_n  ,pad_name_oe_n    ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_out   ,pad_name_out     ,I       ,input,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'PINMUX' == pad_info[pad_info_index["type"]]: 
            print_line.append('connect,'+module_inst+'.pad_name_c          ,pad_name_c                 ,W      ,input,')
            print_line.append('connect,'+module_inst+'.pad_name_i          ,pad_name_i                 ,W      ,output,')
            print_line.append('connect,'+module_inst+'.pad_name_oe_n       ,pad_name_oe_n              ,W      ,output,')
            print_line.append("connect,"+module_inst+".pad_name_func_sel   ,pad_name_func_sel[1:0]     ,W      ,input,") 
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
            replace_pad_name(pad_info_index, pad_info, print_line)
            # function 0
            pin_mux_port_gen_csv(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["normal_attr"]], pad_info[pad_info_index["normal_mode"]:], module_inst)
           # function 1
            pin_mux_port_gen_csv(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["func1_attr"]], pad_info[pad_info_index["func1"]:], module_inst)
            # function 2
            pin_mux_port_gen_csv(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["func2_attr"]], pad_info[pad_info_index["func2"]:], module_inst)
            # function 3
            pin_mux_port_gen_csv(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["func3_attr"]], pad_info[pad_info_index["func3"]:],module_inst)

    print_line.append("#port_inst_end")
    print_line.append("#inst_end============================================================================================================")
    
    print_line.append("#inst_begin===========================================================================================================")
    print_line.append('inst '+filename+'_ring u_'+filename+'_ring')
    print_line.append("#para_inst_begin")
    print_line.append("#para_inst_end")
    print_line.append("#port_inst_begin")
    count = 0
    print_line.append('connect,'+module_inst+'.test_mode     ,test_mode       ,I       ,input,')
    for pad_info in pad_corpus:
        count += 1  
        if 'ANALOG' == pad_info[pad_info_index["type"]]:
            print_line.append('connect ,'+filename+'_ring.PAD_NAME       ,PAD_NAME         ,IO       ,inout,')
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif "POC" == pad_info[pad_info_index["type"]]:
            continue
        elif "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
            continue
        #    print_line.append('connect,'+filename+'_ring.pad_name_reg_vref_sel          ,pad_name_reg_vref_sel[7:0]  ,W   ,input,')
        #    print_line.append('connect,'+filename+'_ring.pad_name_reg_vref_pd           ,pad_name_reg_vref_pd        ,W   ,input,')
        #    print_line.append('connect,'+filename+'_ring.pad_name_pwrokb_h              ,pwrokb_h        ,W   ,input,')
        #    print_line.append('connect,'+filename+'_ring.vref              ,vref        ,W   ,output,')
        #    replace_pad_name(pad_info_index, pad_info, print_line)
        #    replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif  "INNO_GPIO" == pad_info[pad_info_index["pad_cell_type"]]:
            if 'GPI' == pad_info[pad_info_index["type"]] :
                print_line.append("connect,"+filename+"_ring.PAD_NAME       ,PAD_NAME         ,IO      ,inout,")
                print_line.append("connect,"+filename+"_ring.pad_name_oe_n         ,1'b0      ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_i            ,1'b0      ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_drvpd        ,"+pad_info[pad_info_index["drv"]]+"      ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_drvpu        ,"+pad_info[pad_info_index["drv"]]+"      ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_idelay       ,6'b0      ,W   ,input,")   
                print_line.append("connect,"+filename+"_ring.pad_name_odelay       ,6'b0      ,W   ,input,")  
                print_line.append("connect,"+filename+"_ring.pad_name_ie           ,1'b1      ,W   ,input,")    
                print_line.append("connect,"+filename+"_ring.pad_name_fben         ,1'b0      ,W   ,input,")      
                print_line.append("connect,"+filename+"_ring.pad_name_fbsel        ,1'b0      ,W   ,input,")     
                print_line.append("connect,"+filename+"_ring.pad_name_odten        ,1'b0      ,W   ,input,")   
                print_line.append("connect,"+filename+"_ring.pad_name_odtpd        ,4'b0  ,W   ,input,")   
                print_line.append("connect,"+filename+"_ring.pad_name_odtpu        ,4'b0  ,W   ,input,")   
                print_line.append("connect,"+filename+"_ring.pad_name_slew         ,5'b0      ,W   ,input,")     
                print_line.append("connect,"+filename+"_ring.pad_name_smit_rxmode  ,"+pad_info[pad_info_index["rx_smit"]]+"      ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_weakpd       ,"+pad_info[pad_info_index["pd"]]+"      ,W   ,input,")   
                print_line.append("connect,"+filename+"_ring.pad_name_weakpu       ,"+pad_info[pad_info_index["pu"]]+"      ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_c            ,pad_name_c,W   ,output,")
                print_line.append("connect,"+filename+"_ring.pad_name_vref     ,"+pad_info[pad_info_index["io_domain"]].lower()+"_vref        ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_pwrokb_h     ,"+pad_info[pad_info_index["io_domain"]].lower()+"_pwrokb_h        ,W   ,input,")
            else :
                print_line.append('connect,'+filename+'_ring.PAD_NAME       ,PAD_NAME         ,IO      ,inout,')
                print_line.append('connect,'+filename+'_ring.pad_name_oe_n         ,{~pad_name_oe_n}        ,W   ,input,')
                print_line.append('connect,'+filename+'_ring.pad_name_i            ,pad_name_i           ,W   ,input,')
                print_line.append('connect,'+filename+'_ring.pad_name_drvpd        ,pad_name_drvpd[4:0]       ,W   ,input,')
                print_line.append('connect,'+filename+'_ring.pad_name_drvpu        ,pad_name_drvpu[4:0]       ,W   ,input,')     
                print_line.append('connect,'+filename+'_ring.pad_name_idelay       ,pad_name_idelay[5:0]      ,W   ,input,')   
                print_line.append('connect,'+filename+'_ring.pad_name_odelay       ,pad_name_odelay[5:0]      ,W   ,input,')  
                print_line.append('connect,'+filename+'_ring.pad_name_ie           ,pad_name_ie          ,W   ,input,')    
                print_line.append('connect,'+filename+'_ring.pad_name_fben         ,pad_name_fben        ,W   ,input,')      
                print_line.append('connect,'+filename+'_ring.pad_name_fbsel        ,pad_name_fbsel       ,W   ,input,')     
                print_line.append('connect,'+filename+'_ring.pad_name_odten        ,pad_name_odten       ,W   ,input,')   
                print_line.append('connect,'+filename+'_ring.pad_name_odtpd        ,pad_name_odtpd[3:0]       ,W   ,input,')   
                print_line.append('connect,'+filename+'_ring.pad_name_odtpu        ,pad_name_odtpu[3:0]       ,W   ,input,')   
                print_line.append('connect,'+filename+'_ring.pad_name_slew         ,pad_name_slew[4:0]       ,W   ,input,')     
                print_line.append('connect,'+filename+'_ring.pad_name_smit_rxmode  ,pad_name_smit_rxmode ,W   ,input,')
                print_line.append('connect,'+filename+'_ring.pad_name_weakpd       ,pad_name_weakpd      ,W   ,input,')   
                print_line.append('connect,'+filename+'_ring.pad_name_weakpu       ,pad_name_weakpu      ,W   ,input,')
                print_line.append('connect,'+filename+'_ring.pad_name_c            ,pad_name_c           ,W   ,output,')
                print_line.append("connect,"+filename+"_ring.pad_name_vref     ,"+pad_info[pad_info_index["io_domain"]].lower()+"_vref        ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_pwrokb_h     ,"+pad_info[pad_info_index["io_domain"]].lower()+"_pwrokb_h        ,W   ,input,")
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        else:
            #cell_ds_msb = 0
            #cell_st = 0
            #cell_sl = 0
            #cell_msc = 0
            #cell_ps = 0
            #cell_he = 0
            #cell_pe = 0
            for cell_info in pad_cell :
                cell_info_list = cell_info.split(",")
                cell_name = cell_info_list[0]
                if pad_info[pad_info_index["pad_cell_type"]] == cell_name :
                    cell_ds = str(cell_info_list[pad_cell_index["ds"]])
                    cell_st = str(cell_info_list[pad_cell_index["st"]])
                    cell_sl = str(cell_info_list[pad_cell_index["sl"]])
                    cell_msc= str(cell_info_list[pad_cell_index["msc"]])
                    cell_ps = str(cell_info_list[pad_cell_index["ps"]])
                    cell_he = str(cell_info_list[pad_cell_index["he"]])
                    cell_pe = str(cell_info_list[pad_cell_index["pe"]])
                    if "[" in cell_ds :
                        cell_ds_list = cell_ds.split("[", 1)
                        cell_ds_width_list = cell_ds_list[1].split(":", 1)
                        cell_ds_msb = cell_ds_width_list[0]
                    if "[" in cell_st :
                        cell_st_list = cell_st.split("[", 1)
                        cell_st_width_list = cell_st_list[1].split(":", 1)
                        cell_st_msb = cell_st_width_list[0]
            #print(pad_info)
            print_line.append('connect,'+filename+'_ring.PAD_NAME       ,PAD_NAME         ,IO      ,inout,')
            if 'GPI' == pad_info[pad_info_index["type"]] :
                print_line.append("connect,"+filename+"_ring.pad_name_oe_n  ,1'b1      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_i     ,1'b0      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_ie    ,1'b1      ,W       ,input,")
#   241106 ZZQ
#                print_line.append("connect,"+filename+"_ring.pad_name_pu    ,"+pad_info[pad_info_index["pu"]]+"      ,W       ,input,")
#                print_line.append("connect,"+filename+"_ring.pad_name_pd    ,"+pad_info[pad_info_index["pd"]]+"      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_ds    ,"+pad_info[pad_info_index["drv"]]+"    ,W       ,input,")
                #if pd.isna(cell_st) == False :
                if cell_st != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_st    ,2'b0    ,W       ,input,")
                #if pd.isna(cell_sl) == False :
                if cell_sl != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_sl    ,1'b0      ,W       ,input,")
                #if pd.isna(cell_msc) == False :
                if cell_msc != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_msc   ,1'b0      ,W       ,input,")
                #if pd.isna(cell_ps) == False :
                if cell_ps != "nan" :
                    if pad_info[pad_info_index["pu"]] == "1'b1" :
                    	print_line.append("connect,"+filename+"_ring.pad_name_ps    ,1'b0      ,W       ,input,")
                    else :
                        print_line.append("connect,"+filename+"_ring.pad_name_ps    ,1'b0      ,W       ,input,")		    	
#   241106 ZZQ
                else :
                    print_line.append("connect,"+filename+"_ring.pad_name_pu    ,"+pad_info[pad_info_index["pu"]]+"      ,W       ,input,")
                    print_line.append("connect,"+filename+"_ring.pad_name_pd    ,"+pad_info[pad_info_index["pd"]]+"      ,W       ,input,")
                #if pd.isna(cell_he) == False :
                if cell_he != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_he    ,1'b0      ,W       ,input,")
                #if pd.isna(cell_pe) == False :
                if cell_pe != "nan" :
                    if pad_info[pad_info_index["pu"]] == "1'b1" or pad_info[pad_info_index["pd"]] == "1'b1" :
                        print_line.append("connect,"+filename+"_ring.pad_name_pe    ,1'b1      ,W       ,input,")
                    else :
                    	print_line.append("connect,"+filename+"_ring.pad_name_pe    ,1'b0      ,W       ,input,")

            elif 'GPO' == pad_info[pad_info_index["type"]] :
                print_line.append("connect,"+filename+"_ring.pad_name_oe_n  ,1'b0      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_i     ,1'b0      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_ie    ,1'b0      ,W       ,input,")
#   241106 ZZQ
#                print_line.append("connect,"+filename+"_ring.pad_name_pu    ,"+pad_info[pad_info_index["pu"]]+"      ,W       ,input,")
#                print_line.append("connect,"+filename+"_ring.pad_name_pd    ,"+pad_info[pad_info_index["pd"]]+"      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_ds    ,"+pad_info[pad_info_index["drv"]]+"    ,W       ,input,")
                #if pd.isna(cell_st) == False :
                if cell_st != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_st    ,2'b0    ,W       ,input,")
                #if pd.isna(cell_sl) == False :
                if cell_sl != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_sl    ,1'b0      ,W       ,input,")
                #if pd.isna(cell_msc) == False :
                if cell_msc != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_msc   ,1'b0      ,W       ,input,")
                #if pd.isna(cell_ps) == False :
                if cell_ps != "nan" :
                    if pad_info[pad_info_index["pu"]] == "1'b1" :
                        print_line.append("connect,"+filename+"_ring.pad_name_ps    ,1'b1      ,W       ,input,")
                    else :
                        print_line.append("connect,"+filename+"_ring.pad_name_ps    ,1'b0      ,W       ,input,")
#   241106 ZZQ TODO
                else :
                    print_line.append("connect,"+filename+"_ring.pad_name_pu    ,"+pad_info[pad_info_index["pu"]]+"      ,W       ,input,")
                    print_line.append("connect,"+filename+"_ring.pad_name_pd    ,"+pad_info[pad_info_index["pd"]]+"      ,W       ,input,")
                #if pd.isna(cell_he) == False :
                if cell_he != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_he    ,1'b0      ,W       ,input,")
                #if pd.isna(cell_pe) == False :
                if cell_pe != "nan" :
                    if pad_info[pad_info_index["pu"]] == "1'b1" or pad_info[pad_info_index["pd"]] == "1'b1" :
                        print_line.append("connect,"+filename+"_ring.pad_name_pe    ,1'b1      ,W       ,input,")
                    else :
                    	print_line.append("connect,"+filename+"_ring.pad_name_pe    ,1'b0      ,W       ,input,")
            else :
                print_line.append("connect,"+filename+"_ring.pad_name_oe_n  ,pad_name_oe_n    ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_i     ,pad_name_i       ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_ie    ,pad_name_ie      ,W       ,input,")
#   241106 ZZQ
#                print_line.append("connect,"+filename+"_ring.pad_name_pu    ,pad_name_pu      ,W       ,input,")
#                print_line.append("connect,"+filename+"_ring.pad_name_pd    ,pad_name_pd      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_ds    ,pad_name_ds["+str(cell_ds_msb)+":0] ,W       ,input,")
                #if pd.isna(cell_st) == False :
                if cell_st != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_st    ,pad_name_st    ,W       ,input,")
                #if pd.isna(cell_sl) == False :
                if cell_sl != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_sl    ,pad_name_sl      ,W       ,input,")
                #if pd.isna(cell_msc) == False :
                if cell_msc != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_msc   ,"+pad_info[pad_info_index["io_domain"]].lower()+"_msc      ,W       ,input,")
                #if pd.isna(cell_ps) == False :
                if cell_ps != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_ps    ,pad_name_ps      ,W       ,input,")
#   241106 ZZQ
                else :
                    print_line.append("connect,"+filename+"_ring.pad_name_pu    ,pad_name_pu      ,W       ,input,")
                    print_line.append("connect,"+filename+"_ring.pad_name_pd    ,pad_name_pd      ,W       ,input,")
                #if pd.isna(cell_he) == False :
                if cell_he != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_he    ,pad_name_he      ,W       ,input,")
                #if pd.isna(cell_pe) == False :
                if cell_pe != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_pe    ,pad_name_pe      ,W       ,input,")
            print_line.append('connect,'+filename+'_ring.pad_name_c     ,pad_name_c       ,W       ,output,')
            #port_last_process(count, pad_ser, print_line)
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
    print_line.append("#port_inst_end")
    print_line.append("#inst_end============================================================================================================")


    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    #fp.write('\n')
    #fp.write('endmodule')

    fp.close()

    fp = open(gen_filepath+filename+"_vref_tdr_buf_list.txt", "w") 
    for line in tdr_buf_list :
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')

    fp.close()
# }}}

def io_top_gen_model_csv(protocol, design_owner, pad_cell, pad_info_index, gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index) :#{{{
    fp = open(gen_filepath+filename+"_top_model.csv", "w") 

    print_line = []

    print_line.append("#author_begin")
    print_line.append(design_owner)
    print_line.append("#author_end")
    print_line.append("#order_begin")
    print_line.append("False")
    print_line.append("#order_end")
    print_line.append("#keep_begin before_module")
    print_line.append("#keep_end before_module")
    print_line.append("module,"+filename+"_top_model")
    print_line.append("#parameter_begin")
    print_line.append("#parameter_end")
   
    print_line.append("#port_begin")
    print_line.append("#port_end")
    print_line.append("#gen_type_begin")
    print_line.append("v")
    print_line.append("#gen_type_end")
    print_line.append("#csv_begin")
    print_line.append("#csv_end")

    print_line.append("#inst_begin===========================================================================================================")
    #if protocol == "apb" :
    #    print_line.append("inst "+filename.upper()+"_"+protocol+"_reg u_"+filename.upper()+"_"+protocol+"_reg")
    #elif protocol == "ahb" :
    #    print_line.append("inst "+filename.upper()+"_"+protocol+"_reg u_"+filename.upper()+"_"+protocol+"_reg")
    #elif protocol == "dab" :
    print_line.append("inst "+filename.upper()+"_"+protocol+"_reg u_"+filename.upper()+"_"+protocol+"_reg")
    print_line.append("#para_inst_begin")
    print_line.append("#para_inst_end")
    print_line.append("#port_inst_begin")
    if protocol == "apb" :
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.clk                 ,apb_clk            ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.rst_n               ,apb_rst_n          ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.psel                ,apb_sel            ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.penable             ,apb_enable         ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pwrite              ,apb_write          ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.paddr               ,apb_addr[31:0]     ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pwdata              ,apb_wdata[31:0]    ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.prdata              ,apb_rdata[31:0]    ,O         ,output,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pready              ,apb_pready         ,O         ,output,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pslverr              ,apb_slverr         ,O         ,output,")
    elif protocol == "dab" :
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.clk                 ,dab_clk            ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.rst_n               ,dab_rst_n          ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.dab_write           ,dab_write          ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.dab_read            ,dab_read           ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.dab_addr            ,dab_addr[31:0]     ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.dab_wdata           ,dab_wdata[31:0]    ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.dab_rdata           ,dab_rdata[31:0]    ,O         ,output,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.dab_ready           ,dab_ready          ,O         ,output,")
    elif protocol == "ahb" :
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.clk                 ,ahb_clk        ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.rst_n               ,ahb_rst_n      ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hreadyin            ,hreadyin       ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hsel                ,hsel           ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.htrans              ,htrans[1:0]    ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hwrite              ,hwrite         ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hburst              ,hburst[2:0]    ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hsize               ,hsize[2:0]     ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.haddr               ,haddr[31:0]    ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hwdata              ,hwdata[31:0]   ,I         ,input,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hreadyout           ,hreadyout      ,O         ,output,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hresp               ,hresp[1:0]     ,O         ,output,")
        print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.hrdata              ,hrdata[31:0]   ,O         ,output,")


    count = 0
    for pad_info in pad_corpus:
        if 'PINMUX' == pad_info[pad_info_index["type"]] or 'GPIO' == pad_info[pad_info_index["type"]] or 'VREF' == pad_info[pad_info_index["type"]] or 'POC' == pad_info[pad_info_index["type"]]:
            #cell_ds_msb = 0
            #cell_st_msb = 0
            #cell_st = 0
            #cell_sl = 0
            #cell_msc = 0
            #cell_ps = 0
            #cell_he = 0
            #cell_pe = 0
            if  "INNO_GPIO" == pad_info[pad_info_index["pad_cell_type"]]:
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"0_pad_name0_drvpd      ,pad_name0_drvpd[4:0]                     ,W      ,output, ")
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"0_pad_name0_drvpu      ,pad_name0_drvpu[4:0]                     ,W      ,output, ")     
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"0_pad_name0_idelay     ,pad_name0_idelay[5:0]                    ,W      ,output,  ")   
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"0_pad_name0_odelay     ,pad_name0_odelay[5:0]                    ,W      ,output,  ")  
                if 'PINMUX' == pad_info[pad_info_index["type"]]:
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_func_sel  ,pad_name0_func_sel[1:0]     ,W      ,output,")
                                                                                                                                                                                       
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_ie         ,pad_name0_ie                        ,W      ,output,  ")    
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_fben       ,pad_name0_fben                      ,W      ,output,  ")      
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_fbsel      ,pad_name0_fbsel                     ,W      ,output,  ")     
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_odten      ,pad_name0_odten                     ,W      ,output,  ")   
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_odtpd      ,pad_name0_odtpd[3:0]                     ,W      ,output,  ")   
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_odtpu      ,pad_name0_odtpu[3:0]                     ,W      ,output,  ")   
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_slew      ,pad_name0_slew[4:0]                     ,W      ,output,  ")     
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_smit_rxmode,pad_name0_smit_rxmode               ,W      ,output,  ")
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_weakpd     ,pad_name0_weakpd                    ,W      ,output,  ")   
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"1_pad_name0_weakpu     ,pad_name0_weakpu                     ,W      ,output, ") 
                replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name0')
            elif "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_reg_vref_sel       ,pad_name0_reg_vref_sel[7:0]                ,W      ,output,  ")   
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_reg_vref_pd        ,pad_name0_reg_vref_pd                     ,W      ,output, ") 
                if pd.isna(pad_info[pad_info_index["io_domain"]]) == True :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_name0_inno_poc_cell_pad_name0_inno_poc_cell_pwrok      ,pad_name0_inno_poc_cell_pwrok                     ,W      ,output, ")
                replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name0')
            elif "POC" == pad_info[pad_info_index["type"]]:
                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_pad_name_ms                       ,pad_name_ms                     ,W      ,output, ")
                replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            else :
                for cell_info in pad_cell :
                    cell_info_list = cell_info.split(",")
                    cell_name = cell_info_list[0]
                    if pad_info[pad_info_index["pad_cell_type"]] == cell_name :
                        cell_ds = str(cell_info_list[pad_cell_index["ds"]])
                        cell_st = str(cell_info_list[pad_cell_index["st"]])
                        cell_sl = str(cell_info_list[pad_cell_index["sl"]])
                        cell_msc= str(cell_info_list[pad_cell_index["msc"]])
                        cell_ps = str(cell_info_list[pad_cell_index["ps"]])
                        cell_he = str(cell_info_list[pad_cell_index["he"]])
                        cell_pe = str(cell_info_list[pad_cell_index["pe"]])
                        if "[" in cell_ds :
                            cell_ds_list = cell_ds.split("[", 1)
                            cell_ds_width_list = cell_ds_list[1].split(":", 1)
                            cell_ds_msb = cell_ds_width_list[0]
                        if "[" in cell_st :
                            cell_st_list = cell_st.split("[", 1)
                            cell_st_width_list = cell_st_list[1].split(":", 1)
                            cell_st_msb = cell_st_width_list[0]
                if "PINMUX" == pad_info[pad_info_index["type"]] or "GPIO" == pad_info[pad_info_index["type"]] :
#   241106  ZZQ
#                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_pu        ,pad_name0_pu                ,W      ,output,")
#                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_pd        ,pad_name0_pd                ,W      ,output,")
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_ie        ,pad_name0_ie                ,W      ,output,")
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_ds        ,pad_name0_ds["+str(cell_ds_msb)+":0]           ,W      ,output,")
                if 'PINMUX' == pad_info[pad_info_index["type"]]:
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_func_sel  ,pad_name0_func_sel[1:0]     ,W      ,output,")
                #if pd.isna(cell_st) == False :
                if cell_st != "nan" :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_st        ,pad_name0_st["+str(cell_st_msb)+":0]           ,W      ,output,")
                #if pd.isna(cell_sl) == False :
                if cell_sl != "nan" :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_sl        ,pad_name0_sl                ,W      ,output,")
                #if pd.isna(cell_msc) == False :
                #if cell_msc != "nan" :
                #    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_msc        ,pad_name0_msc                ,W      ,output,")
                #if pd.isna(cell_ps) == False :
                if cell_ps != "nan" :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_ps        ,pad_name0_ps                ,W      ,output,")
#   241106 ZZQ
                else :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_pu        ,pad_name0_pu                ,W      ,output,")
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_pd        ,pad_name0_pd                ,W      ,output,")
                #if pd.isna(cell_he) == False :
                if cell_he != "nan" :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_he        ,pad_name0_he                ,W      ,output,")
                #if pd.isna(cell_pe) == False :
                if cell_pe != "nan" :
                    print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_pe        ,pad_name0_pe                ,W      ,output,")
                replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name0')


    replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
    print_line.append("#port_inst_end")
    print_line.append("#inst_end============================================================================================================")

    for pad_info in pad_corpus:
        if "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
            print_line.append("#inst_begin===========================================================================================================")
            print_line.append('inst INNO_POC_CELL u_pad_name_inno_poc_cell')
            print_line.append("#para_inst_begin")
            print_line.append("#para_inst_end")
            print_line.append("#port_inst_begin")
            #   241031 zhengzhiqiang
            if pd.isna(pad_info[pad_info_index["io_domain"]]) == False :
                print_line.append("connect,u_inno_poc_cell.PWROK     ,"+pad_info[pad_info_index["io_domain"]]+"     ,W       ,input,")
            else :
            	print_line.append('connect,u_inno_poc_cell.PWROK     ,pad_name_inno_poc_cell_pwrok       ,W       ,input,')
            print_line.append('connect,u_inno_poc_cell.PWROKB_H  ,pad_name_pwrokb_h    ,W       ,output,')
            print_line.append('connect,u_inno_poc_cell.VREF      ,pad_name_vref        ,W       ,input,')
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#port_inst_end")
            print_line.append("#inst_end============================================================================================================")
            
            print_line.append("#inst_begin===========================================================================================================")
            print_line.append("inst "+pad_info[pad_info_index["pad_cell_type"]].lower()+"_model u_pad_name_vref")
            print_line.append("#para_inst_begin")
            print_line.append("#para_inst_end")
            print_line.append("#port_inst_begin")
            print_line.append("connect,u_inno_poc_cell.reg_vref_sel    ,pad_name_reg_vref_sel   ,W       ,input,")
            print_line.append("connect,u_inno_poc_cell.reg_vref_pd     ,pad_name_reg_vref_pd    ,W       ,input,")
            print_line.append("connect,u_inno_poc_cell.pwrokb_h        ,pad_name_pwrokb_h       ,W       ,input,")
            print_line.append("connect,u_inno_poc_cell.vref            ,pad_name_vref           ,W       ,output,")
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)   
            print_line.append("#port_inst_end")
            print_line.append("#inst_end============================================================================================================")
    

        if "POC" == pad_info[pad_info_index["type"]]:
            print_line.append("#inst_begin===========================================================================================================")
            print_line.append("inst "+pad_info[pad_info_index["pad_cell_type"]]+" u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]])
            print_line.append("#para_inst_begin")
            print_line.append("#para_inst_end")
            print_line.append("#port_inst_begin")
            print_line.append("connect,u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+".MS       ,pad_name_ms         ,W       ,input,")
            print_line.append("connect,u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+".MSC      ,pad_name_msc        ,W       ,output,")
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#port_inst_end")
            print_line.append("#inst_end============================================================================================================")

    print_line.append("#inst_begin===========================================================================================================")
    print_line.append('inst '+filename+'_pin_mux_model u_'+filename+'_pin_mux_model')
    print_line.append("#para_inst_begin")
    print_line.append("#para_inst_end")
    print_line.append("#port_inst_begin")


    count = 0
    module_inst = filename+'_pin_mux_model'
    print_line.append('connect,'+module_inst+'.test_mode     ,test_mode       ,I       ,input,')
    for pad_info in pad_corpus:
        count += 1
        if "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
            replace_pad_name(pad_info_index, pad_info, print_line)
        elif 'GPIO' == pad_info[pad_info_index["type"]]:
            if 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('connect,'+module_inst+'.pad_name_c     ,pad_name_c       ,W       ,input,')
                print_line.append('connect,'+module_inst+'.pad_name_i     ,pad_name_i       ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_oe_n  ,pad_name_oe_n    ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_out   ,pad_name_out     ,I       ,input,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            elif 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('connect,'+module_inst+'.pad_name_c     ,pad_name_c       ,W       ,input,')
                print_line.append('connect,'+module_inst+'.pad_name_i     ,pad_name_i       ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_oe_n  ,pad_name_oe_n    ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_in    ,pad_name_in      ,O       ,output,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            elif 'INOUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('connect,'+module_inst+'.pad_name_c     ,pad_name_c       ,W       ,input,')
                print_line.append('connect,'+module_inst+'.pad_name_i     ,pad_name_i       ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_oe_n  ,pad_name_oe_n    ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_out   ,pad_name_out     ,I       ,input,')
                print_line.append('connect,'+module_inst+'.pad_name_oen   ,pad_name_oen     ,I       ,input,')
                print_line.append('connect,'+module_inst+'.pad_name_in    ,pad_name_in      ,O       ,output,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'GPI' == pad_info[pad_info_index["type"]]:
            if 'INPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('connect,'+module_inst+'.pad_name_i     ,pad_name_i       ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_oe_n  ,pad_name_oe_n    ,W       ,output,')
                print_line.append('connect,'+module_inst+'.pad_name_out   ,pad_name_out     ,I       ,input,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'GPO' == pad_info[pad_info_index["type"]]:
            if 'OUTPUT' == pad_info[pad_info_index["normal_attr"]]:
                print_line.append('connect,'+module_inst+'.pad_name_c     ,pad_name_c       ,W       ,input,')
                print_line.append('connect,'+module_inst+'.pad_name_in    ,pad_name_in      ,O       ,output,')
                replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif 'PINMUX' == pad_info[pad_info_index["type"]]: 
            print_line.append('connect,'+module_inst+'.pad_name_c          ,pad_name_c                 ,W      ,input,')
            print_line.append('connect,'+module_inst+'.pad_name_i          ,pad_name_i                 ,W      ,output,')
            print_line.append('connect,'+module_inst+'.pad_name_oe_n       ,pad_name_oe_n              ,W      ,output,')
            print_line.append("connect,"+module_inst+".pad_name_func_sel   ,pad_name_func_sel[1:0]     ,W      ,input,") 
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
            replace_pad_name(pad_info_index, pad_info, print_line)
            # function 0
            pin_mux_port_gen_model_csv(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["normal_attr"]], pad_info[pad_info_index["normal_mode"]:], module_inst)
           # function 1
            pin_mux_port_gen_model_csv(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["func1_attr"]], pad_info[pad_info_index["func1"]:], module_inst)
            # function 2
            pin_mux_port_gen_model_csv(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["func2_attr"]], pad_info[pad_info_index["func2"]:], module_inst)
            # function 3
            pin_mux_port_gen_model_csv(pad_info_index, count, pad_ser, print_line, pad_info[pad_info_index["func3_attr"]], pad_info[pad_info_index["func3"]:],module_inst)

    print_line.append("#port_inst_end")
    print_line.append("#inst_end============================================================================================================")
    
    print_line.append("#inst_begin===========================================================================================================")
    print_line.append('inst '+filename+'_ring u_'+filename+'_ring')
    print_line.append("#para_inst_begin")
    print_line.append("#para_inst_end")
    print_line.append("#port_inst_begin")
    count = 0
    print_line.append('connect,'+module_inst+'.test_mode     ,test_mode       ,I       ,input,')
    for pad_info in pad_corpus:
        count += 1  
        if 'ANALOG' == pad_info[pad_info_index["type"]]:
            print_line.append('connect ,'+filename+'_ring.PAD_NAME       ,PAD_NAME         ,IO       ,inout,')
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif "POC" == pad_info[pad_info_index["type"]]:
            continue
        elif "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
            continue
        #    print_line.append('connect,'+filename+'_ring.pad_name_reg_vref_sel          ,pad_name_reg_vref_sel[7:0]  ,W   ,input,')
        #    print_line.append('connect,'+filename+'_ring.pad_name_reg_vref_pd           ,pad_name_reg_vref_pd        ,W   ,input,')
        #    print_line.append('connect,'+filename+'_ring.pad_name_pwrokb_h              ,pwrokb_h        ,W   ,input,')
        #    print_line.append('connect,'+filename+'_ring.vref              ,vref        ,W   ,output,')
        #    replace_pad_name(pad_info_index, pad_info, print_line)
        #    replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif  "INNO_GPIO" == pad_info[pad_info_index["pad_cell_type"]]:
            if 'GPI' == pad_info[pad_info_index["type"]] :
                print_line.append("connect,"+filename+"_ring.PAD_NAME       ,PAD_NAME         ,IO      ,inout,")
                print_line.append("connect,"+filename+"_ring.pad_name_oe_n         ,{~pad_name_oe_n}      ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_i            ,pad_name_i      ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_drvpd        ,"+pad_info[pad_info_index["drv"]]+"      ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_drvpu        ,"+pad_info[pad_info_index["drv"]]+"      ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_idelay       ,6'b0      ,W   ,input,")   
                print_line.append("connect,"+filename+"_ring.pad_name_odelay       ,6'b0      ,W   ,input,")  
                print_line.append("connect,"+filename+"_ring.pad_name_ie           ,1'b1      ,W   ,input,")    
                print_line.append("connect,"+filename+"_ring.pad_name_fben         ,1'b0      ,W   ,input,")      
                print_line.append("connect,"+filename+"_ring.pad_name_fbsel        ,1'b0      ,W   ,input,")     
                print_line.append("connect,"+filename+"_ring.pad_name_odten        ,1'b0      ,W   ,input,")   
                print_line.append("connect,"+filename+"_ring.pad_name_odtpd        ,4'b0  ,W   ,input,")   
                print_line.append("connect,"+filename+"_ring.pad_name_odtpu        ,4'b0  ,W   ,input,")   
                print_line.append("connect,"+filename+"_ring.pad_name_slew         ,5'b0      ,W   ,input,")     
                print_line.append("connect,"+filename+"_ring.pad_name_smit_rxmode  ,"+pad_info[pad_info_index["rx_smit"]]+"      ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_weakpd       ,"+pad_info[pad_info_index["pd"]]+"      ,W   ,input,")   
                print_line.append("connect,"+filename+"_ring.pad_name_weakpu       ,"+pad_info[pad_info_index["pu"]]+"      ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_c            ,pad_name_c,W   ,output,")
                print_line.append("connect,"+filename+"_ring.pad_name_vref     ,"+pad_info[pad_info_index["io_domain"]].lower()+"_vref        ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_pwrokb_h     ,"+pad_info[pad_info_index["io_domain"]].lower()+"_pwrokb_h        ,W   ,input,")
            else :
                print_line.append('connect,'+filename+'_ring.PAD_NAME       ,PAD_NAME         ,IO      ,inout,')
                print_line.append('connect,'+filename+'_ring.pad_name_oe_n         ,{~pad_name_oe_n}        ,W   ,input,')
                print_line.append('connect,'+filename+'_ring.pad_name_i            ,pad_name_i           ,W   ,input,')
                print_line.append('connect,'+filename+'_ring.pad_name_drvpd        ,pad_name_drvpd[4:0]       ,W   ,input,')
                print_line.append('connect,'+filename+'_ring.pad_name_drvpu        ,pad_name_drvpu[4:0]       ,W   ,input,')     
                print_line.append('connect,'+filename+'_ring.pad_name_idelay       ,pad_name_idelay[5:0]      ,W   ,input,')   
                print_line.append('connect,'+filename+'_ring.pad_name_odelay       ,pad_name_odelay[5:0]      ,W   ,input,')  
                print_line.append('connect,'+filename+'_ring.pad_name_ie           ,pad_name_ie          ,W   ,input,')    
                print_line.append('connect,'+filename+'_ring.pad_name_fben         ,pad_name_fben        ,W   ,input,')      
                print_line.append('connect,'+filename+'_ring.pad_name_fbsel        ,pad_name_fbsel       ,W   ,input,')     
                print_line.append('connect,'+filename+'_ring.pad_name_odten        ,pad_name_odten       ,W   ,input,')   
                print_line.append('connect,'+filename+'_ring.pad_name_odtpd        ,pad_name_odtpd[3:0]       ,W   ,input,')   
                print_line.append('connect,'+filename+'_ring.pad_name_odtpu        ,pad_name_odtpu[3:0]       ,W   ,input,')   
                print_line.append('connect,'+filename+'_ring.pad_name_slew         ,pad_name_slew[4:0]       ,W   ,input,')     
                print_line.append('connect,'+filename+'_ring.pad_name_smit_rxmode  ,pad_name_smit_rxmode ,W   ,input,')
                print_line.append('connect,'+filename+'_ring.pad_name_weakpd       ,pad_name_weakpd      ,W   ,input,')   
                print_line.append('connect,'+filename+'_ring.pad_name_weakpu       ,pad_name_weakpu      ,W   ,input,')
                print_line.append('connect,'+filename+'_ring.pad_name_c            ,pad_name_c           ,W   ,output,')
                print_line.append("connect,"+filename+"_ring.pad_name_vref     ,"+pad_info[pad_info_index["io_domain"]].lower()+"_vref        ,W   ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_pwrokb_h     ,"+pad_info[pad_info_index["io_domain"]].lower()+"_pwrokb_h        ,W   ,input,")
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        else:
            #cell_ds_msb = 0
            #cell_st = 0
            #cell_sl = 0
            #cell_msc = 0
            #cell_ps = 0
            #cell_he = 0
            #cell_pe = 0
            for cell_info in pad_cell :
                cell_info_list = cell_info.split(",")
                cell_name = cell_info_list[0]
                if pad_info[pad_info_index["pad_cell_type"]] == cell_name :
                    cell_ds = str(cell_info_list[pad_cell_index["ds"]])
                    cell_st = str(cell_info_list[pad_cell_index["st"]])
                    cell_sl = str(cell_info_list[pad_cell_index["sl"]])
                    cell_msc= str(cell_info_list[pad_cell_index["msc"]])
                    cell_ps = str(cell_info_list[pad_cell_index["ps"]])
                    cell_he = str(cell_info_list[pad_cell_index["he"]])
                    cell_pe = str(cell_info_list[pad_cell_index["pe"]])
                    if "[" in cell_ds :
                        cell_ds_list = cell_ds.split("[", 1)
                        cell_ds_width_list = cell_ds_list[1].split(":", 1)
                        cell_ds_msb = cell_ds_width_list[0]
                    if "[" in cell_st :
                        cell_st_list = cell_st.split("[", 1)
                        cell_st_width_list = cell_st_list[1].split(":", 1)
                        cell_st_msb = cell_st_width_list[0]
            #print(pad_info)
            print_line.append('connect,'+filename+'_ring.PAD_NAME       ,PAD_NAME         ,IO      ,inout,')
            if 'GPI' == pad_info[pad_info_index["type"]] :
                print_line.append("connect,"+filename+"_ring.pad_name_oe_n  ,pad_name_oe_n      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_i     ,pad_name_i      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_ie    ,1'b1      ,W       ,input,")
#   241106 ZZQ
#                print_line.append("connect,"+filename+"_ring.pad_name_pu    ,"+pad_info[pad_info_index["pu"]]+"      ,W       ,input,")
#                print_line.append("connect,"+filename+"_ring.pad_name_pd    ,"+pad_info[pad_info_index["pd"]]+"      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_ds    ,"+pad_info[pad_info_index["drv"]]+"    ,W       ,input,")
                #if pd.isna(cell_st) == False :
                if cell_st != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_st    ,2'b0    ,W       ,input,")
                #if pd.isna(cell_sl) == False :
                if cell_sl != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_sl    ,1'b0      ,W       ,input,")
                #if pd.isna(cell_msc) == False :
                if cell_msc != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_msc   ,1'b0      ,W       ,input,")
                #if pd.isna(cell_ps) == False :
                if cell_ps != "nan" :
                    if pad_info[pad_info_index["pu"]] == "1'b1" :
                        print_line.append("connect,"+filename+"_ring.pad_name_ps    ,1'b1      ,W       ,input,")
                    else :
                        print_line.append("connect,"+filename+"_ring.pad_name_ps    ,1'b0      ,W       ,input,")
#   241106 ZZQ
                else :
                    print_line.append("connect,"+filename+"_ring.pad_name_pu    ,"+pad_info[pad_info_index["pu"]]+"      ,W       ,input,")
                    print_line.append("connect,"+filename+"_ring.pad_name_pd    ,"+pad_info[pad_info_index["pd"]]+"      ,W       ,input,")
                #if pd.isna(cell_he) == False :
                if cell_he != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_he    ,1'b0      ,W       ,input,")
                #if pd.isna(cell_pe) == False :
                if cell_pe != "nan" :
                    if pad_info[pad_info_index["pu"]] == "1'b1" or pad_info[pad_info_index["pd"]] == "1'b1" :
                        print_line.append("connect,"+filename+"_ring.pad_name_pe    ,1'b1      ,W       ,input,")
                    else :
                    	print_line.append("connect,"+filename+"_ring.pad_name_pe    ,1'b0      ,W       ,input,")

            elif 'GPO' == pad_info[pad_info_index["type"]] :
                print_line.append("connect,"+filename+"_ring.pad_name_oe_n  ,1'b1      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_i     ,1'b0      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_ie    ,1'b0      ,W       ,input,")
#   241106 ZZQ
#                print_line.append("connect,"+filename+"_ring.pad_name_pu    ,"+pad_info[pad_info_index["pu"]]+"      ,W       ,input,")
#                print_line.append("connect,"+filename+"_ring.pad_name_pd    ,"+pad_info[pad_info_index["pd"]]+"      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_ds    ,"+pad_info[pad_info_index["drv"]]+"    ,W       ,input,")
                #if pd.isna(cell_st) == False :
                if cell_st != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_st    ,2'b0    ,W       ,input,")
                #if pd.isna(cell_sl) == False :
                if cell_sl != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_sl    ,1'b0      ,W       ,input,")
                #if pd.isna(cell_msc) == False :
                if cell_msc != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_msc   ,1'b0      ,W       ,input,")
                #if pd.isna(cell_ps) == False :
                if cell_ps != "nan" :
                    if pad_info[pad_info_index["pu"]] == "1'b1" :
                        print_line.append("connect,"+filename+"_ring.pad_name_ps    ,1'b1      ,W       ,input,")
                    else :
                        print_line.append("connect,"+filename+"_ring.pad_name_ps    ,1'b0      ,W       ,input,")
#   241106 ZZQ
                else :
                    print_line.append("connect,"+filename+"_ring.pad_name_pu    ,"+pad_info[pad_info_index["pu"]]+"      ,W       ,input,")
                    print_line.append("connect,"+filename+"_ring.pad_name_pd    ,"+pad_info[pad_info_index["pd"]]+"      ,W       ,input,")
                #if pd.isna(cell_he) == False :
                if cell_he != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_he    ,1'b0      ,W       ,input,")
                #if pd.isna(cell_pe) == False :
                if cell_pe != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_pe    ,1'b0      ,W       ,input,")
            else :
                print_line.append("connect,"+filename+"_ring.pad_name_oe_n  ,pad_name_oe_n    ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_i     ,pad_name_i       ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_ie    ,pad_name_ie      ,W       ,input,")
#   241106 ZZQ
#                   print_line.append("connect,"+filename+"_ring.pad_name_pu    ,pad_name_pu      ,W       ,input,")
#                   print_line.append("connect,"+filename+"_ring.pad_name_pd    ,pad_name_pd      ,W       ,input,")
                print_line.append("connect,"+filename+"_ring.pad_name_ds    ,pad_name_ds["+str(cell_ds_msb)+":0] ,W       ,input,")
                #if pd.isna(cell_st) == False :
                if cell_st != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_st    ,pad_name_st    ,W       ,input,")
                #if pd.isna(cell_sl) == False :
                if cell_sl != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_sl    ,pad_name_sl      ,W       ,input,")
                #if pd.isna(cell_msc) == False :
                if cell_msc != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_msc   ,"+pad_info[pad_info_index["io_domain"]].lower()+"_msc      ,W       ,input,")
                #if pd.isna(cell_ps) == False :
                if cell_ps != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_ps    ,pad_name_ps      ,W       ,input,")
#   241106 ZZQ
                else :
                    print_line.append("connect,"+filename+"_ring.pad_name_pu    ,pad_name_pu      ,W       ,input,")
                    print_line.append("connect,"+filename+"_ring.pad_name_pd    ,pad_name_pd      ,W       ,input,")
                #if pd.isna(cell_he) == False :
                if cell_he != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_he    ,pad_name_he      ,W       ,input,")
                #if pd.isna(cell_pe) == False :
                if cell_pe != "nan" :
                    print_line.append("connect,"+filename+"_ring.pad_name_pe    ,pad_name_pe      ,W       ,input,")
            print_line.append('connect,'+filename+'_ring.pad_name_c     ,pad_name_c       ,W       ,output,')
            #port_last_process(count, pad_ser, print_line)
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
    print_line.append("#port_inst_end")
    print_line.append("#inst_end============================================================================================================")


    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    #fp.write('\n')
    #fp.write('endmodule')

    fp.close()
# }}}

# pin_mux_port_gen_csv{{{
def pin_mux_port_gen_csv(pad_info_index, count, pad_ser, print_line, pad_direct_idx, pad_name_idx, module_inst):
    #print(pad_direct_idx)
    #print(pad_name_idx)
    if 'OUTPUT' == pad_direct_idx:
        print_line.append('connect,'+module_inst+'.pad_name_out   ,pad_name_out     ,I      ,input,')
        #port_last_process(count, pad_ser, print_line)
        replace_pad_name(pad_info_index, pad_name_idx, print_line)
    elif 'INPUT' == pad_direct_idx:
        #print_line.append('\tinput          pad_name_oen,')
        print_line.append('connect,'+module_inst+'.pad_name_in    ,pad_name_in     ,O      ,output,')
        #port_last_process(count, pad_ser, print_line)
        replace_pad_name(pad_info_index, pad_name_idx, print_line)
    elif 'INOUT' == pad_direct_idx:
        print_line.append('connect,'+module_inst+'.pad_name_out   ,pad_name_out    ,I      ,input,')
        print_line.append('connect,'+module_inst+'.pad_name_oen   ,pad_name_oen    ,I      ,input,')
        print_line.append('connect,'+module_inst+'.pad_name_in    ,pad_name_in     ,O      ,output,')
        #port_last_process(count, pad_ser, print_line)
        replace_pad_name(pad_info_index, pad_name_idx, print_line)
# }}}

# pin_mux_port_gen_model_csv{{{
def pin_mux_port_gen_model_csv(pad_info_index, count, pad_ser, print_line, pad_direct_idx, pad_name_idx, module_inst):
    #print(pad_direct_idx)
    #print(pad_name_idx)
    if 'INPUT' == pad_direct_idx:
        print_line.append('connect,'+module_inst+'.pad_name_out   ,pad_name_out     ,I      ,input,')
        #port_last_process(count, pad_ser, print_line)
        replace_pad_name(pad_info_index, pad_name_idx, print_line)
    elif 'OUTPUT' == pad_direct_idx:
        #print_line.append('\tinput          pad_name_oen,')
        print_line.append('connect,'+module_inst+'.pad_name_in    ,pad_name_in     ,O      ,output,')
        #port_last_process(count, pad_ser, print_line)
        replace_pad_name(pad_info_index, pad_name_idx, print_line)
    elif 'INOUT' == pad_direct_idx:
        print_line.append('connect,'+module_inst+'.pad_name_out   ,pad_name_out    ,I      ,input,')
        print_line.append('connect,'+module_inst+'.pad_name_oen   ,pad_name_oen    ,I      ,input,')
        print_line.append('connect,'+module_inst+'.pad_name_in    ,pad_name_in     ,O      ,output,')
        #port_last_process(count, pad_ser, print_line)
        replace_pad_name(pad_info_index, pad_name_idx, print_line)
# }}}

# pin_mux_port_gen{{{
def pin_mux_port_gen(pad_info_index, count, pad_ser, print_line, pad_direct_idx, pad_name_idx):
    #print(pad_direct_idx)
    #print(pad_name_idx)
    if 'OUTPUT' == pad_direct_idx:
        print_line.append('\tinput          pad_name_out,')
        #port_last_process(count, pad_ser, print_line)
        replace_pad_name(pad_info_index, pad_name_idx, print_line)
    elif 'INPUT' == pad_direct_idx:
        #print_line.append('\tinput          pad_name_oen,')
        print_line.append('\toutput         pad_name_in,')
        #port_last_process(count, pad_ser, print_line)
        replace_pad_name(pad_info_index, pad_name_idx, print_line)
    elif 'INOUT' == pad_direct_idx:
        print_line.append('\tinput          pad_name_out,')
        print_line.append('\tinput          pad_name_oen,')
        print_line.append('\toutput         pad_name_in,')
        #port_last_process(count, pad_ser, print_line)
        replace_pad_name(pad_info_index, pad_name_idx, print_line)
# }}}

# pin_mux_port_gen_model{{{
def pin_mux_port_gen_model(pad_info_index, count, pad_ser, print_line, pad_direct_idx, pad_name_idx):
    #print(pad_direct_idx)
    #print(pad_name_idx)
    if 'INPUT' == pad_direct_idx:
        print_line.append('\tinput          pad_name_out,')
        #port_last_process(count, pad_ser, print_line)
        replace_pad_name(pad_info_index, pad_name_idx, print_line)
    elif 'OUTPUT' == pad_direct_idx:
        #print_line.append('\tinput          pad_name_oen,')
        print_line.append('\toutput         pad_name_in,')
        #port_last_process(count, pad_ser, print_line)
        replace_pad_name(pad_info_index, pad_name_idx, print_line)
    elif 'INOUT' == pad_direct_idx:
        print_line.append('\tinput          pad_name_out,')
        print_line.append('\tinput          pad_name_oen,')
        print_line.append('\toutput         pad_name_in,')
        #port_last_process(count, pad_ser, print_line)
        replace_pad_name(pad_info_index, pad_name_idx, print_line)
# }}}

def print_dont_touch_list(gen_filepath, pad_corpus, pad_info_index, filename) :# {{{
    fp = open(gen_filepath+filename.upper()+"_dontouch.txt", "w")
    print_line = []
    for pad_info in pad_corpus:
        if 'GPIO' == pad_info[pad_info_index["type"]]:
            if 'OUTPUT' != pad_info[pad_info_index["normal_attr"]]:
                #print_line.append("u_"+filename+"_top.u_"+filename+"_pin_mux.pad_name_in_dontouch_buf")
                print_line.append("u_"+filename+"_top/u_"+filename+"_pin_mux/pad_name_in_dontouch_buf")
                replace_pad_name(pad_info_index, pad_info, print_line)
        if 'GPI' == pad_info[pad_info_index["type"]]:
            if 'OUTPUT' != pad_info[pad_info_index["normal_attr"]]:
                #print_line.append("u_"+filename+"_top.u_"+filename+"_pin_mux.pad_name_in_dontouch_buf")
                print_line.append("u_"+filename+"_top/u_"+filename+"_pin_mux/pad_name_in_dontouch_buf")
                replace_pad_name(pad_info_index, pad_info, print_line)
        elif 'PINMUX' == pad_info[pad_info_index["type"]]:
            # function 0
            pad_dontouch_buffer_gen(filename, pad_info_index, pad_info, print_line, pad_info[pad_info_index["normal_attr"]],  pad_info[pad_info_index["normal_mode"]:],  'func0_pad_name')
            # function 1
            pad_dontouch_buffer_gen(filename, pad_info_index, pad_info, print_line, pad_info[pad_info_index["func1_attr"]],  pad_info[pad_info_index["func1"]:],  'func1_pad_name')
            # function 2
            pad_dontouch_buffer_gen(filename, pad_info_index, pad_info, print_line, pad_info[pad_info_index["func2_attr"]],  pad_info[pad_info_index["func2"]:],  'func2_pad_name')
            # function 3
            pad_dontouch_buffer_gen(filename, pad_info_index, pad_info, print_line, pad_info[pad_info_index["func3_attr"]], pad_info[pad_info_index["func3"]:], 'func3_pad_name')
    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')

    fp.close()
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

def io_sdc_gen(gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index, pad_info_index) :#{{{

    fp = open(gen_filepath+filename+".sdc", "w") 
    
    print_line = []

    print_line.append("")
    print_line.append("# "+filename+" constraint")
    #print_line.append("create_clock -name \""+filename+"_in_vclk\" -add -period 10 -waveform {0.0 5}")
    #print_line.append("create_clock -name \""+filename+"_out_vclk\" -add -period 10 -waveform {0.0 5}")

    for pad_info in pad_corpus :
        if pd.isna(pad_info[pad_info_index["nomal_input_clock"]]) == False :
            pad_clk_info = pad_info[pad_info_index["nomal_input_clock"]].split(',')
            #print(pad_clk_info)
            for i in range(0, len(pad_clk_info),2):
                if i == 0 :
                    pad_clk_name = pad_clk_info[0]
                    pad_clk_value = pad_clk_info[1]
                    print_line.append("set_input_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_input_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                else :
                    pad_clk_name = pad_clk_info[i-2]
                    pad_clk_value = pad_clk_info[i-1]
                    print_line.append("set_input_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_input_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
        if pd.isna(pad_info[pad_info_index["nomal_output_clock"]]) == False :
            pad_clk_info = pad_info[pad_info_index["nomal_output_clock"]].split(',')
            #print(pad_clk_info)
            for i in range(0, len(pad_clk_info),2):
                if i == 0 :
                    pad_clk_name = pad_clk_info[0]
                    pad_clk_value = pad_clk_info[1]
                    print_line.append("set_output_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_output_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                else :
                    pad_clk_name = pad_clk_info[i-2]
                    pad_clk_value = pad_clk_info[i-1]
                    print_line.append("set_output_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_output_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
        if pd.isna(pad_info[pad_info_index["func1_input_clock"]]) == False :
            pad_clk_info = pad_info[pad_info_index["func1_input_clock"]].split(',')
            #print(pad_clk_info)
            for i in range(0, len(pad_clk_info),2):
                if i == 0 :
                    pad_clk_name = pad_clk_info[0]
                    pad_clk_value = pad_clk_info[1]
                    print_line.append("set_input_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_input_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                else :
                    pad_clk_name = pad_clk_info[i-2]
                    pad_clk_value = pad_clk_info[i-1]
                    print_line.append("set_input_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_input_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
        if pd.isna(pad_info[pad_info_index["func1_output_clock"]]) == False :
            pad_clk_info = pad_info[pad_info_index["func1_output_clock"]].split(',')
            #print(pad_clk_info)
            for i in range(0, len(pad_clk_info),2):
                if i == 0 :
                    pad_clk_name = pad_clk_info[0]
                    pad_clk_value = pad_clk_info[1]
                    print_line.append("set_output_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_output_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                else :
                    pad_clk_name = pad_clk_info[i-2]
                    pad_clk_value = pad_clk_info[i-1]
                    print_line.append("set_output_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_output_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
        if pd.isna(pad_info[pad_info_index["func2_input_clock"]]) == False :
            pad_clk_info = pad_info[pad_info_index["func2_input_clock"]].split(',')
            #print(pad_clk_info)
            for i in range(0, len(pad_clk_info),2):
                if i == 0 :
                    pad_clk_name = pad_clk_info[0]
                    pad_clk_value = pad_clk_info[1]
                    print_line.append("set_input_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_input_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                else :
                    pad_clk_name = pad_clk_info[i-2]
                    pad_clk_value = pad_clk_info[i-1]
                    #print(pad_clk_info)
                    print_line.append("set_input_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_input_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
        if pd.isna(pad_info[pad_info_index["func2_output_clock"]]) == False :
            pad_clk_info = pad_info[pad_info_index["func2_output_clock"]].split(',')
            #print(pad_clk_info)
            for i in range(0, len(pad_clk_info),2):
                if i == 0 :
                    pad_clk_name = pad_clk_info[0]
                    pad_clk_value = pad_clk_info[1]
                    print_line.append("set_output_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_output_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                else :
                    pad_clk_name = pad_clk_info[i-2]
                    pad_clk_value = pad_clk_info[i-1]
                    print_line.append("set_output_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_output_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
        if pd.isna(pad_info[pad_info_index["func3_input_clock"]]) == False :
            pad_clk_info = pad_info[pad_info_index["func3_input_clock"]].split(',')
            #print(pad_clk_info)
            for i in range(0, len(pad_clk_info),2):
                if i == 0 :
                    pad_clk_name = pad_clk_info[0]
                    pad_clk_value = pad_clk_info[1]
                    print_line.append("set_input_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_input_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                else :
                    pad_clk_name = pad_clk_info[i-2]
                    pad_clk_value = pad_clk_info[i-1]
                    print_line.append("set_input_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_input_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
        if pd.isna(pad_info[pad_info_index["func3_output_clock"]]) == False :
            pad_clk_info = pad_info[pad_info_index["func3_output_clock"]].split(',')
            #print(pad_clk_info)
            for i in range(0, len(pad_clk_info),2):
                if i == 0 :
                    pad_clk_name = pad_clk_info[0]
                    pad_clk_value = pad_clk_info[1]
                    print_line.append("set_output_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_output_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                else :
                    pad_clk_name = pad_clk_info[i-2]
                    pad_clk_value = pad_clk_info[i-1]
                    print_line.append("set_output_delay "+pad_clk_value+"  -max -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
                    print_line.append("set_output_delay 0.0   -min -clock [get_clocks {"+pad_clk_name+"}]  [get_ports "+pad_info[0]+"] -add_delay")
    print_line.append("")

    for pad_info in pad_corpus :
        print_line.append("set_input_transition -max 2.000 [get_ports {"+pad_info[0]+"}]")
        print_line.append("set_input_transition -min 2.000 [get_ports {"+pad_info[0]+"}]")

    print_line.append("")

    for pad_info in pad_corpus :
        print_line.append("set_load -pin_load -max 30 [get_ports {"+pad_info[0]+"}]")
        print_line.append("set_load -pin_load -min 30 [get_ports {"+pad_info[0]+"}]")
    
    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.close()
#}}}

# help{{{
def help():
    print("############## help ####################")
    print("########################################")
    print("generate io_top wrap, io_ring, pin_mux, io_pad & pinmux regfile note")
    print("io_top_gen.py excel_path gen_path")
    print("generate io_top sdc")
    print("io_top_gen.py excel_path gen_path sdc_gen")
# }}}

def io_connet_check_csv(protocol, design_owner, pad_cell, pad_info_index, gen_filepath, filename, pad_corpus, pad_ser, pad_cell_index, design_hier) :#{{{ 
    fp = open(gen_filepath+filename+"_io_check.csv", "w") 
    print_line = []

    count = 0
    #for pad_info in pad_corpus:
    #    if 'PINMUX' == pad_info[pad_info_index["type"]] or 'GPIO' == pad_info[pad_info_index["type"]] or 'VREF' == pad_info[pad_info_index["type"]] or 'POC' == pad_info[pad_info_index["type"]]:
    #        if  "INNO_GPIO" == pad_info[pad_info_index["pad_cell_type"]]:
    #            continue
    #        elif "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
    #            print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_reg_vref_sel       ,pad_name0_reg_vref_sel[7:0]                ,W      ,output,  ")   
    #            print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_ctrl_"+pad_info[pad_info_index["pad_name"]].lower()+"_pad_name0_reg_vref_pd        ,pad_name0_reg_vref_pd                     ,W      ,output, ") 
    #            if pd.isna(pad_info[pad_info_index["io_domain"]]) == True :
    #                print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_name0_inno_poc_cell_pad_name0_inno_poc_cell_pwrok      ,pad_name0_inno_poc_cell_pwrok                     ,W      ,output, ")
    #            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name0')
    #        elif "POC" == pad_info[pad_info_index["type"]]:
    #            print_line.append("connect,"+filename.upper()+"_"+protocol+"_reg.pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_pad_name_ms                       ,pad_name_ms                     ,W      ,output, ")
    #            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
    #        else :
    #            for cell_info in pad_cell :
    #                cell_info_list = cell_info.split(",")
    #                cell_name = cell_info_list[0]
    #                if pad_info[pad_info_index["pad_cell_type"]] == cell_name :
    #                    cell_msc= str(cell_info_list[pad_cell_index["msc"]])

    #replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
    
    for pad_info in pad_corpus:
        if "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
            #if pd.isna(pad_info[pad_info_index["io_domain"]]) == False :
                #print_line.append("connect,u_pad_name_inno_poc_cell_pwrok_test_tdr_mux.func_in        ,"+pad_info[pad_info_index["io_domain"]]+"     ,W       ,input,")
            #    print_line.append(" CONNECTION," "u_pad_name_inno_poc_cell_pwrok_test_tdr_mux_func_in,"  +design_hier+".u_"+filename+"_top"+".u_pad_name_reg_vref_sel_test_tdr_mux,"        "func_in,"  " ,"   "1'b1" )
            #else :
                #print_line.append("connect,u_pad_name_inno_poc_cell_pwrok_test_tdr_mux.func_in    ,pad_name_inno_poc_cell_pwrok     ,W       ,input,")
            #     print_line.append(" CONNECTION," "u_pad_name_inno_poc_cell_pwrok_test_tdr_mux_func_in,"  +design_hier+".u_"+filename+"_top"+".u_pad_name_reg_vref_sel_test_tdr_mux,"        "func_in,"  +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"   "pad_name_inno_poc_cell_pwrok" )
            #print_line.append("connect,u_pad_name_inno_poc_cell_pwrok_test_tdr_mux.func_out       ,dft_pad_name_inno_poc_cell_pwrok ,W       ,output,")
            print_line.append("#inst_begin===========================================================================================================")
            print_line.append('#inst test_tdr_mux u_pad_name_inno_poc_cell_pwrok_test_tdr_mux')
            print_line.append("#    ^_^  ^00^ ^v^   POC_TDR")
            print_line.append("#inst_begin===========================================================================================================")
            print_line.append("#para_inst_begin")
            print_line.append("#para_inst_end")
            print_line.append("#port_inst_begin")
            print_line.append(" CONNECTION," "u_pad_name_inno_poc_cell_pwrok_test_tdr_mux_test_mode,"   
                                                        +design_hier+".u_"+filename+"_top"+".u_pad_name_inno_poc_cell_pwrok_test_tdr_mux,"      "test_mode,"  
                                                        +design_hier+".u_"+filename+"_top,"                                                     "test_mode" )
            if pd.isna(pad_info[pad_info_index["io_domain"]]) == False :
                print_line.append(" CONNECTION," "u_pad_name_inno_poc_cell_pwrok_test_tdr_mux_func_in,"   
                                                        +design_hier+".u_"+filename+"_top"+".u_pad_name_inno_poc_cell_pwrok_test_tdr_mux,"      "func_in,"  
                                                        ","                                                                                     +pad_info[pad_info_index["io_domain"]])
                #print_line.append("connect,u_pad_name_inno_poc_cell_pwrok_test_tdr_mux.func_in        ,"+pad_info[pad_info_index["io_domain"]]+"     ,W       ,input,")
            else :
                #print_line.append("connect,u_pad_name_inno_poc_cell_pwrok_test_tdr_mux.func_in    ,pad_name_inno_poc_cell_pwrok     ,W       ,input,")
                print_line.append(" CONNECTION," "u_pad_name_inno_poc_cell_pwrok_test_tdr_mux_func_in,"   
                                                        +design_hier+".u_"+filename+"_top"+".u_pad_name_inno_poc_cell_pwrok_test_tdr_mux,"      "func_in,"  
                                                        +design_hier+".u_"+filename+"_top"".u_"+filename.upper()+"_"+protocol+"_reg,"           "pad_name_inno_poc_cell_pad_name_inno_poc_cell_pwrok" )
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#port_inst_end")
            print_line.append("#inst_end============================================================================================================")
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#inst_begin===========================================================================================================")
            print_line.append('#inst INNO_POC_CELL u_pad_name_inno_poc_cell')
            print_line.append("#    ^_^  ^00^ ^v^   POC")
            print_line.append("#inst_begin===========================================================================================================")
            #print_line.append('connect,u_inno_poc_cell.PWROK     ,dft_pad_name_inno_poc_cell_pwrok       ,W       ,input,')
            print_line.append(" CONNECTION," "u_pad_name_inno_poc_cell_PWROK,"      +design_hier+".u_"+filename+"_top"+".u_pad_name_inno_poc_cell,"                         "PWROK,"  
                                                                                    +design_hier+".u_"+filename+"_top"+".u_pad_name_inno_poc_cell_pwrok_test_tdr_mux,"      "func_out" )
            #print_line.append(" CONNECTION," "u_pad_name_inno_poc_cell_PWROK,"      +design_hier+".u_"+filename+"_top"+".u_"+pad_info[pad_info_index["io_domain"]].lower()+"_inno_poc_cell,"                         "PWROK,"  
            #                                                                        +design_hier+".u_"+filename+"_top"+".u_"+pad_info[pad_info_index["io_domain"]].lower()+"_inno_poc_cell_pwrok_test_tdr_mux,"      "func_out" )
            #   TODO PWROKB_H
            #print_line.append('connect,u_inno_poc_cell.PWROKB_H  ,pad_name_pwrokb_h    ,W       ,output,')
            #print_line.append('connect,u_inno_poc_cell.VREF      ,pad_name_vref        ,W       ,input,')
            print_line.append(" CONNECTION," "u_pad_name_inno_poc_cell_VREF,"       +design_hier+".u_"+filename+"_top"+".u_pad_name_inno_poc_cell,"    "VREF,"  
                                                                                    +design_hier+".u_"+filename+"_top"+".u_pad_name_vref,"             "vref")
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#inst_end============================================================================================================")
            binary_string = list(reversed(list(bin(128)[2:])))

            print_line.append("#inst_begin===========================================================================================================")
            print_line.append('#inst test_tdr_mux u_pad_name_reg_vref_sel_test_tdr_mux')
            print_line.append("#    ^_^  ^00^ ^v^   VREF_SEL_TDR")
            print_line.append("#inst_begin===========================================================================================================")
            #print_line.append('connect,u_pad_name_reg_vref_sel_test_tdr_mux.test_mode      ,test_mode                 ,I       ,input,')
            print_line.append(" CONNECTION," "u_pad_name_reg_vref_sel_test_tdr_mux_test_mode,"  +design_hier+".u_"+filename+"_top"+".u_pad_name_reg_vref_sel_test_tdr_mux,"         "test_mode,"  
                                                                                                +design_hier+".u_"+filename+"_top,"                                                 "test_mode" )
            #print_line.append('connect,u_pad_name_reg_vref_sel_test_tdr_mux.func_in        ,pad_name_reg_vref_sel     ,W       ,input,')
            print_line.append(" CONNECTION," "u_pad_name_reg_vref_sel_test_tdr_mux_func_in,"    +design_hier+".u_"+filename+"_top"+".u_pad_name_reg_vref_sel_test_tdr_mux,"         "func_in,"  
                                                                                                +design_hier+".u_"+filename+"_top"".u_"+filename.upper()+"_"+protocol+"_reg,"       "pad_ctrl_pad_name_pad_name_reg_vref_sel")
            #   TODO func_out
            #print_line.append('connect,u_pad_name_reg_vref_sel_test_tdr_mux.func_out       ,dft_pad_name_reg_vref_sel[7:0] ,W       ,output,')
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#inst_end============================================================================================================")


            print_line.append("#inst_begin===========================================================================================================")
            print_line.append('#inst test_tdr_mux u_pad_name_reg_vref_pd_test_tdr_mux')
            print_line.append("#    ^_^  ^00^ ^v^   VREF_PD_TDR")
            print_line.append("#inst_begin===========================================================================================================")
            #print_line.append('connect,u_pad_name_reg_vref_pd_test_tdr_mux.test_mode      ,test_mode                ,I       ,input,')
            print_line.append(" CONNECTION," "u_pad_name_reg_vref_pd_test_tdr_mux_test_mode,"   +design_hier+".u_"+filename+"_top"+".u_pad_name_reg_vref_pd_test_tdr_mux,"      "test_mode,"  
                                                                                                +design_hier+".u_"+filename+"_top,"                                             "test_mode" )
            #print_line.append('connect,u_pad_name_reg_vref_pd_test_tdr_mux.func_in        ,pad_name_reg_vref_pd     ,W       ,input,')
            print_line.append(" CONNECTION," "u_pad_name_reg_vref_pd_test_tdr_mux_func_in,"     +design_hier+".u_"+filename+"_top"+".u_pad_name_reg_vref_pd_test_tdr_mux,"      "func_in,"  
                                                                                                +design_hier+".u_"+filename+"_top"".u_"+filename.upper()+"_"+protocol+"_reg,"   "pad_ctrl_pad_name_pad_name_reg_vref_pd")
            #   TODO func_out
            #print_line.append('connect,u_pad_name_reg_vref_pd_test_tdr_mux.func_out       ,dft_pad_name_reg_vref_pd ,W       ,output,')
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#inst_end============================================================================================================")

            print_line.append("#    inst_begin===========================================================================================================")
            print_line.append("#    inst "+pad_info[pad_info_index["pad_cell_type"]].lower()+"_model u_pad_name_vref")
            print_line.append("#    ^_^  ^00^ ^v^   VREF    ")
            print_line.append("#    inst_begin===========================================================================================================")
            #print_line.append("connect,u_inno_poc_cell.reg_vref_sel    ,dft_pad_name_reg_vref_sel[7:0]   ,W       ,input,")
            #print_line.append("connect,u_inno_poc_cell.reg_vref_pd     ,dft_pad_name_reg_vref_pd    ,W       ,input,")
            #print_line.append("connect,u_inno_poc_cell.pwrokb_h        ,pad_name_pwrokb_h       ,W       ,input,")
            print_line.append(" CONNECTION," "u_pad_name_sel,"              +design_hier+".u_"+filename+"_top"+".u_pad_name_vref,"                          "reg_vref_sel,"
                                                                            +design_hier+".u_"+filename+"_top"+".u_pad_name_reg_vref_sel_test_tdr_mux,"     "func_out")
            print_line.append(" CONNECTION," "u_pad_name_pd,"               +design_hier+".u_"+filename+"_top"+".u_pad_name_vref,"                          "reg_vref_pd,"
                                                                            +design_hier+".u_"+filename+"_top"+".u_pad_name_reg_vref_pd_test_tdr_mux,"      "func_out")
            print_line.append(" CONNECTION," "u_pad_name_vref_pwrokb_h,"    +design_hier+".u_"+filename+"_top"+".u_pad_name_vref,"                          "pwrokb_h,"
                                                                            +design_hier+".u_"+filename+"_top"+".u_pad_name_inno_poc_cell,"                 "PWROKB_H") 
            #print_line.append("connect,u_inno_poc_cell.vref            ,pad_name_vref           ,W       ,output,")
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)   
            print_line.append("#inst_end============================================================================================================")
    

        if "POC" == pad_info[pad_info_index["type"]]:
            print_line.append("#    inst_begin===========================================================================================================")
            print_line.append("#    inst test_tdr_mux u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_test_tdr_mux")
            print_line.append("#    ^_^  ^00^ ^v^ +++++++++  check test_mode,ms     ")
            print_line.append("#    inst_begin===========================================================================================================")            
            print_line.append(" CONNECTION," "u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_test_tdr_mux_test_mode,"  +design_hier+".u_"+filename+"_top"+".u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_test_tdr_mux,"       "test_mode,"    +design_hier+   ",test_mode")
            print_line.append(" CONNECTION," "u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_test_tdr_mux_func_in,"       +design_hier+".u_"+filename+"_top"+".u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_test_tdr_mux,"        "func_in,"     
                                                                                                                                    +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"   "pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_pad_name_ms")
            print_line.append(" CONNECTION," "u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_test_tdr_mux_func_out,"      +design_hier+".u_"+filename+"_top"+".u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_test_tdr_mux,"        "func_out,"     
                                                                                                                                    +design_hier+".u_"+filename+"_top"+".u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+   ",MS")
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            
            print_line.append("#inst_end============================================================================================================")

            print_line.append("#    inst_begin===========================================================================================================")
            print_line.append("#    inst u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]])
            print_line.append("#    ^_^  ^00^ ^v^ +++++++++     check POC MS     ")
            print_line.append("#    inst_begin===========================================================================================================")
            #print_line.append("connect,u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+".MS       ,dft_pad_name_ms     ,W       ,input,")
            print_line.append(" CONNECTION," "u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_MS,"     +design_hier+".u_"+filename+"_top"+".u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+","                 "MS,"
                                                                                                                +design_hier+".u_"+filename+"_top"+".u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+"_test_tdr_mux,"    "func_out,")
            #print_line.append("connect,u_pad_name_"+pad_info[pad_info_index["pad_cell_type"]]+".MSC      ,pad_name_msc        ,W       ,output,")
            replace_pad_name(pad_info_index, pad_info, print_line, 'pad_name')
            print_line.append("#inst_end============================================================================================================")


    print_line.append("#    inst_begin===========================================================================================================")
    print_line.append('#    inst '+filename+'_pin_mux u_'+filename+'_pin_mux')
    print_line.append("#    ^_^  ^00^ ^v^               check none")
    print_line.append("#    inst_begin===========================================================================================================")
    print_line.append("#    inst_end============================================================================================================")
 
    print_line.append("#    inst_begin===========================================================================================================")
    print_line.append('#    inst ' 'io_ring'                            )
    print_line.append("#    ^_^  ^00^ ^v^ +++++++++     check vref,pwrpkb_h,msc")
    print_line.append('#    inst '+filename+'_ring u_'+filename+'_ring' )
    print_line.append("#    inst_begin===========================================================================================================")
    count = 0
    # TESTMODE
    print_line.append(" CONNECTION," +filename+"_ring_test_mode,"  +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"       "test_mode,"  +design_hier+".u_"+filename+"_top,"   "test_mode" )
    for pad_info in pad_corpus:
        count += 1  
        if 'ANALOG' == pad_info[pad_info_index["type"]]:
            continue
        elif "POC" == pad_info[pad_info_index["type"]]:
            continue
        elif "INNO_VREF" == pad_info[pad_info_index["pad_cell_type"]]:
            continue
        #    print_line.append('connect,'+filename+'_ring.pad_name_reg_vref_sel          ,pad_name_reg_vref_sel[7:0]  ,W   ,input,')
        #    print_line.append('connect,'+filename+'_ring.pad_name_reg_vref_pd           ,pad_name_reg_vref_pd        ,W   ,input,')
        #    print_line.append('connect,'+filename+'_ring.pad_name_pwrokb_h              ,pwrokb_h        ,W   ,input,')
        #    print_line.append('connect,'+filename+'_ring.vref              ,vref        ,W   ,output,')
        #    replace_pad_name(pad_info_index, pad_info, print_line)
        #    replace_PAD_NAME(pad_info_index, pad_info, print_line)
        elif  "INNO_GPIO" == pad_info[pad_info_index["pad_cell_type"]]:
            print_line.append(" CONNECTION,"    "u_"+filename+"_ring_PAD_NAME,"                 +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"      "PAD_NAME," 
                                                                                                +design_hier+".u_"+filename+"_top,"                             "PAD_NAME")
            if 'PINMUX' == pad_info[pad_info_index["type"]] :
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_drvpd,"       +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_drvpd,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name0_pad_name_drvpd")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_drvpu,"       +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_drvpu,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name0_pad_name_drvpu")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_idelay,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_idelay,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name0_pad_name_idelay")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_odelay,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_odelay,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name0_pad_name_odelay")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_ie,"          +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_ie,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name1_pad_name_ie")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_fben,"        +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_fben,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name1_pad_name_fben")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_fbsel,"       +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_fbsel,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name1_pad_name_fbsel")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_odten,"       +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_odten,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name1_pad_name_odten")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_odtpd,"       +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_odtpd,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name1_pad_name_odtpd")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_odtpu,"       +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_odtpu,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name1_pad_name_odtpu")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_slew,"        +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_slew,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name1_pad_name_slew")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_smit_rxmode," +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_smit_rxmode,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name1_pad_name_smit_rxmode")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_weakpd,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_weakpd,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name1_pad_name_weakpd")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_weakpu,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_weakpu,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"                              "pad_ctrl_pad_name1_pad_name_weakpu")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_vref,"        +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_vref,"       
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+pad_info[pad_info_index["io_domain"]].lower()+"_vref,"             "vref")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_pwrokb_h,"    +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_pwrokb_h,"   
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+pad_info[pad_info_index["io_domain"]].lower()+"_inno_poc_cell,"    "PWROKB_H")
            elif 'GPI' == pad_info[pad_info_index["type"]] :
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_oe_n,"        +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_oe_n,"         " "     ",1'b0")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_idelay,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_idelay,"       " "     ",6'b0")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_odelay,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_odelay,"       " "     ",6'b0")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_ie,"          +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_ie,"           " "     ",1'b1")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_fben,"        +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_fben,"         " "     ",1'b0")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_fbsel,"       +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_fbsel,"        " "     ",1'b0")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_odten,"       +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_odten,"        " "     ",1'b0")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_odtpu,"       +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_odtpu,"        " "     ",4'b0")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_odtpd,"       +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_odtpd,"        " "     ",4'b0")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_slew,"        +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_slew,"         " "     ",5'b0")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_drvpd,"       +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_drvpd,"        " "     ","+pad_info[pad_info_index["drv"]])
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_drvpu,"       +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_drvpu,"        " "     ","+pad_info[pad_info_index["drv"]])
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_smit_rxmode," +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_smit_rxmode,"  " "     ","+pad_info[pad_info_index["rx_smit"]])
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_weakpd,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_weakpd,"       " "     ","+pad_info[pad_info_index["pd"]])
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_weakpu,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_weakpu,"       " "     ","+pad_info[pad_info_index["pu"]])
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_vref,"        +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_vref,"       
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+pad_info[pad_info_index["io_domain"]].lower()+"_vref,"             "vref")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_pwrokb_h,"    +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                                                  "pad_name_pwrokb_h,"   
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+pad_info[pad_info_index["io_domain"]].lower()+"_inno_poc_cell,"    "PWROKB_H")
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
        else :
            print_line.append(" CONNECTION,"    "u_"+filename+"_ring_PAD_NAME,"                 +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"      "PAD_NAME," 
                                                                                                +design_hier+".u_"+filename+"_top,"                             "PAD_NAME")
            cell_ds_msb = 0
            cell_st = 0
            cell_sl = 0
            cell_msc = 0
            cell_ps = 0
            cell_he = 0
            cell_pe = 0
            for cell_info in pad_cell :
                cell_info_list = cell_info.split(",")
                cell_name = cell_info_list[0]
                if pad_info[pad_info_index["pad_cell_type"]] == cell_name :
                    cell_ds = str(cell_info_list[pad_cell_index["ds"]])
                    cell_st = str(cell_info_list[pad_cell_index["st"]])
                    cell_sl = str(cell_info_list[pad_cell_index["sl"]])
                    cell_msc= str(cell_info_list[pad_cell_index["msc"]])
                    cell_ps = str(cell_info_list[pad_cell_index["ps"]])
                    cell_he = str(cell_info_list[pad_cell_index["he"]])
                    cell_pe = str(cell_info_list[pad_cell_index["pe"]])
                    if "[" in cell_ds :
                        cell_ds_list = cell_ds.split("[", 1)
                        cell_ds_width_list = cell_ds_list[1].split(":", 1)
                        cell_ds_msb = cell_ds_width_list[0]
                    if "[" in cell_st :
                        cell_st_list = cell_st.split("[", 1)
                        cell_st_width_list = cell_st_list[1].split(":", 1)
                        cell_st_msb = cell_st_width_list[0]            
            #print(pad_info)
            #print_line.append('connect,'+filename+'_ring.PAD_NAME       ,PAD_NAME         ,IO      ,inout,')
            if 'PINMUX' == pad_info[pad_info_index["type"]] :
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_ie,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                              "pad_name_ie,"        
                                                                                            +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"          "pad_ctrl_pad_name_pad_name_ie")
                print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_ds,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                              "pad_name_ds,"        
                                                                                            +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"          "pad_ctrl_pad_name_pad_name_ds")
                if cell_st != "nan" :
                    print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_st,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                          "pad_name_st,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"      "pad_ctrl_pad_name_pad_name_st")
                if cell_sl != "nan" :
                    print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_sl,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                          "pad_name_sl,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"      "pad_ctrl_pad_name_pad_name_sl")
                if cell_msc != "nan" :
                    print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_msc,"     +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                          "pad_name_msc,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+pad_info[pad_info_index["io_domain"]].lower()+"_"+pad_info[pad_info_index["pad_cell_type"]]+   ",MSC")
                    replace_char_in_strings(print_line,'PRWHSWCDGSD_H','PVDD18POCSD_H')
                    replace_char_in_strings(print_line,'PRWHSWCDGSD_V','PVDD18POCSD_V')
                    replace_char_in_strings(print_line,'PRWHSWCDGSIM_H','PVDD18POCSD_H')
                    replace_char_in_strings(print_line,'PRWHSWCDGSIM_V','PVDD18POCSD_V')
                if cell_ps != "nan" :
                    print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_ps,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                          "pad_name_ps,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"      "pad_ctrl_pad_name_pad_name_ps")
                else :
                    print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_pu,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                          "pad_name_pu,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"      "pad_ctrl_pad_name_pad_name_pu")
                    print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_pd,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                          "pad_name_pd,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"      "pad_ctrl_pad_name_pad_name_pd")
                if cell_he != "nan" :
                    print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_he,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                          "pad_name_he,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"      "pad_ctrl_pad_name_pad_name_he")
                if cell_pe != "nan" :
                    print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_pe,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"                          "pad_name_pe,"        
                                                                                                +design_hier+".u_"+filename+"_top"+".u_"+filename.upper()+"_"+protocol+"_reg,"      "pad_ctrl_pad_name_pad_name_pe")
            else :
                if 'GPI' == pad_info[pad_info_index["type"]] :
                    print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_oe_n,"    +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_oe_n,"         " "   ",1'b1")
                    print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_ie,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_ie,"           " "   ",1'b1")
                elif 'GPO' == pad_info[pad_info_index["type"]] :
                    print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_oe_n,"    +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_oe_n,"         " "   ",1'b0")
                    print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_ie,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_ie,"           " "   ",1'b0")
                else :
                    if cell_st != "nan" :
                        print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_st,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_st,"           " "   ",2'b0")
                    if cell_sl != "nan" :
                        print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_sl,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_sl,"           " "   ",1'b0")
                    if cell_msc != "nan" :
                        print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_msc,"     +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_msc,"          " "   ",1'b0")
                    if cell_ps != "nan" :
                        if pad_info[pad_info_index["pu"]] == "1'b1" :
                            print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_ps,"  +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_ps,"           " "   ",1'b1")
                        else :
                            print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_ps,"  +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_ps,"           " "   ",1'b0")
                    if cell_he != "nan" :
                        print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_he,"      +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_he,"           " "   ",1'b0")
                    if cell_pe != "nan" :
                        if pad_info[pad_info_index["pu"]] == "1'b1" or pad_info[pad_info_index["pd"]] == "1'b1" :
                            print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_pe,"  +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_pe,"           " "   ",1'b1")
                        else :
                            print_line.append(" CONNECTION,"    "u_"+filename+"_ring_pad_name_pe,"  +design_hier+".u_"+filename+"_top"+".u_"+filename+"_ring,"     "pad_name_pe,"           " "   ",1'b0")
            replace_pad_name(pad_info_index, pad_info, print_line)
            replace_PAD_NAME(pad_info_index, pad_info, print_line)
            replace_slash_with_dot(print_line)


    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    #fp.write('\n')
    #fp.write('endmodule')

    fp.close()

# }}}

if __name__ == "__main__":
    main()


