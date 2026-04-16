# SPDX-License-Identifier: Apache-2.0
import os
import shutil

from conan import ConanFile
from conan.errors import ConanException, ConanInvalidConfiguration
from conan.tools.files import copy, get, mkdir, rmdir
from conan.tools.layout import basic_layout


class RustConan(ConanFile):
    name = "rust"
    description = (
        "Pre-built Rust toolchain from static.rust-lang.org (rustc, cargo, std, "
        "and bundled components from the official standalone archive)."
    )
    license = ("Apache-2.0", "MIT")
    url = "https://www.rust-lang.org/"
    homepage = "https://forge.rust-lang.org/infra/other-installation-methods.html#standalone"
    topics = ("rust", "cargo", "rustc", "toolchain", "build-tools")

    package_type = "application"
    settings = "os", "arch"
    short_paths = True

    def layout(self):
        basic_layout(self, src_folder="src")

    def _archive_key(self):
        if self.settings.os == "Windows" and str(self.settings.arch) in ("x86_64",):
            return "Windows_x86_64"
        return None

    def validate(self):
        key = self._archive_key()
        if key is None:
            raise ConanInvalidConfiguration(
                f"rust/{self.version}: no bundled standalone archive for "
                f"{self.settings.os}/{self.settings.arch}. Extend `conandata.yml` with the "
                "matching static.rust-lang.org dist URL and sha256."
            )
        if str(self.version) not in self.conan_data.get("sources", {}):
            raise ConanInvalidConfiguration(f"rust/{self.version} is not listed in conandata.yml")

    def source(self):
        # Conan 2 forbids `self.settings` in source(); the archive is OS/arch-specific, so fetch in build().
        pass

    def build(self):
        key = self._archive_key()
        data = self.conan_data["sources"][str(self.version)][key]
        dist_dir = os.path.join(self.build_folder, "_dist")
        rmdir(self, dist_dir)
        mkdir(self, dist_dir)
        get(
            self,
            url=data["url"],
            sha256=data["sha256"],
            strip_root=True,
            destination=dist_dir,
        )

    def package(self):
        # Standalone layout: rustc/bin, cargo/bin, rust-std-*/lib, ...
        dst = os.path.join(self.package_folder, "rust")
        copy(self, "*", src=os.path.join(self.build_folder, "_dist"), dst=dst)
        # Official tarball keeps host std under rust-std-*/lib/rustlib; rustc expects it under rustc/lib/rustlib.
        self._merge_rust_std_into_rustc(dst)
        if str(self.settings.os) == "Windows":
            self._unblock_zone_identifier(dst)

    def _unblock_zone_identifier(self, rust_root):
        """Strip MOTW Zone.Identifier ADS so build scripts can spawn rustc (Windows SmartScreen)."""
        for rel in (
            os.path.join("rustc", "bin", "rustc.exe"),
            os.path.join("cargo", "bin", "cargo.exe"),
        ):
            path = os.path.join(rust_root, rel)
            if not os.path.isfile(path):
                continue
            try:
                os.remove(path + ":Zone.Identifier")
            except OSError:
                pass

    def _merge_rust_std_into_rustc(self, rust_root):
        rust_std_lib = None
        for name in os.listdir(rust_root):
            if name.startswith("rust-std-") and os.path.isdir(os.path.join(rust_root, name)):
                candidate = os.path.join(rust_root, name, "lib", "rustlib")
                if os.path.isdir(candidate):
                    rust_std_lib = candidate
                    break
        if not rust_std_lib:
            raise ConanException(
                "Rust standalone bundle is missing rust-std-*/lib/rustlib (cannot merge std for rustc)."
            )
        dst_rustlib = os.path.join(rust_root, "rustc", "lib", "rustlib")
        os.makedirs(dst_rustlib, exist_ok=True)
        for item in os.listdir(rust_std_lib):
            src = os.path.join(rust_std_lib, item)
            dest = os.path.join(dst_rustlib, item)
            if os.path.isdir(src):
                shutil.copytree(src, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dest)

    def package_info(self):
        rust = os.path.join(self.package_folder, "rust")
        cargo_bin = os.path.join(rust, "cargo", "bin")
        rustc_bin = os.path.join(rust, "rustc", "bin")
        # cargo invokes rustc; both dirs must be visible (cargo.exe is only under cargo/bin).
        self.buildenv_info.prepend_path("PATH", cargo_bin)
        self.buildenv_info.prepend_path("PATH", rustc_bin)
        self.runenv_info.prepend_path("PATH", cargo_bin)
        self.runenv_info.prepend_path("PATH", rustc_bin)
