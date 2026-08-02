#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import logging
import logging.handlers as loghandlers
import logging.config as logconfig
from optparse import OptionParser
import os
import shutil
import sys
import re
import csv
import time
import copy
import collections

#--------------------------------------------------------------------
#  generate v|sv from csv
#--------------------------------------------------------------------
def parseAssign(fileName):

    with open(fileName,'r') as fr:

        lines = fr.readlines()
        assignInputList = []
        assignOutputList = []

        while lines:
            line = lines.pop(0)
            strTest = ""
            if "assign" in line and ";" in line and "//" not in line:
                strTest += line
            elif "assign" in line and "//" not in line: 
                strTest += line
                line = lines.pop(0)
                while ";" not in line:
                    strTest += line
                    line = lines.pop(0)
                strTest += line
            else:
                pass

            if strTest:
                logging.debug(f"strTest = {strTest}\n")
                matchStr = re.compile(r'[A-Za-z]+[A-Za-z_0-9.]*')
                resList = matchStr.findall(strTest)
                logging.debug(f"resList = {resList}\n")
                if resList:
                    assignInputList.append(resList[1])
                    for i in range(2,len(resList)):
                        assignOutputList.append(resList[i])

        return assignInputList,assignOutputList

def compare_width(width0,width1):
    value1 = 0
    value0 = 0
    flag =  True

    if width0 == "" or width1 == "":
        return flag

    matchStr = re.compile(r'\[(\d)?:?(\d)?\]')
    result1 = matchStr.search(width1).groups()
    result0 = matchStr.search(width0).groups()
    logging.debug(f"width0 result0 = {result0}")
    logging.debug(f"width1 result1 = {result1}")

    if result1:
        if result1[0] == result1[1]:
            value1 = result1[0]
        elif result1[1] == None:
            value1 = result1[0]
        else:
            flag = False
            logging.debug("The {} is not correct format".format(width1))

    else:
        flag = False
        logging.debug("The {} is not correct format".format(width1))

    if result0:
        if result0[0] == result0[1]:
            value0 = result0[0]
        elif result0[1] == None:
            value0 = result0[0]
        else:

            flag = False
            logging.debug("The {} is not correct format".format(width0))
    else:
        flag = False
        logging.debug("The {} is not correct format".format(width0))

    if value0 == value1 and flag == True:
        flag = True
    else:
        flag = False

    return flag

def get_parameter():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--input",  help="input directory", default="nr_top_out.csv")
    parser.add_argument("-o","--output", help="output directory", default="out.v")

    args = parser.parse_args()

    rfile = args.input
    wfile = args.output
    return (rfile, wfile)

def deal_with_error(file):
    srcFile = file.replace('.csv','_bakup.csv')
    shutil.copyfile(srcFile,file)

    exit()

def port_in_list(item,listPort):
    signalFlag = False

    for j in range(0,len(listPort)):
        if item.strip() == listPort[j]:
            signalFlag = True
            break
    return signalFlag

def read_csv_base(type,fileName,inst_name=""):
    linelist = []
    flag = 0
    keyword_begin = "deadbeef"
    keyword_end = "deafbeef"
    if type == "inst":
        keyword_begin = "#inst_begin"
        keyword_end = "#inst_end"

    if type == "para":
        keyword_begin = "#parameter_begin"
        keyword_end = "#parameter_end"

    if type == "order":
        keyword_begin = "#order_begin"
        keyword_end = "#order_end"

        # self.logging.info("generate the para code")
    if type == "port":
        keyword_begin = "#port_begin"
        keyword_end = "#port_end"

    if type == "before_port":    
        keyword_begin = "#keep_begin before_port"
        keyword_end = "#keep_end before_port"
        
    if type == "inc":
        keyword_begin = "#include_begin"
        keyword_end = "#include_end"

    if type == "keep":
        keyword_begin = "keep_begin"
        keyword_end = "keep_end"

    if type == "before_module":
        keyword_begin = "#keep_begin before_module"
        keyword_end = "#keep_end before_module"

    if type == "after_module":
        keyword_begin = "#keep_begin after_module"
        keyword_end = "#keep_end after_module"

    if type == "before_bracket":
        keyword_begin = "#keep_begin before_bracket"
        keyword_end = "#keep_end before_bracket"

    if type == "after_bracket":
        keyword_begin = "#keep_begin after_bracket"
        keyword_end = "#keep_end after_bracket"

    if type == "before_parameter":
        keyword_begin = "#keep_begin before_parameter"
        keyword_end = "#keep_end before_parameter"

    if type == "after_parameter":
        keyword_begin = "#keep_begin after_parameter"
        keyword_end = "keep_end after_parameter"

    if type == "before_wire_reg":
        keyword_begin = "keep_begin before_wire_reg"
        keyword_end = "#keep_end before_wire_reg"

    if type == "after_wire_reg":
        keyword_begin = "#keep_begin after_wire_reg"
        keyword_end = "#keep_end after_wire_reg"

    if type == "before_modport":
        keyword_begin = "#keep_begin before_modport"
        keyword_end = "#keep_end before_modport"

    if type == "after_modport":
        keyword_begin = "#keep_begin after_modport"
        keyword_end = "#keep_end after_modport"

    if type == "before_endmodule":
        keyword_begin = "#keep_begin before_endmodule"
        keyword_end = "#keep_end before_endmodule"

    if type == "after_endmodule":
        keyword_begin = "#keep_begin after_endmodule"
        keyword_end = "#keep_end after_endmodule"

    if type == "keep_inst_before":
        keyword_begin = f"#keep_begin before_inst_{inst_name}"
        keyword_end = f"#keep_end before_inst_{inst_name}"

    if type == "keep_inst_after":
        keyword_begin = f"#keep_begin after_inst_{inst_name}"
        keyword_end = f"#keep_end after_inst_{inst_name}"

    if type == "gen_type":
        keyword_begin = "#gen_type_begin"
        keyword_end = "#gen_type_end"

    if type == "author":
        keyword_begin = "#author_begin"
        keyword_end = "#author_end"

    with open(fileName, "r") as fr:
        for line in fr:

            if type == "modu":
                if line.startswith("module") or line.startswith("class"):

                    return (line.replace(',',' ').strip())

            if keyword_begin in line.strip():

                flag = 1
                continue

            if keyword_end in line.strip():
                flag = 0

                continue

            if flag == 1:
                # if type == "keep":
                #     linelist.append(line)
                # else:
                linelist.append(line.strip())

    return (linelist)

def read_all_keep_info(fileName,inst_list):

    keyword_list = [ "before_module","after_module","before_port","before_bracket","after_bracket","before_parameter","after_parameter","before_wire_reg","after_wire_reg","before_modport",\
                    "after_modport","keep_inst_before","keep_inst_after","before_endmodule","after_endmodule" ]

    dictKeyWord = {}
    dict_keep_before_inst = {}
    dict_keep_after_inst = {}
    
    logging.debug(f"inst_list = {inst_list}")

    for keyword in keyword_list:

        dictKeyWord[keyword] = read_csv_base(keyword,fileName)

        if keyword == "keep_inst_before":
            
            for inst_name in inst_list:
                inst_keep_list = read_csv_base(keyword,fileName,inst_name)
                dict_keep_before_inst[inst_name] = inst_keep_list

            dictKeyWord[keyword] = dict_keep_before_inst

        if keyword == "keep_inst_after":

            for inst_name in inst_list:
                inst_keep_list = read_csv_base(keyword,fileName,inst_name)
                dict_keep_after_inst[inst_name] = inst_keep_list
                
            dictKeyWord[keyword] = dict_keep_after_inst

    logging.debug(f"dictKeyWord = {dictKeyWord}")

    return dictKeyWord

def read_list_content(tempList):
    tmp_content = ""
    for item in tempList:
        tmp_content += item+"\n"

    return tmp_content
    
def deal_with_port_str(line):

    # lineStr = line.replace(' ','')
    line = line.strip()
    tempList = []

    if '{' in line and '}' in line:
        if '"' in line:
            line = line.replace('"',' ')

        match_parameter = re.compile(r'[{](.*)[}]', re.S)
        width = '{' + match_parameter.findall(line)[0] + '}'
        line = line.replace(width,'')

        if len(line.split(',')) == 6:
            tempList = line.split(',')

            connect, port_name, signal_name, attr, direction,checkValue = tempList
        else:
            logging.debug(f"The format {line} is wrong")
            exit()

        signal_name = signal_name.strip() + width + ' '*(len(signal_name)-len(signal_name.strip()))
        logging.debug(f"{connect},port_name = {port_name},signal_name = {signal_name},attr = {attr},direction = {direction},checkValue = {checkValue}")

    else:
        if len(line.split(',')) == 6:
            tempList = line.split(',')
            connect, port_name, signal_name, attr, direction,checkValue = tempList
            logging.debug(f"{connect},port_name = {port_name},signal_name = {signal_name},attr = {attr},direction = {direction},checkValue = {checkValue}")
        else:
            logging.debug(f"The format {line} is wrong")
            exit()


    return connect, port_name, signal_name, attr, direction,checkValue

class topVerilogGenerator():
    '''
    '''
    def __init__(self, rfile, wfile,logging):
        self.rfilename = rfile
        self.wfilename = wfile
        self.content = ""
        self.wire_list = []
        self.input_list = []
        self.output_list = []
        self.inout_list = []
        self.modport_list = []
        self.interface_list = []
        self.logging = logging
        self.keepDict = {}
        self.logging.info("generate the v code")

    def write_file(self,fileType="null"):
        
        if '/' in self.wfilename and not './' in self.wfilename:
            self.wfilename = os.path.dirname(self.wfilename) + os.sep + os.path.basename(self.wfilename).split('.')[0] + '.' + fileType
        else:
            self.wfilename = os.path.basename(self.wfilename).split('.')[0] + '.' + fileType

        with open(self.wfilename, "w") as fw:
            fw.write(self.content)

        self.logging.info("{} Generated!".format(self.wfilename))
        print("Info: {} Generated!".format(self.wfilename))


    def read_csv_data(self):
        linelist = []
        signal_value = ""
        with open(self.rfilename, "r") as fr:
            lines = fr.readlines()

            for line in lines:
                if line.startswith('connect') and (',IF' in line or ',if' in line):
                    _, port_name, signal_name, attr, direction,checkValue = line.split(',')

                    signal_value = signal_name.strip()

                    self.logging.debug(f"line = {line},signal_name = {signal_name},signal_value= {signal_value}")
                    data = "{},{},{}".format(direction.strip()," ",signal_value)
                    linelist.append(data)

        return list(set(linelist))

    def gen_header(self,topFile,authorName):
        fileName = os.path.basename(topFile)
        modName =  fileName.split('.')[0]

        # // =================================================================================================
        # // File Name    : {TOPFILE:<8}
        # // Module       : {MOD}
        # // Function     : {MOD} integration
        # // Type         : RTL
        # // -------------------------------------------------------------------------------------------------

        tmp_content = '''\
// =================================================================================================
// Copyright(C) 2020 - Cygnusemi Co.,Ltd. All rights reserved.                                    
// =================================================================================================
// Powered by Gang He, Shuwei Xuan, Cuiping Zhou, etc.
// =================================================================================================
// File Name    : {TOPFILE}
// Module       : {MOD}
// Function     : {MOD} integration
// Type         : RTL
// -------------------------------------------------------------------------------------------------
// Update History :
// -------------------------------------------------------------------------------------------------
// Rev.Level    Date                  Coded by                Contents
// 1.0          {DATE:<20}      {USERNAME:<8}           {CONTENTS:>8}
//
// =================================================================================================
// End Revision
// =================================================================================================

// =================================================================================================
// RTL Header
// =================================================================================================
'''.format(TOPFILE=fileName,MOD=modName,DATE=time.strftime("%Y-%m-%d %H:%M:%S"), USERNAME=authorName, CONTENTS="Init")
        return (tmp_content)

    def gen_include(self):
        tmp_content = ""
        inc_list = read_csv_base("inc",self.rfilename)
        for item in inc_list:
            tmp_content += item+"\n"
        tmp_content += "\n"
        self.logging.info(f"gen_include----{tmp_content}")
        return (tmp_content)

    def gen_module(self):
        self.logging.info(f"gen_module start")
        modulename = read_csv_base("modu",self.rfilename)
        self.logging.info(f"gen_module---{modulename}")
        return (modulename + "(\n")

    def gen_parameter(self):
        tmp_content = ""
        para_list = read_csv_base("para",self.rfilename)
        self.logging.info(f"para list : {para_list}")

        if len(para_list)==0:
            tmp_content += "(\n"
        else:
            tmp_content += "#(\n"
            for line in para_list:
                self.logging.info(f"para list content = {line}")
                if "`" in line:
                    segStr = line
                else:
                    if line == para_list[-1]:
                        segStr = line.strip().split(',')[1]
                    else:
                        segStr = line.split(',')[1]

                segLen = len(segStr)
                replaceStr = " "*(20-segLen) + "= "
                if line == para_list[-1]:
                    tmp_content += "{}\n".format(line.replace(","," "*4,1).replace(",",replaceStr,1))
                else:
                    tmp_content += "{},\n".format(line.replace(","," "*4,1).replace(",",replaceStr,1))
            tmp_content += ")\n"
            tmp_content += "(\n"
        return (tmp_content)

    def gen_port(self,keepPortList):
        self.tmp_content = ""
        port_list = read_csv_base("port",self.rfilename)
        input_list = []
        output_list = []
        inout_list = []

        interface_list = self.read_csv_data()
        self.logging.debug(f"interface_list = {interface_list}")

        for line in keepPortList:
            input_list.append(line)

        for line in sorted(set(interface_list),key=interface_list.index):
            input_list.append(line)

        for line in port_list:
            if "input" in line:
                input_list.append(line)

        for line in port_list:
            if "output" in line:
                output_list.append(line)

        for line in port_list:
            if "inout" in line:
                inout_list.append(line)

        ############# write top port to csv file ###########################
        orderFlag = read_csv_base("order",self.rfilename)
        self.logging.info(f"orderFlag = {orderFlag}")

        if os.path.dirname(self.rfilename):
            port_info_csv = os.path.dirname(self.rfilename) + os.sep + "port_info_" + os.path.basename(self.rfilename)
            port_info_bak_csv = os.path.dirname(self.rfilename) + os.sep + "port_info_bak_" + os.path.basename(self.rfilename)
        else:
            port_info_csv = "port_info_" + os.path.basename(self.rfilename)
            port_info_bak_csv = "port_info_bak_" + os.path.basename(self.rfilename)

        self.port_info = []
        self.port_info_old = []
        allPortList = []
        portDict = {}
        flag = False

        if os.path.exists(port_info_csv):
            with open(port_info_csv,'r') as fr:
                lines = fr.readlines()
                lines.pop(0)
                for line in lines:
                    self.port_info_old.append(line)

            for line in input_list:
                port_name = line.split(",")[-1]
                self.port_info.append(port_name)
                allPortList.append(line)
                portDict[port_name] = line

            for line in output_list:
                port_name = line.split(",")[-1]
                self.port_info.append(port_name)
                allPortList.append(line)
                portDict[port_name] = line

            for line in inout_list:
                port_name = line.split(",")[-1]
                self.port_info.append(port_name)
                allPortList.append(line)
                portDict[port_name] = line


            if orderFlag[0].strip() == "False":
                portTypeList = ["BUS","CRG","PMU","INT","DFT","SYSCON","FUNC","PAD"]
            else:
                portTypeList = ["PAD"]

            self.topContent = []

            self.logging.info(f"self.port_info = {self.port_info}")
            self.logging.info(f"self.port_info_old = {self.port_info_old}")
            
            for portType in portTypeList:
                tempList = [value for key,value in portDict.items() if self.getPortType(key,portType)]
                tempSubList = [item for item in self.port_info_old if self.equPortType(portType,item)]
                self.logging.info(f"portType:testlist = {portType}:{tempList}")
                self.tmp_content += f"    //{portType} port definition as below\n"
                subPortType = []
                for tempLine in tempSubList:
                    if 3 == len(tempLine.strip().split(',')):
                    	subPortType.append(tempLine.strip().split(',')[2])

                subPortType =  sorted(list(set(subPortType)))
                self.logging.info(f"portType:subPortType = {portType}: {subPortType}")

                ## subType is null
                if not subPortType:
                    if tempList:
                        for tempLine in tempList:
                            self.topContent.append(tempLine.strip().split(',')[-1] + ',' + portType + ',' + "fix_me")
                            self.getPortOrder(tempLine,portType,"fix_me",flag)
                        self.logging.info(f"tempList = {tempList}")

                elif subPortType[0]:
                    for subType in subPortType:
                        if "_" in subType:
                            self.tmp_content += f"    //{subType.split('_')[1]} {portType} port definition as below \n"
                        else:
                            self.tmp_content += f"    //{subType} port definition as below \n"

                        tempSubTypeList = [value for key,value in portDict.items() if self.getPortSubType(key,portType,subType)]
                        for tempLine in tempSubTypeList:
                            self.getPortOrder(tempLine,portType,subType,flag)
                            tempList.remove(tempLine)

                    for tempLine in tempList:
                        self.topContent.append(tempLine.strip().split(',')[-1] + ',' + portType + ',' + "fix_me")
                    self.logging.info(f"tempList = {tempList}")

                else:
                    subType = "fix_me"
                    self.logging.info(f"tempList1 = {tempList}")

                    for tempLine in tempList:
                        self.getPortOrder(tempLine,portType,subType,flag)


            self.logging.info(f"self.port_info = {self.port_info}")
            for tempLine in self.port_info:
                # self.topContent.append(tempLine.strip().split(',')[-1] + ',' + "fix_me")
                self.getPortOrder(portDict[tempLine.strip().split(',')[-1]],"fix_me","fix_me",flag)

            with open(port_info_bak_csv,'w') as fw:
                fw.write("portName,portType,sub"+"\n")
                for item in self.topContent:
                    fw.write(item + "\n")

            shutil.copyfile(port_info_bak_csv,port_info_csv)
            os.remove(port_info_bak_csv)
        
        else:
            print(f"Warining,Please check the {port_info_csv}!")
            port_info = []
            for line in input_list:
                port_name = line.split(",")[-1]
                port_info.append(port_name+'\n')

            for line in output_list:
                port_name = line.split(",")[-1]
                port_info.append(port_name+'\n')

            for line in inout_list:
                port_name = line.split(",")[-1]
                port_info.append(port_name+'\n') 

            with open(port_info_csv,'w') as fw:
                fw.write("portName,portType,sub"+"\n")
                for portName in port_info:
                    fw.write(portName)

            for line in input_list:
                self.port_input_disp(line,flag)

            for line in output_list:
                self.port_output_disp(line,flag)

            for line in inout_list:
                self.port_inout_disp(line,flag)

        return (self.tmp_content.rstrip(',\n') + "\n")

    def equPortType(self,portType,item):
        flag = False

        if 1 == len(item.strip().split(',')):
            if portType == "":
                flag = True

        elif 2 == len(item.strip().split(',')):
            if portType == item.strip().split(',')[1]:
                flag = True

        elif 3 == len(item.strip().split(',')):
            if portType == item.strip().split(',')[1]:
                flag = True
        
        else:
            self.logging.info(f"The wrong {portType} format ")

        return flag


    def getPortOrder(self,tempLine,portType,subType,flag):
        if "input" in tempLine:
            self.port_input_disp(tempLine,flag)
            self.topContent.append(tempLine.split(',')[-1] + ',' + portType + ',' + subType)

        elif "output" in tempLine:
            self.port_output_disp(tempLine,flag)
            self.topContent.append(tempLine.split(',')[-1] + ',' + portType + ',' + subType)

        elif "inout" in tempLine:
            self.port_inout_disp(tempLine,flag)
            self.topContent.append(tempLine.split(',')[-1] + ',' + portType + ',' + subType)
        else:
            self.port_input_disp(tempLine,flag)
            self.topContent.append(tempLine.split(',')[-1] + ',' + portType + ',' + subType)        
                    
    def getPortType(self,key,portType):
        temp_port_info = copy.deepcopy(self.port_info_old)
        resFlat = False

        for item in temp_port_info:
            # print(f"key = {key},item = {item}")
            # if 1 == len(item.strip().split(',')):
            #     if key == item.strip().split(',')[0]:
            #         resFlat = True
            #         if key in self.port_info:
            #             self.port_info.remove(key)

            if 2 == len(item.strip().split(',')):
                if key == item.strip().split(',')[0]:
                    if portType == item.strip().split(',')[1]:
                        resFlat = True
                        if key in self.port_info:
                            self.port_info.remove(key)

            if 3 == len(item.strip().split(',')):
                if key == item.strip().split(',')[0]:
                    if portType == item.strip().split(',')[1]:
                        resFlat = True
                        if key in self.port_info:
                            self.port_info.remove(key)
                # else:
                # 	if key not in self.port_info:
                # 	    self.port_info.append(key)
            # else:
            #     print(f"The worng format item = {item}")
        return resFlat

    def getPortSubType(self,key,portType,subType):
        temp_port_info = copy.deepcopy(self.port_info_old)
        resFlat = False

        for item in temp_port_info:
            if 3 == len(item.strip().split(',')):
                if key == item.strip().split(',')[0] and portType == item.strip().split(',')[1] and subType == item.strip().split(',')[2]:
                    resFlat = True
                    # self.port_info.remove(key)
        return resFlat

    def port_input_disp(self,line,flag):
        if len(line.split(","))>2:
            if "input" in line:
                if ",," in line:
                    val_len = len(line.split(',,')[0])
                    # print(f"val_len = {val_len}")
                    if flag:
                        if val_len >= 37:
                            self.tmp_content += "\t{}\n".format(line.replace(",,"," "))

                        else:
                            self.tmp_content += "\t{}\n".format(line.replace(",,"," "*(37-val_len)))
                    else:
                        if val_len >= 37:
                            self.tmp_content += "\t{},\n".format(line.replace(",,"," "))

                        else:
                            self.tmp_content += "\t{},\n".format(line.replace(",,"," "*(37-val_len)))
                else:
                    segStr = line.split(',')[1]
                    segLen = len(segStr)
                    if flag:
                        self.tmp_content += "\t{}\n".format(line.replace(","," "*2,1).replace(","," "*(30-segLen),1))
                    else:
                        self.tmp_content += "\t{},\n".format(line.replace(","," "*2,1).replace(","," "*(30-segLen),1))
            else:
                if ",," in line:
                    self.tmp_content += "\t{},\n".format(line.replace(",,"," "))

                else:
                    segStr = line.split(',')[0]
                    segLen = len(segStr)
                    if flag:
                        self.tmp_content += "\t{}\n".format(line.replace(","," "*2,1).replace(","," "*(60-segLen),1))
                    else:
                        self.tmp_content += "\t{},\n".format(line.replace(","," "*2,1).replace(","," "*(60-segLen),1))
        else:
            self.tmp_content += "\t"+line+"\n"

        return (self.tmp_content)

    def port_output_disp(self,line,flag):
        if len(line.split(","))>2:
            if ",," in line:
                # if line == output_list[-1]:
                #     tmp_content += "\t{}\n".format(line.replace(",,"," "*31))
                # else:
                self.tmp_content += "\t{},\n".format(line.replace(",,"," "*31))
            else:
                line,width = self.get_mod_port_info(line)
                segStr = width

                if "reg" in segStr:
                    segStr = segStr[2:]

                segLen = len(segStr)
                self.logging.debug(f"segStr = {segStr} and len = {segLen}")

                # if line == output_list[-1]:
                #     data = "\t{}\n".format(line.replace(","," "*1,1).replace(","," "*(30-segLen),1))
                # else:
                data = "\t{},\n".format(line.replace(","," "*1,1).replace(","," "*(30-segLen),1))

                if flag:
                    data = "\t{}\n".format(line.replace(","," "*1,1).replace(","," "*(30-segLen),1))

                if "#" in data:
                    data = data.replace('#',',')
                self.tmp_content += data
        else:
            self.tmp_content += "\t"+line+"\n"

        return self.tmp_content

    def port_inout_disp(self,line,flag):
        if len(line.split(","))>2:
            if ",," in line:
                if flag:
                    self.tmp_content += "\t{}\n".format(line.replace(",,"," "*32))
                else:
                    self.tmp_content += "\t{},\n".format(line.replace(",,"," "*32))
            else:
                line,width = self.get_mod_port_info(line)
                segStr = width

                if "reg" in segStr:
                    segStr = segStr[2:]

                segLen = len(segStr)
                self.logging.debug(f"segStr = {segStr} and len = {segLen}")

                # if line == inout_list[-1]:
                #     data = "\t{}\n".format(line.replace(","," "*1,1).replace(","," "*(31-segLen),1))
                # else:
                data = "\t{},\n".format(line.replace(","," "*1,1).replace(","," "*(31-segLen),1))

                # if '{' in inout_list[-1] and '}' in inout_list[-1]:
                if flag:
                    data = "\t{}\n".format(line.replace(","," "*1,1).replace(","," "*(31-segLen),1))

                if "#" in data:
                    data = data.replace('#',',')
                self.tmp_content += data

        else:
            self.tmp_content += "\t"+line+"\n"

        return self.tmp_content

    def get_mod_port_info(self,line):
        if "{" in line and "}" in line:
            match_parameter = re.compile(r'[{](.*)[}]', re.S)
            width = '{' + match_parameter.findall(line)[0] + '}'
            modifyWidth = width.replace(',','#')
            tempLine = line.replace(width,modifyWidth)
            width = modifyWidth
  

            self.logging.debug(f"width = {width} lineNo = {sys._getframe().f_lineno}")
        else:
            width = line.split(",")[1]
            tempLine = line
       
        return tempLine,width

    def get_inst_module_list(self, inst_list):
        for line in inst_list:
            if line.startswith("inst"):
                _, module_name, inst_name = line.split()
                self.logging.info(f"module name = {module_name} and inst name ={inst_name}")
                break
        
        return (module_name, inst_name)

    def get_inst_para_list(self, inst_list):
        tmp_content = ""
        linelist = []
        flag = 0
        keyword_begin = "para_inst_begin"
        keyword_end = "para_inst_end"
        for line in inst_list:
            if keyword_begin in line:
                flag = 1
                continue
            if keyword_end in line:
                flag = 0
                break
            if flag == 1:
                linelist.append(line.strip())

        return linelist

    def get_inst_port_list(self, inst_list):
        tmp_content = ""
        linelist = []
        flag = 0
        keyword_begin = "port_inst_begin"
        keyword_end = "port_inst_end"
        for line in inst_list:
            if keyword_begin in line:
                flag = 1
                continue
            if keyword_end in line:
                flag = 0
                break
            if flag == 1:
                linelist.append(line.strip())

        return (linelist)

    def get_inst_port_type(self, inst_list, attr_type):
        tmp_content = ""
        linelist = []
        flag = 0
        keyword_begin = "port_inst_begin"
        keyword_end = "port_inst_end"
        for line in inst_list:
            if keyword_begin in line:
                flag = 1
                continue
            if keyword_end in line:
                flag = 0
                break
            if flag == 1:
                if line.strip().endswith(attr_type):
                    linelist.append(line.strip())

        return (linelist)

    def combo_content(self, module_name, inst_name, inst_para_list, inst_port_list):
        tmp_content = ""
        # module_name

        if "keep_inst_before" not in self.keepDict.keys():
            pass

        else:

            tmp_content += read_list_content(self.keepDict["keep_inst_before"][inst_name])

        tmp_content += "\n\t{}".format(module_name)

        if "keep_inst_before" not in self.keepDict.keys():
            pass
        else:
            tmp_content += read_list_content(self.keepDict["keep_inst_after"][inst_name])

        # parameter
        if len(inst_para_list) > 0:
            tmp_content += "\t#(\n"
            for line in inst_para_list:
                if line.startswith("`"):
                    tmp_content += "\t\t"+line+"\n"

                if line.startswith("connect"):
                    _, signal_name, signal_val = line.split(',')
                    signal_name = (signal_name[signal_name.find("."):])

                    if line == inst_para_list[-1]:
                        tmp_content += "\t\t{} ({})\n".format(signal_name.ljust(40), signal_val)

                    else:
                        tmp_content += "\t\t{} ({}),\n".format(signal_name.ljust(40), signal_val)

            tmp_content += "\n)\n"
        tmp_content += "\t{}(\n".format(inst_name)
        # signals
        # self.logging.info(f"inst list = {inst_port_list} and para list = {inst_para_list}")
        for index, line in enumerate(inst_port_list):
            if line.startswith("`"):
                tmp_content += "\t\t"+line+"\n"

            if line.startswith("connect"):
                _, port_name, signal_name, attr, direction,checkValue = deal_with_port_str(line)
                direction = inst_name + "." + direction

                # if '{' in signal_name and '}' in signal_name:
                #     signal_name = self.deal_with_special(signal_name)

                port_name = port_name[port_name.find("."):]
                signal_name = signal_name.strip()

                if attr.replace(" ","") == "W" or attr.replace(" ","") == "w":
                    if signal_name:
                        if "'b" in signal_name and '{' not in signal_name:
                            pass

                        else:
                            flag = port_in_list(signal_name,self.wire_list)

                            if not flag:
                                self.wire_list.append(signal_name)
                    else:
                        pass

                if attr.replace(" ","") == "I" or attr.replace(" ","") == "i":
                    self.input_list.append(signal_name)

                if attr.replace(" ","") == "O" or attr.replace(" ","") == "o":
                    self.output_list.append(signal_name)

                if attr.replace(" ","") == "IO" or attr.replace(" ","") == "io":
                    self.inout_list.append(signal_name)

                if attr.replace(" ","") == "M" or attr.replace(" ","") == "m":
                    if signal_name.strip().endswith('_m'):
                        signal_name = signal_name.replace('_m     ','.master')

                    if signal_name.strip().endswith('_s'):
                        signal_name = signal_name.replace('_s    ','.slave')

                    self.modport_list.append(line)

                if attr.replace(" ","") == "IF" or attr.replace(" ","") == "if":
                    if signal_name.strip().endswith('master'):
                        signal_name = signal_name.replace('.master','_m     ')

                    if signal_name.strip().endswith('slave'):
                        signal_name = signal_name.replace('.slave','_s    ')
                    # data = "{},{},{}".format(direction,"",signal_name)
                    self.interface_list.append(line) #signal_name, direction

                if index == len(inst_port_list)-1:
                    tmp_content += "\t\t{} ({}) //{},{}\n".format(port_name.ljust(60), signal_name.ljust(60), direction.ljust(20),checkValue)

                else:
                    tmp_content += "\t\t{} ({}), //{},{}\n".format(port_name.ljust(60), signal_name.ljust(60), direction.ljust(20),checkValue)

        tmp_content += "\t);\n"
        self.logging.debug(f"wire_list = {self.wire_list} interface_ist = {self.interface_list}, modport_list = {self.modport_list}")
        return (tmp_content)

    def split_inst(self, inst_list):
        group_list = []
        tmp_list = []
        count = 0
        inst_tmp_list = []

        for line in inst_list:
            self.logging.debug(f"split_inst = {line}")

            if line.startswith('inst '):
                inst_tmp_list.append(line.split(' ')[-1])

            if "port_inst_end" not in line:
                tmp_list.append(line)

            else:
                group_list.append(tmp_list)
                tmp_list = []
                count += 1

        self.logging.info(f"group_list = {group_list},count = {count}")
        return group_list,inst_tmp_list

    def gen_instance(self,group_list):
        tmp_content = ""
        tmp_content += '''
// =================================================================================================
// Instance
// =================================================================================================
'''
        # inst_list = read_csv_base("inst",self.rfilename)
        # group_list, inst_name_list = self.split_inst(inst_list)
        for item_list in group_list:
            inst_para_list = []
            inst_port_list = []
            # get module_list
            module_name, inst_name = self.get_inst_module_list(item_list)
            # get para_list
            inst_para_list = self.get_inst_para_list(item_list)
            # get port_list
            inst_port_list = self.get_inst_port_list(item_list)

            # noloadList = self.get_inst_port_type(item_list, "noload")
            # undriveList = self.get_inst_port_type(item_list, "undrive")

            # totalList.extend(noloadList)
            # totalList.extend(undriveList)

            tmp_content += self.combo_content(module_name, inst_name, inst_para_list, inst_port_list)

        # tmp_content += "\nendmodule\n\n"
        return tmp_content

    def gen_wire_declar(self):
        tmp_content = ""
        tmp_content += '''

// =================================================================================================
// Signals Declaration
// =================================================================================================
'''
        self.logging.debug(f"wire list = {self.wire_list}")

        temp_wire_list = list(set(self.wire_list))
        self.wire_list = []
        for item in temp_wire_list:

            if "{" in item and "}" in item:
                self.wire_list.append(item)

            elif "[" in item and "]" in item:
                signal = item[:item.find("[")]
                width = item[item.find("["):]

                temp_wire = [value for value in temp_wire_list if signal in value and width not in value]
                if len(temp_wire) >= 1:
                    self.logging.debug(f"signal = {signal},temp_wire = {temp_wire}")

                    temp_counter = len(temp_wire)
                    value_flag = False

                    for temp_signal in temp_wire:
                        if "[" in temp_signal and "]" in temp_signal:
                            self.logging.debug(f"temp_wire = {temp_wire}\n")
                            signal1 = temp_signal[:temp_signal.find("[")]
                            width1 = temp_signal[temp_signal.find("["):]

                            if signal1.strip() == signal.strip():
                                self.logging.debug(f"width = {width}, width1 = {width1}\n")
                                self.logging.debug(f"signal = {signal}, signal1 = {signal1}\n")
                                temp_counter -= 1

                                if len(width) == 3:
                                    matchValue = re.compile(r"\[(\d*)\]")
                                else:
                                    matchValue = re.compile(r"\[(\d*):(\d*)\]")

                                temp_value = matchValue.search(width).groups()
                                if temp_value:
                                    value = int(temp_value[0])
                                else:
                                    value = 0

                                if len(width1) == 3:
                                    matchValue = re.compile(r"\[(\d*)\]")
                                else:
                                    matchValue = re.compile(r"\[(\d*):(\d*)\]")

                                temp_value1 = matchValue.search(width1).groups()
                                if temp_value1:
                                    value1 = int(temp_value1[0])
                                else:
                                    value1 = 0

                                self.logging.debug(f"value = {value}, value1 = {value1} ,item = {item}\n")
                                if len(width) == 3:
                                    self.logging.debug(f"pass : width = {width}, width1 = {width1} ,item = {item}\n")
                                else:
                                    
                                    if value1 > value:
                                        self.logging.debug(f"pass : value = {value}, value1 = {value1} ,item = {item}\n")
                                        value_flag = True

                                    else:
                                        if temp_counter == 0 and value_flag == False:
                                            self.logging.debug(f"append : value = {value}, value1 = {value1} ,item = {item}\n")

                                            self.wire_list.append(item)
                                        else:
                                            pass

                            else:  ## [] but not equal
                                flag_item = True
                                
                                for item1, count in collections.Counter(temp_wire).items():

                                    if item.split('[')[0] == item1.split('[')[0]:
                                        flag_item = False

                                if flag_item:

                                    self.wire_list.append(item)

                        else: # not [] and not equal

                            self.wire_list.append(item)
        
                else:

                    self.wire_list.append(item)
            else:
                itemValue = item + '['
                temp_wire = [value for value in temp_wire_list if itemValue in value ]
                if len(temp_wire) >= 1:
                    pass
                else:
                    self.wire_list.append(item)

        ###########################
        for item in list(set(self.wire_list)):

            if "{" in item and "}" in item:
                continue

            elif "[" in item:
                
                signal = item[:item.find("[")]
                width = item[item.find("["):]

            else:
                signal = item
                width = ""

            tmp_content += ("\twire {} {};\n".format(width.ljust(40), signal.replace(" ","")))
        return (tmp_content)

    def gen_interface(self):
        modport_list = []
        tmp_content = ""
        tmp_content += '''

// =================================================================================================
// Interface Declaration
// =================================================================================================
''' 
        modport_dict = {} 
        for item in self.modport_list:
            if len(item.split(',')) == 6:
                _, port_name, signal_name, attr, mod_type,checkValue = item.split(',')
            else:
                continue

            port_name = port_name[port_name.find("."):]
            signal_name = signal_name[:signal_name.find(".")]
            modport_dict[signal_name] = mod_type

        for signal_name in list(set(modport_dict.keys())):
            if signal_name in self.interface_list:
                continue
            tmp_content += "\t{} \t\t\t\t{}();\n".format(modport_dict[signal_name].split('.')[0].ljust(60), signal_name.strip().replace(' ',""))
            
        return (tmp_content)

    def gen_keep(self):
        tmp_content = ""
        keep_list = []
        tmp_content = '''
        
// =================================================================================================
// Keep code Declaration
// =================================================================================================
'''
        keep_list = read_csv_base("keep",self.rfilename)
        for line in keep_list:
                tmp_content += "\t"+line
        return (tmp_content)

    def cleanDir(self,dir="./sb_output"):
        if os.path.exists(dir):
            # shutil.rmtree(dir)
            pass
        else:
            os.mkdir(dir)


    def proc_noload_undrive_port(self,totalList,tempContent):

        self.logging.debug(f"totalList = {totalList}")
        delTopPortStr = tempContent
        for value in totalList:
            delTopPortStr = ""
            _, port_name, signal_name, attr, direction,checkValue = value.split(',')
            self.logging.debug(f"signal_name = {signal_name},direction = {direction}")

            if '[' in signal_name:
                signal_name = signal_name.split('[')[0]

            for item in tempContent.split('\n'):
                
                if signal_name.strip() in item and "//" not in item and direction.strip() in item :
                    pass
                else:
                    delTopPortStr += item + '\n'

            tempContent = delTopPortStr

        return delTopPortStr

    def main_process(self,topFile,fileType="null"):
        
        self.cleanDir()

        # if topFile.endswith('.v'):
        #     csvFile =  topFile.replace('.v','.csv')

        # elif topFile.endswith('.sv'):
        #     csvFile =  topFile.replace('.sv','.csv')

        # else:
        #     pass
        fileType = read_csv_base("gen_type",self.rfilename)
        fileType = fileType[0].strip()

        authorName = read_csv_base("author",self.rfilename)
        if authorName:
            
            authorName = authorName[0].strip()

        else:
            print(f"Error: Please add the author info in top file {self.rfilename}")
            exit()

        self.logging.info(f"fileType = {fileType} self.rfilename = {self.rfilename}")

        inst_list = read_csv_base("inst",self.rfilename)

        group_list, inst_name_list = self.split_inst(inst_list)
        self.keepDict = read_all_keep_info(self.rfilename,inst_name_list)

        inst_content = self.gen_instance(group_list)

        tmp_content = ""

        tmp_content += self.gen_header(topFile,authorName)
        tmp_content += self.gen_include()
        tmp_content += read_list_content(self.keepDict["before_module"])

        tmp_content += self.gen_module()

        tmp_content += read_list_content(self.keepDict["after_module"])
        # tmp_content += self.gen_parameter()
        # tmp_content += read_list_content(self.keepDict["before_port"])
        tmp_content += self.gen_port(self.keepDict["before_port"])

        tmp_content += read_list_content(self.keepDict["before_bracket"])
        tmp_content += ");\n"
        tmp_content += read_list_content(self.keepDict["after_bracket"])

        tmp_content += read_list_content(self.keepDict["before_parameter"])

        tmp_content += read_list_content(self.keepDict["after_parameter"])

        tmp_content += read_list_content(self.keepDict["before_wire_reg"])

        tmp_content += self.gen_wire_declar()

        tmp_content += read_list_content(self.keepDict["after_wire_reg"])

        tmp_content += read_list_content(self.keepDict["before_modport"])

        tmp_content += self.gen_interface()

        # tmp_content += self.gen_keep()

        tmp_content += read_list_content(self.keepDict["after_modport"])

        tmp_content += inst_content

        tmp_content += read_list_content(self.keepDict["before_endmodule"])

        tmp_content += "\nendmodule\n\n"

        tmp_content += read_list_content(self.keepDict["after_endmodule"])

        # tmp_content = self.proc_noload_undrive_port(totalList,tmp_content)
        self.content = tmp_content
        self.write_file(fileType)

    
    # def write_finish_info(self,file="sb_output/run.log"):

    #     with open(file,'a+') as fw:
    #         fw.write("soc_build successed")

    #         fw.close()


class ModuleItem():
    '''
    This is Module Class
    '''
    def __init__(self, name):
        self.name = name

class ParameterItem():
    '''
    '''
    def __init__(self, signal_name="", signal_val=""):
        self.signal_name = signal_name
        self.signal_val = signal_val


class PortItem():
    '''
    '''
    def __init__(self, direction="", width="", signal_name=""):
        self.direction = direction
        self.width = width
        self.signal_name = signal_name

#--------------------------------------------------------------------
#  contract v|sv to csv
#--------------------------------------------------------------------

class csvGenerator():
    '''
    This is Csv file generator class
    '''
    def __init__(self,logging):
        self.content = ""
        self.logging = logging
        self.logging.info("init the csv generator")
        self.re_pattern_init()
        self.fileDir = ""

    def re_pattern_init(self):
        self.match_module = re.compile(r',*(module|class)\s+(\w+)', re.I)
        self.match_parameter = re.compile(r'.*(parameter)\s+(\w+)\s*=\s+(\w+)', re.I)
        self.match_port = re.compile(r"(input|output|\S*)\s?(.*)?\s+?(\w+)", re.I)
        self.match_port_new = re.compile(r"(input|output|\S*)\s+?[{](.*)[}]\s+?(\w+)", re.I)

        self.match_interface = re.compile(r"(\w+)(.master|.slave)\s+(\S+)", re.I)
        self.match_wire = re.compile(r"(wire)\s?(.*)?\s+?(\w+)", re.I)
        self.match_inst = re.compile(r',*(module)\s+(\w+)', re.I)
        self.match_inst_parameter = re.compile(r'\s*(.)(\w+)\s*\((\w+)\)', re.I)
        self.match_inst_port = re.compile(r'\s*\.(\S+)\s+\((\S*)\s*\)\S*\s*\/\/(\w*)', re.I)

    def write_csv(self,topPath,fileType,path="./csv/"):
        self.logging.info(f"topFlag = {self.topFlag},modulename = {self.current_modulename}")
        if self.topFlag == True:
            csvFile_inst = self.current_modulename

        if not os.path.exists(path):
            os.mkdir(path)

        with open('{}.csv'.format(path+csvFile_inst),'w', encoding='UTF-8') as fw:
            writer = csv.writer(fw)

            # write modulename field
            line_tmp = tuple(["module",self.current_modulename])
            writer.writerow(line_tmp)

            # write parameter field
            line_tmp = tuple(["#parameter_begin"])
            writer.writerow(line_tmp)
            for item in self.current_parameters:
                if isinstance(item, MicroClass):
                    line_tmp = tuple([item.string])

                else:
                    line_tmp = tuple([item.keyword,item.signal_name, item.signal_value])

                writer.writerow(line_tmp)
            line_tmp = tuple(["#parameter_end"])
            writer.writerow(line_tmp)

            # write port field
            line_tmp = tuple(["#port_begin"])
            writer.writerow(line_tmp)
            for item in self.current_ports:
                if isinstance(item, MicroClass):
                    line_tmp = tuple([item.string])

                elif isinstance(item, InterfaceClass):
                    line_tmp = tuple([item.group_name, item.direction, item.signal_name])

                else:
                    line_tmp = tuple([item.direction, item.width, item.signal_name])

                writer.writerow(line_tmp)
            line_tmp = tuple(["#port_end"])
            writer.writerow(line_tmp)

            line_tmp = tuple(["#csv_begin"])
            writer.writerow(line_tmp)
            line_tmp = tuple(["#csv_end"])
            writer.writerow(line_tmp)

        csvFile = csvFile_inst + ".csv"
        print("Info: {} Generated!".format(csvFile))
        self.logging.info("{} Generated!".format(csvFile))

        # shutil.move(path + csvFile,path + os.sep + csvFile)

        tempPath = path + csvFile_inst + '.csv'


        if os.path.samefile(os.path.dirname(tempPath),os.path.dirname(topPath)):
            pass

        else:
            shutil.copyfile(tempPath,topPath)
                

    def modifyTopFile(self,topPath,del_inst="",path="./sb_output/"):

        startStr = "#csv_begin\n"
        endStr = "#csv_end\n"

        filelist = []

        if del_inst:
            os.remove(path + os.path.basename(del_inst) + ".csv")

        files = os.listdir(path)

        for f in files:
            full_f = os.path.join(path, f)
            if os.path.isfile(full_f) and os.path.basename(topFile).split('.')[0] not in full_f:
                filelist.append(full_f)

        self.logging.debug("all csv files = {}".format(filelist))
        # shutil.copy(topFile,outFile)

        topFilePath = path + os.path.basename(topFile).split('.')[0] + '.csv'

        with open(topFilePath,'a+') as fw:
            fw.write(startStr)
            for file in filelist:
                fw.write(file + "\n")
            fw.write(endStr)


    def createDir(self,file,dir="csv"):

        if '/' in file and not './' in file:

            self.fileDir = os.path.dirname(file) + os.sep + dir

        else:
            self.fileDir = dir

        if os.path.exists(self.fileDir):
            # shutil.rmtree(dir)
            pass
        else:
            os.mkdir(self.fileDir)

        return self.fileDir

    def get_content(self, rfilename):
        with open(rfilename, 'r') as fr:
            self.content_list = self.pre_process(fr)

    def handle2list(self, fhandle):
        port_content_list = []
        [port_content_list.append(line.strip()) for line in fhandle.readlines()]
        return port_content_list

    def filter_comments(self, content_list):
        port_content_list = []
        for line in content_list:
            if line.startswith("//"):
                port_content_list.append(line[:line.find("//")])
            else:
                port_content_list.append(line)
        return port_content_list

    def filter_blankline(self, content_list):
        port_content_list = []
        [port_content_list.append(line) for line in content_list if len(line)!= 0]
        return port_content_list

    def filter_comma(self, content_list):
        port_content_list = []
        for line in content_list:
            if "{" in line and "}" in line:
                match_parameter = re.compile(r'[{](.*)[}]', re.S)
                width = '{' + match_parameter.findall(line)[0] + '}'
                modifyWidth = width.replace(',','#')
                tempValue = line.replace(width,modifyWidth)
                port_content_list.append(tempValue)
            else:
                port_content_list.append(line.replace(",",""))
        # [port_content_list.append(line.replace(",","")) for line in content_list]
        return port_content_list

    def find_port_signal(self, content_list):
        port_content_list = []
        #[port_content_list.append(line.split()[-1][:-1]) for line in content_list]
        [port_content_list.append(line) if "`" in line else port_content_list.append(line.split()) for line in content_list]
        return port_content_list

    def pre_process(self, fhandle):
        port_content_list = []
        # transfer list from file handle
        port_content_list = self.handle2list(fhandle)

        # filter comments info
        port_content_list = self.filter_comments(port_content_list)

        # filter blank line
        port_content_list = self.filter_blankline(port_content_list)

        # filter filter_comma
        port_content_list = self.filter_comma(port_content_list)

        self.current_modulename = self.get_module_name(port_content_list)
        self.logging.info(self.current_modulename)

        # get parameters info
        self.current_parameters = self.get_parameter_info(port_content_list)
        self.logging.info(f"=======Find parameters=============")
        [self.logging.debug(line.string) if isinstance(line, MicroClass) else self.logging.debug("{} {}".format(line.signal_name, line.signal_value)) for line in self.current_parameters]

        self.current_ports = self.get_port_info(port_content_list)

        return port_content_list

    def get_parameter_info(self, content_list):
        parameter_list = []
        parameter_valid = 0
        for i in range(len(content_list)):
            line = content_list[i]
            self.logging.debug(f"{line}")
            if parameter_valid == 1:
                # self.logging.info(f"--------{line}")
                tmp_line = line.replace(")","")
                if "parameter" in tmp_line:
                    tmp_line = self.match_parameter.search(tmp_line).groups()
                    p_item = ParameterClass(tmp_line[0], tmp_line[1], tmp_line[2])
                    parameter_list.append(p_item)
                elif "`" in tmp_line:
                    p_item = MicroClass(tmp_line)
                    parameter_list.append(p_item)
                else:
                    pass
            if "(" in line:
                if "#" in line:
                    parameter_valid = 1
                else:
                    parameter_valid = 0

            if line.startswith(")"):
                parameter_valid = 0
                self.row = i
                break
                # return (parameter_list)
        return (parameter_list)


    def get_port_info(self, content_list):

        port_list = []
        parameter_valid = 0
        has_parameter = 1
        port_valid = 0
        if len(self.current_parameters) == 0:
            has_parameter = 0
            self.row = 0
        self.logging.info(f"has parameter = {has_parameter}")
        for i in range(len(content_list)):

            line = content_list[i]
            if '//' in line:
                line = line.split("//")[0]

            self.logging.debug(f"{line}")
            tmp_line = []
            if "parameter" in line:
                parameter_valid = 1
            if (line.startswith("(") or line.endswith("(")) and (parameter_valid == has_parameter):
                port_valid = 1
            if ");" in line:
                port_valid = 0
                self.row = i
                break
            if port_valid == 1:
                if line.startswith("(") or line.endswith("("):
                    continue
                if line:
                    if "`" in line:
                        p_item = MicroClass(line)
                    elif 'input' in line or 'output' in line:
                        if " reg " in line or " wire " in line:
                            if "reg" in line:
                                line = line.split('reg')[0] + line.split('reg')[1]
                            if "wire" in line:
                                line = line.split('wire')[0] + line.split('wire')[1]

                            line = self.match_port.search(line).groups()
                            [tmp_line.append(l.replace(" ","").replace("\t","")) for l in line]
                            self.logging.info(f"-----reg or wire--- {tmp_line[0]},{tmp_line[1]},{tmp_line[2]}")
                            p_item = PortClass(tmp_line[0], tmp_line[1],tmp_line[2])

                        elif '{' in line and '}' in line:
                            line = line.replace('#',',')
                            line = self.match_port_new.search(line).groups()
                            
                            [tmp_line.append(l.replace(" ","").replace("\t","")) for l in line]
                            tempValue = '{' + tmp_line[1] + '}'.replace('"',' ')

                            p_item = PortClass(tmp_line[0],tempValue,tmp_line[2])

                        elif self.match_interface.search(line):
                            tmp_line = self.match_interface.search(line).groups()

                            p_item = InterfaceClass(tmp_line[0], tmp_line[1], tmp_line[2])

                        else:
                            line = self.match_port.search(line).groups()
                            [tmp_line.append(l.replace(" ","").replace("\t","")) for l in line]
                       
                            p_item = PortClass(tmp_line[0], tmp_line[1],tmp_line[2])
                    else:

                        line = self.match_port.search(line).groups()
                        [tmp_line.append(l.replace(" ","").replace("\t","")) for l in line]
                        p_item = PortClass(tmp_line[0], tmp_line[1],tmp_line[2])


                port_list.append(p_item)
        return (port_list)

    def get_inst_parameter_info(self, content_list):
        parameter_list = []
        parameter_valid = 0

        for i in range(len(content_list)):
            # self.logging.info(f"{line}")
            line = content_list[i]
            
            if parameter_valid == 1:
                # tmp_line = line.replace(")","")

                if "." in line:
                    tmp_line = self.match_inst_parameter.search(line).groups()
                    p_item = ParameterClass("parameter", tmp_line[1], tmp_line[2])
                    parameter_list.append(p_item)
                elif "`" in line:
                    p_item = MicroClass(line)
                    parameter_list.append(p_item)
                else:
                    pass
            if "#" in line:
                parameter_valid = 1
            if line.startswith(")"):
                parameter_valid = 0
                self.row = i
                break
                # return (parameter_list)
        return (parameter_list)

    def get_inst_port_info(self, content_list):
        port_list = []
        port_valid = 0

        for i in range((self.row+1),len(content_list)):
            line = content_list[i]
            self.logging.debug(f"{line}")
            tmp_line = []

            if line.startswith("u") and "(" in line:
                self.inst_name = line.strip().replace('(',"")
                self.logging.info(self.inst_name)
                port_valid = 1
                continue
            if ");" in line:
                port_valid = 0
                self.row = i
                break
            if port_valid == 1:
                # if '//' in line:
                #     line = line.split("//")[0]
                if "`" in line:
                    p_item = MicroClass(line)
                elif self.match_interface.search(line):
                    tmp_line = self.match_interface.search(line).groups()

                    p_item = InterfaceClass(tmp_line[2], tmp_line[1], tmp_line[0])
                else:
                    tmp_line = self.match_inst_port.search(line).groups()

                    if "[" in str(tmp_line[1]):
                        if "[(" in str(tmp_line[1]):
                            port_width = '[' + str(tmp_line[1]).split(')')[0].split('(')[1] + ']'
                        else:
                            port_width = '[' + str(tmp_line[1]).split(']')[0].split('[')[1] + ']'

                    else:
                        port_width = ""
                    p_item = PortClass(tmp_line[2], port_width, tmp_line[0])

                port_list.append(p_item)
        return (port_list)

    def get_wire_info(self,content_list):
        wire_list = []
        self.is_inst = False
        self.is_wire = False

        for i in range(self.row,len(content_list)):
            tmp_line = []
            if 'wire' in content_list[i] and 'wire' not in content_list[i-1]:
                self.is_wire = True

            if self.is_wire == True:
                if "`" in content_list[i]:
                    w_item = MicroClass(line)
                else:
                    line = self.match_wire.search(content_list[i]).groups()
                    [tmp_line.append(l.replace(" ","").replace("\t","")) for l in line]

                    w_item = wileClass(tmp_line[0], tmp_line[1], tmp_line[2])

                wire_list.append(w_item)

            if 'wire' in content_list[i] and 'wire' not in content_list[i+1]:
                if self.is_wire == True:
                    self.is_wire = False
                    self.row = i

                    break

        return wire_list

    def get_instance_info(self,content_list):
        inst_flag = False
        inst_info = {}
        inst_list = []
        
        inst_cont_list = []
        inst_content = []
        for i in range(self.row,len(content_list)):
            line = content_list[i]
            if  i <= (len(content_list)-2) and '#' in content_list[i+1]:
                inst_flag = True
                temp_mod = line.strip()

            if inst_flag == True:
                inst_content.append(line)

            if i <= (len(content_list)-2) and '(' in line:
                tempStr = line.strip().replace('(',"")
                temp_inst_name = temp_mod + '_' + tempStr
                inst_list.append(temp_inst_name)
                self.logging.info(temp_inst_name)

            if inst_flag == True and ");" in line :
                inst_flag = False

                
                inst_cont_list.append(inst_content)
                inst_content = []


        self.inst_info = dict(zip(inst_list,inst_cont_list))

        return self.inst_info

    def get_module_name(self, content_list):
        for line in content_list:
            if "module" in line or "class" in line:
                return (self.match_module.search(line).group(2))


    def get_inst_module_name(self, content_list):
        for i in range(len(content_list)):
            line = content_list[i]
            if i< (len(content_list)-1) and '#' in content_list[i+1]:
                modulename = line.strip()
        return modulename


    def data_process(self,outputFile,fileType):
        self.write_csv(outputFile,fileType)


    def postProcess(self,contentList):
        self.current_modulename = self.get_inst_module_name(contentList)
        self.logging.info(self.current_modulename)

        # get parameters info
        self.current_parameters = self.get_inst_parameter_info(contentList)
        self.logging.info(f"=======find parameters=============")

        self.current_ports = self.get_inst_port_info(contentList)
        self.logging.info(f"=======find ports=============")
        self.logging.debug(self.current_ports)

        self.write_csv()

    def parse_and_gen_csv(self,fileitem,outputFile,fileType):
        self.topFlag = True
        self.logging.info(fileitem)
        self.get_content(fileitem)
        self.data_process(outputFile,fileType)

    def main_process(self,topFile,outputFile,fileType="null"):
        # debug

        self.parse_and_gen_csv(topFile,outputFile,fileType)

class ParameterClass():
    '''
    This is Parameter class
    '''
    def __init__(self, keyword="parameter", signal_name="", signal_value=""):
        self.keyword = keyword
        self.signal_name = signal_name
        self.signal_value = signal_value


class PortClass():
    '''
    This is Port class
    '''
    def __init__(self, direction="", width="", signal_name=""):
        self.direction = direction
        self.width = width
        self.signal_name = signal_name

class PortClass1():
    '''
    This is Port class
    '''
    def __init__(self, direction="", signal_type="",width="", signal_name=""):
        self.direction = direction
        self.signal_type = signal_type
        self.width = width
        self.signal_name = signal_name

class wileClass():
    '''
    This is wire class
    '''
    def __init__(self, keyword="wile", width="", signal_name=""):
        self.keyword = keyword
        self.width = width
        self.signal_name = signal_name

class MicroClass():
    '''
    This is Micro class
    '''
    def __init__(self, string):
        self.string = string


class InterfaceClass():
    '''
    This is Interface class
    '''
    def __init__(self, group_name="", direction="", signal_name=""):
        self.group_name = group_name
        self.direction = direction
        self.signal_name = signal_name





#--------------------------------------------------------------------
#  integrate sub csv to top csv
#--------------------------------------------------------------------

class topCsvGenerator():
    '''
    This is Top Csv file generator class
    '''
    def __init__(self,filename,logging,path = "./sb_output/"):

        self.filename = filename

        self.content = ""
        self.csvlist = []
        self.inst_content = ""
        self.fullpath = ""
        self.logging = logging
        self.inst_name_list = []
        # self.total_inst_same_list = []
        self.mod_sig_list = []
        self.logging.info("integrate the csv")
        # self.cleanDir()

    def cleanDir(self,dir="./sb_output"):
        if os.path.exists(dir):
            pass
        else:
            os.mkdir(dir)

    def get_mod_port_str(self,line):
        if "{" in line and "}" in line:
            match_parameter = re.compile(r'[{](.*)[}]', re.S)
            width = '{' + match_parameter.findall(line)[0] + '}'
            modifyWidth = width.replace(',','#')
            tempLine = line.replace(width,modifyWidth)
            direction,width,signalvalue = tempLine.split(",")
            width = width.replace('#',',')

            self.logging.debug(f"width = {width} lineNo = {sys._getframe().f_lineno}")

        else:
            line = line.replace(' ','')
            direction,width,signalvalue = line.split(",")
       
        return direction,width,signalvalue

    def read_module_info(self, type, inst_name=""):

        self.logging.info(f"inst name = {inst_name}")
        tmp_content = ""
        linelist = []
        flag = 0
        keyword_begin = "deadbeef"
        keyword_end = "deafbeef"
        if type == "csv":
            keyword_begin = "csv_begin"
            keyword_end = "csv_end"
            filename = self.filename
        if type == "para":
            keyword_begin = "parameter_begin"
            keyword_end = "parameter_end"
            self.logging.info("gen the para")
            filename = self.fullpath

        if type == "port":
            keyword_begin = "port_begin"
            keyword_end = "port_end"
            filename = self.fullpath

        if type == "before_port":
            keyword_begin = "#keep_begin before_port"
            keyword_end = "#keep_end before_port"
            filename = self.fullpath

        self.logging.info(f"inst name = {inst_name}, filename = {filename}")
        checkValue = ""

        if '.sv' in filename or '.v' in filename or '.csv' in filename:
            pass
        else:
            print(f"The file format of {filename} is wrong")
            exit()

        with open(filename, "r") as fr:
            for line in fr:
                if type == "csv":
                    tmp_content += line
                if keyword_begin in line:
                    flag = 1
                    continue
                if keyword_end in line:
                    flag = 0
                    break
                if flag == 1:
                    linelist.append(line.strip())

        if type == "csv":
            return (tmp_content, linelist)

        for line in linelist:
            if "`" in line:
                tmp_content += line+"\n"
            else:
                if inst_name == "":
                    inst_name = "u_" + self.inst_name

                if type == "para":
                    _,signalname, signalvalue = line.split(",")
                    tmp_content += "connect,{}.{},{}\n".format(inst_name, signalname.ljust(70), signalvalue)

                if type == "port" or type == "before_port":
                    
                    direction, width, signalname = self.get_mod_port_str(line)
                    connect_name = signalname

                    if "input" in direction:
                        attr = "I"

                    elif "output" in direction:
                        attr = "O"

                    elif "inout" in direction:
                        attr = "IO"

                    else:
                        attr = "IF"
                        if signalname.strip().endswith('_m'):
                            connect_name = signalname[0:(len(signalname)-2)] + "_m"

                        elif signalname.strip().endswith('_s'):
                            connect_name = signalname[0:(len(signalname)-2)] + "_s"
                            
                        else:
                            connect_name = signalname
                    
                    #----------------------------------------change width # to ,----------------------------------------------------
                    if '#' in width:
                        width = width.replace('#',',')
                    #===============================================================================================================

                    tmp_content += "connect,{}.{},{},{},{},{}\n".format(inst_name, signalname.ljust(30),(connect_name+ width).ljust(40), attr.ljust(10), direction,checkValue.rjust(10))

        return (tmp_content)

    def write_csv(self, output_filename,path="./sb_output/"):
        with open(output_filename, "w") as fw:
            fw.write(self.content)

        print("Info: {} Generated!".format(output_filename))
        fileName = os.path.basename(output_filename)
        shutil.copy(output_filename,path + os.sep + fileName)


    def gen_connect(self,inst_name):
        self.logging.info(f"get_connect inst_name = {inst_name}")
        tmp_content = ""
        tmp_content += "#para_inst_begin\n"
        tmp_content += self.read_module_info("para",inst_name)
        tmp_content += "#para_inst_end\n"
        tmp_content += "#port_inst_begin\n"
        
        tmp_content += self.read_module_info("before_port",inst_name)
        tmp_content += self.read_module_info("port",inst_name)
        tmp_content += "#port_inst_end\n"
        return (tmp_content)

    def gen_inst(self,inst_name_u):
        tmp_content = ""
        tmp_content += "#inst_begin==========================================================================================================="
        for item in self.csvlist:
            # gen inst_name
            self.fullpath = item
            inst_name = os.path.basename(item)
            self.logging.info(inst_name)
            self.inst_name = inst_name[:inst_name.find(".")]
            # inst_name_u = "u" + inst_name[:inst_name.find(".")].split('_u')[1]
            self.logging.info(self.inst_name)
            tmp_content += "\ninst {} {}\n".format(self.inst_name, inst_name_u)
            # gen connect
            tmp_content += self.gen_connect(inst_name_u)
        tmp_content += "#inst_end=============================================================================================================\n"
        return (tmp_content)

    def del_same_elements(self,list1,list2):
        same = list(set(list1) & set(list2))
        for i in same:
            list1.remove(i)
            list2.remove(i)

        self.logging.debug(f"test list1={list1}")
        self.logging.debug(f"test list2={list2}")
        return list1

    def del_same_inst_elements(self,list1,list2):
        same = list(set(list1) & set(list2))
        for i in same:
            list1.remove(i)
            list2.remove(i)

        self.logging.debug(f"test list1={list1}")
        self.logging.debug(f"test list2={list2}")
        return list1,list2

    def conbine_list_elements(self,a_list,b_list):
        
        a_list.extend(b_list)

        res = sorted(list(set(a_list)), reverse=True)
        self.logging.debug(res)
        return res

    def gen_top_port(self,topFile,path='./sb_output/'):
        file_input_list = []
        file_output_list = []

        top_input_list = []
        top_output_list = []

        total_input_list = []
        total_output_list = []

        dictInputPort = {}
        dictOutputPort = {}

        filelist = []

        files = os.listdir(path)
        for file in files:
            filePath = os.path.join(path,file)
            if '_u' in file:
                filelist.append(filePath)

            elif '_out' in file:
                newTopFile = filePath
                self.logging.info(f"The new top file = {newTopFile}")
            else:
                self.logging.info(f"The old top file is wrong")

        oldTopFile = topFile

        self.logging.info(filelist)
        tempList = copy.deepcopy(filelist)
        for i in range(len(filelist)):
            filePath = tempList.pop(i)
            file_input_list,file_output_list = self.get_file_port(filePath)

            self.logging.info(f"{filePath},{tempList}")
            total_input_list,total_output_list = self.get_files_port(tempList)

            self.logging.debug(f"--input-total---{i}----{total_input_list}")
            self.logging.debug(f"--output-total---{i}----{total_output_list}")

            dictInputPort[i] = self.del_same_elements(file_input_list,total_output_list)
            dictOutputPort[i] = self.del_same_elements(file_output_list,total_input_list)

            tempList = copy.deepcopy(filelist)

        top_input_list,top_output_list = self.get_file_port(oldTopFile)

        for i in range(len(filelist)):
            top_temp_input_list = self.conbine_list_elements(top_input_list,dictInputPort[i])
            top_temp_output_list = self.conbine_list_elements(top_output_list,dictOutputPort[i])

        self.logging.debug(f"top_temp_input_list = {top_temp_input_list}")
        self.logging.debug(f" top_temp_output_list = {top_temp_output_list}")

        self.write_new_csv(oldTopFile,top_temp_input_list,top_temp_output_list)

        return

    def compare_master_list_element(self,srcList,dstList):
        master_match_list = []
        flag1 = False
        flag2 = False

        for item in srcList:
            item = item.strip()
            match_value1 = item + '_m'
            match_value2 = item + '.master'

            flag1 =  self.port_equal_list(match_value1,dstList)
            flag2 =  self.port_equal_list(match_value2,dstList)

            if flag1 == True:
                 master_match_list.append(match_value1)

            if flag2 == True:
                 master_match_list.append(match_value2)

            self.logging.debug(f"flag1 = {flag1},match_value1 = {match_value1}, match_value2 = {match_value2},flag2 = {flag2}")

        return master_match_list

    def compare_slave_list_element(self,srcList,dstList):
        slave_match_list = []

        for item in srcList:
            item = item.strip()
            match_value1 = item + '_s'
            match_value2 = item + '.slave'

            flag1 =  self.port_equal_list(match_value1,dstList)
            flag2 =  self.port_equal_list(match_value2,dstList)

            if flag1 == True:
                 slave_match_list.append(match_value1)

            if flag2 == True:
                 slave_match_list.append(match_value2)

            self.logging.debug(f"flag1 = {flag1},match_value1 = {match_value1}, match_value2 = {match_value2},flag2 = {flag2}")
                 
        return slave_match_list

    def get_top_one_inst_wiretype(self,topFile,inst_name):
        dictWire = {}
        dictMod = {}
        tempList = []

        with open(topFile,newline='') as fr:
            # csvReader = csv.reader(csvfile,delimiter=' ',quotechar='|')
            lines = fr.readlines()
            for row in lines:
                # if "input" in row or "output" in row:
                if 'connect' in row and inst_name in row:
                    tempList = deal_with_port_str(row)
                    if tempList:
                        keyword,signal_name,port_width,wireType,direction,checkValue = tempList
                        port_width = port_width.replace(" ","")
                        connectName,width = self.get_width_connection_str(port_width)
                        connectName = connectName.strip()

                    else:
                        continue

                    if "input," in row.strip('\n'):
                        # connectName = 'input%' +  connectName.strip()
                        dictWire[connectName] = wireType.strip()
                        self.logging.debug(f"input= {connectName},wireType = {wireType}")

                    elif "inout," in row.strip('\n'):
                        # connectName = 'inout%' +  connectName.strip()
                        dictWire[connectName] = wireType.strip()
                        self.logging.debug(f"inout = {connectName},wireType = {wireType}")

                    elif "output," in row.strip('\n'):
                        # connectName = 'output%' +  connectName.strip()
                        dictWire[connectName] = wireType.strip()
                        self.logging.debug(f"output = {connectName},wireType = {wireType}")

                    else:
                        if "master," in row.strip('\n') or "slave," in row.strip('\n'):

                            if 'M' in wireType or "IF" in wireType or 'm' in wireType or "if" in wireType:

                                dictMod[port_width.strip()] = wireType.strip()
                                self.logging.debug(f"mod interface = {connectName},wireType = {wireType}")

        return dictWire,dictMod

    def gen_top_port_from_top_csv(self,topFile,inst_name,exeCmd,path='./sb_output/'):
        if "updatec" == exeCmd:
            self.inst_name_list = []
            self.inst_name_list.append(inst_name)

        for inst_value in self.inst_name_list:
            inst_name = inst_value.split(' ')[-1].strip()
            self.logging.debug(f"##### {inst_value} start to match other module and cmd = {exeCmd} #######")
            self.gen_inst_port_from_top_csv(topFile,inst_name,exeCmd)

    def gen_inst_port_from_top_csv(self,topFile,inst_name,exeCmd,path='./sb_output/'):
        top_input_list = []
        top_output_list = []
        total_input_list = []
        total_output_list = []
        total_mod_list = []
        dict_intf = {}
        total_intf_master_list = []
        total_intf_slave_list = []
        total_intf_dict = {}
        inst_intf_master_list = []
        inst_intf_slave_list = []


        if "update" in exeCmd:

            inst_input_list,inst_output_list,inst_mod_list,inst_inoutList,inst_dict_intf = self.get_top_file_one_inst_port(topFile,inst_name)
        # inst_input_same_list = list(set(inst_input_list) & set(top_inst_input_list))
        # inst_output_same_list = list(set(inst_output_list) & set(top_inst_output_list))
        # inst_mod_same_list = list(set(inst_mod_list) & set(top_inst_mod_list))
        # inst_intf_same_list = list(set(inst_dict_intf) & set(top_inst_dict_intf))

        # self.total_inst_same_list.extend(inst_input_same_list)
        # self.total_inst_same_list.extend(inst_output_same_list) 
        # self.total_inst_same_list.extend(inst_mod_same_list) 
        # self.total_inst_same_list.extend(inst_intf_same_list) 
        ####################################instance master and slave list##########################################################
        else:
            inst_input_list,inst_output_list,inst_mod_list,inst_inoutList,inst_dict_intf = self.get_top_one_inst_port(topFile,inst_name)

        self.logging.debug(f"--inst_input_list------{inst_input_list}")
        self.logging.debug(f"--inst_output_list-------{inst_output_list}")
        self.logging.debug(f"--inst_mod_list-------{inst_mod_list}")
        ############################################################################################################################

        ####################################total master and slave list#############################################################
        total_input_list,total_output_list,total_mod_list,inoutList,dict_intf = self.get_top_all_inst_port(topFile,inst_name)

        self.logging.debug(f"--total_input_list------{total_input_list}")
        self.logging.debug(f"--total_output_list-------{total_output_list}")
        self.logging.debug(f"--total_mod_list-------{total_mod_list}")
        ############################################################################################################################


        ####################################instance master and slave list##########################################################
        master_mod_list = [value.split('.master')[0] for value in inst_mod_list if value.endswith('.master')]
        slave_mod_list = [value.split('.slave')[0] for value in inst_mod_list if value.endswith('.slave')]

        master_intf_list = [value[:-2] for value in inst_mod_list if value.endswith('_m')]
        slave_intf_list = [value[:-2] for value in inst_mod_list if value.endswith('_s')]

        inst_intf_master_list.extend(master_mod_list)
        inst_intf_master_list.extend(master_intf_list)

        inst_intf_slave_list.extend(slave_intf_list)
        inst_intf_slave_list.extend(slave_mod_list)

        self.logging.debug(f"--inst_intf_master_list-------{inst_intf_master_list}")
        self.logging.debug(f"--inst_intf_slave_list-------{inst_intf_slave_list}")

        ###########################################################################################################################


        ####################################total master and slave list############################################################
        master_mod_list = [value.split('.master')[0] for value in total_mod_list if value.endswith('.master')]
        slave_mod_list = [value.split('.slave')[0] for value in total_mod_list if value.endswith('.slave')]

        master_intf_list = [value[:-2] for value in total_mod_list if value.endswith('_m')]
        slave_intf_list = [value[:-2] for value in total_mod_list if value.endswith('_s')]

        total_intf_master_list.extend(master_mod_list)
        total_intf_master_list.extend(master_intf_list)

        total_intf_slave_list.extend(slave_mod_list)
        total_intf_slave_list.extend(slave_intf_list)
        self.logging.debug(f"--total_intf_master_list-------{total_intf_master_list}")
        self.logging.debug(f"--total_intf_slave_list-------{total_intf_slave_list}")

        ###########################################################################################################################

        #                         Get the top interface contents                                                                 #

        ####################################delete match signal####################################################################

        inst_master_list = list(set(inst_intf_master_list) & set(total_intf_slave_list))
        inst_slave_list = list(set(inst_intf_slave_list) & set(total_intf_master_list))

        self.logging.debug(f"--inst_master_list-------{inst_master_list}")
        self.logging.debug(f"--inst_slave_list-------{inst_slave_list}")

        ###########################################################################################################################

        match_master_list = self.compare_master_list_element(inst_master_list,inst_mod_list)
        slave_master_list = self.compare_slave_list_element(inst_slave_list,inst_mod_list)


        total_inst_match_list = []
        total_inst_match_list.extend(match_master_list)
        total_inst_match_list.extend(slave_master_list)

        self.logging.debug(f"--match_master_list-------{match_master_list}\n")
        self.logging.debug(f"--slave_master_list-------{slave_master_list}\n,total_inst_match_list = {total_inst_match_list}\n")

        ###########################################################################################################################
        ssignInputList = []
        assignOutputList = []
        assignInputList,assignOutputList = parseAssign(topFile)
        assignInputList = list(set(assignInputList))
        assignOutputList = list(set(assignOutputList))
        self.logging.debug(f"assignInputList = {assignInputList}\n,assignOutputList = {assignOutputList}\n")


        #########################################################################################################################

        ###########################################################################################################################
        top_input_wire_list = [item for item in inst_input_list if item in total_output_list]
        top_input_wire_list_assign = [item for item in inst_input_list if item in assignInputList]
        top_input_wire_list = list(set(top_input_wire_list))
        top_input_wire_list_assign = list(set(top_input_wire_list_assign))
        top_input_wire_list.extend(top_input_wire_list_assign)

        top_output_wire_list = [item for item in inst_output_list if item in total_input_list]
        top_output_wire_list_assign = [item for item in inst_output_list if item in assignOutputList]
        top_output_wire_list = list(set(top_output_wire_list))
        top_output_wire_list_assign = list(set(top_output_wire_list_assign))
        top_output_wire_list.extend(top_output_wire_list_assign)

        self.logging.debug(f"top_input_wire_list = {top_input_wire_list}")
        self.logging.debug(f"top_output_wire_list = {top_output_wire_list}")


        self.logging.debug(f"top_input_list = {top_input_list}")
        self.logging.debug(f"top_output_list = {top_output_list}")


        ###########################################################################################################################
        total_top_wire_list = []
        total_top_wire_list.extend(top_input_wire_list)
        total_top_wire_list.extend(top_output_wire_list)
        self.logging.debug(f"total_top_wire_list = {total_top_wire_list}")

        if 'updatec' == exeCmd: # only update as the author modification
            dictWire = {}
            dictMod = {}

            dictWire,dictMod = self.get_top_one_inst_wiretype(topFile,inst_name)
            self.write_hand_csv(topFile,total_input_list,total_output_list,dictWire,list(set(total_inst_match_list)),inst_name,exeCmd)

        else:
            self.write_new_csv(topFile,total_input_list,total_output_list,total_top_wire_list,list(set(total_inst_match_list)),inst_name,exeCmd)


        return


    def write_new_csv(self,new_top_file,total_input_list,total_output_list,total_top_wire_list,intList,inst_name,exeCmd):
        tempFile =  "./sb_output/write_new_csv.csv"
        validFlag = False
        writeFlag = False
        totalLine = []
        top_temp_input_list = []
        top_temp_output_list = []
        top_temp_intf_dict = {}
        inoutList = []

        with open(new_top_file,newline='') as fr:
            lines = fr.readlines()

            for line in lines:

                if "#port_begin" in line:
                    validFlag = True
                    writeFlag = False
                    totalLine.append(line)
                    
                if "#port_end" in line:
                    validFlag = True
                    writeFlag = True
                              
                if validFlag == True and writeFlag == True:
                    pass

                if writeFlag == True:
                    io_flag = False
                    io_flag1 = False
                    io_flag2 = False
                    io_flag3 = False
                    io_flag4 = False
                    # same_flag =  False

                    # generate module input of top attribute
                    if "input," in line.strip() or "output," in line.strip() or "inout" in line.strip():
                        keyword,signal_name,port_width,wireType,direction,checkValue = deal_with_port_str(line)
                        checkValue = " \n"
                        wireType_old = wireType


                        connectName,width = self.get_width_connection_str(port_width)

                        # if not port_width.replace(" ",""):
                        #     line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), "W".ljust(10), direction,checkValue)
                        #     totalLine.append(line_content)
                        #     continue

                        ###################not modify the same signal(attr,port, port width)#############
                        # same_flag =  self.port_equal_list(connectName.strip(),self.total_inst_same_list)

                        # if same_flag ==  True:
                        #     totalLine.append(line)
                        #     continue
                        ###################not modify the same signal(attr,port, port width)#############

                        if '[0:0]' in port_width:
                            self.logging.debug(f"port_width = {port_width}")
                            port_width = port_width.replace('[0:0]','     ')

                        elif "'b" in port_width and '{' not in port_width:
                            wireType = 'W'

                        else:
                            pass
                        # signalvalue = signal_name.split('.')[1]
                        # print(f"wireType = {wireType},wireType_old = {wireType_old}")

                        if "input," in line.strip():
                            io_flag = self.port_equal_list(connectName.strip(),list(set(total_top_wire_list)))
                            io_flag1 = self.port_equal_list(connectName.strip(),total_input_list)
                            io_flag2 = self.port_equal_list(connectName.strip(),total_output_list)

                            self.logging.debug(f"io_flag = {io_flag},io_flag1 = {io_flag1},direction = {direction},port_width = {port_width}")
                            if io_flag == True:  # match
                                if 'del' in exeCmd:
                                    if inst_name in signal_name: # delete the inst signal
                                        pass
                                    else:
                                        if io_flag1 == True:
                                            if io_flag2 == True:
                                                if wireType_old == 'O' or wireType_old == 'o':
                                                    wireType = "O"
                                                else:
                                                    wireType = "W"
                                            else:
                                                wireType = "I"
                                        else:
                                            wireType = "I"
                                else:
                                    if "update" in exeCmd: #update 

                                        io_flag3 = self.port_equal_list(connectName.strip(),self.mod_sig_list)
                                        if io_flag3:
                                            wireType = "W"

                                        else:
                                            wireType = wireType_old

                                    else:
                                        wireType = "W"              #add 

                            else:  # not match
                                if 'del' in exeCmd:
                                    pass
                                else:
                                    if "update" in exeCmd:
                                        # print(f"wireType = {wireType},wireType_old = {wireType_old}")
                                        wireType = wireType_old                 #update 
         

                                    else:                    #add
                                        if inst_name in signal_name:
                                            wireType = "I"

                                        else:
                                            pass
                                
                            line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                            totalLine.append(line_content)


                        # generate module output of top attribute
                        elif "output," in line.strip():

                            io_flag = self.port_equal_list(connectName.strip(),total_top_wire_list)
                            io_flag1 = self.port_equal_list(connectName.strip(),total_input_list)

                            self.logging.debug(f"io_flag = {io_flag},io_flag1 = {io_flag1},direction = {direction},port_width = {port_width}")
                            if io_flag == True:
                                if 'del' in exeCmd:
                                    if inst_name in signal_name: # delete the inst signal
                                        pass

                                    else:
                                        if io_flag1 == True:
                                            wireType = "W"

                                        else:
                                            wireType = "O"
                                else:    
                                    #add and update
                                    if "update" in exeCmd:  #update
                                        # print(f"wireType = {wireType},wireType_old = {wireType_old}")

                                        io_flag3 = self.port_equal_list(connectName.strip(),self.mod_sig_list)
                                        if io_flag3:
                                            wireType = "W"

                                        else:
                                            wireType = wireType_old

                                    else:               #add  
                                        wireType = "W"

                            else:
                                if 'del' in exeCmd:
                                    pass
                                else:  

                                    if "update" in exeCmd: #update 
                                        # print(f"wireType = {wireType},wireType_old = {wireType_old}")
                                        wireType = wireType_old

                                    else:   #add 
                                        if inst_name in signal_name:
                                            wireType = "O"

                                        else:
                                            pass

                            line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                            totalLine.append(line_content)
                    

                        else:
                            line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                            totalLine.append(line_content)

                        wireType = wireType.strip()
                        if "I" == wireType or "i" == wireType:
                            top_temp_input_list.append(port_width.strip())

                        elif "O" == wireType or "o" == wireType:
                            top_temp_output_list.append(port_width.strip())

                        elif "IO" == wireType or "io" == wireType:
                            inoutList.append(port_width.strip())

                        else:
                            pass

                    else:
                        if 'master,' in line.strip() or 'slave,' in line.strip():
                            keyword,signal_name,port_width,wireType,direction,checkValue = deal_with_port_str(line)
                            checkValue = " \n"
                            wireType = wireType.strip()
                            wireType_old = wireType

                            if 'M' == wireType or 'IF' == wireType or 'm' == wireType or 'if' == wireType:
                                signalvalue = port_width.strip()
                                self.logging.debug(f"signalvalue = {signalvalue} wireType = {wireType}")

                                io_flag = self.port_equal_list(signalvalue,intList)
                                self.logging.debug(f"io_flag = {io_flag},direction = {direction}")

                                if io_flag == False:
                                    if 'master' in port_width:
                                        signalvalue1 = port_width.strip().split(".master")[0] + '.slave'
                                        io_flag1 = self.port_equal_list(signalvalue1,intList)

                                        signalvalue2 = port_width.strip().split(".master")[0] + '_s'
                                        io_flag2 = self.port_equal_list(signalvalue2,intList)
                                        self.logging.debug(f"io_flag1 = {io_flag1},io_flag2 = {io_flag2}")
                                        self.logging.debug(f"signalvalue = {signalvalue},signalvalue1 = {signalvalue1},signalvalue2 = {signalvalue2},wireType = {wireType}")
                                        
                                        if io_flag1 or io_flag2:

                                            if 'del' in exeCmd:
                                                wireType = 'IF'

                                            else:
                                                if "update" in exeCmd:  #update
                                                # print(f"wireType = {wireType},wireType_old = {wireType_old}")

                                                    io_flag3 = self.port_equal_list(signalvalue1,self.mod_sig_list)
                                                    io_flag4 = self.port_equal_list(signalvalue2,self.mod_sig_list)

                                                    if io_flag3 or io_flag4:
                                                        wireType = "M"

                                                    else:
                                                        wireType = wireType_old

                                                else:               #add  
                                                    wireType = "M"

                                        else:
                                            pass

                                        if (wireType_old == 'M' or wireType_old == 'm') and (wireType == 'IF' or wireType == 'if'):
                                            port_width = port_width.split(".master")[0] + '_m     ' + port_width.split(".master")[1]

                                        line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                                        totalLine.append(line_content)

                                    elif 'slave' in port_width:
                                        signalvalue1 = port_width.strip().split(".slave")[0] + '.master'
                                        io_flag1 = self.port_equal_list(signalvalue1,intList)

                                        signalvalue2 = port_width.strip().split(".slave")[0] + '_m'
                                        io_flag2 = self.port_equal_list(signalvalue2,intList)
                                        self.logging.debug(f"io_flag1 = {io_flag1},io_flag2 = {io_flag2}")
                                        self.logging.debug(f"signalvalue = {signalvalue},signalvalue1 = {signalvalue1},signalvalue2 = {signalvalue2},wireType = {wireType}")
                                        
                                        if io_flag1 or io_flag2:
                                            if 'del' in exeCmd:
                                                wireType = 'IF'
                                            else:
                                                if "update" in exeCmd:  #update
                                                # print(f"wireType = {wireType},wireType_old = {wireType_old}")

                                                    io_flag3 = self.port_equal_list(signalvalue1,self.mod_sig_list)
                                                    io_flag4 = self.port_equal_list(signalvalue2,self.mod_sig_list)

                                                    if io_flag3 or io_flag4:
                                                        wireType = "M"

                                                    else:
                                                        wireType = wireType_old

                                                else:               #add  
                                                    wireType = "M"
                                        
                                        else:
                                            pass

                                        if (wireType_old == 'M' or wireType_old == 'm') and (wireType == 'IF' or wireType == 'if'):
                                            port_width = port_width.split(".slave")[0] + '_s    ' + port_width.split(".slave")[1]

                                        line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                                        totalLine.append(line_content)
                                    
                                    else:
                                        if port_width.strip().endswith('_m'):
                                            signalvalue1 = port_width.strip().split("_m")[0] + '_s'
                                            io_flag1 = self.port_equal_list(signalvalue1,intList)

                                            signalvalue2 = port_width.strip().split("_m")[0] + '.slave'
                                            io_flag2 = self.port_equal_list(signalvalue2,intList)
                                            self.logging.debug(f"signalvalue = {signalvalue},signalvalue1 = {signalvalue1},signalvalue2 = {signalvalue2},wireType = {wireType}")
                                            self.logging.debug(f"io_flag1 = {io_flag1},io_flag2 = {io_flag2}")
                                            

                                            if io_flag1 or io_flag2:

                                                if 'del' in exeCmd:
                                                    wireType = 'IF'
                                                else:
                                                    if "update" in exeCmd:  #update
                                                    # print(f"wireType = {wireType},wireType_old = {wireType_old}")

                                                        io_flag3 = self.port_equal_list(signalvalue1,self.mod_sig_list)
                                                        io_flag4 = self.port_equal_list(signalvalue2,self.mod_sig_list)

                                                        if io_flag3 or io_flag4:
                                                            wireType = "M"

                                                        else:
                                                            wireType = wireType_old

                                                    else:               #add  
                                                        wireType = "M"
                                            
                                            else:
                                                pass

                                            if (wireType_old == 'IF' or wireType_old == 'if') and (wireType == 'M' or wireType == 'm'):
                                                port_width = port_width.split("_m")[0] + '.master' + port_width.split("_m")[1][5:]

                                            line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                                            totalLine.append(line_content)

                                        elif port_width.strip().endswith('_s'):
                                            signalvalue1 = port_width.strip().split("_s")[0] + '_m'
                                            io_flag1 = self.port_equal_list(signalvalue1,intList)
                                            
                                            signalvalue2 = port_width.strip().split("_s")[0] + '.master'
                                            io_flag2 = self.port_equal_list(signalvalue2,intList)
                                            self.logging.debug(f"signalvalue = {signalvalue},signalvalue1 = {signalvalue1},signalvalue2 = {signalvalue2},wireType = {wireType}")
                                            self.logging.debug(f"io_flag1 = {io_flag1},io_flag2 = {io_flag2}")
                                            
                                            if io_flag1 or io_flag2:

                                                if 'del' in exeCmd:
                                                    wireType = 'IF'

                                                else:
                                                    if "update" in exeCmd:  #update
                                                    # print(f"wireType = {wireType},wireType_old = {wireType_old}")

                                                        io_flag3 = self.port_equal_list(signalvalue1,self.mod_sig_list)
                                                        io_flag4 = self.port_equal_list(signalvalue2,self.mod_sig_list)

                                                        if io_flag3 or io_flag4:
                                                            wireType = "M"

                                                        else:
                                                            wireType = wireType_old

                                                    else:               #add  
                                                        wireType = "M"
                                            else:
                                                pass

                                            if (wireType_old == 'IF' or wireType_old == 'if') and (wireType == 'M' or wireType == 'm'):
                                                port_width = port_width.split("_s")[0] + '.slave' + port_width.split("_s")[1][4:]

                                            line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                                            totalLine.append(line_content)

                                        else:
                                            totalLine.append(line)

                                else: # the inst ownself match signal
                                    if 'del' == exeCmd:
                                        pass
                                    else:
                                        if "update" in exeCmd:  #update
                                        # print(f"wireType = {wireType},wireType_old = {wireType_old}")

                                            io_flag3 = self.port_equal_list(signalvalue,self.mod_sig_list)

                                            if io_flag3 :
                                                wireType = "M"

                                            else:
                                                wireType = wireType_old

                                        else:               #add  
                                            wireType = "M"

                                    line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                                    totalLine.append(line_content)

                            else: # other wiretype
                                # totalLine.append(line)
                                wireType = 'IF'
                                line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                                totalLine.append(line_content)

                        else:  # not master or slave
                            totalLine.append(line)

                    validFlag = False
                    
                elif validFlag == True:  # pre top port info
                    pass

                else:   # write top parameter and module info
                    if line:
                        totalLine.append(line)
                    self.logging.debug(line.strip('\n'))

            self.logging.debug(f"top_temp_input_list = {top_temp_input_list}\n,top_temp_output_list = {top_temp_output_list}\n,inoutList = {inoutList}\n,top_temp_intf_dict = {top_temp_intf_dict}")

        match_width = re.compile(r'\{.*\}')   
        with open(tempFile,'w', encoding='UTF-8') as fw:
            for item in totalLine:
                if "port_begin" in item:
                    fw.write(item)

                    for data in top_temp_intf_dict.keys():
                        line_tmp = top_temp_intf_dict[data] + ',,' + data

                        fw.write(line_tmp + '\n')

                    for data in list(set(top_temp_input_list)):

                        direction = 'input'
                        if '{' in data and '}' in data:
                            width = match_width.findall(data)[0]
                            signal_name = ""
                            self.logging.debug(f"width = {width} signal_name = {signal_name}")

                        elif '[' in data:
                            width = '[' + data.split('[')[1].split(']')[0] + ']'
                            if len(data.split('[')[1].split(']')[0]) == 1:
                                width = ""
                            signal_name = data.split('[')[0]

                        else:
                            width = ''
                            signal_name = data

                        line_tmp = direction + ',' + width + ',' + signal_name
                        fw.write(line_tmp + '\n')

                    for data in list(set(top_temp_output_list)):

                        direction = 'output'
                        if '{' in data and '}' in data:
                            width = match_width.findall(data)[0]
                            signal_name = ""
                            self.logging.debug(f"width = {width} signal_name = {signal_name}")

                        elif '[' in data:
                            width = '[' + data.split('[')[1].split(']')[0] + ']'
                            if len(data.split('[')[1].split(']')[0]) == 1:
                                width = ""
                            signal_name = data.split('[')[0]

                        else:
                            width = ''
                            signal_name = data
                            
                        line_tmp = direction + ',' + width + ',' + signal_name
                        fw.write(line_tmp+ '\n')

                    for data in list(set(inoutList)):
                        direction = 'inout'

                        if '[' in data:
                            width = '[' + data.split('[')[1].split(']')[0] + ']'
                            if len(data.split('[')[1].split(']')[0]) == 1:
                                width = ""
                            signal_name = data.split('[')[0]

                        else:
                            width = ''
                            signal_name = data
                            
                        line_tmp = direction + ',' + width + ',' + signal_name
                        fw.write(line_tmp+ '\n')
                else:
                    fw.write(item)
                
        shutil.copy(tempFile,new_top_file)
        # os.remove(tempFile)

        return


    def write_hand_csv(self,new_top_file,total_input_list,total_output_list,dictWire,intList,inst_name,exeCmd):
        tempFile =  "./sb_output/write_hand_csv.csv"
        validFlag = False
        writeFlag = False
        totalLine = []
        top_temp_input_list = []
        top_temp_output_list = []
        top_temp_intf_dict = {}
        inoutList = []

        with open(new_top_file,newline='') as fr:
            lines = fr.readlines()

            for line in lines:

                if "#port_begin" in line:
                    validFlag = True
                    writeFlag = False
                    totalLine.append(line)
                    
                if "#port_end" in line:
                    validFlag = True
                    writeFlag = True
                              
                if validFlag == True and writeFlag == True:
                    pass

                if writeFlag == True:
                    io_flag = False

                    # generate module input of top attribute
                    if "input," in line.strip() or "output," in line.strip() or "inout" in line.strip():
                        keyword,signal_name,port_width,wireType,direction,checkValue = deal_with_port_str(line)
                        checkValue = " \n"
                        wireType_old = wireType
                        connectName,width = self.get_width_connection_str(port_width)
                        if '[0:0]' in port_width:
                            self.logging.debug(f"port_width = {port_width}")
                            port_width = port_width.replace('[0:0]','     ')

                        elif "'b" in port_width and '{' not in port_width:
                            wireType = 'W'

                        else:
                            pass

                        io_flag = self.port_equal_list(connectName.strip(),dictWire.keys())

                        self.logging.debug(f"io_flag = {io_flag},direction = {direction},port_width = {port_width}")
                        if io_flag == True:
                            wireType = dictWire[connectName.strip()]
                        else:
                            pass
                            
                        line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                        totalLine.append(line_content)

                        wireType = wireType.strip()
                        if "I" == wireType or "i" == wireType:
                            top_temp_input_list.append(port_width.strip())

                        elif "O" == wireType or "o" == wireType:
                            top_temp_output_list.append(port_width.strip())

                        elif "IO" == wireType or "io" == wireType:
                            inoutList.append(port_width.strip())

                        else:
                            pass

                    else:
                        if 'master,' in line.strip() or 'slave,' in line.strip():
                            keyword,signal_name,port_width,wireType,direction,checkValue = deal_with_port_str(line)
                            checkValue = " \n"
                            wireType = wireType.strip()
                            wireType_old = wireType

                            if 'M' == wireType or 'IF' == wireType or 'm' == wireType or 'if' == wireType:
                                signalvalue = port_width.strip()
                                self.logging.debug(f"signalvalue = {signalvalue} wireType = {wireType}")

                                io_flag = self.port_equal_list(signalvalue,intList)
                                self.logging.debug(f"io_flag = {io_flag},direction = {direction}")

                                if io_flag == False:
                                    if 'master' in port_width:
                                        signalvalue1 = port_width.strip().split(".master")[0] + '.slave'
                                        io_flag1 = self.port_equal_list(signalvalue1,intList)

                                        signalvalue2 = port_width.strip().split(".master")[0] + '_s'
                                        io_flag2 = self.port_equal_list(signalvalue2,intList)
                                        self.logging.debug(f"io_flag1 = {io_flag1},io_flag2 = {io_flag2}")
                                        self.logging.debug(f"signalvalue = {signalvalue},signalvalue1 = {signalvalue1},signalvalue2 = {signalvalue2},wireType = {wireType}")
                                        
                                        if io_flag1 or io_flag2:

                                            wireType = 'M'
                                        else:
                                            pass

                                        if (wireType_old == 'M' or wireType_old == 'm') and (wireType == 'IF' or wireType == 'if'):
                                            port_width = port_width.split(".master")[0] + '_m     ' + port_width.split(".master")[1]

                                        line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                                        totalLine.append(line_content)

                                    elif 'slave' in port_width:
                                        signalvalue1 = port_width.strip().split(".slave")[0] + '.master'
                                        io_flag1 = self.port_equal_list(signalvalue1,intList)

                                        signalvalue2 = port_width.strip().split(".slave")[0] + '_m'
                                        io_flag2 = self.port_equal_list(signalvalue2,intList)
                                        self.logging.debug(f"io_flag1 = {io_flag1},io_flag2 = {io_flag2}")
                                        self.logging.debug(f"signalvalue = {signalvalue},signalvalue1 = {signalvalue1},signalvalue2 = {signalvalue2},wireType = {wireType}")
                                        
                                        if io_flag1 or io_flag2:
                 
                                            wireType = 'M'
                                        
                                        else:
                                            pass

                                        if (wireType_old == 'M' or wireType_old == 'm') and (wireType == 'IF' or wireType == 'if'):
                                            port_width = port_width.split(".slave")[0] + '_s    ' + port_width.split(".slave")[1]

                                        line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                                        totalLine.append(line_content)
                                    
                                    else:
                                        if port_width.strip().endswith('_m'):
                                            signalvalue1 = port_width.strip().split("_m")[0] + '_s'
                                            io_flag1 = self.port_equal_list(signalvalue1,intList)

                                            signalvalue2 = port_width.strip().split("_m")[0] + '.slave'
                                            io_flag2 = self.port_equal_list(signalvalue2,intList)
                                            self.logging.debug(f"signalvalue = {signalvalue},signalvalue1 = {signalvalue1},signalvalue2 = {signalvalue2},wireType = {wireType}")
                                            self.logging.debug(f"io_flag1 = {io_flag1},io_flag2 = {io_flag2}")
                                            

                                            if io_flag1 or io_flag2:

                                                wireType = 'M'
                                        
                                            else:
                                                pass

                                            if (wireType_old == 'IF' or wireType_old == 'if') and (wireType == 'M' or wireType == 'm'):
                                                port_width = port_width.split("_m")[0] + '.master' + port_width.split("_m")[1][5:]

                                            line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                                            totalLine.append(line_content)

                                        elif port_width.strip().endswith('_s'):
                                            signalvalue1 = port_width.strip().split("_s")[0] + '_m'
                                            io_flag1 = self.port_equal_list(signalvalue1,intList)
                                            
                                            signalvalue2 = port_width.strip().split("_s")[0] + '.master'
                                            io_flag2 = self.port_equal_list(signalvalue2,intList)
                                            self.logging.debug(f"signalvalue = {signalvalue},signalvalue1 = {signalvalue1},signalvalue2 = {signalvalue2},wireType = {wireType}")
                                            self.logging.debug(f"io_flag1 = {io_flag1},io_flag2 = {io_flag2}")
                                            
                                            if io_flag1 or io_flag2:

                                                wireType = 'M'
                                            else:
                                                pass

                                            if (wireType_old == 'IF' or wireType_old == 'if') and (wireType == 'M' or wireType == 'm'):
                                                port_width = port_width.split("_s")[0] + '.slave' + port_width.split("_s")[1][4:]

                                            line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                                            totalLine.append(line_content)

                                        else:
                                            totalLine.append(line)

                                else: # the inst ownself match signal

                                    wireType = 'M'

                                    line_content = "{},{},{},{},{},{}".format(keyword,signal_name.ljust(30), (port_width).ljust(30), wireType.ljust(10), direction,checkValue)
                                    totalLine.append(line_content)

                            else: # other wiretype
                                totalLine.append(line)

                        else:  # not master or slave
                            totalLine.append(line)

                    validFlag = False
                    
                elif validFlag == True:  # pre top port info
                    pass
                else:   # write top parameter and module info
                    if line:
                        totalLine.append(line)
                    self.logging.debug(line.strip('\n'))

            self.logging.debug(f"top_temp_input_list = {top_temp_input_list}\n,top_temp_output_list = {top_temp_output_list}\n,inoutList = {inoutList}\n")

        match_width = re.compile(r'\{.*\}')
        with open(tempFile,'w', encoding='UTF-8') as fw:
            for item in totalLine:
                if "port_begin" in item:
                    fw.write(item)

                    for data in top_temp_intf_dict.keys():
                        line_tmp = top_temp_intf_dict[data] + ',,' + data

                        fw.write(line_tmp + '\n')

                    for data in list(set(top_temp_input_list)):
                        direction = 'input'
                        if '{' in data and '}' in data:
                            width = match_width.findall(data)[0]
                            signal_name = ""
                            self.logging.debug(f"width = {width} signal_name = {signal_name}")
                        elif '[' in data:
                            width = '[' + data.split('[')[1].split(']')[0] + ']'
                            signal_name = data.split('[')[0]
                        else:
                            width = ''
                            signal_name = data

                        line_tmp = direction + ',' + width + ',' + signal_name
                        fw.write(line_tmp + '\n')

                    for data in list(set(top_temp_output_list)):
                        direction = 'output'
                        if '{' in data and '}' in data:
                            width = match_width.findall(data)[0]
                            signal_name = ""
                            self.logging.debug(f"width = {width} signal_name = {signal_name}")
                        elif '[' in data:
                            width = '[' + data.split('[')[1].split(']')[0] + ']'
                            signal_name = data.split('[')[0]
                        else:
                            width = ''
                            signal_name = data
                            
                        line_tmp = direction + ',' + width + ',' + signal_name
                        fw.write(line_tmp+ '\n')

                    for data in list(set(inoutList)):
                        direction = 'inout'
                        if '[' in data:
                            width = '[' + data.split('[')[1].split(']')[0] + ']'
                            signal_name = data.split('[')[0]
                        else:
                            width = ''
                            signal_name = data
                            
                        line_tmp = direction + ',' + width + ',' + signal_name
                        fw.write(line_tmp+ '\n')
                else:
                    fw.write(item)
                
        shutil.copy(tempFile,new_top_file)

        return

    def value_in_list(self,value,tempList):
        flag = False
        for item in tempList:
            if value.strip() == item.strip():
                flag = True
        return flag


    def write_list_to_csv(self,tempFile,tempList):

        with open(tempFile,'w', encoding='UTF-8') as fw:
            for item in tempList:

                fw.write(item)


    def check_port_info_to_csv(self,topFile,totalConflict,totalNoload,totalUndrive,totalFloating,mutli_port_conflict,mutli_wireType_conflict):
        tempFile =  "./sb_output/check_port_info_to_csv.csv"
        validFlag = False
        startLable = "#port_inst_begin"
        endLable = "#port_inst_end"
        topFlag = False
        floating_flag = False
        outputList = []
        inputList = []
        inoutList = []
        ifdict = {}
        line_content_list = []

        with open(topFile,newline='') as fr:
            lines = fr.readlines()

            for line in lines:
                checkValue = ""

                if startLable in line:
                    validFlag = True

                if endLable in line:
                    validFlag = False

                if line:
                    if validFlag == True and startLable not in line:
                        keyword,signal_name,port_width,wireType,direction,checkValue = deal_with_port_str(line)
                        connectName,width = self.get_width_connection_str(port_width)

                        checkValue = ""
                        noload_flag = False
                        undrive_flag = False
                        floating_flag = False
                        conflict_flag = False
                        port_width_flag = False
                        wireType_flag = False


                        self.logging.debug(f"connectName = {connectName}")
                        conflict_flag = self.value_in_list(connectName,totalConflict)
                        port_width_flag = self.value_in_list(connectName,mutli_port_conflict)
                        wireType_flag = self.value_in_list(connectName,mutli_wireType_conflict)
                        self.logging.debug(f"conflict_flag = {conflict_flag}")

                        if 'output' in direction:
                            if 'O' == wireType.strip() or 'o' == wireType.strip():
                                outputList.append(port_width.strip())
                                noload_flag = self.value_in_list(connectName,totalNoload)

                            elif 'W' == wireType.strip() or 'w' == wireType.strip():
                                noload_flag = self.value_in_list(connectName,totalNoload)
                                self.logging.debug(f"noload_flag = {noload_flag}")

                            else:
                                pass

                        elif 'input' in direction:
                            if 'I' == wireType.strip() or 'i' == wireType.strip():
                                inputList.append(port_width.strip())

                            elif 'W' == wireType.strip() or 'w' == wireType.strip():
                                undrive_flag = self.value_in_list(connectName,totalUndrive)
                                self.logging.debug(f"undrive_flag = {undrive_flag},port_width = {port_width}")

                            elif 'O' == wireType.strip() or 'o' == wireType.strip():
                                outputList.append(port_width.strip())
                                undrive_flag = self.value_in_list(connectName,totalNoload)
                                self.logging.debug(f"undrive_flag = {undrive_flag}")
                            
                            else:
                                pass

                        elif 'inout' in direction:
                            if 'IO' == wireType.strip() or 'io' == wireType.strip():
                                inoutList.append(port_width.strip())

                            else:
                                pass
                        else:
                            if '.master' in connectName:
                                connectName1 = connectName.replace('.master','')

                            elif '.slave' in connectName:
                                connectName1 = connectName.replace('.slave','')

                            else:
                                connectName1 = connectName

                            floating_flag = self.value_in_list(connectName1,totalFloating)


                            if 'IF' in wireType or 'if' in wireType:
                                ifdict[connectName] = direction.strip()
                                if connectName.strip().endswith('.master') or connectName.strip().endswith('.slave'):
                                    checkValue = "mismacth"

                            else:
                                if port_width.strip().endswith('_m'):
                                    port_width = port_width.replace('_m     ','.master')

                                elif port_width.strip().endswith('_s'):
                                    port_width = port_width.replace('_s    ','.slave')

                                else:
                                    # wireType = 'M'
                                    self.logging.debug(f"\033[1;32mWarning:The {port_width} is IF type \033[0m")

                            self.logging.debug(f"floating_flag = {floating_flag}, connectName = {connectName},checkValue = {checkValue}")

                        if noload_flag:
                            checkValue = "noload" 
                            self.logging.debug(f"noload data = {line}")

                        elif undrive_flag:
                            checkValue = "undrive --- fixme"
                            self.logging.debug(f"undrive data = {line}")

                        elif floating_flag:
                            # checkValue = "floating"

                            if wireType.strip() == "M" or wireType.strip() == "m":
                                checkValue = "floating"
                                # print(connectName)

                            else:
                                pass

                            self.logging.debug(f"floating data = {line}")

                            if port_width.strip().endswith('_m'):
                                port_width = port_width.replace('_m     ','.master')

                            elif port_width.strip().endswith('_s'):
                                port_width = port_width.replace('_s    ','.slave')

                            else:
                                self.logging.debug(f"\033[1;32mWarning:The {port_width} is wrong \033[0m")

                        else:
                            pass

                        if port_width_flag:
                            checkValue = "width_mismatch --- fixme"
                            self.logging.debug(f"conflict data = {line}")

                        if conflict_flag:
                            checkValue = "conflict --- fixme"
                            self.logging.debug(f"conflict data = {line}")

                        if wireType_flag:
                            checkValue = "multi_attrb --- fixme"
                            self.logging.debug(f"conflict data = {line}")

                        
                        if "'b" in port_width and '{' not in port_width:
                            checkValue = "Tie constant"
                            wireType = "W"

                        if not port_width.replace(' ',''):
                            checkValue = "Floating"
                            wireType = "W"

                        if '{' in port_width and '}' in port_width:
                            checkValue = ""

                        line_content = "{},{},{},{},{},{}\n".format(keyword,signal_name.ljust(60), (port_width).ljust(80), wireType.ljust(10), direction, checkValue.strip().rjust(10))
                        line_content_list.append(line_content)

                    else:
                        line_content_list.append(line)

        self.write_list_to_csv(tempFile,line_content_list)

        shutil.copy(tempFile,topFile)

        return inputList,outputList,inoutList,ifdict

    def write_port_info_to_csv(self,topFile,inputList,outputList,inoutList,ifdict):
        tempFile =  "./sb_output/" + "write_port_info_to_csv.csv"
        topFlag = False
        topStartLable = "#port_begin"
        topEndLable = "#port_end"
        validFlag = False
        content_list = []

        with open(topFile,newline='') as fr:
            lines = fr.readlines()
            for line in lines:
                if topStartLable in line:
                    topFlag = True
                    content_list.append(line)
                    continue

                if topEndLable in line:
                    validFlag = True

                if topFlag == True and validFlag == True:
                    for item in ifdict.keys():
                        connectName,width = self.get_width_connection_str(item)
                        dataLine = ifdict[item] + ',' + width + ',' + connectName + '\n'
                        content_list.append(dataLine)

                    inputList_order = sorted(set(inputList),key=inputList.index)

                    for item in inputList_order:
                        connectName,width = self.get_width_connection_str(item)

                        if connectName:
                            if len(width) == 3:
                                width = ""

                            dataLine = 'input' + ',' + width + ',' + connectName + '\n'


                            content_list.append(dataLine)

                        else:
                            pass


                    outputList_order = sorted(set(outputList),key=outputList.index)

                    for item in outputList_order:
                        connectName,width = self.get_width_connection_str(item)
                        if connectName:
                            if len(width) == 3:
                                width = ""

                            dataLine = 'output' + ',' + width + ',' + connectName + '\n'
                            content_list.append(dataLine)

                        else:
                            pass


                    inoutList_order = sorted(set(inoutList),key=inoutList.index)

                    for item in inoutList_order:
                        connectName,width = self.get_width_connection_str(item)

                        if connectName:
                            if len(width) == 3:
                                width = ""

                            dataLine = 'inout' + ',' + width + ',' + connectName + '\n'
                            content_list.append(dataLine)

                        else:
                            pass

                    topFlag = False
                    validFlag = False
                    content_list.append(line)

                elif topFlag == True and validFlag == False:
                    pass

                else:
                    content_list.append(line)

        with open(tempFile,'w', encoding='UTF-8') as fw:
            for item in content_list:
                fw.write(item)

        shutil.copy(tempFile,topFile)
            
        return

    def get_top_inst_port(self,filePath,inst_name):
        inputList = []
        outputList = []

        with open(filePath,newline='') as fr:
            self.logging.info(f"---get_top_inst_port---")
            lines = fr.readlines()
            for row in lines:
                # if "input" in row or "output" in row:
                if inst_name in row:
                    if "input," in row.strip() or "output," in row.strip() or "inout," in row.strip():

                        keyword,signal_name,port_width,wireType,direction,checkValue = deal_with_port_str(row)

                        signalVal = signal_name.replace((inst_name + '.'),"").strip()

                        if '{' in port_width and '}' in port_width:
                            match_width = re.compile(r'\{.*\}')
                            width = match_width.findall(port_width)[0]

                        elif "[" in port_width:
                            width = "[" + port_width.split('[')[1].split(']')[0] + "]"
                            if len(port_width.split('[')[1].split(']')[0]) == 1:
                                width = ""

                        else:
                            width = ""

                        inputList.append(f"{direction}%{signalVal}{width}")

        return inputList

    def get_top_all_inst_port(self,filePath,inst_name):
        inputList = []
        outputList = []
        modList = []
        inoutList = []
        dictMod = {}
        tempList = []

        with open(filePath,newline='') as fr:
            lines = fr.readlines()
            for row in lines:
                if 'connect' in row and inst_name not in row:
                    tempList = deal_with_port_str(row)

                    if tempList:
                        keyword,signal_name,port_width,wireType,direction,checkValue = tempList
                        port_width = port_width.replace(" ","")
                        connectName,width = self.get_width_connection_str(port_width)
                    else:
                        continue

                    if port_width:
                        pass
                    else:    #null connection not involve match
                        continue

                    if "input," in row.strip('\n'):

                        inputList.append(f"{connectName}")
                        self.logging.debug(f"input={connectName}")

                    elif "inout," in row.strip('\n'):
                        if 'io' == wireType.strip() or "IO" == wireType.strip():
                            inoutList.append(f"{connectName}")
                            self.logging.debug(f"inout = {connectName}")

                    elif "output," in row.strip('\n'):

                        outputList.append(f"{connectName}")
                        self.logging.debug(f"output={connectName}")

                    else:
                        if "master," in row.strip('\n') or "slave," in row.strip('\n'):

                            if 'M' in wireType or "IF" in wireType or 'm' in wireType or "if" in wireType:
                                modList.append(f"{connectName}")
                                dictMod[port_width.strip()] = direction.strip()
                                self.logging.debug(f"mod interface={connectName},direction = {direction}")

        return inputList,outputList,modList,inoutList,dictMod

    def get_top_file_one_inst_port(self,filePath,inst_name):
        inputList = []
        outputList = []
        modList = []
        inoutList = []
        dictMod = {}
        tempList = []

        with open(filePath,newline='') as fr:
            lines = fr.readlines()
            for row in lines:
                if 'connect' in row and inst_name in row:
                    tempList = deal_with_port_str(row)

                    if tempList:
                        keyword,signal_name,port_width,wireType,direction,checkValue = tempList
                        port_width = port_width.replace(" ","")
                        connectName,width = self.get_width_connection_str(port_width)
                    else:
                        continue

                    if port_width:
                        pass
                    else:    #null connection not involve match
                        continue

                    if "input," in row.strip('\n'):

                        inputList.append(f"{connectName}")
                        self.logging.debug(f"input={connectName}")

                    elif "inout," in row.strip('\n'):
                        if 'io' == wireType.strip() or "IO" == wireType.strip():
                            inoutList.append(f"{connectName}")
                            self.logging.debug(f"inout = {connectName}")

                    elif "output," in row.strip('\n'):

                        outputList.append(f"{connectName}")
                        self.logging.debug(f"output={connectName}")

                    else:
                        if "master," in row.strip('\n') or "slave," in row.strip('\n'):

                            if 'M' in wireType or "IF" in wireType or 'm' in wireType or "if" in wireType:
                                modList.append(f"{connectName}")
                                dictMod[port_width.strip()] = direction.strip()
                                self.logging.debug(f"mod interface={connectName},direction = {direction}")

        return inputList,outputList,modList,inoutList,dictMod

    def get_top_direct_port(self,filePath):
        inputList = []
        outputList = []
        inoutList = []
        interfaceList = []

        with open(filePath,newline='') as fr:

            lines = fr.readlines()
            for row in lines:

                if 'connect' in row:
                    if row.strip().endswith("input"):
                        keyword,signal_name,port_width,wireType,direction,checkValue = row.split(',')
                        if 'I' == wireType:
                            port_width = port_width.replace(" ","")
                            inputList.append(f"{port_width}")
                            self.logging.debug(f"input ---- {port_width}")

                    elif row.strip().endswith("output"):
                        keyword,signal_name,port_width,wireType,direction,checkValue = row.split(',')
                        if 'O' == wireType:
                            port_width = port_width.replace(" ","")
                            outputList.append(f"{port_width}")
                            self.logging.debug(f"output={port_width}")

                    elif row.strip().endswith("inout"):
                        keyword,signal_name,port_width,wireType,direction,checkValue = row.split(',')
                        if 'IO' == wireType:
                            port_width = port_width.replace(" ","")
                            inoutList.append(f"{port_width}")
                            self.logging.debug(f"inout={port_width}")
                    else:
                        if row.strip().endswith('master') or row.strip().endswith('slave'):
                            keyword,signal_name,port_width,wireType,direction,checkValue = row.split(',')
                            if 'IF' == wireType or 'if' == wireType:
                                port_width = port_width.replace(" ","")
                                interfaceList.append(f"{port_width}")
                                self.logging.debug(f"inout={port_width}")
                        
        return inputList,outputList,inoutList,interfaceList


    def input_port_info(self,tempList,strName,strType):
        for item in tempList:
            self.logging.debug(f"Warning:{strName} {item} {strType}")

    def combine_list(self,list1,list2):
        totalList = []
        for item in list1:
            totalList.append(item)

        for item in list2:
            totalList.append(item)

        return totalList

    def get_width_connection_str_list(self,port_width_list):
        connet_width_list = []
        for item in port_width_list:
            connet_width_list.append(self.get_width_connection_str(item))

        return connet_width_list

    def check_multi_port_wireType(self,dictElement):

        port_width_list = [ dictElement[key][2].replace(","," ").replace(" ","") for key in dictElement.keys() ]
        self.logging.debug(f"port_width_list = {port_width_list}")

        port_with_connect_list = [ item for item in port_width_list if item]

        collect_width_list = [ self.get_width_connection_str(item) for item in port_with_connect_list ]
        collect_width_list = [list(item) for item in collect_width_list]
        self.logging.debug(f"collect_width_list = {collect_width_list}")

        collect_name_list_attr = [ item[0] for item in collect_width_list ]
        collect_name_list = [ item[0] for item in collect_width_list if item[1]]
        self.logging.debug(f"collect_name_list = {collect_name_list}")

        multi_port_list  = [ item for item, count in collections.Counter(collect_name_list).items() if count > 1 ]
        self.logging.debug(f"multi_port_list = {multi_port_list}")

        conflict_width_list = [ item for item in collect_width_list if item[0] in multi_port_list ]
        self.logging.debug(f"conflict_width_list = {conflict_width_list}")

        mutli_port_conflict = [ item for item in multi_port_list if self.get_port_width_set(item,collect_width_list)]
        self.logging.debug(f"mutli_port_conflict = {mutli_port_conflict}")

        multi_port_list_wire  = [ item for item, count in collections.Counter(collect_name_list_attr).items() if count > 1 ]
        mutli_wireType_conflict = [ item for item in multi_port_list_wire if self.get_port_wireType_set(item,dictElement)]
        self.logging.debug(f"mutli_wireType_conflict = {mutli_wireType_conflict}")

        return mutli_port_conflict,mutli_wireType_conflict


    def get_port_width_set(self,connectName,tempList):

        flag = False
        width_list = []

        for item in tempList:
            if connectName == item[0]:
                width_list.append(item[1])

        if len(width_list) > 1:
            value = width_list.pop()

            while width_list:
                value1 = width_list.pop()

                if (len(value) == 3) or (len(value1) == 3):
                    flag_eq = compare_width(value,value1)

                    if flag_eq:
                        continue
                    else:
                        flag = True
                        break

                else:
                    if value == value1:
                        continue
                    else:
                        flag = True
                        break

        self.logging.debug(f"flag = {flag},width_list = {width_list}")
        
        return flag

    def get_port_wireType_set(self,connectName,tempDict):

        flag = False
        wireType_list = []

        for item in tempDict.keys():
            connectNameValue,width = self.get_width_connection_str(tempDict[item][2].replace(","," ").replace(" ",""))

            if connectName == connectNameValue:
                wireType_list.append(tempDict[item][3].replace(","," ").replace(" ",""))

        self.logging.debug(f"wireType_list = {wireType_list}")

        if len(wireType_list) > 1:
            value = wireType_list.pop()

            while wireType_list:
                value1 = wireType_list.pop()

                if value.lower() == value1.lower():
                    continue

                else:
                    flag = True
                    break

                self.logging.debug(f"value = {value},value1 = {value1}")

        self.logging.debug(f"flag = {flag},connectName = {connectName}")
        
        return flag

    def check_port_info(self,filePath):
        topInputList = []
        topOutputList = []
        topInoutList = []
        topInterfaceList = []
        instInputList = []
        instOutputList = []
        instModList = []
        instIoList = []
        wInputList = []
        wOutputList = []
        instIfList = []
        totalConflict = []
        totalNoload = []
        totalUndrive = []
        totalFloating = []
        floatingIntf = []
        dictElement = {}


        topInputList,outputList,inoutList,intfList = self.get_top_csv_port_attr(filePath)

        instInputList,instOutputList,instModList,instIoList,instIfList,wInputList,wOutputList,dictElement = self.get_top_inst_port_attr(filePath)
        self.logging.info(f"wInputList = {wInputList},wOutputList = {wOutputList}")

        mutli_port_conflict,mutli_wireType_conflict = self.check_multi_port_wireType(dictElement)

        ##########################################################################################
        # Get assign port value
        ##########################################################################################
        ssignInputList = []
        assignOutputList = []
        assignInputList,assignOutputList = parseAssign(filePath)
        assignInputList = list(set(assignInputList))
        assignOutputList = list(set(assignOutputList))
        self.logging.debug(f"assignInputList = {assignInputList}\n,assignOutputList = {assignOutputList}\n")

        ############### ############### ############### ############### ############ ###############
        # conflict check report
        ############ ############### ############### ############### ############### ###############

        print(f"Prompt: conflict check founded!")
        totalOutPutList = self.combine_list(instOutputList,wOutputList)
        totalOutPutList = self.combine_list(assignInputList,totalOutPutList)

        outputConflict = [item for item, count in collections.Counter(totalOutPutList).items() if count > 1]
        if outputConflict:
            self.input_port_info(outputConflict,"output","conflict")
            totalConflict.extend(outputConflict)

        modConflict = [item for item, count in collections.Counter(instModList).items() if count > 1]
        if modConflict:
            self.input_port_info(modConflict,"mod","conflict")
            totalConflict.extend(modConflict)

        ioConflict = [item for item, count in collections.Counter(instIoList).items() if count > 1]
        if ioConflict:
            self.input_port_info(instIoList,"inout","conflict")
            totalConflict.extend(ioConflict)

        ############### ############### ############### ############### ############ ###############
        # undrive check report
        ############ ############### ############### ############### ############### ###############
        print(f"Prompt: undrive check founded!")

        inst_master_list_tmp = [i.replace('.master','') for i in instModList if '.master' in i]
        inst_slave_list_tmp = [i.replace('.slave','') for i in instModList if '.slave' in i]

        inst_master_list = [i for i in inst_master_list_tmp if i not in inst_slave_list_tmp]
        inst_slave_list = [i for i in inst_slave_list_tmp if i not in inst_master_list_tmp]
        floatingIntf.extend(inst_master_list)
        floatingIntf.extend(inst_slave_list)

        if floatingIntf:
            self.input_port_info(floatingIntf,"interface","floating")
            totalFloating.extend(floatingIntf)
        self.logging.debug(f"floatingIntf = {floatingIntf}")

        # undriveWire = [i for i in wInputList if i not in wOutputList]
        # undriveWire = [i for i in undriveWire if i not in instOutputList]
        undriveWire = [i for i in wInputList if not self.port_equal_list(i,wOutputList)]
        undriveWire = [i for i in undriveWire if not self.port_equal_list(i,instOutputList)]
        undriveWire = [i for i in undriveWire if not self.port_equal_list(i,assignInputList)]

        if undriveWire:
            self.input_port_info(undriveWire,"input","undrive")
            totalUndrive.extend(undriveWire)
        self.logging.debug(f"totalUndrive = {totalUndrive}")


        ############### ############### ############### ############### ############ ###############
        # noload check report
        ############ ############### ############### ############### ############### ###############
        print(f"Prompt: noload check founded!")
        self.logging.debug(f"wOutputList = {wOutputList},instOutputList = {instOutputList}")
        # noloadWire = [i for i in wOutputList if i not in wInputList]
        # noloadWire = [i for i in noloadWire if i not in instInputList] 
        noloadWire = [i for i in wOutputList if not self.port_equal_list(i,wInputList)]
        noloadWire = [i for i in noloadWire if not self.port_equal_list(i,instInputList)] 
        noloadWire = [i for i in noloadWire if not self.port_equal_list(i,assignOutputList)] 

        if noloadWire:
            self.input_port_info(noloadWire,"input","noload")
            totalNoload.extend(noloadWire)
        self.logging.info(f"totalConflict = {totalConflict}\n,totalNoload = {totalNoload}\n,totalUndrive = {totalUndrive}\n,totalFloating = {totalFloating}\n")

        inputList,outputList,inoutList,ifdict = self.check_port_info_to_csv(filePath,totalConflict,totalNoload,totalUndrive,totalFloating,mutli_port_conflict,mutli_wireType_conflict)
        self.logging.debug(f"inputList = {inputList}\n,outputList = {outputList}\n,inoutList = {inoutList}\n,ifdict = {ifdict}\n")
        self.write_port_info_to_csv(filePath,inputList,outputList,inoutList,ifdict)

        return

    def get_top_csv_port_attr(self,filePath):
        inputList = []
        outputList = []
        inoutList = []
        interfaceList = []

        start = "port_begin"
        end = "port_end"
        startFlag = False

        matchStr = re.compile(r'[A-Za-z]+[A-Za-z_0-9]+')
        with open(filePath,newline='') as fr:

            lines = fr.readlines()
            for row in lines:

                if start in row:
                    startFlag = True

                if end in row:
                    startFlag = False
                    break

                if startFlag == True and start not in row:
                    connectNameList = []

                    direction,width,signalvalue = self.get_mod_port_str(row)
                    port_width = signalvalue.strip()

                    if '{' in port_width and '}' in port_width:
                        connectNameList = matchStr.findall(port_width)
                        self.logging.debug(f"connectNameList = {connectNameList}")

                    else:
                        connectNameList.append(port_width)

                    if row.strip().startswith("input"):
                        for port_width in connectNameList:
                            inputList.append(f"{port_width}")
                            self.logging.debug(f"input = {port_width}")

                    elif row.strip().startswith("output"):
                        for port_width in connectNameList:
                            outputList.append(f"{port_width}")
                            self.logging.debug(f"output = {port_width}")

                    elif row.strip().startswith("inout"):
                        for port_width in connectNameList:
                            inoutList.append(f"{port_width}")
                            self.logging.debug(f"inout = {port_width}")

                    else:
                        for port_width in connectNameList:
                            interfaceList.append(f"{port_width}")
                            self.logging.debug(f"interface port = {port_width}")
                        
        return inputList,outputList,inoutList,interfaceList

    def get_top_one_inst_port(self,filePath,inst_name):
        inputList = []
        outputList = []
        modList = []
        inoutList = []
        dictMod = {}
        tempList = []

        with open(filePath,newline='') as fr:

            lines = fr.readlines()
            for row in lines:

                if 'connect' in row and inst_name in row:

                    tempList = deal_with_port_str(row)

                    if tempList:
                        keyword,signal_name,port_width,wireType,direction,checkValue = tempList
                        port_width = port_width.replace(" ","")
                        connectName,width = self.get_width_connection_str(port_width)

                        if port_width:
                            pass
                        else:    #null connection not involve match
                            continue
                    else:
                        continue

                    if "input," in row.strip('\n'):

                        inputList.append(f"{connectName}")
                        self.logging.debug(f"input={connectName}")

                    elif "inout," in row.strip('\n'):
    
                        if 'io' == wireType.strip() or "IO" == wireType.strip():
                            inoutList.append(f"{connectName}")
                            self.logging.debug(f"inout = {connectName}")

                    elif "output," in row.strip('\n'):

                        outputList.append(f"{connectName}")
                        self.logging.debug(f"output={connectName}")

                    else:
                        if "master," in row.strip('\n') or "slave," in row.strip('\n'):

                            if 'M' in wireType or "IF" in wireType or 'm' in wireType or "if" in wireType:
                                modList.append(f"{connectName}")
                                dictMod[port_width.strip()] = direction.strip()
                                self.logging.debug(f"mod interface={connectName},direction = {direction}")


        return inputList,outputList,modList,inoutList,dictMod

    def get_top_inst_port_attr(self,filePath):
        inputList = []
        outputList = []
        wInputList = []
        wOutputList = []
        modList = []
        ioList = []
        ifList = []
        dictElement = {}

        matchStr = re.compile(r'[A-Za-z]+[A-Za-z_0-9]+')
        with open(filePath,newline='') as fr:

            lines = fr.readlines()
            for row in lines:
                if 'connect' in row and len(row.split(',')) != 3:
                    # define the list for connect name
                    connectNameList = []

                # if 6 == len(row.split(',')):
                    tempList = deal_with_port_str(row)
                    keyword,signal_name,port_width,wireType,direction,checkValue = tempList
                    port_width = port_width.replace(" ","")

                    if not port_width:
                        continue

                    if '{' in port_width and '}' in port_width:
                        connectNameList = matchStr.findall(port_width)
                        self.logging.info(f"connectNameList = {connectNameList}")

                        if connectNameList:
                            pass

                        else:
                            connectName,width = self.get_width_connection_str(port_width)
                            connectNameList.append(connectName)
                    else:
                        connectName,width = self.get_width_connection_str(port_width)
                        connectNameList.append(connectName)

                    dictElement[signal_name.strip()] = tempList

                    if 'input,' in row.strip():
                        
                        if "I" == wireType.strip() or "i" ==  wireType.strip():
                            for connectName in connectNameList:
                                inputList.append(f"{connectName.strip()}")
                                self.logging.debug(f"input port = {connectName}")

                        elif "w" == wireType.strip() or "W" ==  wireType.strip():
                            for connectName in connectNameList:
                                wInputList.append(f"{connectName.strip()}")
                                self.logging.debug(f"input wire port = {connectName}")

                        elif "O" == wireType.strip() or "o" ==  wireType.strip():
                            for connectName in connectNameList:
                                wInputList.append(f"{connectName}")
                                self.logging.debug(f"output port = {connectName}")

                        elif "IO" == wireType.strip() or "io" ==  wireType.strip():
                            for connectName in connectNameList:
                                ioList.append(f"{connectName.strip()}")
                                self.logging.debug(f"ioList port = {connectName}")

                        else:
                            self.logging.debug(f"\033[1;32mWarning:input {port_width} is mod type \033[0m")

                    elif 'output,' in row.strip():

                        if "O" in wireType or "o" in wireType:
                            for connectName in connectNameList:
                                outputList.append(f"{connectName}")
                                self.logging.debug(f"output port = {connectName}")

                        elif 'W' in wireType or 'w' in wireType:
                            for connectName in connectNameList:
                                wOutputList.append(f"{connectName}")
                                self.logging.debug(f"output wire port = {connectName}")

                        elif 'IO' in wireType or 'io' in wireType:
                            for connectName in connectNameList:
                                ioList.append(f"{connectName.strip()}")
                                self.logging.debug(f"ioList port = {connectName}")

                        else:
                            self.logging.debug(f"\033[1;32mWarning:output {connectName} is wrong type {wireType} \033[0m")
                    else:
                        if 'master' in row.strip() or 'slave' in row.strip():
                            self.logging.debug(f"signal_name = {signal_name},port_width ------=-------- {port_width},wireType = {wireType}")

                            if 'M' in wireType or 'm' in wireType:
                                modList.append(f"{port_width.strip()}")
                                self.logging.debug(f"mod port = {port_width}")

                            elif 'IF' in wireType or 'if' in wireType:
                                ifList.append(f"{port_width.strip()}")
                                self.logging.debug(f"interface port = {port_width}")
                            else:
                                self.logging.debug(f"\033[1;32mWarning:mod {port_width} is wrong type {wireType} \033[0m")
                    # else:
                    #     self.logging.info(f"The row = {row} is not valid")
                        
        return inputList,outputList,modList,ioList,ifList,wInputList,wOutputList,dictElement

    def get_files_port(self,filelist):
        inputList = []
        outputList = []

        for filePath in filelist:
            with open(filePath,newline='') as csvfile:
                csvReader = csv.reader(csvfile,delimiter=' ',quotechar='|')
                for row in csvReader:
                    # if "input" in row or "output" in row:
                    if row:
                        if "//" in row[0]:
                            line = row[0].split("//")[0]

                        else:
                            line = row[0]
                        if 'input' in line:
                            direction,port_width,signal_name = line.split(',')
                            if port_width:

                                inputList.append(f"{signal_name}{port_width}")
                                # pass
                            else:

                                inputList.append(f"{signal_name}")
                        if 'output' in line:
                            direction,port_width,signal_name = line.split(',')
                            if port_width:

                                outputList.append(f"{signal_name}{port_width}")
                                # pass
                            else:

                                outputList.append(f"{signal_name}")
        return inputList,outputList


    def get_file_port(self,filePath):
        inputList = []
        outputList = []
        with open(filePath,newline='') as csvfile:
            csvReader = csv.reader(csvfile,delimiter=' ',quotechar='|')
            for row in csvReader:
                # if "input" in row or "output" in row:
                if row:
                    if "//" in row[0]:
                        line = row[0].split("//")[0]
                    else:
                        line = row[0]
                    if 'input' in line:
                        direction,port_width,signal_name = line.split(',')
                        if port_width:
                            self.logging.info(f"{direction},{signal_name}{port_width}")
                            inputList.append(f"{signal_name}{port_width}")

                        else:
                            inputList.append(f"{signal_name}")
                    if 'output' in line:
                        direction,port_width,signal_name = line.split(',')
                        if port_width:
                            self.logging.info(f"{direction},{signal_name}{port_width}")
                            outputList.append(f"{signal_name}{port_width}")

                        else:
                            outputList.append(f"{signal_name}")
        self.logging.debug(f"file path = {filePath}---input---{inputList}")
        self.logging.debug(f"file path = {filePath}---output---{outputList}")

        return inputList,outputList

    def get_top_port(self,filePath):
        self.logging.info(f"---get_top_port---")
        inputList = []
        inoutList = []
        # modPortList = []

        start = "#port_begin"
        end = "#port_end"
        validFlag = False

        with open(filePath,'r') as fr:
            lines = fr.readlines()
            for line in lines:
                # if "input" in row or "output" in row:
                if line:
                    if "connect" in line:
                        continue

                    if start in line:
                        validFlag = True
                        continue

                    if end in line:
                        validFlag = False
                        break

                    if validFlag == True:
                        if line.startswith("input") or line.startswith("output") or "master" in  line or "slave" in line:

                            direction,port_width,signal_name = self.get_mod_port_str(line)
                            signal_name = signal_name.strip()
                            inputList.append(f"{direction}%{signal_name}{port_width}")
                            self.logging.debug(f"{direction}%{signal_name}{port_width}")

                        if line.startswith("inout"):
                            direction,port_width,signal_name = self.get_mod_port_str(line)
                            signal_name = signal_name.strip()
                            inoutList.append(f"{direction}%{signal_name}{port_width}")
                            self.logging.debug(f"{direction}%{signal_name}{port_width}")

                    else:
                        continue

        return inputList,inoutList

    def get_keep_top_port(self,filePath):
        self.logging.info(f"---get_keep_top_port---")
        inputList = []
        inoutList = []
        # modPortList = []

        start = "#port_begin"
        end = "#port_end"
        validFlag = False

        with open(filePath,'r') as fr:
            lines = fr.readlines()
            for line in lines:
                # if "input" in row or "output" in row:
                if line:
                    if "connect" in line:
                        continue

                    if "keep_begin before_port" in line:
                        validFlag = True
                        continue

                    if "keep_end before_port" in line:
                        validFlag = False
                        break

                    if validFlag == True:
                        if line.startswith("input") or line.startswith("output") or "master" in  line or "slave" in line:
                            direction,port_width,signal_name = self.get_mod_port_str(line)
                            signal_name = signal_name.strip()
                            inputList.append(f"{direction}%{signal_name}{port_width}")
                            self.logging.debug(f"{direction}%{signal_name}{port_width}")

                        if line.startswith("inout"):
                            direction,port_width,signal_name = self.get_mod_port_str(line)
                            signal_name = signal_name.strip()
                            inoutList.append(f"{direction}%{signal_name}{port_width}")
                            self.logging.debug(f"{direction}%{signal_name}{port_width}")

                    else:
                        continue

        return inputList,inoutList
    def get_top_port_list(self,filePath):
        self.logging.info(f"---get_top_port list---")
        inputList = []
        outputList = []
        inoutList = []
        modList = []
        # modPortList = []

        start = "#port_begin"
        end = "#port_end"
        validFlag = False

        with open(filePath,'r') as fr:
            lines = fr.readlines()
            for line in lines:
                # if "input" in row or "output" in row:
                if line:
                    if "connect" in line:
                        continue

                    if start in line:
                        validFlag = True
                        continue

                    if end in line:
                        validFlag = False
                        break

                    if validFlag == True:
                        direction,port_width,signal_name = self.get_mod_port_str(line)
                        signal_name = signal_name.strip()
                        if line.startswith("input"):
                            inputList.append(f"{signal_name}{port_width}")

                        elif line.startswith("output"):
                            outputList.append(f"{signal_name}{port_width}")

                        elif "master" in  line or "slave" in line:
                            modList.append(f"{signal_name}{port_width}")

                        elif line.startswith("inout"):
                            inoutList.append(f"{signal_name}{port_width}")

                        else:
                            continue
                    else:
                        continue

        return inputList,outputList,inoutList,modList


    def get_inst_from_top(self,topFile,fileType="null",path="./sb_output/"):
        stringInst = 'inst '
        inst_name_list = []
        module_name_list = []
        dictInst = {}

        self.logging.info(f"top file = {topFile}")
        with open(topFile,'r') as fr:
            lines = fr.readlines()
            for line in lines:
                # self.logging.info(line.strip('\n'))
                if line.strip('\n').startswith(stringInst):
                    module_name = line.strip().split(' ')[1]
                    temp_inst_name = line.strip().split(' ')[2]
                    inst_name_list.append(temp_inst_name)
                    module_name_list.append(module_name)

        # dictInst = dict(zip(inst_name_list,module_name_list))
        self.logging.info(f"inst_name_list = {inst_name_list}")
        self.logging.info(f"mod_name_list = {module_name_list}")

        return inst_name_list,module_name_list

    def get_inst_info_from_top(self,topFile,inst_name,fileType="null",path="./sb_output/"):

        self.logging.info(f"filename = {self.filename}")

        if inst_name in self.filename:
            stringInst = 'inst ' + str(inst_name)
            with open(topFile,'r') as fr:
                lines = fr.readlines()

                for line in lines:
                    if stringInst in line.strip('\n'):
                        self.inst_name_list.append(line.strip('\n').split(' ')[2])
        else:
            stringInst = 'inst ' + os.path.splitext(os.path.basename(str(self.filename)))[0] + " " + str(inst_name)

            self.logging.info(f"The module name {stringInst}")
            self.inst_name_list.append(inst_name)

        return

    def top_update_inst(self,topFile,inst_name,fileType="null",path="./sb_output/"):

        self.logging.info(f"inst name = {self.inst_name_list}")


        for inst_name in self.inst_name_list:
            # inst_name = inst_name.split(' ')[2]
            self.update_inst_module(topFile,inst_name,fileType="null",path="./sb_output/")

        return 

    def get_csv_path(self,topFile,csv_path,exeCmd,fileType="null"):

        csv_list = self.get_csv_path_list(topFile)

        pa = re.compile(r"(u\d*_)S*")

        strInst = pa.findall(csv_path)
        self.logging.info(f"strInst = {strInst},csv_path = {csv_path}")

        if os.path.exists(csv_path):
            csv_File = os.path.basename(csv_path)

        else:
            if strInst:

                strInst = csv_path
                _,tempModule = self.get_the_inst_module_counter(topFile,strInst,exeCmd)
                csv_File = tempModule
            
            else:
                csv_File = csv_path
                self.logging.info("Warining, please check the inst name format")


        # if strInst: ##need to confirm
   
            # _,tempModule = self.get_the_inst_module_counter(topFile,csv_path,exeCmd)
            # csv_File = tempModule

        # else:

        #     csv_File = csv_path

        self.logging.info(f"csv list = {csv_list},csv_File = {csv_File}")
        

        csvFlag = False
        for csvFile in csv_list:

            if csv_File in os.path.basename(csvFile):
                
                if "$" in csvFile:
                    self.filename = str_convert(csvFile)

                else:
                    self.filename = csvFile.strip()

                csvFlag = True

            else:
                pass  # need add the path to csv

        #################################################################################################
        if "update" in exeCmd and (self.filename.strip().endswith('.sv') or self.filename.strip().endswith('.v')):

            genCsv = csvGenerator(logging)

            inputFile = self.filename.strip()
            # print(opt.input)

            outputDir = genCsv.createDir(inputFile)

            if inputFile.endswith('.v'):

                outputFile = inputFile.replace('.v','.csv')

            else:

                outputFile = inputFile.replace('.sv','.csv')


                outputFile = outputDir + os.sep + os.path.basename(outputFile)


            genCsv.main_process(inputFile,outputFile,fileType)

            self.logging.info(f"inputFile = {inputFile},outputFile = {outputFile}")


        ##################################################################################################
        if csvFlag == True:
            print(f"\033[1;32mWarning: {csv_File} existed already. No action here. \033[0m")   

        else:
            if "update" in exeCmd:

                print(f"\033[1;32mError: {csv_File} could not be opened. Stop here. Please check it and try again. \033[0m")
                exit()

            else:
                
                if '.sv' in topFile or '.v' in topFile:
                    topcsv = topFile.replace('.sv','csv')

                else:
                    topcsv = topFile

                print(f"\033[1;32mInfo: {csv_File} has been added to the {topcsv}. \033[0m")

                if '/' in self.filename and './' not in self.filename:
                    self.filename = os.path.dirname(csv_path) + os.sep + csv_File
                    
                else:
                    self.filename = csv_File
            # exit()

        return self.filename

    def get_all_csv_path(self,topFile):
        csv_list = self.get_csv_path_list(topFile)
        filename = ""
        modName = ""
        dictCsvFile = {}
        self.logging.info(f"csv list = {csv_list}")

        for csvFile in csv_list:
                
            filename = os.path.basename(csvFile).strip()
           
            modName = os.path.basename(filename).split('.')[0]
            dictCsvFile[filename] = modName

        self.logging.info(f"dictCsvFile = {dictCsvFile}")

        return dictCsvFile

    def get_width_connection_str(self,inputStr):
        
        if '{' in inputStr and '}' in inputStr:
            inputStr = inputStr.replace('"',' ')
            match_parameter = re.compile(r'[{](.*)[}]', re.S)
            width0 = '{' + match_parameter.findall(inputStr)[0] + '}'

            inputStr = inputStr.strip()
            connectName0 = inputStr[0:(len(inputStr)-len(width0))]
            self.logging.debug(f"-----------connectName0 = {connectName0},-----------width0 = {width0}")

        elif "[" in inputStr:
            connectName0 = inputStr.strip().split('[')[0]
            width0 = "[" + inputStr.strip().split('[')[1].split(']')[0] + "]"

        else:
            connectName0 = inputStr.strip()
            width0 = ""
        


        return connectName0,width0

    def update_inst_module(self,topFile,inst_name,fileType="null",path="./sb_output/"):
        self.logging.info(f"update_inst_module")
        filelist = []
        start = "#inst_begin"
        end = "#inst_end"

        csvPath = self.filename
        outputFile = path + os.path.basename(topFile).replace('.csv',('_out' + '.csv'))
        inst_u_name = inst_name

        csvPath = self.modify_to_csv_path()

        shutil.copy(csvPath,(path + os.sep + os.path.basename(csvPath)))

        self.csvlist.append((path + os.sep + os.path.basename(csvPath)))
        self.logging.info(f"self.csvlist = {self.csvlist} ,csvPath = {csvPath}")


        for i in range(len(self.csvlist)):
            file_input_list = []
            file_inout_list = []
            file_modport_list = []
            dst_input_list = []
            dst_output_list = []
            dictInputPort = {}
            dictOutputPort = {}

            filePath = self.csvlist[i]

            file_input_list,file_inout_list = self.get_keep_top_port(filePath)   #update module file path
            keep_input_list,keep_inout_list = self.get_top_port(filePath)   #update module file path

            file_input_list.extend(keep_input_list)
            file_inout_list.extend(keep_inout_list)

            file_input_list.extend(file_inout_list)

            self.logging.info(f"--file_input_list---{i}----{file_input_list}")
            self.logging.info(f"--file_inout_list----{i}----{file_inout_list}")

            self.logging.info(f"file path = {filePath},top file = {topFile}")
            dst_input_list = self.get_top_inst_port(topFile,inst_name)  #top module
            self.logging.info(f"--dst_input_list--------{dst_input_list}")

            startFlag = False
            # signalFlag = True
            # # topSignalFlag = False
            # inputFlag = False
            # outputFlag = False
            line_content = ""
            index = 0
            checkValue = ""
            line_content_list = []
            # sigEndFlag = False
            # signalFlag = True



            with open(topFile,newline='') as fr:
                lines = fr.readlines()
                # self.logging.debug(f"file_input_list = {file_input_list}")
                for i in range(len(lines)):
                    if lines[i]:
                        if (i < len(lines) -1) and start in lines[i] and inst_name in lines[i+1]:
                            startFlag = True
                            self.logging.info(f"start {i} line = {len(lines)} to {inst_name} check the port,startFlag = {startFlag}")

                        if (i < len(lines) -1) and end in lines[i+1] and "port_inst_end" in lines[i] and inst_name in lines[i-1]:

                            startFlag = False

                            self.logging.info(f" end = {end}, line = {lines[i]} line-1 = {lines[i-1]}")

                            if file_input_list:  # add multi port

                                for item in file_input_list:

                                    tempValue = item
                                    direction1,width1,signalname1,connectName1 = self.get_port_parameters(tempValue)

                                    if 'input' in direction1:
                                        wireType = 'I'

                                    elif 'inout' in direction1:
                                        wireType = 'IO'

                                    elif 'output' in direction1:
                                        wireType = 'O'

                                    else:
                                        wireType = 'M'

                                    line_content = "connect,{}.{},{},{},{},{}".format(inst_name, signalname1.ljust(30), (signalname1 + width1).strip().ljust(40), wireType.ljust(10), direction1,checkValue)
                                    line_content_list.append(line_content)
                                    self.mod_sig_list.append(signalname1)

                            # else:   # add one port
                            #     if sigEndFlag == True: # only end for file input list as null

                            #         topSignalFlag = port_in_list(signalname1+width1,dst_input_list) #top csv

                            #         if topSignalFlag == False:  #add mod port

                            #             if signalname1.strip().endswith('_m'):
                            #                 signalname = signalname1.replace('_m','.master')
                            #                 wireType = 'M'

                            #             elif signalname1.strip().endswith('_s'):
                            #                 signalname = signalname1.replace('_s','.slave')
                            #                 wireType = 'M'

                            #             else:
                            #                 if '.master' in direction1 or '.slave' in direction1:
                            #                     wireType = 'IF'

                            #                 else:
                            #                     if "input" in direction1:
                            #                         wireType = 'I'

                            #                     if "output" in direction1:
                            #                         wireType = 'O'

                            #             line_content = "connect,{}.{},{},{},{},{}".format(inst_name, signalname1.ljust(30), (signalname1+ width1).ljust(40), wireType.ljust(10), direction1,checkValue)
                            #             line_content_list.append(line_content)
                            #             self.mod_sig_list.append(signalname1)

                            #             sigEndFlag = False
                            #     else:
                            #         pass

                            self.logging.info(f"end {i} line to check the port")

                        signalVal = ""
                        # tempValue = ""

                        if startFlag == True:
                            # wireType = 'W'
                            # topSignalFlag = False
                
                            if "input" in lines[i] or "output" in lines[i] or "master" in lines[i] or "slave" in lines[i] or "inout" in lines[i]:
                                keyword,signal_name,connect_width,wireType,direction,checkValue = deal_with_port_str(lines[i])

                                if inst_name not in signal_name:
                                    if '.sv' in topFile or '.v' in topFile:
                                        topcsv = topFile.replace('.sv','csv')

                                    else:
                                        topcsv = topFile
                                        
                                    print(f"Error: The Instance {inst_name} of this moudle could not be founded here. Please check if it existed in the {topcsv}.")
                                    deal_with_error(topFile)

                                signalname0 = signal_name.replace((inst_name + '.'),"").strip()
                                checkValue = checkValue + '\n'

                                connectName0,width0 = self.get_width_connection_str(connect_width)
                                self.logging.debug(f"connectName0 = {connectName0},width0 = {width0}")

                                if file_input_list:
                                    
                                    tempValue = file_input_list[0]
                                    
                                    direction1,width1,signalname1,connectName1 = self.get_port_parameters(tempValue)
                                    signalname1 = signalname1.strip()
                                    connectName1 = connectName1.strip()

   
                                    self.logging.debug(f"signalname0 = {signalname0},signalname1 = {signalname1}")

                                    if signalname0.strip() == signalname1: #update for the same signal
                                        
                                        self.logging.debug(f"connectName0 = {connectName0},connectName1 = {connectName1}")

                                        flag_eq = False
                                        # print(f"width0 = {width0},width1 = {width1}")
                                        if len(width0) == 3 or len(width1) == 3:
                                            flag_eq = compare_width(width0,width1)
                                        else:
                                            if width1 == width0:
                                                flag_eq = True

                                        if connectName0.strip() == connectName1:

                                            self.logging.debug(f"module Value = {tempValue},direction = {direction},direction1 = {direction1},wireType = {wireType}")

                                            if direction.strip() == direction1.strip() and flag_eq == True:
                                                line_content_list.append(lines[i])
                                                self.logging.debug(f" direction not changed and flag_eq == True ,connectName0 = {connectName0},connectName1 = {connectName1},checkValue = {checkValue}")

                                            elif '{' in width0 and '}' in width0:
                                                line_content_list.append(lines[i])

                                            else:  # direction changed
                                                line_content = "connect,{}.{},{},{},{},{}".format(inst_name, signalname1.ljust(30), (connectName1+ width1).strip().ljust(40), wireType.ljust(10), direction1,checkValue)
                                                line_content_list.append(line_content)

                                                if direction.strip() != direction1.strip():
                                                    self.mod_sig_list.append(signalname1)

                                                self.logging.debug(f" direction changed or width changed ,connectName0 = {connectName0},connectName1 = {connectName1},checkValue = {checkValue}")

                                        else:

                                            if flag_eq == True and direction.strip() == direction1.strip():
                                                line_content_list.append(lines[i])

                                            elif '{' in width0 and '}' in width0:
                                                line_content_list.append(lines[i])
                                                
                                            else:
                                                if direction.strip() != direction1.strip():
                                                    self.mod_sig_list.append(signalname1)

                                                else:
                                                    checkValue = "confirm\n"

                                                line_content = "connect,{}.{},{},{},{},{}".format(inst_name, signalname1.ljust(30), (connectName1+ width1).strip().ljust(40), wireType.ljust(10), direction1,checkValue)
                                                line_content_list.append(line_content)

                                            self.logging.debug(f"width1 = {width1},direction1 = {direction1},checkValue = {checkValue}")

                                        self.logging.debug(f"signalname0 = {signalname0}!= signalname1 = {signalname1},temp value = {tempValue}")

                                        file_input_list.remove(file_input_list[0])
                                        continue


                                    else:  #signalname0 != signalname1 ,update info for different signal  

                                        self.logging.debug(f"signalname0 = {signalname0}!= signalname1 = {signalname1},temp value = {tempValue}")
                                        curSignalFlag = False
                                        topSignalFlag = False
                                        curSignalFlag1 = False
                                        topSignalFlag1 = False
                                        width0_bak = ""
                                        width1_bak = ""

                                        # print(f"width0={width0},lens={len(width0)}")
                                        if len(width0) == 5:
                                            curSignalFlag = port_in_list((direction.strip()+'%'+signalname0+width0),file_input_list) #module csv
                                            
                                            curSignalFlag1 = port_in_list((direction.strip()+'%'+signalname0+width0_bak),file_input_list) #module csv
                                        else:
                                            curSignalFlag = port_in_list((direction.strip()+'%'+signalname0+width0),file_input_list) #module csv

               
                                        if len(width1) == 5:
                                            topSignalFlag = port_in_list((direction1.strip() +'%'+ signalname1+width1),dst_input_list) #top csv
                                            
                                            topSignalFlag1 = port_in_list((direction1.strip() +'%'+ signalname1+width1_bak),dst_input_list) #top csv
                                            # print(f"topSignalFlag1={topSignalFlag1},width1={width1}")

                                        else:
                                            topSignalFlag = port_in_list((direction1.strip() +'%'+ signalname1+width1),dst_input_list) #top csv

                                        self.logging.debug(f"curSignalFlag = {curSignalFlag},topSignalFlag = {topSignalFlag},curSignalFlag1 = {curSignalFlag1},topSignalFlag1 = {topSignalFlag1}")
                                        # print(f"curSignalFlag = {curSignalFlag},topSignalFlag = {topSignalFlag},curSignalFlag1 = {curSignalFlag},topSignalFlag1 = {topSignalFlag}")

                                        if curSignalFlag == False and curSignalFlag1 == False:  #del mod port
                                            self.logging.info(f"delete mod port = {lines[i]}")
                                            # print(f"delete mod port = {lines[i]}")
                                            # print(f"signalname0 = {signalname0}!= signalname1 = {signalname1},temp value = {tempValue}")

                                        else: #signal existed
                                            line_content_list.append(lines[i])
                                            if curSignalFlag == True:
                                                file_input_list.remove((direction.strip() +'%'+ signalname0+width0))

                                            if curSignalFlag1 == True:
                                                file_input_list.remove((direction.strip() +'%'+ signalname0+width0_bak))

                                        if topSignalFlag == False and topSignalFlag1 == False:  #add mod port
                                            if signalname1.strip().endswith('_m'):
                                                signalname = signalname1.replace('_m','.master')
                                                wireType = 'M'

                                            elif signalname1.strip().endswith('_s'):
                                                signalname = signalname1.replace('_s','.slave')
                                                wireType = 'M'

                                            else:
                                                if '.master' in direction or '.slave' in direction:
                                                    wireType = 'IF'
                                                else:
                                                    if "input" in direction1:
                                                        wireType = 'I'

                                                    if "output" in direction1:
                                                        wireType = 'O'

                                            line_content = "connect,{}.{},{},{},{},{}".format(inst_name, signalname1.ljust(30), (signalname1+ width1).strip().ljust(40), wireType.ljust(10), direction1,checkValue)
                                            line_content_list.append(line_content)

                                            self.mod_sig_list.append(signalname1)
                                            file_input_list.remove(file_input_list[0])

                                        else: # Dont do anything
                                            pass

                                    #         if file_input_list:
                                    #             tempValue = file_input_list[0]
                                    #             # file_input_list.remove(file_input_list[0])
                                    #             direction1,width1,signalname1,connectName1 = self.get_port_parameters(tempValue)

                                    #             # add the signal for multi line
                                    #             while signalname0 != signalname1 and file_input_list:
                                    #                 if signalname1.strip().endswith('_m'):
                                    #                     signalname = signalname1.replace('_m','.master')
                                    #                     wireType = 'M'

                                    #                 elif signalname1.strip().endswith('_s'):
                                    #                     signalname = signalname1.replace('_s','.slave')
                                    #                     wireType = 'M'

                                    #                 else:
                                    #                     if '.master' in direction or '.slave' in direction:
                                    #                         wireType = 'IF'
                                    #                     else:
                                    #                         if "input" in direction1:
                                    #                             wireType = 'I'

                                    #                         if "output" in direction1:
                                    #                             wireType = 'O'

                                    #                 line_content = "connect,{}.{},{},{},{},{}".format(inst_name, signalname1.ljust(30), (signalname1 + width1).ljust(40), wireType.ljust(10), direction1,checkValue)
                                    #                 line_content_list.append(line_content)
                                    #                 self.mod_sig_list.append(signalname1)

                                    #                 if file_input_list:
                                    #                     tempValue = file_input_list[0]
                                    #                     file_input_list.remove(file_input_list[0])
                                    #                     direction1,width1,signalname1,connectName1 = self.get_port_parameters(tempValue)

                                    #                 else:

                                    #                     self.logging.info(f"loop lines = {lines[i]}")  #mod port 
                                    #                     # # file_input_list.remove(file_input_list[0])
                                    #                     # line_content_list.append(lines[i])
                                    #                     continue

                                    #     # file_input_list is empty,maybe need to print the former port
                                    #     else:
                                    #         sigEndFlag = True   #update only one line
                                    #         self.logging.info(f"remove | remain signal lines = {lines[i]}")  #mod port 
                                    #         continue

                                    #     line_content_list.append(lines[i])
                                    #     signalFlag == True

                                    # else: # add port
                                    #     line_content_list.append(lines[i])
                                    #     file_input_list.remove((direction.strip() +'%'+ signalname0+width0))
                                    #     # signalFlag == False
                                    #     continue


                                else:  #file_input_list is empty, delete all ports
                                    pass

                            else:  #not port and mod information,parameter info
                                line_content_list.append(lines[i])
                                self.logging.debug(f"debug other line info = {lines[i]}") # 

                        # startFlag = False            
                        else:  #IF,INOUT
                            line_content_list.append(lines[i])
                    else:
                        line_content_list.append(lines[i])

            self.write_list_to_csv(outputFile,line_content_list)

            shutil.copy(outputFile,topFile)

        return

    def get_port_parameters(self,tempValue):
        
        direction = tempValue.split('%')[0]
        tempValue = tempValue.split('%')[1]

        # if '{' in tempValue and '}' in tempValue:
        signalname,width = self.get_width_connection_str(tempValue.strip())
        connetName = signalname
        self.logging.debug(f"signalname = {signalname}")

        return direction,width,signalname,connetName

    def port_equal_list(self,item,listPort):
        ''' Not remove list elements'''
        signalFlag = False
        for value in listPort:

            if item == value.strip():
                signalFlag = True
                break

        return signalFlag

    def add_many_inst_module(self,exeCmd,topFile,inst_name,fileType="null",path="./sb_output/"):
        runTime = exeCmd.replace("add","")    #execute x times for addx command
        self.logging.info(f"run time = {runTime} and fileType = {fileType}")

        if runTime:
            for i in range(int(runTime)):
                temp_inst_name = "u" + str(i) + "_" + inst_name.split('u_')[1]
                self.logging.info(temp_inst_name)
                self.add_inst_module(topFile,temp_inst_name,exeCmd,fileType)

        else:
            self.add_inst_module(topFile,inst_name,exeCmd,fileType)

    def get_top_content(self,topFile):
        with open(topFile,newline='') as fr:
            lines = fr.readlines()

        return lines

    def add_csv_to_top(self,topFile):
        content = self.get_top_content(topFile)

        with open(topFile,'w') as fw:
            for line in content:

                if "#csv_end" in line:
                    fw.write(self.filename + "\n")
                    fw.write(line)

                else:
                    fw.write(line)
        return

    def check_inst_path(self,topFile,module_name):
        pathFlag = False
        with open(topFile,newline='') as fr:
            lines = fr.readlines()

            for line in lines:
                if "#csv_begin" in line:
                    validFlag = True

                if "#csv_end" in line:
                    validFlag = False
                    break

                if validFlag == True:
                    if module_name in line:
                        pathFlag = True

        return pathFlag


    def get_the_inst_module_counter(self,topFile,inst_name,exeCmd):
        mod_inst_flag = False
        add_inst_flag = False
        moduleName = ""
        counter = 0

        instlist,modulelist = self.get_inst_from_top(topFile)
        self.logging.info(f"inst list = {instlist},mod list = {modulelist}")

        for index in range(len(instlist)):
            if inst_name == instlist[index] :

                if "add" in exeCmd:
                    print(f"\033[1;32mError: {inst_name} existed already. Exited.\033[0m")
                    exit()

                elif "del" in exeCmd:
                    mod_inst_flag = True
                    moduleName = modulelist[index]
                    break

                elif "update" in exeCmd:
                    moduleName = modulelist[index]
                    break

                else:
                    pass

        if add_inst_flag == False and "add" in exeCmd:  # add new inst
            add_inst_flag = True

        if mod_inst_flag == False and "del" in exeCmd:
            print(f"\033[1;32mInfo: maybe have some other instances of this module existed. \033[0m")

            
        self.logging.info(f"mod_inst_flag = {mod_inst_flag},add_inst_flag = {add_inst_flag}")
        if "del" in exeCmd:
            
            if mod_inst_flag == True : #del instance

                for mod in modulelist:
                    if mod == moduleName:
                        counter = counter + 1

            else: #del module
                for mod in modulelist:
                    if mod == inst_name:
                        counter = 1

        if add_inst_flag == True and "add" in exeCmd:

            modName =  os.path.basename(self.filename).split('.')[0]
            for mod in modulelist:
                if mod == modName:
                    counter += 1

        if add_inst_flag == False and "update" in exeCmd:

            modName =  os.path.basename(self.filename).split('.')[0]
            for mod in modulelist:
                if mod == modName:
                    counter += 1
                    moduleName = modName

        self.logging.info(f"counter = {counter},module_name = {moduleName}")
        return counter,moduleName

    def modify_to_csv_path(self):

        csvPath = ""
        if '/' in self.filename and not './' in self.filename:
            if '.v' in self.filename:
                csvPath = os.path.dirname(self.filename) + os.sep + 'csv' + os.sep + os.path.basename(self.filename)
                csvPath = csvPath.replace('.v','.csv')

            elif '.sv' in self.filename:
                csvPath = os.path.dirname(self.filename) + os.sep + 'csv' + os.sep + os.path.basename(self.filename)
                csvPath = csvPath.replace('.sv','.csv')

            else:
                csvPath = self.filename
        else:
            if '.v' in self.filename:
                csvPath = 'csv' + os.sep + self.filename.replace('.v','.csv')

            elif '.sv' in self.filename:
                csvPath = 'csv' + os.sep + self.filename.replace('.sv','.csv')

            else:
                csvPath = self.filename

        return csvPath

    def add_inst_module(self,topFile,inst_name,exeCmd,fileType="null",path="./sb_output/"):
        
        self.csvlist = []
        pathFlag = False

        self.logging.info(f"inst_name  = {inst_name} filename = {self.filename}")
        outputFile = path + os.path.basename(topFile).replace('.csv',('_out' + '.csv'))

        csvPath = self.modify_to_csv_path()
        self.csvlist.append(csvPath)

        self.counter,tempModule = self.get_the_inst_module_counter(topFile,inst_name,exeCmd)

        if self.counter >= 1:
            pathFlag = True

        tempContent = self.gen_inst(inst_name)

        validFlag = False
        instFlag = False

        with open(topFile,newline='') as fr,open(outputFile,'w', encoding='UTF-8') as fw:
            csvReader = fr.readlines()
            for row in csvReader:

                if "#csv_begin" in row:
                    validFlag = True

                if validFlag == True and "#csv_end" not in row:
                    if pathFlag == True: #delete the same csv path

                        instFlag = True
                        fw.write(row)
                    else:  #csv begin and csv path
                        fw.write(row)

                else:
                    if "#csv_end" not in row:
                        fw.write(row)

                if "#csv_end" in row:
                    if pathFlag == False:

                        filePath = self.filename
                        fw.write(filePath + "\n")

                    validFlag = False
                    fw.write(row)
                    fw.write(tempContent)

        self.logging.info(f"inst flag = {instFlag}")

        # with open(outputFile, "a+") as fw:
        #     fw.write(tempContent)
        shutil.copy(outputFile,topFile)

    def get_inst_mod_name(self,inst_name,tempList):

        tempInstName = ""
        for inst_mode in tempList:
            if inst_mode == inst_name:
                tempInstName = inst_name

        return tempInstName

    def check_del_csv_path(self,topFile,inst_name,exeCmd):
        self.counter,tempModule = self.get_the_inst_module_counter(topFile,inst_name,exeCmd)
        instlist,modulelist = self.get_inst_from_top(topFile)
        
        inst_temp_name = ""
        inst_temp_name_value = self.get_inst_mod_name(inst_name,instlist)
        mod_temp_name_value = self.get_inst_mod_name(inst_name,modulelist)
        self.logging.info(f"inst_temp_name_value = {inst_temp_name_value},mod_temp_name_value = {mod_temp_name_value}")

        self.inst_mod_Flag = False
        if instlist:
            if inst_name != inst_temp_name_value and inst_name != mod_temp_name_value:
                print((f"\033[1;32mError: {inst_name} not existed. Exited, Please check and try again.\033[0m"))
                exit()

            else:
                if inst_name == inst_temp_name_value:
                    self.inst_mod_Flag = False
                    modIndex = instlist.index(inst_name)
                    self.mod_name = modulelist[modIndex]

                else:
                    self.inst_mod_Flag = True
                    self.mod_name = inst_name

                self.del_inst_module(topFile,inst_name)

        else:
            print(f"\033[1;32mError: {inst_name} not existed. Exited, Please check and try again.\033[0m")
            exit()
        
    def get_csv_path_list(self,topFile):
        csvStart = "csv_begin"
        csvEnd = "csv_end"
        csv_flag = False
        csv_list = []
        
        with open(topFile,newline='') as fr:
            lines = fr.readlines()
            for line in lines:

                if csv_flag == True and csvEnd not in line:

                    self.logging.debug(f" csv path = {line}")
                    csv_list.append(line)

                if csvStart in line:
                    csv_flag = True

                if csvEnd in line:
                    csv_flag = False
                    break

        return csv_list

    def del_inst_module(self,topFile,inst_name,path="./sb_output/"):

        result = ""
        start = "#inst_begin"
        end = "#inst_end"
        startFlag = False
        csvFlag = False
        csvStart = "#csv_begin"
        csvEnd = "#csv_end"
        inst_mod = ""

        if self.inst_mod_Flag == True:
            inst_match = 'inst ' + inst_name

        else:
            inst_match = 'inst ' + self.mod_name + ' ' + inst_name
        self.logging.info(f"inst_mod_Flag = {self.inst_mod_Flag},inst match = {inst_match}")

        outputFile = path + os.path.basename(topFile).replace('.csv',('_out' + '.csv'))
        with open(topFile,newline='') as fr,open(outputFile,'w', encoding='UTF-8') as fw:
            lines = fr.readlines()
            for i in range(len(lines)):
                if start in lines[i] and inst_match in lines[i+1].strip() and self.inst_mod_Flag == True: #module
                    startFlag = True
                    inst_mod = lines[i+1].split(' ')[1]
                    self.logging.info(f"start {i} and mod = {inst_mod}")

                elif start in lines[i] and inst_match == lines[i+1].strip() and self.inst_mod_Flag == False: #instance
                    startFlag = True
                    inst_mod = lines[i+1].split(' ')[1]
                    self.logging.info(f"start {i} and mod = {inst_mod}")

                if csvStart in lines[i]:
                    csvFlag = True

                if csvEnd in lines[i]:
                    csvFlag = False

                if startFlag == True:
                    pass

                else:  #delete csv file
                    self.logging.debug(f"counter = {self.counter}  and line = {lines[i]} csvFlag = {csvFlag}")
                    if csvFlag == True and self.counter <= 1:
                        self.logging.debug(f"debug  {lines[i]}")
                        if csvStart in lines[i]:
                            fw.write(lines[i])
                        else:
                            pass
                    else:
                        fw.write(lines[i])

                if end in lines[i]:
                    startFlag = False
                    self.logging.info(f"end {i}")

        shutil.copy(outputFile,topFile)
        return inst_mod

    def main_process(self, wfilename,inst_name,fileType="null"):
        self.content, self.csvlist = self.read_module_info("csv")
        self.content += self.gen_inst(inst_name)
        self.write_csv(wfilename)


#--------------------------------------------------------------------
#  main process
#--------------------------------------------------------------------

def loginit(curDir,logname="run.log"):
    logger = logging.getLogger(logname)
    logger.setLevel(logging.DEBUG)

    # loghandler = logging.StreamHandler()    # 日志信息输出到终端
    curPath = curDir
    logPathFile = curPath + os.sep + "sb_output" + os.sep + logname
    logDir = curPath + os.sep + "sb_output"

    if os.path.exists(logPathFile):
        os.remove(logPathFile)
    
    if not os.path.exists(logDir):
        os.mkdir(logDir)

    loghandler = logging.FileHandler(logPathFile) #日志信息输出到文件
    # loghandler = loghandlers.RotatingFileHandler(logpath,maxBytes=1024*1,backupCount=5) # 根据文件大小轮换日志文件
    loghandler = loghandlers.TimedRotatingFileHandler(logPathFile,when='M',interval=1,backupCount=5) # 根据时间轮换日志文件
    loghandler.setLevel(logging.DEBUG)
    # loghandler.setLevel(logging.INFO)
    # 创建格式器(打印日志的时间-打印日志级别的名称-打印当前执行程序名-打印日志的当前函数-打印日志的当前行号: 日志信息)
    logformatter = logging.Formatter('%(asctime)s-%(levelname)s-%(filename)s-%(funcName)s-%(lineno)d: %(message)s')
    # 将格式器添加到处理器中
    loghandler.setFormatter(logformatter)
    # 将处理器添加到记录器中
    logger.addHandler(loghandler)
    return logger,loghandler

def gen_top_csv(filePath):
    templateList = []

    if not os.path.exists(filePath):
        modname = os.path.basename(opt.process).split('.')[0]

        templateList.append(f"#author_begin\n")
        templateList.append(f"null\n")
        templateList.append(f"#author_end\n")

        templateList.append(f"#order_begin\n")
        templateList.append(f"False\n")
        templateList.append(f"#order_end\n")

        templateList.append(f"#keep_begin before_module\n")
        templateList.append(f"#keep_end before_module\n")

        templateList.append(f"module,{modname}\n")

        templateList.append(f"#keep_begin after_module\n")
        templateList.append(f"#keep_end after_module\n")

        templateList.append(f"#keep_begin before_port\n")
        templateList.append(f"#keep_end before_port\n")

        templateList.append(f"#port_begin\n")
        templateList.append(f"#port_end\n")

        templateList.append(f"#keep_begin before_bracket\n")
        templateList.append(f"#keep_end before_bracket\n")

        templateList.append(f"#keep_begin after_bracket\n")
        templateList.append(f"#keep_end after_bracket\n")

        templateList.append(f"#keep_begin before_parameter\n")
        templateList.append(f"#keep_end before_parametert\n")

        templateList.append(f"#parameter_begin\n")
        templateList.append(f"#parameter_end\n")

        templateList.append(f"#keep_begin after_parameter\n")
        templateList.append(f"#keep_end after_parametert\n")

        templateList.append(f"#keep_begin before_wire_reg\n")
        templateList.append(f"#keep_end before_wire_reg\n")
        templateList.append(f"#keep_begin after_wire_reg\n")
        templateList.append(f"#keep_end after_wire_reg\n")

        templateList.append(f"#keep_begin before_modport\n")
        templateList.append(f"#keep_end before_modport\n")
        templateList.append(f"#keep_begin after_modport\n")
        templateList.append(f"#keep_end after_modport\n")

        templateList.append(f"#gen_type_begin\n")
        templateList.append(f"v\n")
        templateList.append(f"#gen_type_end\n")

        templateList.append(f"#csv_begin\n")
        templateList.append(f"#csv_end\n")

        templateList.append(f"#keep_begin before_inst_$name\n")
        templateList.append(f"#keep_end before_inst_$name\n")
        templateList.append(f"#keep_begin after_inst_$name\n")
        templateList.append(f"#keep_end after_inst_$name\n")
       
        templateList.append(f"#keep_begin before_endmodule\n")
        templateList.append(f"#keep_end before_endmodule\n")
        templateList.append(f"#keep_begin after_endmodule\n")
        templateList.append(f"#keep_end after_endmodule\n")

        with open(opt.process,'w') as fw:
            for item in templateList:
                fw.write(item)

def check_csv_file(topFile):
    csv_list = self.get_csv_path_list(topFile)


def search_csv_path(topFile,csv_path):
    filename = ""
    csv_list = search_csv_path_list(topFile)
    csv_File = os.path.basename(csv_path)
    
    logging.info(f"csv list = {csv_list},csv_File = {csv_File}")

    csvFlag = False

    for csvFile in csv_list:

        if csv_File in csvFile:

            filename = csvFile.strip()

            csvFlag = True

    if csvFlag == True:
        logging.info(f"\033[1;32mWarning:{filename} existed \033[0m")
        # print(f"\033[1;32mWarning:---------{filename} ------------existed \033[0m")


    else:
        logging.info(f"\033[1;32mWarning:{filename} not existed,add the first time \033[0m")


        if '/' in csv_path and './' not in csv_path:
            filename = os.path.dirname(csv_path) + os.sep + csv_File

        else:
            filename = csv_File

    if "$" in filename:
        filename = str_convert(filename)

    return filename


def search_csv_path_list(topFile):
    csvStart = "csv_begin"
    csvEnd = "csv_end"
    csv_flag = False
    csv_list = []
    
    with open(topFile,newline='') as fr:
        lines = fr.readlines()
        for line in lines:
            if csv_flag == True and csvEnd not in line:
                csv_list.append(line)

            if csvStart in line:
                csv_flag = True

            if csvEnd in line:
                csv_flag = False
                break

    return csv_list
#--------------------------------------------------------------------
#  support default top name
#
#--------------------------------------------------------------------
def modifyFileName(top_module):

    fileName = ""
    if '.csv' in top_module:

        fileName = top_module

    else:
        fileName = top_module + '.csv'

    return fileName

#--------------------------------------------------------------------
#  deal the different format input 
#
#--------------------------------------------------------------------
def str_convert(item):

    if "$HW" in item:
        value = os.popen("echo $HW").read()[:-1]
        item = item.replace("$HW",value)

    elif "$XML" in item:
        value = os.popen("echo $XML").read()[:-1]
        item = item.replace("$XML",value)

    elif "$RTL" in item:
        value = os.popen("echo $RTL").read()[:-1]
        item = item.replace("$RTL",value)

    elif "$SOC_PATH" in item:
        value = os.popen("echo $SOC_PATH").read()[:-1]
        item = item.replace("$SOC_PATH",value)
    else:
        pass

    return item.strip()

def get_hw_path(inputStr):
    value = ""

    for item in inputStr:

        if "$HW" in item:
            value = item

    return value

def write_gen_type_to_csv(topFile,fileType):
    
    tempFile =  "./sb_output/gen_type_csv.csv"
    validFlag = False
    startLable = "#gen_type_begin"
    endLable = "#gen_type_end"

    line_content_list = []

    with open(topFile,newline='') as fr:
        lines = fr.readlines()

        for line in lines:
            if startLable in line:
                validFlag = True
                
            if endLable in line:
                validFlag = False


            if validFlag == True and startLable not in line:
                line_content_list.append(f"{fileType}\n")

            else:
                line_content_list.append(line)

    with open(tempFile,'w') as fw:

        for line in line_content_list:
            fw.write(line)


    shutil.copy(tempFile,topFile)

    return 


def write_author_to_csv(topFile,authorName):
    
    tempFile =  "./sb_output/author_csv.csv"
    validFlag = False
    startLable = "#author_begin"
    endLable = "#author_end"

    line_content_list = []

    with open(topFile,newline='') as fr:
        lines = fr.readlines()

        for line in lines:
            if startLable in line:
                validFlag = True
                
            if endLable in line:
                validFlag = False


            if validFlag == True and startLable not in line:
                if "null" in line:
                    line_content_list.append(f"{authorName}\n")

                else:
                    line_content_list.append(f"{line}")

            else:
                line_content_list.append(line)

    with open(tempFile,'w') as fw:

        for line in line_content_list:
            fw.write(line)


    shutil.copy(tempFile,topFile)

    return

def inputCommand(inputStr,opt):

    inputStr = [ str_convert(item) for item in inputStr]
    # default verilog file 
    fileType='null'
    if len(inputStr) >= 2:
        if inputStr[1] == "addcsv":
            if 4 == len(inputStr):
                exeCmd,inst_module,top_module = inputStr[1:]

            else:
                print("Error: addcsv command format is wrong. Exit, please check and try again.")
                exit()

            top_module = modifyFileName(top_module)

            opt.input = inst_module
            opt.process = top_module
            inst_name = ""
          
            opt.step1 = "disable"
            opt.step2 = "enable"
            opt.step3 = "disable"

        
        elif "add" in inputStr[1]:

            if len(inputStr) == 6: 
                exeCmd,inst_module,inst_name,top_module,fileType = inputStr[1:]

            elif len(inputStr) == 5:
                exeCmd,inst_module,inst_name,top_module = inputStr[1:]

                if not inst_name.startswith('u_'):
                    fileType = top_module
                    top_module = inst_name
                    inst_name = 'u_' + os.path.basename(inst_module).split('.')[0]
 
            elif len(inputStr) == 4:
                exeCmd,inst_module,top_module = inputStr[1:]
                inst_name = 'u_' + os.path.basename(inst_module).split('.')[0]

            else:
                print(f"Error: add command format is wrong. Exit, please check and try again.")
                exit()

            print(f"Info: {exeCmd},{inst_module},{inst_name},{top_module}")

            if inst_module.endswith('.v') or inst_module.endswith('.sv'):
                opt.step1 = "enable"
                
            else:
                opt.step1 = "disable"

            opt.step2 = "enable"
            opt.step3 = "enable"

            top_module = modifyFileName(top_module)
            opt.input = inst_module
            opt.process = top_module

            if fileType == "sv":
                opt.output = top_module.replace('.csv','.sv')
            else:
                opt.output = top_module.replace('.csv','.v')

        elif inputStr[1] == "updatec":

            if len(inputStr) == 5: 
                exeCmd,inst_name,top_module,fileType = inputStr[1:]
            elif len(inputStr) == 4:
                exeCmd,inst_name,top_module = inputStr[1:]
            else:
                print("Error: updatec command format is wrong. Exit, please check and try again.")
                exit()
            print(f"Info: {exeCmd},{inst_name},{top_module}")

            top_module = modifyFileName(top_module)

            opt.process = top_module
            if fileType == "sv":
                opt.output = top_module.replace('.csv','.sv')
            else:
                opt.output = top_module.replace('.csv','.v')

            opt.step1 = "disable"
            opt.step2 = "enable"
            opt.step3 = "enable" 

        elif inputStr[1] == "update":

            if len(inputStr) == 5:
                exeCmd,inst_name,top_module,fileType = inputStr[1:]

                if ".csv" in inst_name or ".sv" in inst_name:
                    print(f"Error: the instance or module name of {inst_name} is wrong, it should be nake name. Please correct it and try again. Thanks.")
                    exit()

                if fileType not in ["v" ,"sv","null"]:
                    print(f"Error: please check the file type, it should be v or sv, default is v. Please correct it and try again. Thanks.")
                    exit()

            elif len(inputStr) == 4:
                exeCmd,inst_name,top_module = inputStr[1:]

                if ".csv" in inst_name or ".sv" in inst_name:
                    print(f"Error: the instance or module name of {inst_name} is wrong, it should be nake name. Please correct it and try again. Thanks.")
                    exit()

            else:
                print("Error: update command format is wrong. Exit, please check and try again.")
                exit()
            print(f"Info: {exeCmd},{inst_name},{top_module}")

            # if inst_module.endswith('.v') or inst_module.endswith('.sv'):
            #     opt.step1 = "enable"
            # else:
            #     opt.step1 = "disable"

            top_module = modifyFileName(top_module)

            opt.input = inst_name
            opt.process = top_module
            opt.step1 = "disable"

            if fileType == "sv":
                opt.output = top_module.replace('.csv','.sv')

            else:
                opt.output = top_module.replace('.csv','.v')

            opt.step2 = "enable"
            opt.step3 = "enable" 

        elif inputStr[1] == "updateall":

            if len(inputStr) == 4: 
                exeCmd,top_module,fileType = inputStr[1:]

            elif len(inputStr) == 3:
                exeCmd,top_module = inputStr[1:]

            else:
                print("Error: updateall command format is wrong. Exit, please check and try again.")
                exit()

            print(f"Info: {exeCmd},{top_module},{fileType}")

            opt.step1 = "disable"

            top_module = modifyFileName(top_module)

            opt.process = top_module
            inst_name = ""

            if fileType == "sv":
                opt.output = top_module.replace('.csv','.sv')

            else:
                opt.output = top_module.replace('.csv','.v')

            opt.step2 = "enable"
            opt.step3 = "enable" 

        elif inputStr[1] == "gen" :
            if len(inputStr) == 3:
                exeCmd,top_module = inputStr[1:]

            elif len(inputStr) == 4:
                exeCmd,top_module,fileType = inputStr[1:]

            else:
                print("Error: gen command format is wrong. Exit, please check and try again.")
                exit()

            top_module = modifyFileName(top_module)
            # print(f"{exeCmd},{top_module}")
            opt.step1 = "disable"
            opt.step2 = "disable"
            opt.step3 = "enable"
            # opt.input = top_module
            # opt.input = inst_module.replace(".csv",fileType)
            opt.process = top_module
            opt.output = top_module.replace(".csv",".v")

            if len(inputStr) == 4:
                opt.output = fileType + os.sep + os.path.basename(opt.output)

            inst_name = ""

        elif inputStr[1] == "check":
            if len(inputStr) == 3:
                exeCmd,top_module = inputStr[1:]

            else:
                print("Error: check command format is wrong. Exit, please check and try again.")
                exit()

            top_module = modifyFileName(top_module)
            opt.step1 = "disable"
            opt.step2 = "enable"
            opt.step3 = "disable"
            # opt.input = top_module
            # opt.input = inst_module.replace(".csv",fileType)
            opt.process = top_module
            opt.output = top_module.replace(".csv",".v")
            inst_name = ""
            
        elif inputStr[1] == "cov":
            if len(inputStr) == 3:
                exeCmd,inst_module = inputStr[1:]

            elif len(inputStr) == 4:
                exeCmd,inst_module,fileType = inputStr[1:]

            else:
                print("Error: cov command format is wrong. Exit, please check and try again.")
                exit()

            opt.step1 = "enable"
            opt.step2 = "disable"
            opt.step3= "disable"
            # opt.input = top_module
            opt.input = inst_module
            opt.output = inst_module.replace(".v",".csv")
            inst_name = ""

        elif inputStr[1] == "del":
            if len(inputStr) == 4:
                exeCmd,inst_name,top_module = inputStr[1:]

            elif len(inputStr) == 5:
                exeCmd,inst_name,top_module,fileType = inputStr[1:]

            else:
                print("Error: del command format is wrong. Exit, please check and try again.")
                exit()
            
            inst_module = inst_name
            print(f"Info: {exeCmd},{inst_module},{inst_name},{top_module}")

            top_module = modifyFileName(top_module)

            opt.input = inst_module
            opt.process = top_module

            if fileType == "sv":
                opt.output = top_module.replace('.csv','.sv')
            else:
                opt.output = top_module.replace('.csv','.v')
            
            opt.step1 = "disable"
            opt.step2 = "enable"
            opt.step3 = "enable"

        else:
            print(f"Error: {inputStr[1]} command does not exist. Exit, please check and try again.")
            exit()
    else:
        helpStr = "Usage: soc_build.py [cmds] args               \n\
        Cmds: add,addx,del,update,gen,cov,addcsv,check           \n\
        The detail cmds and args could be as follow:             \n\
        add .../module.csv|v instance .../top.csv <v|sv>         \n\
        addx .../module.csv|v instance .../top.csv <v|sv>        \n\
        del instance|module .../top.csv <v|sv>                   \n\
        update instance|module .../top.csv <v|sv>                \n\
        updateall .../top.csv <v|sv>                             \n\
        updatec instance .../top.csv                             \n\
        gen .../top.csv <path>                                   \n\
        cov .../top.v                                            \n\
        addcsv csvpath .../top.csv                               \n\
        check .../top.csv                                        \n\
        comments: the instance name must start with 'u_'         \n\
                  if no <v|sv> inputed, the default type is '.v'"

        print("--------------------------------------------------------")
        print(helpStr)
        print("--------------------------------------------------------")
        exit()

    fileTypeValue = fileType
    return exeCmd,opt,inst_name,fileTypeValue

def argparse():
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    parser.add_option("-i", "--input", dest="input",help="input file",default='./input/nr_top.v')
    parser.add_option("-p", "--process", dest="process",help="Output file in process",default='./sb_output/nr_top_out.csv')
    parser.add_option("-o", "--output", dest="output",help="Verilog file of output",default='./sb_output/nr_top_out.v')
    parser.add_option("-c", "--step1", dest="step1",help="Contract verilog to csv file",default='enable')
    parser.add_option("-t", "--step2", dest="step2",help="Integrate module csv to top csv",default='enable')
    parser.add_option("-g", "--step3", dest="step3",help="Generate verilog file from csv",default='enable')
    parser.add_option("-l", "--command", dest="cmd",help="support command line as following format:                 \
                                                          add module.csv|v instance top.csv                         \
                                                          addx module.csv|v instance top.csv                        \
                                                          del instance|module top.csv                               \
                                                          update instance|module top.csv                            \
                                                          updateall top.csv                                         \
                                                          updatec instance top.csv                                  \
                                                          gen top.csv verilog_path                                  \
                                                          cov top.v                                                 \
                                                          addcsv csvpath top.csv                                    \
                                                          check top.csv                                             \
                                                          ",default='./input')


    (options, args) = parser.parse_args()
    return options

#--------------------------------------------------------------------
#  get the file list 
#
#--------------------------------------------------------------------
def getFileList(path):
    filelist = []
    files =   os.listdir(path)

    for f in files:
        full_f = os.path.join(path, f)
        if os.path.isfile(full_f):
            filelist.append(full_f)

    return filelist

#--------------------------------------------------------------------
#  bakup the original file
#
#--------------------------------------------------------------------
def bakupFile(opt):
    # if os.path.dirname(opt.input):
    #     input_bakup = os.path.dirname(opt.input) + os.sep + os.path.basename(opt.input).replace('.','_bakup.')
    # else:
    #     input_bakup = os.path.basename(opt.input).replace('.','_bakup.')

    # if os.path.dirname(opt.output):
    #     output_bakup = os.path.dirname(opt.output) + os.sep + os.path.basename(opt.output).replace('.','_bakup.')
    # else:
    #     output_bakup = os.path.basename(opt.output).replace('.','_bakup.')

    if os.path.dirname(opt.process):
        process_bakup =   os.path.dirname(opt.process) + os.sep + os.path.basename(opt.process).replace('.','_bakup.')
        process_bakup = os.path.dirname(process_bakup) + os.sep + '.' + os.path.basename(process_bakup)

    else:
        process_bakup = os.path.basename(opt.process).replace('.','_bakup.')
        process_bakup = '.' + os.path.basename(process_bakup)

    # if os.path.exists(opt.input):
    #     shutil.copy(opt.input,input_bakup)

    # if os.path.exists(opt.output):
    #     shutil.copy(opt.output,output_bakup)

    if os.path.exists(opt.process):
        shutil.copy(opt.process,process_bakup)




if __name__ == '__main__':

    curDir = os.getcwd()
    logging,loghandler = loginit(curDir)
    filePath = ""

    opt = argparse()

    # write_csv_path = get_hw_path(sys.argv)
    # print(f"write_csv_path = {write_csv_path}")

    exeCmd,opt,inst_name,fileType = inputCommand(sys.argv,opt)
    bakupFile(opt)
    checkFlag = False
    tempDir = curDir + os.sep + "sb_output"
    exeCmd = exeCmd.strip()

    if not os.path.exists(tempDir):
        os.mkdir(tempDir)

    gen_top_csv(opt.process)

    if opt.step1 == "enable":
        print("Info: start to convert the verilog files to csv files...")
        csvGenObj = csvGenerator(logging)


        filePath = search_csv_path(opt.process,opt.input)
        opt.input = filePath
        # print(opt.input)

        csvGenObj.createDir(opt.input)

        if '/' in opt.input and not './' in opt.input:
            outputFile = os.path.dirname(opt.input) + os.sep + 'csv' + os.sep + os.path.basename(opt.input)

        else:
            outputFile = 'csv' + os.sep + os.path.basename(opt.input)


        if opt.input.endswith('.v'):
            outputFile = outputFile.replace('.v','.csv')

        else:
            outputFile = outputFile.replace('.sv','.csv')

        csvGenObj.main_process(opt.input,outputFile,fileType)
    
    if opt.step2 == "enable":
        inteObj = topCsvGenerator(opt.input,logging)

        # inteObj.get_inst_info_from_top(opt.process,inst_name,exeCmd,fileType)
        write_author_to_csv(opt.process,os.environ['USER'])

        if fileType != "null":
            write_gen_type_to_csv(opt.process,fileType)
            
        else:
            fileType = read_csv_base("gen_type",opt.process)
            fileType = fileType[0].strip()

        logging.info(f"fileType = {fileType}")

        if ("add" in exeCmd and "addcsv" not in exeCmd) or "update" == exeCmd:
            inteObj.get_csv_path(opt.process,opt.input,exeCmd,fileType)

        inteObj.get_inst_info_from_top(opt.process,inst_name,exeCmd,fileType)

        if "addcsv" == exeCmd:
            inteObj.add_csv_to_top(opt.process)

        elif "add" in exeCmd and "addcsv" not in exeCmd:
            inteObj.add_many_inst_module(exeCmd,opt.process,inst_name,fileType)

        elif "del" == exeCmd:
            inteObj.gen_top_port_from_top_csv(opt.process,inst_name,exeCmd)
            inteObj.check_del_csv_path(opt.process,inst_name,exeCmd)

        elif "update" in exeCmd:
            if "update" == exeCmd:
                inteObj.top_update_inst(opt.process,inst_name,fileType)

            elif "updateall" == exeCmd:
                dictModName = inteObj.get_all_csv_path(opt.process)
                logging.info(dictModName)

                for key in dictModName.keys():
                    inteObj.get_csv_path(opt.process,key,exeCmd,fileType)
                    inteObj.top_update_inst(opt.process,dictModName[key],fileType)

            elif "updatec" == exeCmd:
                inteObj.gen_top_port_from_top_csv(opt.process,inst_name,exeCmd)

            else:
                pass

        elif "check" in exeCmd:
            inteObj.check_port_info(opt.process)
            checkFlag = True

        else:
            print(f"Error: {exeCmd} command does not exist. Exit, please check and try again.")
            exit(0)

        if checkFlag == False and "del" not in exeCmd and 'updatec' not in exeCmd:
            print("Info: start to contract inst csv files to top csv file...")
            inteObj.gen_top_port_from_top_csv(opt.process,inst_name,exeCmd)
        # inteObj.main_process(opt.process,inst_name,fileType="null")         

    if opt.step3 == "enable":
        print("Info: start to create the module...")
        # if "gen" in exeCmd:
        inteObj = topCsvGenerator(opt.input,logging)
        inteObj.check_port_info(opt.process)

        genVObj = topVerilogGenerator(opt.process, opt.output, logging)
        genVObj.main_process(opt.output,fileType)


    loghandler.close()

    if os.path.exists(tempDir):
       shutil.rmtree(tempDir)



   

