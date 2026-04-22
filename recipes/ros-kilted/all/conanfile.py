# SPDX-License-Identifier: Apache-2.0

# ------------------------------------------------------------------------------
# Pixi inventory (ros2/ros2 kilted pixi.toml [dependencies]) → this recipe
# Columns: pixi name | bucket | where it lands in Conan-first layout
#   require = self.requires / host; tool = self.tool_requires; pip = PyEnv.install
#   pyenv = interpreter only (PyEnv py_version); skip = system / not modeled here
# ------------------------------------------------------------------------------
# | pixi                         | bucket   | notes                                      |
# |------------------------------|----------|--------------------------------------------|
# | 7zip                         | tool     | tool_requires 7zip/* (ConanCenter; pixi)  |
# | colcon-cmake … test-result   | pip      | explicit colcon-* pins/ranges like pixi   |
# | argcomplete                  | pip      |                                            |
# | asio                         | require  | asio/*                                    |
# | assimp                       | require  | assimp/* (parity pin when added)          |
# | benchmark                    | require  | benchmark/*                               |
# | bullet                       | require  | bullet3/* (conda name bullet)            |
# | catkin_pkg                   | pip      |                                            |
# | cmake                        | tool     | cmake/*                                   |
# | console_bridge               | require  | console_bridge/*                        |
# | coverage                     | pip      |                                            |
# | cppcheck                     | tool     | cppcheck/*                                |
# | cryptography                 | pip      |                                            |
# | cunit                        | require  | cunit/*                                   |
# | curl                         | require  | covered by libcurl/* (same stack)         |
# | distlib                      | pip      |                                            |
# | docutils                     | pip      |                                            |
# | eigen                        | require  | eigen/*                                   |
# | empy                         | pip      |                                            |
# | flake8 (+ blind-except …)    | pip      | flake8 ecosystem                          |
# | git                          | skip     | system prerequisite (see docstring)       |
# | gmock                        | require  | gtest/* supplies GMock                    |
# | graphviz                     | require  | graphviz/* if binaries needed for docs  |
# | gtest                        | require  | gtest/*                                   |
# | importlib-metadata           | pip      |                                            |
# | iniconfig                    | pip      | pytest stack                              |
# | lark                         | pip      |                                            |
# | libcurl                      | require  | libcurl/*                                 |
# | lxml                         | pip      |                                            |
# | lz4-c                        | require  | lz4/*                                     |
# | mccabe                       | pip      | flake8-related                            |
# | mypy, mypy_extensions        | pip      |                                            |
# | nlohmann_json                | require  | nlohmann_json/*                           |
# | numpy                        | pip      |                                            |
# | opencv                       | require  | opencv/*                                  |
# | openssl                      | require  | openssl/*                                 |
# | orocos-kdl                   | skip     | C++ from ROS workspace; no Conan require   |
# | packaging                    | pip      |                                            |
# | pathspec                     | pip      |                                            |
# | pip                          | skip     | UV / PyEnv manages installer              |
# | pluggy                       | pip      | pytest stack                              |
# | psutil                       | pip      |                                            |
# | pybind11                     | require  | pybind11/*                                |
# | pycodestyle                  | pip      |                                            |
# | pydocstyle                   | pip      |                                            |
# | pydot                        | pip      |                                            |
# | pyflakes                     | pip      |                                            |
# | pygraphviz                   | pip      | pip (+ graphviz host/tool if enabled)     |
# | pyparsing                    | pip      |                                            |
# | pyqt                         | pip      | PyQt wheels / Qt runtime (heavy)          |
# | pyqt5-sip                    | pip      |                                            |
# | pytest (+ cov/mock/…)        | pip      | pytest ecosystem                          |
# | python                       | pyenv    | PyEnv(self, py_version=…) → 3.12.3        |
# | python-dateutil              | pip      |                                            |
# | python-fastjsonschema        | pip      |                                            |
# | python-orocos-kdl            | pip      | pip KDL bindings (pixi also has C orocos) |
# | pyyaml                       | pip      | PyYAML (distinct from C yaml below)       |
# | qt                           | skip     | optional huge stack; pyqt often enough    |
# | rust                         | tool     | rust/* tool_requires (see profile: newer  |
# |                              |          | than pixi 1.75.0 for zenoh)               |
# | setuptools                   | pip      |                                            |
# | six                          | pip      |                                            |
# | snowballstemmer              | pip      |                                            |
# | spdlog                       | require  | spdlog/*                                  |
# | sqlite                       | require  | sqlite3/*                                 |
# | tinyxml2                     | require  | tinyxml2/*                                |
# | typing_extensions            | pip      |                                            |
# | uncrustify                   | tool     | uncrustify/*                              |
# | vcstool                      | pip      |                                            |
# | yaml-cpp                     | require  | yaml-cpp/*                                |
# | yamllint                     | pip      |                                            |
# | yaml (libyaml C)             | require  | libyaml/* or transitive; not PyYAML       |
# | zipp                         | pip      |                                            |
# | zstd                         | require  | zstd/*                                    |
# ------------------------------------------------------------------------------
# Recipe-only (not in pixi.toml): fmt/*, zenoh-c/*, zenoh-cpp/* → require (zenoh
#   system build; fmt transitive/tooling as needed by other requires).
# ------------------------------------------------------------------------------
# Workspace-only: [target.win-64.activation.env] QT_QPA_PLATFORM_PLUGIN_PATH → Qt
#   from pixi env; with Conan-first builds map to system/Qt or optional qt pkg.
# ------------------------------------------------------------------------------

import os
import sys

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration, ConanException
from conan.tools.cmake import CMakeDeps, CMakeToolchain
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import (
    apply_conandata_patches,
    copy,
    download,
    mkdir,
    replace_in_file,
    rmdir,
    save,
)
from conan.tools.microsoft import VCVars
from conan.tools.system import PyEnv


# Pip mirror of ros2/ros2 kilted pixi.toml [dependencies]: colcon-* uses same bounds as
# pixi; everything else uses pixi == pins (PyPI names). Omitted: pip (UV), git (system), rust
# (Conan tool_requires; newer than pixi for zenoh — see profile).
PIP_BUILD_TOOLS = (
    # --- colcon (pixi version ranges) ---
    "colcon-cmake>=0.2.28,<0.3",
    "colcon-core>=0.17.1,<0.18",
    "colcon-defaults>=0.2.8,<0.3",
    "colcon-library-path>=0.2.1,<0.3",
    "colcon-metadata>=0.2.5,<0.3",
    "colcon-mixin>=0.2.3,<0.3",
    "colcon-output>=0.2.13,<0.3",
    "colcon-package-information>=0.4.0,<0.5",
    "colcon-package-selection>=0.2.10,<0.3",
    "colcon-parallel-executor>=0.2.4,<0.3",
    "colcon-pkg-config>=0.1.0,<0.2",
    "colcon-powershell>=0.4.0,<0.5",
    "colcon-python-setup-py>=0.2.7,<0.3",
    "colcon-recursive-crawl>=0.2.3,<0.3",
    "colcon-ros>=0.5.0,<0.6",
    "colcon-ros-domain-id-coordinator>=0.2.1,<0.3",
    "colcon-test-result>=0.3.8,<0.4",
    # --- pixi Python pins (conda name → PyPI where different) ---
    "argcomplete==3.1.4",
    "catkin_pkg==1.0.0",
    "coverage==7.4.4",
    "cryptography==41.0.7",
    "distlib==0.3.8",
    "docutils==0.20.1",
    "empy==3.3.4",
    "flake8==7.0.0",
    "flake8-blind-except==0.2.1",
    "flake8-builtins==2.1.0",
    "flake8-class-newline==1.6.0",
    "flake8-comprehensions==3.14.0",
    "flake8-deprecated==2.2.1",
    "flake8-docstrings==1.6.0",
    "flake8-import-order==0.18.2",
    "flake8-quotes==3.4.0",
    "importlib-metadata==4.13.0",
    "iniconfig==1.1.1",
    "lark==1.1.9",
    "lxml==5.2.1",
    "mccabe==0.7.0",
    "mypy==1.9.0",
    "mypy-extensions==1.0.0",
    "numpy==1.26.4",
    "packaging==24.0",
    "pathspec==0.12.1",
    "pluggy==1.4.0",
    "psutil==5.9.8",
    "pycodestyle==2.11.1",
    "pydocstyle==6.3.0",
    "pydot==1.4.2",
    "pyflakes==3.2.0",
    #"pygraphviz==1.11",
    "pyparsing==3.1.1",
    "PyQt5==5.15.9",
    "PyQt5-sip==12.12.2",
    "pytest==7.4.4",
    "pytest-cov==4.1.0",
    "pytest-mock==3.12.0",
    "pytest-repeat==0.9.3",
    "pytest-rerunfailures==12.0",
    "pytest-runner==6.0.0",
    "pytest-timeout==2.2.0",
    "python-dateutil==2.8.2",
    "fastjsonschema==2.19.0",  # pixi: python-fastjsonschema
    #"python-orocos-kdl==1.5.1",
    "PyYAML==6.0.1",
    "setuptools==68.1.2",
    "six==1.16.0",
    "snowballstemmer==2.2.0",
    "typing_extensions==4.10.0",
    "vcstool==0.3.0",
    "yamllint==1.33.0",
    "zipp==1.0.0",
    "wheel",
)


class Ros2KiltedConan(ConanFile):
    name = "ros-kilted"
    version = "0.1.0"
    provides = "ros"  # To avoid name conflicts with other ros packages: ros-rolling, ros-humble, etc.
    exports_sources = "conandata.yml", "patches/*"
    # package_type = "library"  # TODO: which is the best type?
    license = "Apache-2.0"
    url = "https://docs.ros.org/en/kilted/"
    description = "ROS 2 Kilted merged install from source, dependencies via Conan + PyEnv."
    settings = "os", "compiler", "build_type", "arch"

    def layout(self):
        # Single-tree colcon workspace: src/, build/, install/, log/ under ros2_ws/
        ws = "ros2_ws"
        self.folders.source = ws
        self.folders.build = ws
        self.folders.generators = os.path.join(ws, "conan")

    def requirements(self):
        # Host pins vs kilted pixi.toml: exact where CC matches; else nearest (documented here).
        # console_bridge 1.0.2 (pixi 1.0.1 — 1.0.1 not on ConanCenter). cunit/2.1-3 is CC’s id for 2.1.3.
        # graphviz/9.0.0: no Windows MSVC binary on ConanCenter from `conan list`; keep pygraphviz-only on pip.
        self.requires("openssl/3.3.2")
        self.requires("zlib/1.3.1")
        self.requires("fmt/10.2.1")
        # Temporarily off: no matching ConanCenter prebuilt for this Windows/MSVC profile (re-enable with
        # --build=missing or after binaries exist). Missing-binary set included:
        # assimp/5.3.1, cppcheck/2.15.0, dav1d/1.5.3, ffmpeg/4.4.4, freetype/2.13.2, libcurl/8.5.0,
        # libtiff/4.6.0, libvpx/1.15.2, libwebp/1.3.2, libx265/3.6, opencv/4.9.0, openh264/2.6.0,
        # protobuf/3.21.12, spdlog/1.12.0, xz_utils/5.8.3 (opencv pulls most of the media stack).
        self.requires("spdlog/1.12.0")  # pixi env requires 1.12.0 while spdlog_vendor requires 1.5.0
        self.requires("eigen/3.4.0")
        self.requires("yaml-cpp/0.8.0")
        # self.requires("libcurl/8.5.0")
        self.requires("sqlite3/3.45.2")
        self.requires("lz4/1.9.4")
        self.requires("zstd/1.5.5")
        self.requires("tinyxml2/10.0.0")
        self.requires("nlohmann_json/3.11.3")
        self.requires("asio/1.28.1")
        self.requires("gtest/1.17.0")
        self.requires("benchmark/1.8.3", options={"shared": True})
        self.requires("console_bridge/1.0.2")
        # self.requires("assimp/5.3.1")
        # self.requires("opencv/4.9.0")
        self.requires("bullet3/3.25")
        self.requires("cunit/2.1-3")
        self.requires("libyaml/0.2.5")
        self.requires("zenoh-c/1.8.0")
        self.requires("zenoh-cpp/1.8.0")
        self.requires("pybind11/2.11.1")

    def build_requirements(self):
        self.tool_requires("cmake/3.28.5")
        # self.tool_requires("cppcheck/2.15.0")  # see requirements() comment: missing binary for profile
        self.tool_requires("uncrustify/0.78.1")
        # 7zip: pixi build tooling; ConanCenter ships 7z.exe on PATH for Windows x86_64.
        self.tool_requires("7zip/23.01")

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
        # Deep Conan build dirs + long rosidl Python extension names exceed MSVC's
        # practical path limit (~260); object paths then fail as C1083 with '' filename.
        if self.settings.os == "Windows":
            tc.cache_variables["CMAKE_OBJECT_PATH_MAX"] = 220
            tc.variables["CMAKE_OBJECT_PATH_MAX"] = 220
        tc.variables["Python3_ROOT_DIR"] = py_root
        tc.variables["Python3_EXECUTABLE"] = py_exe
        tc.variables["Python_ROOT_DIR"] = py_root
        tc.variables["Python_EXECUTABLE"] = py_exe
        tc.variables["CMAKE_POLICY_DEFAULT_CMP0091"] = "NEW"
        tc.variables["USE_SYSTEM_ZENOH"] = True
        tc.generate()
        #self._patch_conan_toolchain_cmp0091_early()
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
        pyenv = PyEnv(self, folder=self.source_folder)
        pyenv.install(["setuptools==68.1.2", "vcstool==0.3.0"])
        repos = os.path.join(self.source_folder, "ros2.repos")
        download(self, **self.conan_data["sources"][str(self.version)], filename=repos)
        src_dir = os.path.join(self.source_folder, "src")
        if os.path.isdir(src_dir):
            rmdir(self, src_dir)
        mkdir(self, src_dir)
        vcs_path = os.path.join(pyenv.env_dir, "Scripts", "vcs")
        self.run(f'{vcs_path} import --input "{repos}" src', cwd=self.source_folder, env="conanbuild")
        apply_conandata_patches(self)

    def build(self):
        cmd = (
            f'colcon build --merge-install '
            f'--cmake-args="-DCMAKE_POLICY_DEFAULT_CMP0091=NEW -DUSE_SYSTEM_ZENOH=ON" '
            '--catkin-skip-building-tests '
            '--packages-up-to rclcpp '  # rclcpp, demo_nodes_cpp, type_description_interfaces
            '--event-handlers console_cohesion+'
        )
        self.run(cmd, env="conanbuild")

    def package(self):
        inst = os.path.join(self.build_folder, "install")
        if not os.path.isdir(inst):
            raise ConanException(f"No merged install found at {inst}")
        copy(self, "*", src=inst, dst=os.path.join(self.package_folder, "install"))

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "none")

        install = os.path.join(self.package_folder, "install")
        bindir = os.path.join(install, "bin")
        if os.path.isdir(bindir):
            self.runenv_info.prepend_path("PATH", bindir)
        self.runenv_info.append_path("AMENT_PREFIX_PATH", install)
        self.buildenv_info.append_path("AMENT_PREFIX_PATH", install)

        # Colcon prefix (merged install under Conan package_folder). Hooks use this when
        # consumers apply runenv before sourcing local_setup from a different cwd.
        self.runenv_info.define("COLCON_CURRENT_PREFIX", install)
        self.buildenv_info.define("COLCON_CURRENT_PREFIX", install)

        # colcon local_setup.* and ament prefix hooks embed a build-time Python path.
        # Pre-set these so consumers (VirtualRunEnv / conanrun) override before calling
        # local_setup.bat/ps1. Profile: ros2-kilted/*:user.ros2:python_executable=/path/to/python.exe
        py_exe = self.conf.get("user.ros2:python_executable", default=sys.executable)
        if py_exe:
            self.runenv_info.define("COLCON_PYTHON_EXECUTABLE", py_exe)
            self.runenv_info.define("AMENT_PYTHON_EXECUTABLE", py_exe)
            self.buildenv_info.define("COLCON_PYTHON_EXECUTABLE", py_exe)
            self.buildenv_info.define("AMENT_PYTHON_EXECUTABLE", py_exe)

        # Consumers often use local_setup.bat; document path.
        self.conf_info.define_path("user.ros2:install_prefix", install)
        setup_script_path = os.path.join(install, "setup")
        setup_script_path_sh = setup_script_path + ".sh"
        setup_script_path_bat = setup_script_path + ".bat"
        setup_script_path_ps1 = setup_script_path + ".ps1"
        self.output.info(f"[bash] Setup the ROS Kilted environment: 'source {setup_script_path_sh}'")
        self.output.info(f"[batch] Setup the ROS Kilted environment: 'call {setup_script_path_bat}'")
        self.output.info(f"[powershell] Setup the ROS Kilted environment: '. {setup_script_path_ps1}'")
        self.conf_info.define_path("user.ros2.setup_sh", setup_script_path_sh)
        self.conf_info.define_path("user.ros2.setup_bat", setup_script_path_bat)
        self.conf_info.define_path("user.ros2.setup_ps1", setup_script_path_ps1)
