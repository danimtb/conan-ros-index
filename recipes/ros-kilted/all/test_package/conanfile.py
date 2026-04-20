import os

from conan import ConanFile
from conan.tools.build import can_run, cross_building
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import load, save

class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualBuildEnv"
    test_type = "explicit"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.28 <4]")

    def _inject_setup_script(self, script_name):
        ros = self.dependencies["ros2-kilted"]
        setup_script_path = os.path.join(ros.package_folder, "install", "setup.bat")
        load(self, setup_script_path)
        conanbuild_path = os.path.join(self.generators_folder, f"{script_name}.bat")
        conanbuild_content = load(self, conanbuild_path) + "\ncall " + setup_script_path
        save(self, conanbuild_path, conanbuild_content)

    def build(self):
        self._inject_setup_script("conanbuild")
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if not can_run(self) or cross_building(self):
            return
        self._inject_setup_script("conanrun")
        bin_path = os.path.join(self.cpp.build.bindirs[0], "test_package_node")
        self.run(bin_path, env="conanrun")
