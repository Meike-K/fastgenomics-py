
    OOooOoO    Oo    .oOOOo.  oOoOOoOOo  .oOOOo.
    o         o  O   o     o      o     .O     o                              o
    O        O    o  O.           o     o
    oOooO   oOooOoOo  `OOoo.      O     O
    O       o      O       `O     o     O   .oOOo .oOo. 'OoOo. .oOo. `oOOoOO. O  .oOo  .oOo
    o       O      o        o     O     o.      O OooO'  o   O O   o  O  o  o o  O     `Ooo.
    o       o      O O.    .O     O      O.    oO O      O   o o   O  o  O  O O  o         O
    O'      O.     O  `oooO'      o'      `OooO'  `OoO'  o   O `OoO'  O  o  o o' `OoO' `OoO'

---

# About

This python module handles all common interfaces of your application to the FASTGenomics runtime:

 * Input/Output of files
 * Parameters

and provides some convenience functions.

Example:
``` python
from fastgenomics import io as fg_io

# get all parameters
parameters = fg_io.get_parameters()
...
# get a specific parameter
my_parameter = fg_io.get_parameter('my_parameter')
...
# load a file
my_input_path = fg_io.get_input_path('my_input_key')
with my_input_path.open() as f:
    # do something like f.read()
    pass

# store a file
my_output_path = fg_io.get_output_path('my_output_key')
...

```

# Testing without docker
If you want to work without docker, your paths will likely not match /fastgenomics for data and /app for your manifest. You can set two environment variables to ease testing:
- APP_ROOT_DIR: This path should contain manifest.json, normally this is /app.
- DATA_ROOT_DIR: This path should contain you test data - normally, this is /fastgenomics.

e.g. 
``` python
import os
os.environ("APP_ROOT_DIR") = "/usr/local/sample_app/"
os.environ("DATA_ROOT_DIR") = "/usr/local/sample_app/data"

# load fastgenomicy-py when the environment variables are set.
from fastgenomics import io as fg_io 
```
# App-Checker

Additionally it comes with an app-checker `check_my_app`, which checks for you:
 * the app directory structure
 * manifest.json

Usage:
``` txt
check_my_app [-h] [--input [APP_DIR]] -n APP_NAME [-r DOCKER_REGISTRY] [-d] [-f]

FASTGenomics App Checker

optional arguments:
  -h, --help            show this help message and exit
  --input [APP_DIR]     Path to your application
  -n APP_NAME, --name APP_NAME
                        Path to sample_data
  -r DOCKER_REGISTRY, --registry DOCKER_REGISTRY
                        URL of the docker-registry
  -d, --docker          create docker-compose.yml
  -f, --filemapping     create input_file_mapping.json
```

Just run `check_my_app --name <my_new_app>` and check it.

It can create for you:
 * a `docker-compose.yml`
 * the `input_file_mappings.json` for your sample data

 Just run `check_my_app --name <my_new_app> -d -f` to create both.

For more details see our [Hello Genomics Python App](https://github.com/fastgenomics/hello_genomics_calc_py36).
