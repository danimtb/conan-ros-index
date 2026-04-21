# conan-ros-index

Conan recipes for building and packaging [ROS 2](https://docs.ros.org/) from sources following the instructions for each platform:

- Windows: https://docs.ros.org/en/kilted/Installation/Alternatives/Windows-Development-Setup.html
- macOS: https://docs.ros.org/en/kilted/Installation/Alternatives/macOS-Development-Setup.html
- Linux: https://docs.ros.org/en/kilted/Installation/Alternatives/Ubuntu-Development-Setup.html

## Recipes

| Package     | Description                                      |
| ----------- | ------------------------------------------------ |
| `ros2-kilted` | ROS 2 **Kilted** all-in-one recipe |

## Dependencies (from this repository)

| Package     | Description                                      |
| ----------- | ------------------------------------------------ |
| `zenoh-c` | Eclipse Rust zenoh c library |
| `zenoh-cpp` | Eclipse C++ wrapper header library for zenoh c |
| `rust` | Rust/Cargo tool require to build the libraries |

## Recipes development

To develop the `ros-kilted` recipe, use the local development flow to iterate the different methods of the recipe

```
cd recipes/ros-kilted/all
conan source recipes/ros-kilted/all --version 0.1.0
conan build recipes/ros-kilted/all --version 0.1.0 --profile profiles/windows-msvc
conan export-pkg recipes/ros-kilted/all --version 0.1.0 --profile profiles/windows-msvc  # Executes test_package too
```

Finally, create the package:

```
conan create recipes/ros-kilted/all --version 0.1.0 --profile profiles/windows-msvc
```

## Usage

Add this repository as a [`local-recipes-index`](https://docs.conan.io/2/tutorial/conan_repositories/setup_local_recipes_index.html#local-recipes-index-repository) remote so `ros-kilted` (and other reipces not available in conan-center) resolve like any other recipe.

```bash
git clone https://github.com/danimtb/conan-ros-index.git
conan remote add conan-ros2-index ./conan-ros-index --type local-recipes-index
```

Then install or build from the index, for example:

```bash
conan install --requires=ros-kilted/0.1.0 --build=missing --profile profiles/windows-msvc
```

## License

Recipe metadata and supporting files in this repository are licensed under the MIT License — see [LICENSE](LICENSE). The upstream ROS 2 archives are subject to their own licenses (see the ROS 2 project).
