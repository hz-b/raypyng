import pandas as pd

def save_data_as_py_AXUV(filepath, output_path):
    # Load the CSV data into a DataFrame
    df = pd.read_csv(filepath)
    
    # Create a dictionary where the keys are the energy values and the values are from the 'Photon_to_nAmp_BestOf' column
    data_dict = df.set_index('Energy[keV]')['Photon_to_nAmp_BestOf'].to_dict()
    
    # Create or open the Python file where the dictionary will be written
    with open(output_path, 'w') as file:
        # Write the dictionary to the file formatted as a Python dictionary
        file.write('AXUV_dict = ' + str(data_dict) + '\n')

def save_data_as_py_GaAsP(filepath, output_path):
    # Load the CSV data into a DataFrame
    df = pd.read_csv(filepath)
    
    # Create a dictionary where the keys are the energy values and the values are from the 'Photon_to_nAmp_BestOf' column
    data_dict = df.set_index('Energy[keV]')['Photon_to_nAmp'].to_dict()
    
    # Create or open the Python file where the dictionary will be written
    with open(output_path, 'w') as file:
        # Write the dictionary to the file formatted as a Python dictionary
        file.write('GaAsP_dict = ' + str(data_dict) + '\n')


csv_file_path = 'GaAsP.csv'
output_py_path = 'GaAsP.py'
save_data_as_py_GaAsP(csv_file_path, output_py_path)
csv_file_path = 'AXUV.csv'
output_py_path = 'AXUV.py'
save_data_as_py_AXUV(csv_file_path, output_py_path)
from GaAsP import GaAsP_dict
from AXUV import AXUV_dict


def load_data_from_py_AXUV():
    # Convert the dictionary back to a DataFrame
    df = pd.DataFrame(list(AXUV_dict.items()),
    columns=['Energy[keV]', 'Photon_to_nAmp_BestOf'])    
    return df

def load_data_from_py_GaAsP():
    # Convert the dictionary back to a DataFrame
    df = pd.DataFrame(list(GaAsP_dict.items()),
    columns=['Energy[keV]', 'Photon_to_nAmp'])
    return df


df = load_data_from_py_AXUV()
print(df.head())


df = load_data_from_py_GaAsP()
print(df.head())
