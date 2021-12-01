# RML2SHACL 

A tool to generate SHACL shapes from RML mapping files for RDF graphs validation. 



# Prerequisite

Install the required dependencies: 
```bash
pip install -r requirements.txt
```


# Usage 


General usage info: 

``` 
usage: main.py [-h] [-logLevel LOGLEVEL] MAPPING_FILE

positional arguments:
  MAPPING_FILE          RML mapping file to be converted into SHACL shapes.

optional arguments:
  -h, --help            show this help message and exit
  -logLevel LOGLEVEL, -l LOGLEVEL
                        Logging level of this script
                        Possible values: INFO,DEBUG,WARN

```




To generate your shacl shapes: 

```bash 
python3 main.py MAPPING_FILE
```

For more clarity to locate the generated shape file, please 
delete the ``shapes/`` directory that came with this repo first. 
Otherwise, the generated shape file will have the same parent paths as the 
mapping file but under the ``shapes/``. 


Eg: 

If you execute the following:
```
python3 main.py evaluation/astrea_test/ssn/mapping.ttl
```

The generated shape file will then be located here: 
``shapes/evaluation/astrea_test/ssn/mapping.ttl-output-shape.ttl``






