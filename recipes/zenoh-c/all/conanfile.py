# SPDX-License-Identifier: Apache-2.0
import os
import shutil
import subprocess

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.microsoft import is_msvc
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import copy, get, replace_in_file


class ZenohcConan(ConanFile):
    name = "zenoh-c"
    description = "C API for Eclipse Zenoh (Rust-backed), built via upstream CMake."
    license = ("Apache-2.0", "EPL-2.0")
    url = "https://github.com/eclipse-zenoh/zenoh-c"
    homepage = "https://zenoh.io"
    topics = ("zenoh", "networking", "messaging", "pubsub", "ros2")

    package_type = "library"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "unstable_api": [True, False],
        "shared_memory": [True, False],
        # Windows MSVC: repackage upstream standalone zip instead of CMake+cargo (see conandata prebuilt_windows_msvc).
        "upstream_binary": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "unstable_api": False,
        "shared_memory": False,
        "upstream_binary": False,
    }

    def _use_upstream_binary(self):
        return (
            bool(self.options.get_safe("upstream_binary"))
            and str(self.settings.os) == "Windows"
            and str(self.settings.compiler) == "msvc"
        )

    def configure(self):
        if self.options.get_safe("upstream_binary") and (
            str(self.settings.os) != "Windows" or str(self.settings.compiler) != "msvc"
        ):
            raise ConanInvalidConfiguration(
                "zenoh-c:upstream_binary=True is only valid for Windows with compiler=msvc."
            )
        if self.options.shared:
            self.options.rm_safe("fPIC")
        elif self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.16 <4]")
        if not self._use_upstream_binary():
            # Must match rust-toolchain.toml for this tag (1.8.0 → 1.93.0).
            self.tool_requires("rust/1.93.0")

    def validate_build(self):
        if self._use_upstream_binary():
            return
        try:
            self.dependencies.get("rust", build=True)
            return
        except KeyError:
            pass
        if shutil.which("cargo") is None:
            raise ConanInvalidConfiguration(
                "zenoh-c requires Rust/Cargo: add a `rust/*` `tool_requires` matching this tag's "
                "rust-toolchain.toml (e.g. zenoh-c 1.8.0 uses Rust 1.93.0), or install Rust so `cargo` is on PATH."
            )

    def source(self):
        # `self.options` is not available in `source()`; always fetch sources (unused when upstream_binary=True).
        get(self, **self.conan_data["sources"][str(self.version)], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.cache_variables["ZENOHC_BUILD_WITH_UNSTABLE_API"] = self.options.unstable_api
        tc.cache_variables["ZENOHC_BUILD_WITH_SHARED_MEMORY"] = self.options.shared_memory
        if not self.options.shared and self.settings.os != "Windows":
            tc.cache_variables["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.get_safe(
                "fPIC", True
            )
        if self._use_upstream_binary():
            tc.generate()
            return

        rust = self.dependencies.build["rust"]
        rust_root = os.path.join(rust.package_folder, "rust")
        # Windows: upstream `add_custom_command` passes `${cargo_flags}` as a CMake list (`;`-separated).
        # A batch file runs cargo with a single argv string (subprocess.list2cmdline).
        if str(self.settings.os) == "Windows":
            gen_dir = os.path.join(self.build_folder, "generators")
            os.makedirs(gen_dir, exist_ok=True)
            bat_path = os.path.join(gen_dir, "zenoh_cargo.bat")
            bt = str(self.settings.build_type)
            cfg_dir = "debug" if bt == "Debug" else "release"
            manifest = os.path.normpath(os.path.join(self.build_folder, cfg_dir, "Cargo.toml"))
            opaque = os.path.normpath(os.path.join(self.build_folder, "opaque-types"))
            rustc_long = os.path.normpath(os.path.join(rust_root, "rustc", "bin", "rustc.exe"))
            cargo_long = os.path.normpath(os.path.join(rust_root, "cargo", "bin", "cargo.exe"))
            feats = []
            if self.options.shared_memory:
                feats.append("shared-memory")
            if self.options.unstable_api:
                feats.append("unstable")
            cmd = [cargo_long, "build"]
            if bt != "Debug":
                cmd.append("--release")
            cmd.append(f"--manifest-path={manifest}")
            if feats:
                cmd.append("--features=" + ",".join(feats))
            cargo_inv = subprocess.list2cmdline(cmd)
            bat_body = "\r\n".join(
                [
                    "@echo off",
                    "setlocal",
                    f'set "OPAQUE_TYPES_BUILD_DIR={opaque}"',
                    f'set "RUSTC={rustc_long}"',
                    f'set "CARGO={cargo_long}"',
                    cargo_inv,
                    "if errorlevel 1 exit /b %ERRORLEVEL%",
                    "",
                ]
            )
            with open(bat_path, "w", encoding="utf-8", newline="\r\n") as f:
                f.write(bat_body)
            tc.cache_variables["ZENOHC_CONAN_CARGO_WRAPPER"] = bat_path.replace("\\", "/")
        tc.generate()

        vbe = VirtualBuildEnv(self)
        env = vbe.environment()
        env.define("CARGO_HOME", os.path.join(self.build_folder, ".cargo_home"))
        env.prepend_path("PATH", os.path.join(rust_root, "cargo", "bin"))
        env.prepend_path("PATH", os.path.join(rust_root, "rustc", "bin"))
        if str(self.settings.os) == "Windows":
            rustc_abs = os.path.normpath(os.path.join(rust_root, "rustc", "bin", "rustc.exe")).strip()
            cargo_abs = os.path.normpath(os.path.join(rust_root, "cargo", "bin", "cargo.exe")).strip()
            env.define("RUSTC", rustc_abs)
            env.define("CARGO", cargo_abs)
        vbe.generate()

        if str(self.settings.os) == "Windows":
            patch_old = (
                "COMMAND ${CMAKE_COMMAND} -E env OPAQUE_TYPES_BUILD_DIR=${CMAKE_BINARY_DIR}/opaque-types "
                "cargo ${ZENOHC_CARGO_CHANNEL} build ${cargo_flags}"
            )
            patch_new = 'COMMAND cmd /C "${ZENOHC_CONAN_CARGO_WRAPPER}"'
            replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"), patch_old, patch_new)

    def build(self):
        if self._use_upstream_binary():
            upstream_dir = os.path.join(self.build_folder, "upstream")
            os.makedirs(upstream_dir, exist_ok=True)
            meta = self.conan_data["prebuilt_windows_msvc"][str(self.version)]
            get(self, url=meta["url"], sha256=meta["sha256"], destination=upstream_dir)
            return
        cmake = CMake(self)
        cmake.configure()
        cmake._build(env="conanbuild")  # noqa: SLF001 — propagate VirtualBuildEnv to Ninja/cmake --build

    def package(self):
        if self._use_upstream_binary():
            copy(self, "*", os.path.join(self.build_folder, "upstream"), self.package_folder)
            return
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        # CMakeDeps: expose `find_package(zenohc)` + target `zenohc::lib` (matches upstream names).
        # Do not add upstream `lib/cmake/zenohc` to `builddirs` or CONFIG mode may load that config
        # instead of Conan-generated files (which lacked `libs` before we set them here).
        self.cpp_info.set_property("cmake_file_name", "zenohc")

        lib = self.cpp_info.components["lib"]
        lib.set_property("cmake_target_name", "zenohc::lib")
        lib.includedirs = ["include"]
        lib.bindirs = ["bin"]
        lib.libdirs = ["lib"]

        if self.options.shared:
            if self.settings.os == "Windows" and is_msvc(self):
                lib.libs = ["zenohc.dll"]
            else:
                lib.libs = ["zenohc"]
            lib.defines.append("ZENOHC_DYN_LIB")
        else:
            lib.libs = ["zenohc"]
            if self.settings.os == "Windows":
                lib.system_libs.extend(
                    [
                        "ws2_32",
                        "crypt32",
                        "secur32",
                        "bcrypt",
                        "ncrypt",
                        "userenv",
                        "ntdll",
                        "iphlpapi",
                        "runtimeobject",
                    ]
                )

    def package_id(self):
        self.info.options.rm_safe("fPIC")
