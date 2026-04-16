cmake_minimum_required(VERSION 3.16)
project(test_package_zenohc LANGUAGES C)

find_package(zenohc REQUIRED CONFIG)

add_executable(main main.c)
target_link_libraries(main PRIVATE zenohc::lib)
