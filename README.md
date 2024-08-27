# JSON to C++ class generator
## Description
A simple Python script that generates C++ classes from a JSON schema file. RapidJSON is used as a backend for JSON serialization and deserialization in the C++ code. An example CMake project fetches and builds RapidJSON (and GoogleTest) from the repository, so there is no need to install it into the system.

## Installing
You don’t necessarily need anything other than the json2cpp.py script. You can download it separately if you want. Alternatively, you can clone this repository to get the example_schema.json file and see how it is used in C++ code.

```
git clone https://github.com/mattilaa/json2cpp
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
```
src/main
tests/test_example_classes
```
### More help
```
python3 json2cpp.py -h
```
### Example generator code
```cpp
enum class EyeColor {
    Brown,
    Blue,
    Green,
    Hazel,
    Gray
};

class Person {
public:
    struct Body {
        struct PhysicalAttributes {
            EyeColor eyeColor;
            std::string hairColor;

            void fromJson(const rapidjson::Value& json);
            rapidjson::Value toJson(rapidjson::Document::AllocatorType& allocator) const;

            void validate() const;
        };

        double weight;
        double height;
        PhysicalAttributes physicalAttributes;

        void fromJson(const rapidjson::Value& json);
        rapidjson::Value toJson(rapidjson::Document::AllocatorType& allocator) const;

        void validate() const;
    };

    std::string name;
    int age;
    Body body;

    Person();
    std::string getName() const;
    void setName(std::string value);
    int getAge() const;
    void setAge(int value);
    Body getBody() const;
    void setBody(Body value);

    void fromJson(const rapidjson::Value& json);
    rapidjson::Value toJson(rapidjson::Document::AllocatorType& allocator) const;

    void validate() const;
};
```
### TODO: Add schema format documentation
