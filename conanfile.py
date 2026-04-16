# SPDX-License-Identifier: Apache-2.0
"""
ROS 2 Kilted (Windows) from source using Conan — replaces pixi entirely.

Prerequisites (see profiles/windows-msvc-kilted):
  - Windows 10+, long paths enabled (MAX_PATH)
  - Visual Studio / Build Tools with C++ (MSVC)
  - Git on PATH (for vcstool)
  - UV on PATH if using PyEnv(py_version=...) (Conan 2 PyEnv)
"""

import os

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import copy, download, mkdir, replace_in_file, rmdir, save
from conan.tools.microsoft import VCVars
from conan.tools.system import PyEnv


ROS2_REPOS_URL = "https://raw.githubusercontent.com/ros2/ros2/kilted/ros2.repos"

PIP_BUILD_TOOLS = (
    "colcon-common-extensions",
    "vcstool",
    "empy>=3.3,<4",
    "catkin_pkg",
    "setuptools>=68",
    "wheel",
    "numpy>=1.26,<3",
    "PyYAML>=6,<7",
    "lxml>=5,<6",
)


class Ros2KiltedConan(ConanFile):
    name = "ros2-kilted"
    version = "0.1.0"
    no_copy_source = True
    package_type = "application"
    license = "Apache-2.0"
    url = "https://docs.ros.org/en/kilted/Installation/Alternatives/Windows-Development-Setup.html"
    description = "ROS 2 Kilted merged install from source (Windows), dependencies via Conan + PyEnv."
    settings = "os", "compiler", "build_type", "arch"

    def configure(self):
        if self.settings.os != "Windows":
            raise ConanInvalidConfiguration("This recipe targets Windows only.")

    def layout(self):
        # Single-tree colcon workspace: src/, build/, install/, log/ under ros2_ws/
        ws = "ros2_ws"
        self.folders.source = ws
        self.folders.build = ws
        self.folders.generators = os.path.join(ws, "conan")

    def requirements(self):
        # Native deps commonly expected on the Windows dev overlay (ConanCenter).
        # Packages not on ConanCenter (e.g. orocos-kdl) are built from the ROS workspace.
        self.requires("openssl/[>=3.2 <4]")
        self.requires("zlib/[>=1.2.13 <2]")
        self.requires("spdlog/[>=1.12 <1.16]")
        self.requires("eigen/3.4.0")
        self.requires("yaml-cpp/0.8.0")
        self.requires("libcurl/[>=8.4 <9]")
        self.requires("sqlite3/[>=3.45.0 <3.50]")
        self.requires("lz4/1.9.4")
        self.requires("zstd/[>=1.5 <1.6]")
        self.requires("tinyxml2/[>=9.0.0 <11]")
        self.requires("nlohmann_json/3.11.3")
        self.requires("asio/[>=1.28 <1.30]")
        self.requires("gtest/[>=1.14 <1.16]")
        self.requires("benchmark/[>=1.8 <1.9]")
        self.requires("console_bridge/1.0.2")
        self.requires("fmt/[>=10.2 <12]")
        self.requires("zenoh-c/1.8.0")
        self.requires("zenoh-cpp/1.8.0")
        self.requires("pybind11/2.11.1")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.28 <3.30]")

    def generate(self):
        pyenv = PyEnv(self)
        pyenv.install(list(PIP_BUILD_TOOLS))
        pyenv.generate()
        # Colcon must not descend into site-packages under this venv.
        save(self, os.path.join(pyenv.env_dir, "COLCON_IGNORE"), "")

        py_exe = pyenv.env_exe.replace("\\", "/")
        py_root = pyenv.env_dir.replace("\\", "/")

        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_TESTING"] = False
        tc.cache_variables["Python3_ROOT_DIR"] = pyenv.env_dir
        tc.cache_variables["Python3_EXECUTABLE"] = pyenv.env_exe
        tc.cache_variables["Python_ROOT_DIR"] = pyenv.env_dir
        tc.cache_variables["Python_EXECUTABLE"] = pyenv.env_exe
        tc.cache_variables["CMAKE_POLICY_DEFAULT_CMP0091"] = "NEW"
        tc.cache_variables["USE_SYSTEM_ZENOH"] = True
        tc.variables["Python3_ROOT_DIR"] = py_root
        tc.variables["Python3_EXECUTABLE"] = py_exe
        tc.variables["Python_ROOT_DIR"] = py_root
        tc.variables["Python_EXECUTABLE"] = py_exe
        tc.variables["CMAKE_POLICY_DEFAULT_CMP0091"] = "NEW"
        tc.variables["USE_SYSTEM_ZENOH"] = True
        tc.generate()
        self._patch_conan_toolchain_cmp0091_early()
        cmakedeps = CMakeDeps(self)
        cmakedeps.set_property("tinyxml2", "cmake_file_name", "TinyXML2")
        cmakedeps.set_property("tinyxml2", "cmake_extra_variables", {"TINYXML2_LIBRARY": "tinyxml2::tinyxml2"})
        cmakedeps.set_property("asio", "cmake_file_name", "Asio")
        cmakedeps.generate()
        VCVars(self).generate()
        vbe = VirtualBuildEnv(self)
        # CMake honors CMAKE_TOOLCHAIN_FILE from the environment when not passed on the command
        # line; colcon-spawned cmake inherits conanbuild and still loads Conan’s toolchain + Python.
        toolchain_file = os.path.abspath(
            os.path.join(self.generators_folder, CMakeToolchain.filename)
        ).replace("\\", "/")
        vbe.environment().define("CMAKE_TOOLCHAIN_FILE", toolchain_file)
        vbe.environment().define("CMAKE_POLICY_DEFAULT_CMP0091", "NEW")
        #vbe.environment().prepend_path("PATH", os.path.join(pyenv.env_dir, "Scripts"))
        vbe.generate()

    def _patch_conan_toolchain_cmp0091_early(self):
        """Conan's vs_runtime block runs cmake_policy(GET CMP0091) before variables set the default.
        Colcon does not preset CMP0091; set the policy at the top of the toolchain so the check passes.
        """
        path = os.path.join(self.generators_folder, CMakeToolchain.filename)
        block = (
            "include_guard()\n"
            "message(STATUS \"Using Conan toolchain: ${CMAKE_CURRENT_LIST_FILE}\")\n"
        )
        injection = (
            "include_guard()\n"
            "if(POLICY CMP0091)\n"
            "  cmake_policy(SET CMP0091 NEW)\n"
            "endif()\n"
            "message(STATUS \"Using Conan toolchain: ${CMAKE_CURRENT_LIST_FILE}\")\n"
        )
        replace_in_file(self, path, block, injection, strict=True)

    def source(self):
        download(self, ROS2_REPOS_URL, os.path.join(self.source_folder, "ros2.repos"), verify=True)
        repos = os.path.join(self.source_folder, "ros2.repos")
        src_dir = os.path.join(self.source_folder, "src")
        if os.path.isdir(src_dir):
            rmdir(self, src_dir)
        mkdir(self, src_dir)
        self.run(f'vcs import --input "{repos}" src', cwd=self.source_folder, env="conanbuild")

    def build(self):
        cmd = (
            f'colcon build --merge-install '
            f'--cmake-args "-DCMAKE_POLICY_DEFAULT_CMP0091=NEW" "-DUSE_SYSTEM_ZENOH=ON" '
            '--catkin-skip-building-tests '
            '--packages-up-to fastdds '  # demo_nodes_cpp
            '--event-handlers console_cohesion+'
        )
        self.run(cmd, env="conanbuild")

    def package(self):
        inst = os.path.join(self.build_folder, "install")
        if not os.path.isdir(inst):
            raise ConanException(f"No merged install found at {inst}")
        copy(self, "*", src=inst, dst=os.path.join(self.package_folder, "install"))

    def package_id(self):
        # skip_vcs does not change the graph of built artifacts when sources match.
        self.info.options.rm_safe("skip_vcs")

    def package_info(self):
        install = os.path.join(self.package_folder, "install")
        bindir = os.path.join(install, "bin")
        if os.path.isdir(bindir):
            self.runenv_info.prepend_path("PATH", bindir)
        self.runenv_info.append_path("AMENT_PREFIX_PATH", install)
        self.buildenv_info.append_path("AMENT_PREFIX_PATH", install)

        # Consumers often use local_setup.bat; document path.
        self.conf_info.define_path("user.ros2:install_prefix", install)
