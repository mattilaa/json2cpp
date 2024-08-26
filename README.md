# JSON to C++ class generator
## Description
A simple Python script that generates C++ classes from a JSON schema file. RapidJSON is used as a backend for JSON serialization and deserialization in the C++ code. An example CMake project fetches and builds RapidJSON (and GoogleTest) from the repository, so there is no need to install it into the system.

## Installing
You don’t necessarily need anything other than the json2cpp.py script. You can download it separately if you want. Alternatively, you can clone this repository to get the example_schema.json file and see how it is used in C++ code.

```
git clone https://github.com/mattilaa
```
## Examples

### Simple usage
```
python3 json2cpp.py --schema schema/example_schema.json
```
This generates files with default names in the default location.
```
.
├── json2cpp_gen.cpp
├── json2cpp_gen.h
```
### Example of custom locations and generated file names
```
python3 json2cpp.py --schema schema/example_schema.json --ocpp src --oheader include --ofile myclasses
```
Result
```
.
├── include
│   └── myclasses.h
└── src
    └── myclasses.cpp
```
### Building example
```
mkdir build
cd build
cmake ..
make
```
Example targets
´´´
src/main
tests/test_example_classes
´´´
### More help
```
python3 json2cpp.py -h
```

### TODO: Add schema format documentation
