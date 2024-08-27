import argparse
import json
import os
import sys
from enum import Enum

class JsonToCppConverter:
    def __init__(self, json_schema, header_file, implementation_file):
        self.json_schema = json_schema
        self.header_file = header_file
        self.implementation_file = implementation_file
        self.metadata, self.enums, self.classes = self.read_json_schema()
        self.namespace = self.metadata.get("namespace", "")
        self.all_classes = set(class_spec['name'] for class_spec in self.classes)
        self.all_enums = {enum_spec['name']: enum_spec for enum_spec in self.enums}

    def read_json_schema(self):
        with open(self.json_schema, "r") as f:
            schema = json.load(f)
        return schema.get("metadata", {}), schema.get("enums", []), schema.get("classes", [])

    def generate_enum_declaration(self, enum_spec):
        enum_name = enum_spec['name']
        enum_values = enum_spec['values']

        cpp_code = f"enum class {enum_name} {{\n"
        cpp_code += ",\n".join(f"    {value}" for value in enum_values)
        cpp_code += "\n};\n\n"

        return cpp_code

    def generate_enum_implementation(self, enum_spec):
        enum_name = enum_spec['name']
        enum_values = enum_spec['values']

        cpp_code = f"template<>\n"
        cpp_code += f"std::string to_string<{enum_name}>({enum_name} value) {{\n"
        cpp_code += "    switch (value) {\n"
        for value in enum_values:
            cpp_code += f'        case {enum_name}::{value}: return "{value}";\n'
        cpp_code += '        default: return "Unknown";\n'
        cpp_code += "    }\n"
        cpp_code += "}\n\n"

        cpp_code += f"template<>\n"
        cpp_code += f"{enum_name} from_string<{enum_name}>(const std::string& str) {{\n"
        for value in enum_values:
            cpp_code += f'    if (str == "{value}") return {enum_name}::{value};\n'
        cpp_code += f"    throw std::invalid_argument(\"Invalid {enum_name} value: \" + str);\n"
        cpp_code += "}\n\n"

        return cpp_code

    def generate_cpp_class_declaration(self, class_spec, parent_class="", indent_level=0):
        class_name = class_spec['name']
        attributes = class_spec['attributes']
        inner_structs = class_spec.get('inner_structs', [])
        object_type = class_spec.get('object_type', 'Class')

        full_class_name = f"{parent_class}::{class_name}" if parent_class else class_name
        indent = "    " * indent_level
        cpp_code = ""

        cpp_code += f"{indent}{object_type.lower()} {class_name} {{\n"

        if object_type == 'Class':
            cpp_code += f"{indent}public:\n"

        # Generate inner structs at the same indentation level as other members
        for inner_struct in inner_structs:
            cpp_code += self.generate_cpp_class_declaration(inner_struct, full_class_name, indent_level + 1)
            cpp_code += "\n"

        # Generate attributes
        for attr in attributes:
            attr_type = attr['type']
            if attr_type in self.all_classes:
                cpp_code += f"{indent}    std::shared_ptr<{attr_type}> {attr['name']};\n"
            else:
                cpp_code += f"{indent}    {attr_type} {attr['name']};\n"

        if object_type == 'Class':
            # Generate constructor declaration
            cpp_code += f"\n{indent}    {class_name}();\n"

            # Generate getter and setter declarations
            for attr in attributes:
                attr_name = attr['name']
                attr_type = attr['type']
                if attr_type in self.all_classes:
                    cpp_code += f"{indent}    const std::shared_ptr<{attr_type}>& get{attr_name.capitalize()}() const;\n"
                    cpp_code += f"{indent}    void set{attr_name.capitalize()}(const std::shared_ptr<{attr_type}>& value);\n"
                elif attr_type.startswith("std::vector<"):
                    cpp_code += f"{indent}    const {attr_type}& get{attr_name.capitalize()}() const;\n"
                    cpp_code += f"{indent}    void set{attr_name.capitalize()}(const {attr_type}& value);\n"
                else:
                    cpp_code += f"{indent}    {attr_type} get{attr_name.capitalize()}() const;\n"
                    cpp_code += f"{indent}    void set{attr_name.capitalize()}({attr_type} value);\n"

        # Generate method declarations for both Class and Struct
        cpp_code += f"{indent}    void fromJson(const rapidjson::Value& json);\n"
        cpp_code += f"{indent}    rapidjson::Value toJson(rapidjson::Document::AllocatorType& allocator) const;\n"
        cpp_code += f"{indent}    void validate() const;\n"

        cpp_code += f"{indent}}};\n"

        return cpp_code

    def generate_cpp_class_implementation(self, class_spec, parent_class=""):
        class_name = class_spec['name']
        attributes = class_spec['attributes']
        inner_structs = class_spec.get('inner_structs', [])
        constraints = class_spec.get('constraints', {})
        object_type = class_spec.get('object_type', 'Class')

        full_class_name = f"{parent_class}::{class_name}" if parent_class else class_name
        cpp_code = f"// {full_class_name} implementation\n\n"

        # Generate inner struct implementations
        for inner_struct in inner_structs:
            cpp_code += self.generate_cpp_class_implementation(inner_struct, full_class_name)
            cpp_code += "\n"

        if object_type == 'Class':
            # Generate constructor
            cpp_code += f"{full_class_name}::{class_name}() {{}}\n\n"

            # Generate getter and setter implementations
            for attr in attributes:
                attr_name = attr['name']
                attr_type = attr['type']

                # Check if the attribute type is an inner struct
                if attr_type in [struct['name'] for struct in inner_structs]:
                    attr_type = f"{full_class_name}::{attr_type}"

                # Handle shared_ptr types
                if attr_type in self.all_classes:
                    cpp_code += f"const std::shared_ptr<{attr_type}>& {full_class_name}::get{attr_name.capitalize()}() const {{ return {attr_name}; }}\n"
                    cpp_code += f"void {full_class_name}::set{attr_name.capitalize()}(const std::shared_ptr<{attr_type}>& value) {{ {attr_name} = value; }}\n\n"
                elif attr_type.startswith("std::vector<"):
                    cpp_code += f"const {attr_type}& {full_class_name}::get{attr_name.capitalize()}() const {{ return {attr_name}; }}\n"
                    cpp_code += f"void {full_class_name}::set{attr_name.capitalize()}(const {attr_type}& value) {{ {attr_name} = value; }}\n\n"
                else:
                    cpp_code += f"{attr_type} {full_class_name}::get{attr_name.capitalize()}() const {{ return {attr_name}; }}\n"
                    cpp_code += f"void {full_class_name}::set{attr_name.capitalize()}({attr_type} value) {{ {attr_name} = value; }}\n\n"

            # Generate fromJson method
            cpp_code += f"void {full_class_name}::fromJson(const rapidjson::Value& json) {{\n"
            for attr in attributes:
                attr_name = attr['name']
                attr_type = attr['type']
                if attr_type == "std::string":
                    cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsString()) set{attr_name.capitalize()}(json[\"{attr_name}\"].GetString());\n"
                elif attr_type == "int":
                    cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsInt()) set{attr_name.capitalize()}(json[\"{attr_name}\"].GetInt());\n"
                elif attr_type == "double":
                    cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsDouble()) set{attr_name.capitalize()}(json[\"{attr_name}\"].GetDouble());\n"
                elif attr_type in self.all_classes:
                    cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsObject()) {{\n"
                    cpp_code += f"        {attr_name} = std::make_shared<{attr_type}>();\n"
                    cpp_code += f"        {attr_name}->fromJson(json[\"{attr_name}\"]);\n"
                    cpp_code += f"    }}\n"
                elif attr_type in [struct['name'] for struct in inner_structs]:
                    cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsObject()) {attr_name}.fromJson(json[\"{attr_name}\"]);\n"
                elif attr_type in self.all_enums:
                    cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsString()) set{attr_name.capitalize()}(from_string<{attr_type}>(json[\"{attr_name}\"].GetString()));\n"
            cpp_code += "}\n\n"

            # Generate toJson method
            cpp_code += f"rapidjson::Value {full_class_name}::toJson(rapidjson::Document::AllocatorType& allocator) const {{\n"
            cpp_code += "    rapidjson::Value json(rapidjson::kObjectType);\n"
            for attr in attributes:
                attr_name = attr['name']
                attr_type = attr['type']
                if attr_type == "std::string":
                    cpp_code += f"    json.AddMember(\"{attr_name}\", rapidjson::Value(get{attr_name.capitalize()}().c_str(), allocator).Move(), allocator);\n"
                elif attr_type in ["int", "double"]:
                    cpp_code += f"    json.AddMember(\"{attr_name}\", get{attr_name.capitalize()}(), allocator);\n"
                elif attr_type in self.all_classes:
                    cpp_code += f"    if ({attr_name}) {{\n"
                    cpp_code += f"        json.AddMember(\"{attr_name}\", {attr_name}->toJson(allocator), allocator);\n"
                    cpp_code += f"    }}\n"
                elif attr_type in [struct['name'] for struct in inner_structs]:
                    cpp_code += f"    json.AddMember(\"{attr_name}\", {attr_name}.toJson(allocator), allocator);\n"
                elif attr_type in self.all_enums:
                    cpp_code += f"    json.AddMember(\"{attr_name}\", rapidjson::Value(to_string(get{attr_name.capitalize()}()).c_str(), allocator).Move(), allocator);\n"
            cpp_code += "    return json;\n"
            cpp_code += "}\n\n"

            # Generate validate method
            cpp_code += f"bool {full_class_name}::validate() const {{\n"
            for attr_name, constraint in constraints.items():
                attr_type = next(attr['type'] for attr in attributes if attr['name'] == attr_name)
                if 'min' in constraint:
                    cpp_code += f"    if (get{attr_name.capitalize()}() < {constraint['min']}) return false;\n"
                if 'max' in constraint:
                    cpp_code += f"    if (get{attr_name.capitalize()}() > {constraint['max']}) return false;\n"

            for attr in attributes:
                attr_name = attr['name']
                attr_type = attr['type']
                if attr_type in self.all_classes:
                    cpp_code += f"    if ({attr_name} && !{attr_name}->validate()) return false;\n"
                elif attr_type in [struct['name'] for struct in inner_structs]:
                    cpp_code += f"    if (!{attr_name}.validate()) return false;\n"

            cpp_code += "    return true;\n"
            cpp_code += "}\n\n"
        else:  # For Struct
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
                elif attr_type in self.all_classes:
                    cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsObject()) {{\n"
                    cpp_code += f"        {attr_name} = std::make_shared<{attr_type}>();\n"
                    cpp_code += f"        {attr_name}->fromJson(json[\"{attr_name}\"]);\n"
                    cpp_code += f"    }}\n"
                elif attr_type in [struct['name'] for struct in inner_structs]:
                    cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsObject()) {attr_name}.fromJson(json[\"{attr_name}\"]);\n"
                elif attr_type in self.all_enums:
                    cpp_code += f"    if (json.HasMember(\"{attr_name}\") && json[\"{attr_name}\"].IsString()) {attr_name} = from_string<{attr_type}>(json[\"{attr_name}\"].GetString());\n"
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
                elif attr_type in self.all_classes:
                    cpp_code += f"    if ({attr_name}) {{\n"
                    cpp_code += f"        json.AddMember(\"{attr_name}\", {attr_name}->toJson(allocator), allocator);\n"
                    cpp_code += f"    }}\n"
                elif attr_type in [struct['name'] for struct in inner_structs]:
                    cpp_code += f"    json.AddMember(\"{attr_name}\", {attr_name}.toJson(allocator), allocator);\n"
                elif attr_type in self.all_enums:
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
                if attr_type in self.all_classes:
                    cpp_code += f"    if ({attr_name} && !{attr_name}->validate()) return false;\n"
                elif attr_type in [struct['name'] for struct in inner_structs]:
                    cpp_code += f"    if (!{attr_name}.validate()) return false;\n"

            cpp_code += "    return true;\n"
            cpp_code += "}\n\n"

        return cpp_code

    def generate_cpp_files(self):
        # Generate header file
        with open(self.header_file, 'w') as f:
            f.write("#pragma once\n\n")
            f.write("#include <string>\n")
            f.write("#include <memory>\n")
            f.write("#include <vector>\n")
            f.write("#include <stdexcept>\n")
            f.write("#include <rapidjson/document.h>\n\n")

            f.write(f"namespace {self.namespace} {{\n\n")

            # Add template declarations for to_string and from_string
            f.write("template<typename EnumType>\n")
            f.write("std::string to_string(EnumType value);\n\n")
            f.write("template<typename EnumType>\n")
            f.write("EnumType from_string(const std::string& str);\n\n")

            # Generate enum declarations
            for enum_spec in self.enums:
                f.write(self.generate_enum_declaration(enum_spec))

            # Generate class declarations
            for class_spec in self.classes:
                f.write(self.generate_cpp_class_declaration(class_spec))
                f.write("\n")

            f.write(f"}} // namespace {self.namespace}\n")

        print(f"Header file created: {self.header_file}")

        # Generate implementation file
        with open(self.implementation_file, 'w') as f:
            f.write(f"#include \"{os.path.basename(self.header_file)}\"\n\n")
            f.write(f"namespace {self.namespace} {{\n\n")

            # Generate enum implementations
            for enum_spec in self.enums:
                f.write(self.generate_enum_implementation(enum_spec))

            # Generate class implementations
            for class_spec in self.classes:
                f.write(self.generate_cpp_class_implementation(class_spec))
                f.write("\n")

            f.write(f"}} // namespace {self.namespace}\n")

        print(f"C++ file created: {self.implementation_file}")


def main():
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

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.createdir:
        os.makedirs(args.ocpp, exist_ok=True)
        os.makedirs(args.oheader, exist_ok=True)
    else:
        if not os.path.isdir(args.ocpp) or not os.path.isdir(args.oheader):
            print("Output directories do not exist and were not generated.", file=sys.stderr)
            sys.exit(1)

    output_cpp = os.path.join(args.ocpp, args.ofile)
    output_header = os.path.join(args.oheader, args.ofile)

    converter = JsonToCppConverter(args.schema, f"{output_header}.h", f"{output_cpp}.cpp")
    converter.generate_cpp_files()
    print("Done.")


if __name__ == "__main__":
    main()
