import platform

from test.examples_tools import run

run("python -m pip install -q --upgrade pip colcon-common-extensions catkin_pkg")

run("conan install -s compiler.cppstd=17 --build=missing")


if platform.system() == "Windows":
    run("call build/Release/generators/conanrosenv.bat && colcon build --event-handlers console_cohesion+")
else:
    run(". ./build/Release/generators/conanrosenv.sh && colcon build --event-handlers console_cohesion+")
