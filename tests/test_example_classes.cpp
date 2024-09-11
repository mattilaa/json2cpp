#include "example_classes.h"
#include <gtest/gtest.h>
#include <rapidjson/document.h>
#include <rapidjson/stringbuffer.h>
#include <rapidjson/writer.h>

using namespace example;

TEST(GeneratedClassesTest, PersonSerialization) {
    Person person;
    person.name = "John Doe";
    person.age = 30;
    person.body.weight = 70.5;
    person.body.height = 1.75;
    person.body.physicalAttributes.eyeColor = EyeColor::Blue;
    person.body.physicalAttributes.hairColor = "Brown";

    EXPECT_NO_THROW(person.validate());

    rapidjson::Document doc;
    auto& allocator = doc.GetAllocator();
    rapidjson::Value personJson = person.toJson(allocator);

    rapidjson::StringBuffer buffer;
    rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
    personJson.Accept(writer);

    std::string jsonStr = buffer.GetString();

    EXPECT_TRUE(jsonStr.find("\"name\":\"John Doe\"") != std::string::npos);
    EXPECT_TRUE(jsonStr.find("\"age\":30") != std::string::npos);
    EXPECT_TRUE(jsonStr.find("\"weight\":70.5") != std::string::npos);
    EXPECT_TRUE(jsonStr.find("\"height\":1.75") != std::string::npos);
    EXPECT_TRUE(jsonStr.find("\"eyeColor\":\"Blue\"") != std::string::npos);
    EXPECT_TRUE(jsonStr.find("\"hairColor\":\"Brown\"") != std::string::npos);
}

TEST(GeneratedClassesTest, PersonDeserialization) {
    const char* json = R"(
        {
            "name": "Jane Doe",
            "age": 25,
            "body": {
                "weight": 60.0,
                "height": 1.65,
                "physicalAttributes": {
                    "eyeColor": "Green",
                    "hairColor": "Blonde"
                }
            }
        }
    )";

    rapidjson::Document doc;
    doc.Parse(json);

    Person person;
    EXPECT_NO_THROW(person.fromJson(doc));

    EXPECT_NO_THROW(person.validate());
    EXPECT_EQ(person.name, "Jane Doe");
    EXPECT_EQ(person.age, 25);
    EXPECT_DOUBLE_EQ(person.body.weight, 60.0);
    EXPECT_DOUBLE_EQ(person.body.height, 1.65);
    EXPECT_EQ(person.body.physicalAttributes.eyeColor, EyeColor::Green);
    EXPECT_EQ(person.body.physicalAttributes.hairColor, "Blonde");
}

TEST(GeneratedClassesTest, PersonValidation) {
    Person person;
    person.name = "John Doe";
    person.age = 30;
    person.body.weight = 70.5;
    person.body.height = 1.75;
    person.body.physicalAttributes.eyeColor = EyeColor::Blue;
    person.body.physicalAttributes.hairColor = "Brown";

    EXPECT_NO_THROW(person.validate());

    // Test age constraint
    person.age = -1;
    EXPECT_THROW(person.validate(), std::out_of_range);
    person.age = 151;
    EXPECT_THROW(person.validate(), std::out_of_range);
    person.age = 30;
    EXPECT_NO_THROW(person.validate());

    // Test weight constraint
    person.body.weight = -1;
    EXPECT_THROW(person.validate(), std::out_of_range);
    person.body.weight = 501;
    EXPECT_THROW(person.validate(), std::out_of_range);
    person.body.weight = 70.5;
    EXPECT_NO_THROW(person.validate());

    // Test height constraint
    person.body.height = -0.1;
    EXPECT_THROW(person.validate(), std::out_of_range);
    person.body.height = 3.1;
    EXPECT_THROW(person.validate(), std::out_of_range);
    person.body.height = 1.75;
    EXPECT_NO_THROW(person.validate());
}

TEST(GeneratedClassesTest, FamilySerialization) {
    Family family;
    family.familyName = "Doe";

    family.father = std::make_shared<Person>();
    family.father->name = "John Doe";
    family.father->age = 40;
    family.father->body.weight = 80.0;
    family.father->body.height = 1.80;
    family.father->body.physicalAttributes.eyeColor = EyeColor::Brown;
    family.father->body.physicalAttributes.hairColor = "Black";

    family.mother = std::make_shared<Person>();
    family.mother->name = "Jane Doe";
    family.mother->age = 38;
    family.mother->body.weight = 65.0;
    family.mother->body.height = 1.70;
    family.mother->body.physicalAttributes.eyeColor = EyeColor::Blue;
    family.mother->body.physicalAttributes.hairColor = "Blonde";

    Person child;
    child.name = "Jimmy Doe";
    child.age = 10;
    child.body.weight = 40.0;
    child.body.height = 1.40;
    child.body.physicalAttributes.eyeColor = EyeColor::Green;
    child.body.physicalAttributes.hairColor = "Brown";
    family.children.push_back(child);

    EXPECT_NO_THROW(family.validate());

    rapidjson::Document doc;
    auto& allocator = doc.GetAllocator();
    rapidjson::Value familyJson = family.toJson(allocator);

    rapidjson::StringBuffer buffer;
    rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
    familyJson.Accept(writer);

    std::string jsonStr = buffer.GetString();

    EXPECT_TRUE(jsonStr.find("\"familyName\":\"Doe\"") != std::string::npos);
    EXPECT_TRUE(jsonStr.find("\"name\":\"John Doe\"") != std::string::npos);
    EXPECT_TRUE(jsonStr.find("\"name\":\"Jane Doe\"") != std::string::npos);
    EXPECT_TRUE(jsonStr.find("\"name\":\"Jimmy Doe\"") != std::string::npos);
}

TEST(GeneratedClassesTest, FamilyDeserialization) {
    const char* json = R"(
        {
            "familyName": "Smith",
            "father": {
                "name": "John Smith",
                "age": 45,
                "body": {
                    "weight": 80.0,
                    "height": 1.80,
                    "physicalAttributes": {
                        "eyeColor": "Brown",
                        "hairColor": "Black"
                    }
                }
            },
            "mother": {
                "name": "Mary Smith",
                "age": 42,
                "body": {
                    "weight": 65.0,
                    "height": 1.70,
                    "physicalAttributes": {
                        "eyeColor": "Blue",
                        "hairColor": "Blonde"
                    }
                }
            },
            "children": [
                {
                    "name": "Jimmy Smith",
                    "age": 15,
                    "body": {
                        "weight": 60.0,
                        "height": 1.65,
                        "physicalAttributes": {
                            "eyeColor": "Green",
                            "hairColor": "Brown"
                        }
                    }
                }
            ]
        }
    )";

    rapidjson::Document doc;
    doc.Parse(json);

    Family family;
    EXPECT_NO_THROW(family.fromJson(doc));

    EXPECT_NO_THROW(family.validate());
    EXPECT_EQ(family.familyName, "Smith");
    EXPECT_EQ(family.father->name, "John Smith");
    EXPECT_EQ(family.father->age, 45);
    EXPECT_EQ(family.mother->name, "Mary Smith");
    EXPECT_EQ(family.mother->age, 42);
    EXPECT_EQ(family.children.size(), 1);
    EXPECT_EQ(family.children[0].name, "Jimmy Smith");
    EXPECT_EQ(family.children[0].age, 15);
}

TEST(GeneratedClassesTest, EnumSerialization) {
    Person person;
    person.name = "John Doe";
    person.age = 30;
    person.body.weight = 70.5;
    person.body.height = 1.75;
    person.body.physicalAttributes.eyeColor = EyeColor::Blue;
    person.body.physicalAttributes.hairColor = "Brown";

    EXPECT_NO_THROW(person.validate());

    rapidjson::Document doc;
    auto& allocator = doc.GetAllocator();
    rapidjson::Value personJson = person.toJson(allocator);

    rapidjson::StringBuffer buffer;
    rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
    personJson.Accept(writer);

    std::string jsonStr = buffer.GetString();

    EXPECT_TRUE(jsonStr.find("\"eyeColor\":\"Blue\"") != std::string::npos);
}

TEST(GeneratedClassesTest, EnumDeserialization) {
    const char* json = R"(
        {
            "name": "Jane Doe",
            "age": 25,
            "body": {
                "weight": 60.0,
                "height": 1.65,
                "physicalAttributes": {
                    "eyeColor": "Green",
                    "hairColor": "Blonde"
                }
            }
        }
    )";

    rapidjson::Document doc;
    doc.Parse(json);

    Person person;
    EXPECT_NO_THROW(person.fromJson(doc));

    EXPECT_NO_THROW(person.validate());
    EXPECT_EQ(person.name, "Jane Doe");
    EXPECT_EQ(person.age, 25);
    EXPECT_DOUBLE_EQ(person.body.weight, 60.0);
    EXPECT_DOUBLE_EQ(person.body.height, 1.65);
    EXPECT_EQ(person.body.physicalAttributes.eyeColor, EyeColor::Green);
    EXPECT_EQ(person.body.physicalAttributes.hairColor, "Blonde");
}

TEST(GeneratedClassesTest, EnumInvalidValue) {
    const char* json = R"(
        {
            "name": "Invalid",
            "age": 30,
            "body": {
                "weight": 70.0,
                "height": 1.75,
                "physicalAttributes": {
                    "eyeColor": "Purple",
                    "hairColor": "Black"
                }
            }
        }
    )";

    rapidjson::Document doc;
    doc.Parse(json);

    Person person;
    EXPECT_THROW(person.fromJson(doc), std::invalid_argument);
}

int main(int argc, char** argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
