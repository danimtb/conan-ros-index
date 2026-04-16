cmake_minimum_required(VERSION 3.16)
project(test_package_zenoh_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(zenohc REQUIRED CONFIG)
find_package(zenohcxx REQUIRED CONFIG)

add_executable(main main.cpp)
target_link_libraries(main PRIVATE zenohcxx::zenohc)