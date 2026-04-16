import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout, CMakeDeps
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv
from conan.tools.microsoft import VCVars, is_msvc


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    test_type = "explicit"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <4]")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()
        CMakeDeps(self).generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        ext = ".exe" if self.settings.os == "Windows" else ""
        if os.path.exists(exe := os.path.join(self.cpp.build.bindir, f"main{ext}")):
            self.run(exe, env="conanrun")
