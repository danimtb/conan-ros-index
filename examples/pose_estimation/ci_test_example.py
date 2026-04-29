import platform

from test.examples_tools import run

run("conan install -s compiler.cppstd=17 --build=missing")
run("conan build -s compiler.cppstd=17 --build=missing")


run("python -m pip install -q --upgrade pip colcon-common-extensions")
run("conan install -s compiler.cppstd=17 --build=missing")

if platform.system() == "Windows":
  run("cmd.exe //C \"call build/Release/generators/conanrosenv.bat && cmake --preset conan-release && cmake --build --preset conan-release")
else:
  run("source build/Release/generators/conanrosenv.sh")
  run("cmake --preset conan-release")
  run("cmake --build --preset conan-release")
