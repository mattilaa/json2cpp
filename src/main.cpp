#include "example_classes.h"
#include <iostream>
#include <rapidjson/stringbuffer.h>
#include <rapidjson/writer.h>

using namespace example;

int main() {
    Person person;
    person.name = "John Doe";
    person.age = 30;
    person.body.weight = 70.5;
    person.body.height = 1.75;
    person.body.physicalAttributes.eyeColor = EyeColor::Blue;
    person.body.physicalAttributes.hairColor = "Brown";

    rapidjson::Document doc;
    auto& allocator = doc.GetAllocator();
    rapidjson::Value personJson = person.toJson(allocator);

    rapidjson::StringBuffer buffer;
    rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
    personJson.Accept(writer);

    std::cout << "Generated JSON: " << buffer.GetString() << std::endl;

    return 0;
}
