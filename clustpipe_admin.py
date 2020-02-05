"""
This file contains the Admin class, which list 
functions used for administration tasks related to 
the ClusterPipe.
"""

#==================================================
# Requested imports
#==================================================

import os
import copy
import numpy as np
import pickle


#==================================================
# Cluster class
#==================================================

class Admin():
    """ 
    Admin class. 
    This class serves as parser to the ClusterPipe class and 
    contains administrative related tools.
    
    Methods
    ----------  
    - _check_obsID(self, obsID)
    - config_save(self)
    - config_load(self)
    """
    
    #==================================================
    # Check obsID
    #==================================================
    
    def _check_obsID(self, obsID):
        """
        Validate the obsID given by the user
        
        Parameters
        ----------
        - obsID

        Outputs
        -------
        - obsID (list): obsID once validated
        
        """
        
        if obsID is None:
            obsID = self.obs_setup.obsid
            
        else:        
            # Case of obsID as a string, i.e. single run
            if type(obsID) == str:
                if obsID in self.obs_setup.obsid:
                    obsID = [obsID] # all good, just make it as a list
                else:
                    raise ValueError("The given obsID does not match any of the available observation ID.")
                
            # Case of obsID as a list, i.e. multiple run
            elif type(obsID) == list:
                good = np.array(obsID) == np.array(obsID) # create an array of True
                for i in range(len(obsID)):
                    # Check type
                    if type(obsID[i]) != str:
                        raise ValueError("The given obsID should be a string or a list of string.")
                
                    # Check if the obsID is valid and flag
                    if obsID[i] not in self.obs_setup.obsid:
                        if not self.silent: print('WARNING: obsID '+obsID[i]+' does not exist, ignore it')
                        good[i] = False

                # Select valid obsID
                if np.sum(good) == 0:
                    raise ValueError("None of the given obsID exist")
                else:
                    obsID = list(np.array(obsID)[good])
                    
                # Remove duplicate
                obsID = list(set(obsID))
                    
                # Case of from format
            else:
                raise ValueError("The obsID should be either a list or a string.")
    
        return obsID

    
    #==================================================
    # Save the simulation configuration
    #==================================================
    
    def config_save(self):
        """
        Save the configuration for latter use
        
        Parameters
        ----------

        Outputs
        -------
        
        """
        
        # Create the output directory if needed
        if not os.path.exists(self.output_dir): os.mkdir(self.output_dir)

        # Save
        with open(self.output_dir+'/config.pkl', 'wb') as pfile:
            pickle.dump(self.__dict__, pfile, pickle.HIGHEST_PROTOCOL)
            
            
    #==================================================
    # Load the simulation configuration
    #==================================================
    
    def config_load(self, config_file):
        """
        Save the configuration for latter use
        
        Parameters
        ----------
        - config_file (str): the full name to the configuration file

        Outputs
        -------
        
        """

        with open(config_file, 'rb') as pfile:
            par = pickle.load(pfile)
            
        self.__dict__ = par



        
