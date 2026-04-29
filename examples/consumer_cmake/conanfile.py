import os

from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.files import load, save

class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeDeps", "CMakeToolchain"
    test_type = "explicit"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("ros-kilted/0.1.0")

    def _inject_setup_script(self, script_name):
        ros = self.dependencies["ros-kilted"]
        is_windows = self.settings.os == "Windows"
        if is_windows:
            setup_script_path = os.path.join(ros.package_folder, "install", "setup.bat")
            conanbuild_path = os.path.join(self.generators_folder, f"{script_name}.bat")
            invocation = f"\ncall {setup_script_path}"
        else:
            setup_script_path = os.path.join(ros.package_folder, "install", "setup.sh")
            conanbuild_path = os.path.join(self.generators_folder, f"{script_name}.sh")
            # `.` (dot) is POSIX-portable; `source` is bash/zsh-specific
            invocation = f"\n. {setup_script_path}"
        if not os.path.isfile(setup_script_path):
            raise FileNotFoundError(
                f"ROS setup script not found at {setup_script_path}. "
                f"Expected it inside the ros-kilted package folder.")
        conanbuild_content = load(self, conanbuild_path) + invocation
        save(self, conanbuild_path, conanbuild_content)

    def build(self):
        self._inject_setup_script("conanbuild")
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
