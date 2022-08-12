#from .simulate import Simulate
from .rml import ObjectElement,ParamElement, BeamlineElement
import numpy as np



class Simulate: pass

################################################################
class SimulationRecipe:
    def params(self,sim): return None
    def exports(self,sim): return None
    def simulation_name(self,sim): return None

################################################################
class ResolvingPower(SimulationRecipe):
    """_summary_

    Args:
        SimulationRecipe (_type_): _description_
    """
    def __init__(self, energy_range:range, exported_object:ObjectElement,/, *args,source:ObjectElement=None,sim_folder:str=None, repeat:int=1, cpu:int=1, force:bool=False):
    
        if not isinstance(source, ObjectElement) and source != None:
            raise TypeError('The source must be an ObjectElement part of a beamline, while it is a', type(source))
        if not isinstance(energy_range, (range,np.ndarray)):
           raise TypeError('The energy_range must be an a ragne or a numpy array, while it is a', type(energy_range))
        if not isinstance(exported_object, ObjectElement):
            raise TypeError('The exported_object must be an ObjectElement part of a beamline, while it is a', type(exported_object))

        self.source = source
        self.energy_range = energy_range
        self.exported_object = exported_object
        self.args = args
        self.sim_folder = sim_folder
    
    def params(self,sim:Simulate):
        params = []

        # find source and add to param with defined user energy range
        found_source = False
        if self.source == None:
            for oe in sim.rml.beamline.children():
                if hasattr(oe,"photonEnergy"):
                    self.source = oe
                    found_source = True
                    break        
            if found_source!=True:
                raise AttributeError('I did not find the source')        
        params.append({self.source.photonEnergy:self.energy_range})
        
        # handle free/optional arguments
        if self.args:
            for a in self.args:
                if not isinstance(a,dict):
                    raise TypeError('The args must be dictionaries, while I found a',type(a) )
                params.append(a)
        
        # turn reflectivity of all elements off, grating eff to 100%
        for oe in sim.rml.beamline.children():
                if hasattr(oe,"reflectivityType"):
                    params.append({oe.reflectivityType:0})

        # all done, return resulting params
        return params

    def exports(self,sim:Simulate):
        #params
        if sim.analyze:
            return [{self.exported_object:'ScalarBeamProperties'}]
        else:
            return [{self.exported_object:'RawRaysOutgoing'}]

    def simulation_name(self,sim:Simulate):
        if self.sim_folder is None:
            return 'RP'
        else: 
            return self.sim_folder

################################################################

    