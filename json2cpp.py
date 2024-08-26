import argparse
import json
import os
import sys

def read_json_schema(file_path):
    with open(file_path, "r") as f:
        schema = json.load(f)
    return schema.get("metadata", {}), schema.get("classes", [])

def generate_enum_declaration(enum_spec, namespace):
    enum_name = enum_spec['name']
    enum_values = enum_spec['values']

    cpp_code = f"namespace {namespace} {{\n\n"
    cpp_code += f"enum class {enum_name} {{\n"
    cpp_code += ",\n".join(f"    {value}" for value in enum_values)
    cpp_code += "\n};\n\n"

    cpp_code += f"std::string to_string({enum_name} value);\n"
    cpp_code += f"{enum_name} from_string(const std::string& str);\n\n"

    cpp_code += "} // namespace " + namespace + "\n\n"

    return cpp_code

def generate_enum_implementation(enum_spec, namespace):
    enum_name = enum_spec['name']
    enum_values = enum_spec['values']

    cpp_code = f"std::string to_string({enum_name} value) {{\n"
    cpp_code += "    switch (value) {\n"
    for value in enum_values:
        cpp_code += f'        case {enum_name}::{value}: return "{value}";\n'
    cpp_code += '        default: return "Unknown";\n'
    cpp_code += "    }\n"
    cpp_code += "}\n\n"

    cpp_code += f"{enum_name} from_string(const std::string& str) {{\n"
    for value in enum_values:
        cpp_code += f'    if (str == "{value}") return {enum_name}::{value};\n'
    cpp_code += f"    throw std::invalid_argument(\"Invalid {enum_name} value: \" + str);\n"
    cpp_code += "}\n\n"


    return cpp_code

def generate_cpp_class_declaration(class_spec, all_classes, enums, namespace, parent_class=""):
    class_name = class_spec['name']
    attributes = class_spec['attributes']
    inner_structs = class_spec.get('inner_structs', [])

    full_class_name = f"{parent_class}::{class_name}" if parent_class else class_name
    cpp_code = ""

    if not parent_class:
        cpp_code += f"namespace {namespace} {{\n\n"

    cpp_code += f"class {class_name} {{\npublic:\n"

    # Generate inner structs
    for inner_struct in inner_structs:
        cpp_code += generate_cpp_class_declaration(inner_struct, all_classes, enums, namespace, full_class_name)
        cpp_code += "\n"

    # Generate attributes
    for attr in attributes:
        attr_type = attr['type']
        if attr_type in all_classes:
            cpp_code += f"    std::shared_ptr<{attr_type}> {attr['name']};\n"
        else:
            cpp_code += f"    {attr_type} {attr['name']};\n"

    # Generate constructor declaration
    cpp_code += f"\n    {class_name}();\n"

    # Generate method declarations
    cpp_code += "    void fromJson(const rapidjson::Value& json);\n"
    cpp_code += "    rapidjson::Value toJson(rapidjson::Document::AllocatorType& allocator) const;\n"
    cpp_code += "    bool validate() const;\n"

    cpp_code += "};\n"

    if not parent_class:
        cpp_code += "\n} // namespace " + namespace + "\n"
    return cpp_code

def generate_cpp_class_implementation(class_spec, all_classes, enums, namespace, parent_class=""):
    class_name = class_spec['name']
    attributes = class_spec['attributes']
    inner_structs = class_spec.get('inner_structs', [])
    constraints = class_spec.get('constraints', {})

    full_class_name = f"{parent_class}::{class_name}" if parent_class else class_name
    cpp_code = f"// {full_class_name} implementation\n\n"

    # Generate inner struct implementations
    for inner_struct in inner_structs:
        cpp_code += generate_cpp_class_implementation(inner_struct, all_classes, enums, namespace, full_class_name)
        cpp_code += "\n"

    # Generate constructor
    cpp_code += f"{full_class_name}::{class_name}() {{}}\n\n"

    # Generate fromJson method
    cpp_code += f"void {full_class_name}::fromJson(const rapidjson::Value& json) {{\n"
    for attr in attributes:
        attr_name = attr['name']
        attr_type = attr['type']
        if attr_type == "std::string":
            cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsString()) {attr_name} = json[\"{attr_name}\"].GetString();\n"
        elif attr_type == "int":
            cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsInt()) {attr_name} = json[\"{attr_name}\"].GetInt();\n"
        elif attr_type == "double":
            cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsDouble()) {attr_name} = json[\"{attr_name}\"].GetDouble();\n"
        elif attr_type in all_classes:
            cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsObject()) {{\n"
            cpp_code += f"        {attr_name} = std::make_shared<{attr_type}>();\n"
            cpp_code += f"        {attr_name}->fromJson(json[\"{attr_name}\"]);\n"
            cpp_code += f"    }}\n"
        elif attr_type in [struct['name'] for struct in inner_structs]:
            cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsObject()) {attr_name}.fromJson(json[\"{attr_name}\"]);\n"
        elif attr_type in enums:
            cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsString()) {attr_name} = from_string(json[\"{attr_name}\"].GetString());\n"
    cpp_code += "}\n\n"

    # Generate toJson method
    cpp_code += f"rapidjson::Value {full_class_name}::toJson(rapidjson::Document::AllocatorType& allocator) const {{\n"
    cpp_code += "    rapidjson::Value json(rapidjson::kObjectType);\n"
    for attr in attributes:
        attr_name = attr['name']
        attr_type = attr['type']
        if attr_type == "std::string":
            cpp_code += f"    json.AddMember(\"{attr_name}\", rapidjson::Value({attr_name}.c_str(), allocator).Move(), allocator);\n"
        elif attr_type in ["int", "double"]:
            cpp_code += f"    json.AddMember(\"{attr_name}\", {attr_name}, allocator);\n"
        elif attr_type in all_classes:
            cpp_code += f"    if ({attr_name}) {{\n"
            cpp_code += f"        json.AddMember(\"{attr_name}\", {attr_name}->toJson(allocator), allocator);\n"
            cpp_code += f"    }}\n"
        elif attr_type in [struct['name'] for struct in inner_structs]:
            cpp_code += f"    json.AddMember(\"{attr_name}\", {attr_name}.toJson(allocator), allocator);\n"
        elif attr_type in enums:
            cpp_code += f"    json.AddMember(\"{attr_name}\", rapidjson::Value(to_string({attr_name}).c_str(), allocator).Move(), allocator);\n"
    cpp_code += "    return json;\n"
    cpp_code += "}\n\n"

    # Generate validate method
    cpp_code += f"bool {full_class_name}::validate() const {{\n"
    for attr_name, constraint in constraints.items():
        attr_type = next(attr['type'] for attr in attributes if attr['name'] == attr_name)
        if 'min' in constraint:
            cpp_code += f"    if ({attr_name} < {constraint['min']}) return false;\n"
        if 'max' in constraint:
            cpp_code += f"    if ({attr_name} > {constraint['max']}) return false;\n"

    for attr in attributes:
        attr_name = attr['name']
        attr_type = attr['type']
        if attr_type in all_classes:
            cpp_code += f"    if ({attr_name} && !{attr_name}->validate()) return false;\n"
        elif attr_type in [struct['name'] for struct in inner_structs]:
            cpp_code += f"    if (!{attr_name}.validate()) return false;\n"

    cpp_code += "    return true;\n"
    cpp_code += "}\n\n"

    return cpp_code

def generate_cpp_files(json_schema, header_file, implementation_file):
    metadata, classes = read_json_schema(json_schema)
    namespace = metadata.get("namespace", "")
    all_classes = set(class_spec['name'] for class_spec in classes if class_spec.get('type') != 'enum')
    enums = set(enum_spec['name'] for enum_spec in classes if enum_spec.get('type') == 'enum')

    # Generate header file
    with open(header_file, 'w') as f:
        f.write("#pragma once\n\n")
        f.write("#include <string>\n")
        f.write("#include <memory>\n")
        f.write("#include <vector>\n")
        f.write("#include <stdexcept>\n")
        f.write("#include <rapidjson/document.h>\n\n")

        # Generate enum declarations
        for enum_spec in classes:
            if enum_spec.get('type') == 'enum':
                f.write(generate_enum_declaration(enum_spec, namespace))

        # Generate class declarations
        for class_spec in classes:
            if class_spec.get('type') != 'enum':
                f.write(generate_cpp_class_declaration(class_spec, all_classes, enums, namespace))
                f.write("\n")

    print(f"Header file created: {header_file}")

    # Generate implementation file
    with open(implementation_file, 'w') as f:
        f.write(f"#include \"{os.path.basename(header_file)}\"\n\n")
        f.write(f"namespace {namespace} {{\n\n")

        # Generate enum implementations
        for enum_spec in classes:
            if enum_spec.get('type') == 'enum':
                f.write(generate_enum_implementation(enum_spec, ""))
                f.write("\n")

        # Generate class implementations
        for class_spec in classes:
            if class_spec.get('type') != 'enum':
                f.write(generate_cpp_class_implementation(class_spec, all_classes, enums, ""))
                f.write("\n")

        f.write(f"}} // namespace {namespace}\n")

    print(f"C++ file created: {implementation_file}")


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(
        description='JSON to C++ struct generator',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--schema",
        type=str,
        required=True,
        help="Schema input file name for C++ struct generation. Example: schema.json",
    )
    parser.add_argument(
        "--oheader",
        type=str,
        default=".",
        help="Output path for generated C++ .h file. Example: include",
    )
    parser.add_argument(
        "--ocpp",
        type=str,
        default=".",
        help="Output path for generated C++ .cpp file. Example: generated",
    )
    parser.add_argument(
        "--ofile",
        type=str,
        default="json2cpp_gen",
        help="Output file name for generated C++ files",
    )
    parser.add_argument(
        "--create-dir",
        dest="createdir",
        action="store_true",
        default=True,
        help="Force creating output directories",
    )

    # Error checks
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        exit(1)

    args = parser.parse_args()

    if args.createdir is True:
        os.makedirs(args.ocpp, exist_ok=True)
        os.makedirs(args.oheader, exist_ok=True)
    else:
        if not os.path.isdir(args.ocpp) or not os.path.isdir(args.oheader):
            print(sys.stderr, "Output directories not exist and not generated.")
            exit(1)

    output_cpp = os.path.join(args.ocpp, args.ofile)
    output_header = os.path.join(args.oheader, args.ofile)

    generate_cpp_files(f"{args.schema}", f"{output_header}.h", f"{output_cpp}.cpp")
    print("Done.")
