Environment tools needed
------------------------

- Compiler
- CMake
- colcon

Build steps
-----------

```
cd examples/consumer_colcon_cpp
conan install
call build-release/conan/conanrosenv.bat
colcon build
call install/setup.bat

install\consumer_node\lib\consumer_node\consumer_node
```

TODO
----

The execution of the node should be done with:

```
# after colcon build
call install/setup.bash
ros2 run consumer_node consumer_node
```

But the ros2 CLI is still nota available in ros-kilted recipe