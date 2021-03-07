#define CATCH_CONFIG_MAIN
#include "../single_include/catch2/catch.hpp"

unsigned int
Factorial(unsigned int number)
{
    return number <= 1 ? number : Factorial(number - 1) * number;
}

TEST_CASE("factorials", "[math]")
{
    REQUIRE(Factorial(1) == 1);
    REQUIRE(Factorial(2) == 2);
    REQUIRE(Factorial(3) == 6);
    REQUIRE(Factorial(10) == 3628800);
}

TEST_CASE("addition", "[math]")
{
    REQUIRE(1 + 0 == 1);
    REQUIRE(1 + 1 == 2);
}

TEST_CASE("multiplication", "[math][!hide]")
{
    REQUIRE(1 * 0 == 1);  // fail
    REQUIRE(1 * 1 == 1);
}

TEST_CASE("common setup", "[vector][container]")
{
    std::vector<int> v(5);
    SECTION("Check 5")
    {
        REQUIRE(v.size() == 5);
        v.resize(10);
        REQUIRE(v.size() == 10);
    }
    SECTION("Check 5 Again")
    {
        REQUIRE(v.size() == 5);
        v.resize(10);
        REQUIRE(v.size() == 10);
    }
}

SCENARIO("resize vectors", "[vector][container]")
{
    GIVEN("A vector with some items")
    {
        std::vector<int> v(5);

        REQUIRE(v.size() == 5);
        REQUIRE(v.capacity() >= 5);

        WHEN("the size is increased")
        {
            v.resize(10);

            THEN("the size and capacity change")
            {
                REQUIRE(v.size() == 10);
                REQUIRE(v.capacity() >= 10);
            }
        }
        WHEN("the size is reduced")
        {
            v.resize(0);

            THEN("the size changes but not capacity")
            {
                REQUIRE(v.size() == 0);
                REQUIRE(v.capacity() >= 5);
            }
        }
        WHEN("more capacity is reserved")
        {
            v.reserve(10);

            THEN("the capacity changes but not the size")
            {
                REQUIRE(v.size() == 5);
                REQUIRE(v.capacity() >= 10);
            }
        }
        WHEN("less capacity is reserved")
        {
            v.reserve(0);

            THEN("neither size nor capacity are changed")
            {
                REQUIRE(v.size() == 5);
                REQUIRE(v.capacity() >= 5);
            }
        }
    }
}
