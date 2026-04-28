import os

from conan import ConanFile
from conan.tools.cmake import CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import load, save
from conan.tools.microsoft import VCVars
from conan.tools.ros import ROSEnv


class PoseEstimationConan(ConanFile):
    package_type = "application"
    settings = "os", "compiler", "build_type", "arch"

    # OpenCV 4.5.5 + FFmpeg: CMakeDeps emits ffmpeg targets that link libwebp::libwebp
    # before that target exists (Conan Center; macOS/Linux source builds). FFmpeg WebP
    # in avcodec is optional for typical OpenCV use; see conan-center-index#28939.
    default_options = {"ffmpeg/*:with_libwebp": False}

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("ros-kilted/0.1.0")
        self.requires("tensorflow-lite/2.12.0")
        self.requires("opencv/4.5.5")

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

    def generate(self):
        CMakeToolchain(self).generate()
        CMakeDeps(self).generate()
        ROSEnv(self).generate()
        self._inject_setup_script("conanrosenv")
        VCVars(self).generate()
