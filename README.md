
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

```python
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
If you want to work without docker, your paths will likely not match `/fastgenomics` for data and `/app` for your manifest. You can set two environment variables to ease testing:

- `FG_APP_DIR`: This path should contain `manifest.json`, normally this is `/app`.

    ```
    $FG_APP_DIR/manifest.json
    ```

- `FG_DATA_ROOT`: This path should contain you test data and output directories - normally, this is `/fastgenomics`.

    ```
    $FG_DATA_ROOT/data/...
    $FG_DATA_ROOT/config/parameters.json
    $FG_DATA_ROOT/output/
    $FG_DATA_ROOT/summary/
    ```

e.g.

```python
import os

# set paths for local development *before* importing fastgenomics 
os.environ["FG_APP_DIR"] = "/abs_path/to/my_app/"
os.environ["FG_DATA_ROOT"] = "/abs_path/to/my/sample_data"

from fastgenomics import io as fg_io
```

# App-Checker

Additionally it comes with an app-checker `check_my_app`, which checks for you:

 * the app directory structure
 * manifest.json

Usage:

```
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
