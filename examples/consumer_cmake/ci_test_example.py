from test.examples_tools import run

run("conan install -s compiler.cppstd=17 --build=missing")
run("conan build -s compiler.cppstd=17")
