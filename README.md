# HIV Tools Navigator
## The Engine

The Navigator Engine process and manages decision logic to determine what should happen next
to a given data structure.

## Loading init graph to DB
```
cd navigator_engine
pipenv run flask navigator-engine load-graph
```
It will use the `Estimates_Navigator_BDG_Validations.xls` ini file as default.
In order to run it with custom init file do:
```
pipenv run flask navigator-engine load-graph /path/to/custom_graph_config_file.xlsx 
```
