cmake_minimum_required(VERSION 3.16)
project(JsonClassConverter)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(PYTHON_SCRIPT "${CMAKE_SOURCE_DIR}/json2cpp.py")
set(SCHEMA_FILE "${CMAKE_SOURCE_DIR}/schema/example_schema.json")
set(GENERATED_DIR_CPP "${CMAKE_SOURCE_DIR}/generated")
set(GENERATED_DIR_HPP "${CMAKE_SOURCE_DIR}/include")
set(GENERATED_FILE_PREFIX "example_classes")

set(GENERATED_FILES
    ${GENERATED_DIR_HPP}/example_classes.h
    ${GENERATED_DIR_CPP}/example_classes.cpp
)

add_custom_command(
    OUTPUT ${GENERATED_FILES}
    COMMAND ${CMAKE_COMMAND} -E env python3 ${PYTHON_SCRIPT}
        --schema ${SCHEMA_FILE}
        --ocpp ${GENERATED_DIR_CPP}
        --oheader ${GENERATED_DIR_HPP}
        --ofile ${GENERATED_FILE_PREFIX}
    DEPENDS ${PYTHON_SCRIPT} ${SCHEMA_FILE}
    COMMENT "Running Python script to generate C++ files"
    VERBATIM
)

include(FetchContent)

# Add RapidJSON
set(RAPIDJSON_BUILD_TESTS OFF CACHE BOOL "Disable RapidJSON tests" FORCE)
set(RAPIDJSON_BUILD_EXAMPLES OFF CACHE BOOL "Disable RapidJSON examples" FORCE)
set(RAPIDJSON_BUILD_DOC OFF CACHE BOOL "Disable Doxygen" FORCE)
FetchContent_Declare(
    rapidjson
    GIT_REPOSITORY https://github.com/Tencent/rapidjson.git
    GIT_TAG v1.1.0
)
FetchContent_MakeAvailable(rapidjson)

# Add Google Test
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG release-1.11.0
)
FetchContent_MakeAvailable(googletest)

add_library(example_classes STATIC
    ${GENERATED_DIR_CPP}/example_classes.cpp
)
target_include_directories(example_classes PUBLIC
    ${CMAKE_SOURCE_DIR}
    ${rapidjson_SOURCE_DIR}/include
    ${GENERATED_DIR_HPP}
)

add_subdirectory(src)
add_subdirectory(tests)
