# SPDX-License-Identifier: Apache-2.0
import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import get


class ZenohCppConan(ConanFile):
    name = "zenoh-cpp"
    description = (
        "Header-only C++17 bindings for Eclipse Zenoh (zenoh-c backend in this recipe)."
    )
    license = ("Apache-2.0", "EPL-2.0")
    url = "https://github.com/eclipse-zenoh/zenoh-cpp"
    homepage = "https://zenoh.io"
    topics = ("zenoh", "networking", "messaging", "pubsub", "ros2", "header-only")

    package_type = "header-library"
    settings = "os", "compiler", "build_type", "arch"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        # zenoh-cpp releases track zenoh-c API; keep versions aligned.
        self.requires(f"zenoh-c/{self.version}")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][str(self.version)], strip_root=True)

    def generate(self):
        CMakeDeps(self).generate()
        tc = CMakeToolchain(self)
        tc.cache_variables["ZENOHCXX_ZENOHC"] = True
        tc.cache_variables["ZENOHCXX_ZENOHPICO"] = False
        tc.cache_variables["ZENOHCXX_ENABLE_TESTS"] = False
        tc.cache_variables["ZENOHCXX_ENABLE_EXAMPLES"] = False
        tc.generate()
        VirtualBuildEnv(self).generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "zenohcxx")
        self.cpp_info.set_property("cmake_target_name", "zenohcxx::zenohc")
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.builddirs = [os.path.join("lib", "cmake", "zenohcxx")]
        self.cpp_info.requires = ["zenoh-c::lib"]
        # Same as upstream `zenohcxx_zenohc` INTERFACE: headers in zenohc.hxx gate on this macro.
        self.cpp_info.defines.append("ZENOHCXX_ZENOHC")

    def package_id(self):
        self.info.clear()
