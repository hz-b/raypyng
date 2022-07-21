# -*- coding: utf-8 -*-
"""
Created on Mon Sep 10 09:21:21 2018

@author: Simone Vadilonga
"""
import numpy as np
import xml.etree.ElementTree as ET
import os
import glob
from pathlib import Path
import random

#import matplotlib.pyplot as plt
from shutil import copyfile, rmtree
import itertools
import time

from RayPy_utils import *




class RayPy():
    '''     Here short description of the class
    '''

    def __init__(self, directory, rml_file):

        self.directory = directory
        self.rml_file = rml_file
        self.N_ind_par = 0 #number of indipendent parameter
        self.N_dep_par = 0 #number of indipendent parameter
        self.N_random_par = 0
        self.list_ind_par = [] # used by paramScan
        self.pscan_obj_list = []
        self.pscan_par_id = []
        self.min_max_list = []
        self.v = True
        self.repeat = 1
        return

    def RayVerbose(self, verbose:bool):
        if isinstance(verbose,bool):
            self.v = verbose
        else:
            raise Exception("Verbose accepts only True or False")

    def PrintXmlFile(self):
        show_tree(self.directory+self.rml_file)

    def SetRayLocation(self, ray_loc):
        self.ray_loc = ray_loc + " -b"
        print('set ray loc',self.ray_loc, 'yo')

    def SetExportedData(self, exp_data):
        self.exp_data = "\""+exp_data+"\""

    def SetExportedObject(self, exp_obj):
        self.exp_obj = "\""+exp_obj+"\""

    def SetFileLocation(self, file_loc):
        self.file_loc = file_loc

    def AddRandomParameter(self, obj_name, par_id, min_max_value):
        self.N_random_par += 1
        self.pscan_obj_list.append(obj_name)
        self.pscan_par_id.append(par_id)
        self.min_max_list.append(min_max_value)
        
    def AddIndependentParameter(self, obj_name, par_id, ind_par):
        self.ind_par = ind_par
        self.N_ind_par += 1
        self.pscan_obj_list.append(obj_name)
        self.pscan_par_id.append(par_id)
        self.calc_loop(self.ind_par)

    def AddDependentParameter(self, obj_name, par_id,dep_par,dependency):
        if self.N_ind_par == 0:
            raise Exception('First add an Indipendent Parameter!')
        self.N_dep_par += 1
        self.pscan_obj_list.append(obj_name)
        self.pscan_par_id.append(par_id)
        self.calc_loop(dep_par, False, dependency)
    
    def calc_loop(self, parameter, independent = True, dependency = 0, noprint=0):
        if independent == True:
            self.list_ind_par.append(parameter)
            self.values = []
            for t in itertools.product(*self.list_ind_par):
                self.values.append(t)
        if independent == False:
            #print('here self.values',self.values)
            #print('parameter', parameter)
            #print('list_ind_par',self.list_ind_par)
            counter = 1
            index = 0
            for i in range(len(self.values)):
                #print('index', index, 'i',i, 'q',int(len(self.values)/len(parameter)),counter%int(len(self.values)/len(parameter)))
                #for j in range(len(self.values[i])):
                self.values[i]=self.values[i]+(parameter[index],)
                #print('self.values',counter,self.values)
                if (counter%int(len(self.values)/len(parameter)))== 0: 
                    index +=1
                counter+=1
                    #print(self.values[i][dependency],self.list_ind_par[dependency][j])
                    #if self.values[i][dependency] == self.list_ind_par[dependency][j]:
                        ##print(self.values[i][dependency],self.list_ind_par[dependency][j])
                        #self.values[i]=self.values[i]+(parameter[j],)
            #print('self.values',self.values)
                        
        print ('\n############################################')
        print ('\nYou implemented', len(self.values), 'scans,')
        print ('with ', self.N_ind_par, 'indipendent parameter(s)')
        print ('and ', self.N_dep_par, 'indipendent parameter(s)')
        #for i in range(len(self.values)):
        #    print (i, self.values[i])

    def CreateRmlFiles(self, attribute, first_file = 0, current_directory = '', repeat=False):
        # writing new configuration files changing the value of the parameter
        print('\n#######################################')
        print('Creating .rml files')
        print('...')
        #print('self.values',self.values)
        if repeat:
            self.repeat=repeat
        for n in range (0,self.repeat):
            #print ('N', n)
            count = 0
            subdir = current_directory+'ScanParam_' + attribute+'_'+str(n)+'/'
            if not os.path.exists(subdir):
                os.makedirs(subdir)
            for par2 in range(len(self.values)):
                xml_string = replace_Nvalue_by_id(self.directory+self.rml_file,
                                                    self.pscan_obj_list,
                                                    self.pscan_par_id,
                                                    self.values[par2])
                #print('pscanobj list', self.pscan_obj_list)
                #print('pscan_par_id list', self.pscan_par_id)
                #print('values list', self.values[par2])
                    #if not os.path.exists(subdir+str(count)):
                    #os.makedirs(subdir+str(count))
                xml_name = subdir+str(count)+'_'+self.rml_file
                PrintXml2File(xml_name, xml_string.decode("utf-8"))
                count += 1
            #creating looper file and Ytrain
            Y_train = []
            with open(subdir+'/looper.csv', 'w') as f:
                f.write('sep =\t \n')
                f.write('P0\t')
                #print (values_list)
                for i in range(len(self.pscan_obj_list)):
                    f.write(self.pscan_obj_list[i]+'_'+self.pscan_par_id[i]+'\t')
                for i in range(len(self.values)):
                    #print ('i', i)
                    f.write('\n')
                    f.write(str(i)+ '\t')
                    #print('length',len(self.values))
                    #print('length',len(self.values[i]))
                    #print('i',i)
                    #print('length',self.values[i])
                    for j in range(len(self.values[0])):
                        #print('j',j)
                        f.write(str(self.values[i][j])+ '\t')
                        Y_train.append(self.values[i][j])
                Y_train = np.array(Y_train)
                Y_train = Y_train.reshape((len(self.values), len(self.values[0]) ))
                np.savetxt(subdir+'Y_dataset.dat', Y_train)
        print('DONE')
        print('#######################################\n') 
            
    def CreateRandomRmlFiles(self, attribute, n_files, first_file = 0, current_directory = ''):
        # writing new configuration files changing the value of the parameter
        count = 0
        subdir = current_directory+'ScanParam_' + attribute+'/'
        if not os.path.exists(subdir):
            os.makedirs(subdir)
        
        #print('pscanobj list', self.pscan_obj_list)
        #print('pscan_par_id list', self.pscan_par_id)
        #print('min_max_list', self.min_max_list)
        
        
        #print('values list', self.values)
        minmax_values_all = []
        self.values = []
        for i in range(n_files):
            minmax_values = []
            for minmax in self.min_max_list:
                minmax_values.append(random.uniform(minmax[0], minmax[1]))
            minmax_values_all.append(minmax_values)
            self.values.append(minmax_values)
            xml_string = replace_Nvalue_by_id(self.directory+self.rml_file,
                                                 self.pscan_obj_list,
                                                 self.pscan_par_id,
                                                 minmax_values)
            xml_name = subdir+str(count)+'_'+self.rml_file
            PrintXml2File(xml_name, xml_string.decode("utf-8"))
            count += 1
        #creating looper file and Ytrain
        Y_train = []
        with open(subdir+'/looper.csv', 'w') as f:
            f.write('sep =\t \n')
            f.write('P0\t')
            for i in range(len(self.pscan_obj_list)):
                f.write(self.pscan_obj_list[i]+'_'+self.pscan_par_id[i]+'\t')
            for i in range(n_files):
                f.write('\n')
                f.write(str(i)+ '\t')
                for j in range(len(minmax_values_all[0])):
                    f.write(str(minmax_values_all[i][j])+ '\t')
                    Y_train.append(minmax_values_all[i][j])
            Y_train = np.array(Y_train)
            Y_train = Y_train.reshape((len(minmax_values_all), len(minmax_values_all[0]) ))
            np.savetxt(subdir+'Y_dataset.dat', Y_train)

    def StartSimulations(self, attribute,  first_file = 0, current_directory = '',cpus=False):
        subdir = current_directory+'ScanParam_' + attribute+'/'
        Number_Jobs  = len(self.values)
        print ('\n##############################################')
        print ('Starting simulations\n')
        if cpus == False:
            Number_Workers=mp.cpu_count()
        else:
            Number_Workers=cpus
        print ('I found: ',Number_Workers, 'workers (cpu)')
        jobs_todo = mp.JoinableQueue()
        #print ('jobs to do ',jobs_todo)
        results = mp.Queue()
        counter=Number_Jobs
        consumers = [Worker(jobs_todo, results, self.ray_loc) for i in range(Number_Workers)]
        for w in consumers:
            w.start()
        print('rml location', subdir + str(0)+'_'+ self.rml_file + '.rml')
        if first_file >= counter:
            print('ERROR, CHECK THE FIRST FILE, IS TOO HIGH \n')
            print('first file', first_file)
            print('last file', counter)
            sys.exit("Check the error above")
            
        for i in range(first_file, counter):
            rml_loc = subdir + str(i)+'_'+ self.rml_file + '.rml'
            #print('this is the rml location', rml_loc)
            ray_stuff = self.v, self.ray_loc, rml_loc, self.exp_obj, self.exp_data, subdir, i
            jobs_todo.put(Job(ray_stuff))
        for i in range(Number_Workers):
            jobs_todo.put(None)
        jobs_todo.join()
        collect_results=[]
        while counter:
            result = results.get()
            collect_results.append(result)
            counter -= 1
        print(result)

    def CheckSimulations(self, attribute, current_directory = '',cpus=False, repeat = False):
        ''' This method checks if the rml files in the ScaParam directory have been all simulated and extracted. It simulates the missing files.
        '''
        ### checking rml vs csv files
        print('#######################################')
        print('Start Checking Simulations')
        print('...')
        if repeat:
            self.repeat=repeat
        #print(self.repeat)
        for n in range(0,self.repeat):
            subdir = current_directory+'ScanParam_' + attribute+'_'+str(n)+'/'
            if n==0:
                rml_list = glob.glob(subdir+'*.rml')
                sim_list = glob.glob(subdir+'*.csv')
            else:
                rml_list += glob.glob(subdir+'*.rml')
                sim_list += glob.glob(subdir+'*.csv')
        exp_object = self.exp_obj.replace('"', '')
        exp_object = exp_object.split(',')
        exp_data = self.exp_data.replace('"', '')
        missing_simulations = []
        missing_simulations_numbers = []
        missing_simulations_length = 1
        exp_data_list=exp_data.split(',')
        #print ('EXPORTED DATA:', exp_data_list, exp_data_list[0])
        rml_list = sorted(rml_list)
        sim_list = sorted(sim_list)
        #for r in rml_list:
            #print('rml_list', r)
        #print('\n\n')
        #for s in sim_list:
            #print('sim_list', s)
        #print('FOR LOOP')
        for n in range(0,self.repeat):
            temp_sim=[]
            temp_sim_number=[]
            subdir = current_directory+'ScanParam_' + attribute+'_'+str(n)+'/'
            #print('subdir', subdir)
            for i in range(0,len(self.values)):
                #print('i', i)
                for obj in exp_object:
                    for exp_data_el in exp_data_list:
                        sim = Path(subdir+str(i)+'_'+obj+'-'+exp_data_el+'.csv')
                        #print(sim)
                        if sim.is_file() == True:
                            #print('Found')
                            temp_sim.append(None)
                            temp_sim_number.append(None)
                            pass
                        elif sim.is_file() == False:
                            #print('Missing')
                            missing_rml = subdir+str(i)+'_'+self.rml_file+'.rml'
                            #print('missing:',sim)
                            temp_sim.append(missing_rml)
                            temp_sim_number.append(i)
                            break
            missing_simulations.append(temp_sim)
            missing_simulations_numbers.append(temp_sim_number)
                        
        #print('\n\n\n')
        #print('msn',missing_simulations_numbers)
        #print('missing simulations:')
        for m in range(len(missing_simulations)):
            #print('before', missing_simulations_numbers[m] )
            missing_simulations[m] = list( dict.fromkeys(missing_simulations[m]))
            missing_simulations_numbers[m] = list( dict.fromkeys(missing_simulations_numbers[m]))
            #print('after', missing_simulations_numbers[m] )
        msn = 0
        none_occurences = 0
        for m in range(0,len(missing_simulations_numbers)):
            #print('m',missing_simulations_numbers[m])
            msn+=len(missing_simulations_numbers[m])
            none_occurences += missing_simulations_numbers[m].count(None)
        #print ('msn', msn)
        ### simulating the missing files
        print('I still have to do', msn-none_occurences, 'simulations!!!!')
        if msn-none_occurences == 0:
            print('#######################################')
            sys.exit(0)
        if msn != 0:
            Number_Jobs  = msn-none_occurences
            print ('Starting simulations\n')
            if cpus == False:
                Number_Workers=mp.cpu_count()
            else:
                Number_Workers=cpus
            print ('I found: ',Number_Workers, 'workers (cpu)')
            jobs_todo = mp.JoinableQueue()
            results = mp.Queue()
            counter=Number_Jobs
            consumers = [Worker(jobs_todo, results, self.ray_loc) for i in range(Number_Workers)]
            for w in consumers:
                w.start()
            # here is different: I send only the files that have not been calculated
            print('counter', counter)
            ind = msn
            print('counter', counter)
            sim_numb = 0
            print('\n\n\n Now we fill the jobs')
            for mis_sim_num_batch in missing_simulations_numbers:
                subdir = current_directory+'ScanParam_' + attribute+'_'+str(sim_numb)+'/'
                sim_numb+=1
                for i in mis_sim_num_batch:
                    print('i', i)
                    if i == None:
                        print('I pass')
                        pass
                    else:
                        rml_loc = subdir + str(i)+'_'+ self.rml_file + '.rml'
                        print (rml_loc)
                        ray_stuff = self.v, self.ray_loc, rml_loc, self.exp_obj, self.exp_data, subdir, i
                        jobs_todo.put(Job(ray_stuff))
            for i in range(Number_Workers):
                jobs_todo.put(None)
            jobs_todo.join()
            collect_results=[]
            while counter:
                result = results.get()
                collect_results.append(result)
                counter -= 1
            print(result)
            
        
    
                    
                

        
        