# try to build manta instances from valid and invalid configuration files

from os import listdir
from os.path import isfile
from manta import Manta


# Valid Configurations

print(" ==== Testing valid configurations ====")
valid_configs_path = 'test/api_gen/valid_configs/'
for config_file in sorted(listdir(valid_configs_path)):
    caught_exception = None
    try:
        m = Manta(valid_configs_path + config_file)
    
    except Exception as e:
        caught_exception = e
        
    if caught_exception is None:
        print(f" -> config file {config_file} raised no exceptions.")
    
    else:
        raise RuntimeError(f"Configuration {config_file} shouldn't have raised an exception, but raised  {caught_exception}")



print('\n')

# Invalid Configurations

print(" ==== Testing invalid configurations ====")
invalid_configs_path = 'test/api_gen/invalid_configs/'
for config_file in sorted(listdir(invalid_configs_path)):
    caught_exception = None
    try:
        m = Manta(invalid_configs_path + config_file)
    
    except Exception as e:
        caught_exception = e

    if caught_exception is not None: 
        print(f" -> config file {config_file} raised the following exception:  {caught_exception}")
    
    else:
        raise RuntimeError(f"Configuration {config_file} should have raised an exception, but did not!")
