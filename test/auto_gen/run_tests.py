# try to build manta instances from valid and invalid configuration files

from os import listdir
from os.path import isfile
from manta import Manta


# Valid Configurations

# test that they make a python API without errors
# TODO: test that their verilog passes lint

print(" ==== Testing valid configurations ====")
valid_configs_path = "test/auto_gen/valid_configs/"
for config_file in sorted(listdir(valid_configs_path)):
    caught_exception = None
    try:
        m = Manta(valid_configs_path + config_file)

    except Exception as e:
        caught_exception = e

    if caught_exception is None:
        print(f" -> no exceptions correctly raised by config file {config_file}")

    else:
        raise RuntimeError(
            f"Configuration {config_file} shouldn't have raised an exception, but raised  {caught_exception}"
        )


print("\n")

# Invalid Configurations

# test that they throw errors when generating a python API

print(" ==== Testing invalid configurations ====")
invalid_configs_path = "test/auto_gen/invalid_configs/"
for config_file in sorted(listdir(invalid_configs_path)):
    caught_exception = None
    try:
        m = Manta(invalid_configs_path + config_file)

    except Exception as e:
        caught_exception = e

    if caught_exception is not None:
        print(
            f" -> exception correctly raised by config file {config_file}:  {caught_exception}"
        )

    else:
        raise RuntimeError(
            f"Configuration {config_file} should have raised an exception, but did not!"
        )
