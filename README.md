
    OOooOoO    Oo    .oOOOo.  oOoOOoOOo  .oOOOo.
    o         o  O   o     o      o     .O     o                              o
    O        O    o  O.           o     o
    oOooO   oOooOoOo  `OOoo.      O     O
    O       o      O       `O     o     O   .oOOo .oOo. 'OoOo. .oOo. `oOOoOO. O  .oOo  .oOo
    o       O      o        o     O     o.      O OooO'  o   O O   o  O  o  o o  O     `Ooo.
    o       o      O O.    .O     O      O.    oO O      O   o o   O  o  O  O O  o         O
    O'      O.     O  `oooO'      o'      `OooO'  `OoO'  o   O `OoO'  O  o  o o' `OoO' `OoO'

---

[![Build Status](https://travis-ci.org/FASTGenomics/fastgenomics-py.png?branch=master)](https://travis-ci.org/FASTGenomics/fastgenomics-py)

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

# Testing
If you want to test file input/output, you have to provide a sample `config/input_file_mapping.json`.

## Testing without docker
If you want to work without docker, your paths will likely not match our default

 - `/app`  
   path to your app, must contain `manifest.json`
 - `/fastgenomics`
   path to sample data. Should contain `config/`, `data/`, `output/`, `summary/`.  

However, you can set them by providing environment variables `FG_APP_DIR` and `FG_DATA_ROOT`
or by setting paths within your code: 

```python
from fastgenomics import io as fg_io

fg_io.set_paths("path_to/my_app", "path_to_my/sample_data")
```
Keep in mind to reset the paths to default (just by not setting paths), when transforming your app
into an docker-image!

For more details see our [Hello Genomics Python App](https://github.com/fastgenomics/hello_genomics_calc_py36).
