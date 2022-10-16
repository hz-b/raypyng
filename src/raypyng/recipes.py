from .rml import ObjectElement
import numpy as np



class Simulate: pass

################################################################
class SimulationRecipe:
    def params(self,sim): return None
    def exports(self,sim): return None
    def simulation_name(self,sim): return None

################################################################
class ResolvingPower(SimulationRecipe):
    """Recipe for resolving power simulations.
    
    The eflectivity is automatically switched off for all elements, 
    the source if automatically recognized.

    Args:
            energy_range (np.array, list): the energies to simulate in eV
            exported_object (ObjectElement): the object to export
            source (ObjectElement, optional): the source object. 
                                              If None is provided, an automatic recogniton 
                                              of the source will be tried. Defaults to None.
            sim_folder (str, optional): the name of the simulation folder. If None, the rml 
                                        filename will be used. Defaults to None.
    """
    def __init__(self, energy_range:range, exported_object:ObjectElement,/, *args,source:ObjectElement=None,sim_folder:str=None):
        """
        Args:
            energy_range (np.array, list): the energies to simulate in eV
            exported_object (ObjectElement): the object to export
            source (ObjectElement, optional): the source object. 
                                              If None is provided, an automatic recogniton 
                                              of the source will be tried. Defaults to None.
            sim_folder (str, optional): the name of the simulation folder. If None, the rml 
                                        filename will be used. Defaults to None.
        """        
    
        if not isinstance(source, ObjectElement) and source != None:
            raise TypeError('The source must be an ObjectElement part of a beamline, while it is a', type(source))
        if not isinstance(energy_range, (range,np.ndarray)):
           raise TypeError('The energy_range must be an a ragne or a numpy array, while it is a', type(energy_range))
        if isinstance(exported_object, list):
            for exp_obj in exported_object:
                if not isinstance(exp_obj, ObjectElement):
                    raise TypeError('The exported_object must be an ObjectElement part of a beamline, while it is a', type(exported_object))
        else:
            if not isinstance(exported_object, ObjectElement):
                raise TypeError('The exported_object must be an ObjectElement part of a beamline, while it is a', type(exported_object))
            else:
                exported_object = [exported_object]

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
        params = []
        if sim.analyze:
            export = "ScalarBeamProperties"
        else: 
            export = "RawRaysOutgoing"
        for exp_obj in self.exported_object:
            params.append({exp_obj:export})
        return params

    def simulation_name(self,sim:Simulate):
        if self.sim_folder is None:
            return 'RP'
        else: 
            return self.sim_folder
            
################################################################
class Flux(SimulationRecipe):
    """Recipe for flux simulations.
    
    The reflectivity is automatically switched on for all elements, 
    and the source is automatically identified.

    Args:
            energy_range (np.array, list): the energies to simulate in eV
            exported_object (ObjectElement): the object to export
            source (ObjectElement, optional): the source object. 
                                              If None is provided, an automatic recogniton 
                                              of the source will be tried. Defaults to None.
            sim_folder (str, optional): the name of the simulation folder. If None, the rml 
                                        filename will be used. Defaults to None.
    """
    def __init__(self, energy_range:range, exported_object:ObjectElement,/, *args,source:ObjectElement=None,sim_folder:str=None):
        """
        Args:
            energy_range (np.array, list): the energies to simulate in eV
            exported_object (ObjectElement): the object to export
            source (ObjectElement, optional): the source object. 
                                              If None is provided, an automatic recogniton 
                                              of the source will be tried. Defaults to None.
            sim_folder (str, optional): the name of the simulation folder. If None, the rml 
                                        filename will be used. Defaults to None.
        """        
    
        if not isinstance(source, ObjectElement) and source != None:
            raise TypeError('The source must be an ObjectElement part of a beamline, while it is a', type(source))
        if not isinstance(energy_range, (range,np.ndarray)):
           raise TypeError('The energy_range must be an a ragne or a numpy array, while it is a', type(energy_range))
        if isinstance(exported_object, list):
            for exp_obj in exported_object:
                if not isinstance(exp_obj, ObjectElement):
                    raise TypeError('The exported_object must be an ObjectElement part of a beamline, while it is a', type(exported_object))
        else:
            if not isinstance(exported_object, ObjectElement):
                raise TypeError('The exported_object must be an ObjectElement part of a beamline, while it is a', type(exported_object))
            else:
                exported_object = [exported_object]

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
        
        # turn reflectivity of all elements on, grating eff to 100%
        for oe in sim.rml.beamline.children():
                if hasattr(oe,"reflectivityType"):
                    params.append({oe.reflectivityType:1})

        # all done, return resulting params
        return params

    def exports(self,sim:Simulate):
        params = []
        if sim.analyze:
            export = "ScalarBeamProperties"
        else: 
            export = "RawRaysOutgoing"
        for exp_obj in self.exported_object:
            params.append({exp_obj:export})
        return params

    def simulation_name(self,sim:Simulate):
        if self.sim_folder is None:
            return 'Flux'
        else: 
            return self.sim_folder

################################################################

class BeamWaist(SimulationRecipe):
    """Recipe for beamwaist simulations.
    
    At one defined energy export RawRaysOutgoing for all 
    optical elements, including image planes.

    Args:
            energy_range (np.array, list): the energies to simulate in eV
            source (ObjectElement, optional): the source object. If None is provided, 
                                              an automatic recogniton of the source 
                                              will be tried. Defaults to None.
            nrays (int): number of rays for the source
            sim_folder (str, optional): the name of the simulation folder. 
                                        If None, the rml filename will be used. 
                                        Defaults to None.
        
    """
    def __init__(self, energy:float,/,source:ObjectElement=None,nrays:int=None,sim_folder:str=None):
        """
        Args:
            energy_range (np.array, list): the energies to simulate in eV
            source (ObjectElement, optional): the source object. If None is provided, 
                                              an automatic recogniton of the source 
                                              will be tried. Defaults to None.
            nrays (int): number of rays for the source
            sim_folder (str, optional): the name of the simulation folder. 
                                        If None, the rml filename will be used. 
                                        Defaults to None.
        
        """        
    
        if not isinstance(energy, (int,float)):
           raise TypeError('The energy must be an a int or float, while it is a', type(energy))

        self.source = source
        self.energy = energy
        self.nrays  = nrays
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
        params.append({self.source.photonEnergy:self.energy})
        
        for oe in sim.rml.beamline.children():
                for par in oe:
                    try:
                        params.append({par.reflectivityType:0})
                    except:
                        pass

        # all done, return resulting params
        return params

    def exports(self,sim:Simulate):
        oe_list=[]
        for oe in sim.rml.beamline.children():
            oe_list.append(oe)
        exports = []
        for oe in oe_list:
            exports.append({oe:'RawRaysOutgoing'})
            # print('DEBUG:: exported oe', oe.name)
        return exports

    def simulation_name(self,sim:Simulate):
        if self.sim_folder is None:
            return 'Beamwaist'
        else: 
            return self.sim_folder

################################################################

    