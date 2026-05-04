import platform

from test.examples_tools import run

run("conan install -s compiler.cppstd=17 --build=missing")

if platform.system() == "Windows":
    run(
        r"call .\build\generators\conanbuild.bat && "
        r"cmake --preset conan-release && cmake --build --preset conan-release"
    )
else:
    run(
        ". ./build/Release/generators/conanbuild.sh && "
        "cmake --preset conan-release && cmake --build --preset conan-release"
    )
