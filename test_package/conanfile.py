import os

from conan import ConanFile
from conan.tools.build import can_run, cross_building
from conan.tools.system import PyEnv


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.28 <4]")

    def generate(self):
        pyenv = PyEnv(self, py_version="3.12.3")
        pyenv.install(
            [
                "colcon-common-extensions",
                "setuptools>=68",
                "wheel",
            ]
        )
        pyenv.generate(scope="build")

    def test(self):
        if not can_run(self) or cross_building(self):
            return
        if self.settings.os != "Windows":
            self.output.warning("test_package demos are only automated on Windows cmd.")
            return

        ros = self.dependencies["ros2-kilted"]
        install = os.path.join(ros.package_folder, "install")
        setup = os.path.join(install, "local_setup.bat")
        if not os.path.isfile(setup):
            raise AssertionError(f"Expected ROS install at {setup}")

        demo = os.path.join(self.source_folder, "demo_smoke.py")
        self.run(f'call "{setup}" && python "{demo}"', env="conanbuild")

        ws = os.path.join(self.source_folder, "minimal_ws")
        self.run(
            f'call "{setup}" && cd /d "{ws}" && colcon build --merge-install',
            env="conanbuild",
        )
