# -*- coding: utf-8 -*-
"""
Created on Mon Sep 10 09:47:49 2018

@author: Simone Vadilonga
"""

import xml.etree.ElementTree as ET
from lxml import etree

import subprocess
import sys
import multiprocessing as mp

import time
import platform
import signal
import os


##########################################
### XML PARSING
#########################################
def show(elem, indent=0):
    print (' ' * indent + elem.tag, elem.attrib, elem.text)
    for child in elem.findall('*'):
        show(child, indent +5)

def show_tree(xml_file):
    """ Parameters:
        xml_file: string
            The path to the XML file

        The function prints out the tree of the XML file
    """
    tree = ET.parse(xml_file+'.rml')
    root = tree.getroot()
    show(root)


def replace_Nvalue_by_id(xml_file,obj_list,par_list,value_list):
    """Parameters:  xml_file : string
                        The path to the xml file to modify

                    obj_list : list of string
                        The name of the objects to modify

                    par_name : list of strings
                        The id of the parameters to modify

                    value : list of int or float
                        The new value of the parameters to modify


       Return: str_xml_file : string
                       A string containing the new XML file, if the
                       attribute "auto" is switched on, it will be turned off
                       for the selected element. If it does not exist it will
                       be created and and set to off.

    """
    root = etree.parse(xml_file+'.rml')

    count = 0
    for obj_name in obj_list:
        par_name = par_list[count]
        value = value_list[count]
        object = root.xpath("//object[@name = '%s']" % (obj_name))
        if len(object)==0:
            raise Exception("Wrong Object name:", obj_name)
        param =  object[0].xpath("param[@id = '%s']" % par_name)[0].text
        if not param:
            raise Exception("Wrong parameter id", par_name)
        #this changes the value of the parameter
        object[0].xpath("param[@id = '%s']" % par_name)[0].text = str(value)
        # this changes the status of auto from on to off
        object[0].xpath("param[@id = '%s']" % par_name)[0].set('auto', 'F')
        count += 1

    str_xml_file = etree.tostring(root,
                                  pretty_print=True,
                                  xml_declaration = True,
                                  encoding='UTF-8')
    return str_xml_file


def PrintXml2File(file_name, xml_string):
    """Parameters:  file_name : string
                        The name of the xml file to be created

                    xml_string : string
                        a string containg the xml file

    """
    with open(file_name+'.rml', "w") as text_file:
        text_file.write(xml_string)

######################
### DATA ANALYSIS ####
######################
def read_header(path_to_file):
    """
    Parameters: the path to the csv file with the results

    Return a list of strings, the labels of each column

    """
    with open(path_to_file) as fp:
        for i, line in enumerate(fp):
            #print i,line
            if i == 1:
                header = line
                break
    words = header.split()
    return words

#################################
#### GREGOR IMPLEMENTATION ######
#################################
class Worker(mp.Process):
    def __init__(self, task_Q, result_Q, ray_loc):
        mp.Process.__init__(self)
        self.task_Q = task_Q
        self.result_Q = result_Q
        self.ray_loc = ray_loc
    def run(self):
        #a = 20
        env = dict(os.environ)
        #env['LD_LIBRARY_PATH'] = '/home/vadilonga/RAY-UI-development/'
        process_name = self.name
        ray_process = subprocess.Popen(self.ray_loc, shell=True, stdin=subprocess.PIPE, #
        stdout=subprocess.PIPE, env=env)
        counter=0
        while True:
            if counter%10 == 0:
                print('RESTART')
                ray_process.stdin.write(b"quit\n")
                ray_process.stdin.flush()
                ray_process.wait()
                ray_process = subprocess.Popen(self.ray_loc, 
                                           shell=True, 
                                           stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE, 
                                            env=env)
                
            print ('counter',counter)
            next_task = self.task_Q.get()
            #print(process_name, self.task_Q.get())
            if next_task is None:
                print('Killing '+str(process_name))
                self.task_Q.task_done()
                break
            #print('here')
            print(str(process_name)+' doing '+str(next_task))
            answer = next_task(ray_process)
            self.task_Q.task_done()
            self.result_Q.put(answer)
            counter +=1
        ray_process.stdin.write(b"quit\n")
        ray_process.stdin.flush()
        ray_process.wait()
        
        return


def wait_for_ray_output(ray_process, success_string = 'trace success', fail_string = '',verbose=True):
    """_summary_

    Args:
        ray_process (_type_): _description_
        success_string (str, optional): _description_. Defaults to 'trace success'.
        fail_string (str, optional): _description_. Defaults to ''.
        verbose (bool, optional): _description_. Defaults to True.
    """
    out = "dummy-start-value"
    while len(out) > 0 and out != success_string:
       out = ray_process.stdout.readline().decode('utf8').rstrip('\n')
       if verbose:
	       print(out)



def single_job(ray_stuff, ray_process):
    ray_verbose, ray_loc, rml_loc, exp_obj, exp_data, exp_loc, prefix = ray_stuff
    print ('Starting Single Job')
    #ray_verbose = True
    if ray_verbose == True:
        print ('################')
        print ('pid', ray_process.pid)
    env = dict(os.environ)
    load_command = bytes('load '+ rml_loc + '\n', "utf-8" )
    ray_process.stdin.write(load_command)
    if ray_verbose == True:
        print ("loading rml file", rml_loc)
    ray_process.stdin.flush()
    if ray_verbose == True:
        print(ray_process.stdout.readline())
    if ray_verbose == True:
        print ("start tracing")
    trace_command=bytes('trace'+'\n', encoding='utf-8')
    ray_process.stdin.write(trace_command)
    ray_process.stdin.flush()
    wait_for_ray_output(ray_process, success_string = 'trace success', verbose=False)

    if ray_verbose == True:
        print ("exporting")
    export_command=bytes("export "+exp_obj+" "+exp_data+" "+exp_loc+" "+str(prefix)+'_'+" \n", encoding='utf-8')
    print('export command', export_command)
    ray_process.stdin.write(export_command)
    ray_process.stdin.flush()
    #print('OUT',ray_process.stdout.readline())
    wait_for_ray_output(ray_process, success_string = 'export success', verbose=False)


class Job(object):
    def __init__(self, ray_stuff):
        self.ray_stuff = ray_stuff
    def __call__(self,a):
        try:
            single_job(self.ray_stuff, a)
            self.result='done'
        except:
            self.result='error'
            raise
        return self.result
    def __str__(self):
        return str(self.ray_stuff[-1])