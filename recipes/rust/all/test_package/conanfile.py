from conan import ConanFile
from conan.tools.env import VirtualBuildEnv


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    test_type = "explicit"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def generate(self):
        VirtualBuildEnv(self).generate()

    def build(self):
        pass

    def test(self):
        self.run("cargo --version", env="conanbuild")
        self.run("rustc --version", env="conanbuild")
