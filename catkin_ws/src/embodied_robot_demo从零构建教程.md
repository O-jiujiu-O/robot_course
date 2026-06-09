# 从空 Catkin 工作空间逐步构建 `embodied_robot_demo`

> 目标读者：第一次接触 ROS、Catkin、URDF、Gazebo 的学习者  
> 目标系统：Ubuntu 20.04、ROS Noetic、Gazebo Classic 11  
> 最终成果：从空的 `catkin_ws/src/` 开始，逐步建立当前项目中的 `embodied_robot_demo` ROS 包  
> 分工说明：A 负责包骨架、机器人模型、Gazebo 场景、控制器和基础启动文件；B 负责控制 API、视觉、语音和任务编排代码

---

## 0. 必须先理解：`catkin_make` 不会生成项目源码

执行：

```bash
cd ~/robot_course/catkin_ws
catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3
```

并不会自动生成 `embodied_robot_demo` 中的机器人模型、场景或程序。

在执行 `catkin_make` 前，`src/` 中必须已经存在源码：

```text
catkin_ws/
└── src/
    └── embodied_robot_demo/
        ├── CMakeLists.txt
        ├── package.xml
        ├── config/
        ├── launch/
        ├── scripts/
        ├── urdf/
        └── worlds/
```

`catkin_make` 的作用是读取这些源码和配置，检查 ROS 包依赖，并生成：

```text
catkin_ws/
├── build/       # CMake 中间文件和构建缓存
├── devel/       # ROS 开发环境，包括 devel/setup.bash
└── src/         # 人工编写的源码，catkin_make 不会替你创建
```

因此，正确教学顺序是：

```text
创建工作空间
    ↓
创建 ROS 包骨架
    ↓
逐个编写模型、场景、控制器和程序文件
    ↓
执行 catkin_make
    ↓
使用 roslaunch 和 rosrun 运行
```

---

## 1. 最终目录与角色分工

最终需要构建：

```text
catkin_ws/src/embodied_robot_demo/
├── CMakeLists.txt
├── package.xml
├── requirements-voice.txt
├── config/
│   ├── controllers.yaml
│   └── display.rviz
├── launch/
│   ├── display.launch
│   ├── gazebo_demo.launch
│   └── multimodal_demo.launch
├── scripts/
│   ├── robot_control_api.py
│   ├── task_orchestrator.py
│   ├── vision_node.py
│   └── voice_node.py
├── urdf/
│   └── embodied_robot.urdf.xacro
└── worlds/
    └── simple_room.world
```

### 1.1 A 负责创建和理解的文件

```text
CMakeLists.txt
package.xml
config/controllers.yaml
config/display.rviz
launch/display.launch
launch/gazebo_demo.launch
urdf/embodied_robot.urdf.xacro
worlds/simple_room.world
```

A 必须理解这些文件，因为它们决定：

- ROS 包依赖。
- 四轮移动底盘结构。
- 两自由度机械臂结构。
- 固定两指夹爪结构。
- 相机位置和图像 Topic。
- Gazebo 场景。
- 机械臂控制器。

### 1.2 B 负责创建和理解的文件

```text
requirements-voice.txt
launch/multimodal_demo.launch
scripts/robot_control_api.py
scripts/task_orchestrator.py
scripts/vision_node.py
scripts/voice_node.py
```

B 必须理解这些文件，因为它们决定：

- 底盘和机械臂控制 API。
- 红色目标视觉识别。
- 离线中文语音识别。
- 多模态任务编排。

### 1.3 为什么 A 仍要保留 B 的文件

`embodied_robot_demo` 必须是一个完整 ROS 包，不能拆成 A 包和 B 包。A 不需要负责 B 的程序实现，但最终合并后，A 的机器也应保留完整目录，以便进行集成测试。

---

## 2. 第一步：创建空 Catkin 工作空间

### 2.1 确认未进入 Conda 环境

```bash
conda deactivate 2>/dev/null || true
which python3
```

应输出：

```text
/usr/bin/python3
```

### 2.2 加载 ROS Noetic

```bash
source /opt/ros/noetic/setup.bash
echo $ROS_DISTRO
```

预期：

```text
noetic
```

### 2.3 创建工作空间

```bash
mkdir -p ~/robot_course/catkin_ws/src
cd ~/robot_course/catkin_ws
catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3
```

此时 `src/` 中还没有课程项目，只会生成一个基础工作空间。

检查：

```bash
find ~/robot_course/catkin_ws -maxdepth 2 -type d | sort
```

应看到：

```text
catkin_ws
catkin_ws/build
catkin_ws/devel
catkin_ws/src
```

首次初始化后，Catkin 还会在 `catkin_ws/src/` 中生成一个顶层 `CMakeLists.txt`。它用于标识整个 `src/` 是 Catkin 源码空间，不是课程包自己的 `CMakeLists.txt`，不要删除或随意修改。

---

## 3. 第二步：使用 `catkin_create_pkg` 创建 ROS 包骨架

### 3.1 执行创建命令

```bash
cd ~/robot_course/catkin_ws/src

catkin_create_pkg embodied_robot_demo \
  rospy \
  std_msgs \
  geometry_msgs \
  sensor_msgs \
  cv_bridge \
  image_transport \
  robot_state_publisher \
  gazebo_ros \
  xacro
```

该命令会自动生成：

```text
embodied_robot_demo/
├── CMakeLists.txt
└── package.xml
```

这两个文件只是初始模板，还需要继续修改。

### 3.2 创建功能目录

```bash
cd ~/robot_course/catkin_ws/src/embodied_robot_demo
mkdir -p config launch scripts urdf worlds
```

检查：

```bash
find . -maxdepth 2 -type d | sort
```

### 3.3 此时目录状态

```text
embodied_robot_demo/
├── CMakeLists.txt          # catkin_create_pkg 自动生成，后续修改
├── package.xml             # catkin_create_pkg 自动生成，后续修改
├── config/                 # 人工创建，目前为空
├── launch/                 # 人工创建，目前为空
├── scripts/                # 人工创建，目前为空
├── urdf/                   # 人工创建，目前为空
└── worlds/                 # 人工创建，目前为空
```

现在执行 `catkin_make` 只能证明空包骨架合法，还没有机器人可以运行。

---

## 4. 第三步：编写 `package.xml`

### 4.1 `package.xml` 的作用

`package.xml` 是 ROS 包清单，声明：

- 包名称和版本。
- 维护者和许可证。
- 构建工具。
- 运行所需 ROS 包。

如果依赖没有声明，其他人执行 `rosdep install` 时就无法自动安装所需组件。

### 4.2 编辑文件

```bash
gedit ~/robot_course/catkin_ws/src/embodied_robot_demo/package.xml
```

将内容修改为：

```xml
<?xml version="1.0"?>
<package format="2">
  <name>embodied_robot_demo</name>
  <version>1.0.0</version>
  <description>Course demo of a mobile manipulator with Gazebo, vision, voice, and task orchestration.</description>

  <maintainer email="student@example.com">Student</maintainer>
  <license>MIT</license>

  <buildtool_depend>catkin</buildtool_depend>

  <depend>controller_manager</depend>
  <depend>cv_bridge</depend>
  <depend>effort_controllers</depend>
  <depend>gazebo_plugins</depend>
  <depend>gazebo_ros</depend>
  <depend>gazebo_ros_control</depend>
  <depend>geometry_msgs</depend>
  <depend>image_transport</depend>
  <depend>joint_state_controller</depend>
  <depend>robot_state_publisher</depend>
  <depend>rospy</depend>
  <depend>sensor_msgs</depend>
  <depend>std_msgs</depend>
  <depend>xacro</depend>
  <exec_depend>joint_state_publisher_gui</exec_depend>
  <exec_depend>rviz</exec_depend>

  <export>
    <gazebo_ros gazebo_model_path="${prefix}"/>
  </export>
</package>
```

### 4.3 关键依赖解释

| 依赖 | 用途 |
|---|---|
| `gazebo_ros` | Gazebo 与 ROS 通信 |
| `gazebo_plugins` | 四轮驱动和相机插件 |
| `gazebo_ros_control` | Gazebo 中加载 ROS 控制器 |
| `controller_manager` | 管理机械臂控制器 |
| `effort_controllers` | 使用力矩接口执行关节位置控制 |
| `joint_state_controller` | 发布关节状态 |
| `robot_state_publisher` | 根据关节状态发布机器人 TF |
| `xacro` | 将 Xacro 展开为 URDF |
| `cv_bridge` | ROS 图像与 OpenCV 图像转换 |
| `rospy` | Python ROS 节点 |

### 4.4 检查 XML

```bash
xmllint --noout ~/robot_course/catkin_ws/src/embodied_robot_demo/package.xml
```

没有输出表示 XML 结构正确。

---

## 5. 第四步：编写 `CMakeLists.txt`

### 5.1 `CMakeLists.txt` 的作用

该文件告诉 Catkin：

- 当前包依赖哪些组件。
- 哪些 Python 脚本是可执行 ROS 节点。
- 哪些资源目录需要安装。

### 5.2 编辑文件

```bash
gedit ~/robot_course/catkin_ws/src/embodied_robot_demo/CMakeLists.txt
```

写入：

```cmake
cmake_minimum_required(VERSION 3.0.2)
project(embodied_robot_demo)

find_package(catkin REQUIRED COMPONENTS
  cv_bridge
  gazebo_ros
  geometry_msgs
  image_transport
  robot_state_publisher
  rospy
  sensor_msgs
  std_msgs
  xacro
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/robot_control_api.py
  scripts/task_orchestrator.py
  scripts/vision_node.py
  scripts/voice_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY config launch urdf worlds
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
```

### 5.3 为什么脚本尚未创建也可以先写

此处先声明最终会存在四个 Python 节点。脚本不存在时执行 `catkin_make` 可能报错，因此在 B 尚未提交脚本前，A 有两种做法：

1. 等 B 提交四个脚本后再进行最终编译。
2. A 开发模型时，暂时注释 `catkin_install_python` 整段，待集成时恢复。

推荐使用第一种做法；当前完整项目已经包含 B 的脚本，无需注释。

---

## 6. 第五步：从最小机器人开始编写 Xacro

机器人模型是本项目的核心。不要一次写完全部模型后才测试，应分阶段增加组件。

文件路径：

```text
~/robot_course/catkin_ws/src/embodied_robot_demo/urdf/embodied_robot.urdf.xacro
```

### 6.1 URDF/Xacro 基础概念

| 元素 | 含义 |
|---|---|
| `link` | 刚体，例如底盘、车轮、连杆 |
| `joint` | 两个刚体之间的连接 |
| `visual` | RViz/Gazebo 中看到的外观 |
| `collision` | 物理碰撞形状 |
| `inertial` | 质量、质心和惯量 |
| `transmission` | ROS 控制器和仿真关节之间的接口 |
| Gazebo `plugin` | 驱动、相机等仿真功能 |

### 6.2 阶段 1：只创建蓝色底盘

先编辑：

```bash
gedit ~/robot_course/catkin_ws/src/embodied_robot_demo/urdf/embodied_robot.urdf.xacro
```

写入最小模型：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="embodied_robot">
  <material name="blue">
    <color rgba="0.1 0.35 0.8 1"/>
  </material>

  <link name="base_footprint"/>

  <joint name="base_footprint_joint" type="fixed">
    <parent link="base_footprint"/>
    <child link="base_link"/>
    <origin xyz="0 0 0.20"/>
  </joint>

  <link name="base_link">
    <visual>
      <geometry><box size="0.52 0.42 0.18"/></geometry>
      <material name="blue"/>
    </visual>
    <collision>
      <geometry><box size="0.52 0.42 0.18"/></geometry>
    </collision>
    <inertial>
      <mass value="12.0"/>
      <inertia ixx="0.2088" ixy="0" ixz="0"
               iyy="0.3028" iyz="0" izz="0.4468"/>
    </inertial>
  </link>
</robot>
```

展开并检查：

```bash
cd ~/robot_course/catkin_ws
rosrun xacro xacro \
  src/embodied_robot_demo/urdf/embodied_robot.urdf.xacro \
  > /tmp/embodied_robot.urdf
check_urdf /tmp/embodied_robot.urdf
```

预期只能看到：

```text
base_footprint
base_link
```

### 6.3 阶段 2：加入 Xacro 参数和惯量宏

在 `<robot>` 后加入参数：

```xml
  <xacro:property name="pi" value="3.141592653589793"/>
  <xacro:property name="wheel_radius" value="0.09"/>
  <xacro:property name="wheel_width" value="0.045"/>
  <xacro:property name="wheel_y" value="0.22"/>
  <xacro:property name="wheel_x" value="0.18"/>
```

加入盒体、圆柱和车轮惯量宏：

```xml
  <xacro:macro name="box_inertial" params="mass x y z">
    <inertial>
      <mass value="${mass}"/>
      <inertia ixx="${mass * (y*y + z*z) / 12.0}" ixy="0" ixz="0"
               iyy="${mass * (x*x + z*z) / 12.0}" iyz="0"
               izz="${mass * (x*x + y*y) / 12.0}"/>
    </inertial>
  </xacro:macro>

  <xacro:macro name="cylinder_inertial" params="mass radius length">
    <inertial>
      <mass value="${mass}"/>
      <inertia ixx="${mass * (3*radius*radius + length*length) / 12.0}" ixy="0" ixz="0"
               iyy="${mass * (3*radius*radius + length*length) / 12.0}" iyz="0"
               izz="${mass * radius*radius / 2.0}"/>
    </inertial>
  </xacro:macro>

  <xacro:macro name="wheel_inertial" params="mass radius length">
    <inertial>
      <origin rpy="${pi/2} 0 0"/>
      <mass value="${mass}"/>
      <inertia ixx="${mass * (3*radius*radius + length*length) / 12.0}" ixy="0" ixz="0"
               iyy="${mass * (3*radius*radius + length*length) / 12.0}" iyz="0"
               izz="${mass * radius*radius / 2.0}"/>
    </inertial>
  </xacro:macro>
```

宏的意义是避免为四个相同车轮重复编写相同惯量。

### 6.4 阶段 3：加入四轮稳定底盘

加入深色材质：

```xml
  <material name="dark"><color rgba="0.12 0.12 0.14 1"/></material>
```

创建车轮宏：

```xml
  <xacro:macro name="wheel" params="prefix x y">
    <link name="${prefix}_wheel_link">
      <visual>
        <origin rpy="${pi/2} 0 0"/>
        <geometry>
          <cylinder radius="${wheel_radius}" length="${wheel_width}"/>
        </geometry>
        <material name="dark"/>
      </visual>
      <collision>
        <origin rpy="${pi/2} 0 0"/>
        <geometry>
          <cylinder radius="${wheel_radius}" length="${wheel_width}"/>
        </geometry>
      </collision>
      <xacro:wheel_inertial mass="0.8"
                            radius="${wheel_radius}"
                            length="${wheel_width}"/>
    </link>

    <joint name="${prefix}_wheel_joint" type="continuous">
      <parent link="base_link"/>
      <child link="${prefix}_wheel_link"/>
      <origin xyz="${x} ${y} -0.105"/>
      <axis xyz="0 1 0"/>
      <dynamics damping="0.05" friction="0.0"/>
    </joint>

    <gazebo reference="${prefix}_wheel_link">
      <mu1>1.2</mu1>
      <mu2>1.2</mu2>
      <kp>1000000</kp>
      <kd>10</kd>
    </gazebo>
  </xacro:macro>
```

实例化四个车轮：

```xml
  <xacro:wheel prefix="left" x="${wheel_x}" y="${wheel_y}"/>
  <xacro:wheel prefix="right" x="${wheel_x}" y="${-wheel_y}"/>
  <xacro:wheel prefix="left_rear" x="${-wheel_x}" y="${wheel_y}"/>
  <xacro:wheel prefix="right_rear" x="${-wheel_x}" y="${-wheel_y}"/>
```

四个关节名称最终为：

```text
left_wheel_joint
right_wheel_joint
left_rear_wheel_joint
right_rear_wheel_joint
```

其中原来的 `left_wheel_joint` 和 `right_wheel_joint` 作为前轮关节保留，新增两个后轮关节。四轮结构用于解决高机械臂使两轮底盘前倾的问题。

再次执行：

```bash
rosrun xacro xacro \
  ~/robot_course/catkin_ws/src/embodied_robot_demo/urdf/embodied_robot.urdf.xacro \
  > /tmp/embodied_robot.urdf
check_urdf /tmp/embodied_robot.urdf
```

### 6.5 阶段 4：加入机械臂底座和第一连杆

加入材质：

```xml
  <material name="orange"><color rgba="1.0 0.45 0.05 1"/></material>
  <material name="silver"><color rgba="0.65 0.68 0.72 1"/></material>
```

加入机械臂底座：

```xml
  <link name="arm_base_link">
    <visual>
      <geometry><cylinder radius="0.10" length="0.08"/></geometry>
      <material name="silver"/>
    </visual>
    <collision>
      <geometry><cylinder radius="0.10" length="0.08"/></geometry>
    </collision>
    <xacro:cylinder_inertial mass="1.0" radius="0.10" length="0.08"/>
  </link>

  <joint name="arm_base_joint" type="fixed">
    <parent link="base_link"/>
    <child link="arm_base_link"/>
    <origin xyz="0 0 0.13"/>
  </joint>
```

加入第一连杆和肩关节：

```xml
  <link name="arm_link_1">
    <visual>
      <origin xyz="0 0 0.18"/>
      <geometry><box size="0.07 0.07 0.36"/></geometry>
      <material name="orange"/>
    </visual>
    <collision>
      <origin xyz="0 0 0.18"/>
      <geometry><box size="0.07 0.07 0.36"/></geometry>
    </collision>
    <inertial>
      <origin xyz="0 0 0.18"/>
      <mass value="1.2"/>
      <inertia ixx="0.01345" ixy="0" ixz="0"
               iyy="0.01345" iyz="0" izz="0.00098"/>
    </inertial>
  </link>

  <joint name="arm_joint_1" type="revolute">
    <parent link="arm_base_link"/>
    <child link="arm_link_1"/>
    <origin xyz="0 0 0.04"/>
    <axis xyz="0 1 0"/>
    <limit lower="-1.20" upper="1.20" effort="35" velocity="1.5"/>
    <dynamics damping="0.8" friction="0.1"/>
  </joint>
```

`arm_joint_1` 的高度为 `0.04 m`，正好等于灰色圆柱底座长度的一半，因此第一橙色连杆不会悬空。

### 6.6 阶段 5：加入第二连杆

```xml
  <link name="arm_link_2">
    <visual>
      <origin xyz="0 0 0.15"/>
      <geometry><box size="0.06 0.06 0.30"/></geometry>
      <material name="orange"/>
    </visual>
    <collision>
      <origin xyz="0 0 0.15"/>
      <geometry><box size="0.06 0.06 0.30"/></geometry>
    </collision>
    <inertial>
      <origin xyz="0 0 0.15"/>
      <mass value="0.8"/>
      <inertia ixx="0.00624" ixy="0" ixz="0"
               iyy="0.00624" iyz="0" izz="0.00048"/>
    </inertial>
  </link>

  <joint name="arm_joint_2" type="revolute">
    <parent link="arm_link_1"/>
    <child link="arm_link_2"/>
    <origin xyz="0 0 0.36"/>
    <axis xyz="0 1 0"/>
    <limit lower="-1.50" upper="1.50" effort="25" velocity="1.8"/>
    <dynamics damping="0.6" friction="0.08"/>
  </joint>
```

两个橙色柱体分别表示机械臂的大臂和小臂。它们不是装饰，而是由两个旋转关节连接的刚性连杆。

### 6.7 阶段 6：加入固定开口两指夹爪

夹爪保持为一个固定的 `tool_link`，包含一个掌座和两根指爪：

```xml
  <link name="tool_link">
    <visual name="gripper_palm_visual">
      <origin xyz="0 0 0.025"/>
      <geometry><box size="0.10 0.16 0.05"/></geometry>
      <material name="silver"/>
    </visual>
    <visual name="left_finger_visual">
      <origin xyz="0 0.065 0.11"/>
      <geometry><box size="0.04 0.03 0.14"/></geometry>
      <material name="dark"/>
    </visual>
    <visual name="right_finger_visual">
      <origin xyz="0 -0.065 0.11"/>
      <geometry><box size="0.04 0.03 0.14"/></geometry>
      <material name="dark"/>
    </visual>

    <collision name="gripper_palm_collision">
      <origin xyz="0 0 0.025"/>
      <geometry><box size="0.10 0.16 0.05"/></geometry>
    </collision>
    <collision name="left_finger_collision">
      <origin xyz="0 0.065 0.11"/>
      <geometry><box size="0.04 0.03 0.14"/></geometry>
    </collision>
    <collision name="right_finger_collision">
      <origin xyz="0 -0.065 0.11"/>
      <geometry><box size="0.04 0.03 0.14"/></geometry>
    </collision>

    <inertial>
      <origin xyz="0 0 0.07"/>
      <mass value="0.35"/>
      <inertia ixx="0.00120" ixy="0" ixz="0"
               iyy="0.00065" iyz="0" izz="0.00125"/>
    </inertial>
  </link>

  <joint name="tool_joint" type="fixed">
    <parent link="arm_link_2"/>
    <child link="tool_link"/>
    <origin xyz="0 0 0.30"/>
  </joint>
```

该夹爪没有开合关节，只用于直观表示末端执行器，不能声称已经实现真实抓取。

### 6.8 阶段 7：加入相机

```xml
  <link name="camera_link">
    <visual>
      <geometry><box size="0.08 0.10 0.07"/></geometry>
      <material name="dark"/>
    </visual>
    <collision>
      <geometry><box size="0.08 0.10 0.07"/></geometry>
    </collision>
    <xacro:box_inertial mass="0.2" x="0.08" y="0.10" z="0.07"/>
  </link>

  <joint name="camera_joint" type="fixed">
    <parent link="base_link"/>
    <child link="camera_link"/>
    <origin xyz="0.27 0 0.10"/>
  </joint>

  <link name="camera_optical_link"/>

  <joint name="camera_optical_joint" type="fixed">
    <parent link="camera_link"/>
    <child link="camera_optical_link"/>
    <origin xyz="0.045 0 0" rpy="${-pi/2} 0 ${-pi/2}"/>
  </joint>
```

其中：

- `camera_link` 是 RViz 中可见的黑色相机外壳。
- `camera_optical_link` 是不可见的光学坐标系。
- 相机位于底盘前端。

### 6.9 阶段 8：加入机械臂 transmission

Gazebo 中的 ROS 控制器需要通过 transmission 找到机械臂关节：

```xml
  <transmission name="arm_joint_1_transmission">
    <type>transmission_interface/SimpleTransmission</type>
    <joint name="arm_joint_1">
      <hardwareInterface>hardware_interface/EffortJointInterface</hardwareInterface>
    </joint>
    <actuator name="arm_joint_1_motor">
      <hardwareInterface>hardware_interface/EffortJointInterface</hardwareInterface>
      <mechanicalReduction>1</mechanicalReduction>
    </actuator>
  </transmission>

  <transmission name="arm_joint_2_transmission">
    <type>transmission_interface/SimpleTransmission</type>
    <joint name="arm_joint_2">
      <hardwareInterface>hardware_interface/EffortJointInterface</hardwareInterface>
    </joint>
    <actuator name="arm_joint_2_motor">
      <hardwareInterface>hardware_interface/EffortJointInterface</hardwareInterface>
      <mechanicalReduction>1</mechanicalReduction>
    </actuator>
  </transmission>
```

### 6.10 阶段 9：加入 Gazebo 控制与传感器插件

加入 `gazebo_ros_control`：

```xml
  <gazebo>
    <plugin name="gazebo_ros_control" filename="libgazebo_ros_control.so">
      <robotNamespace>/</robotNamespace>
    </plugin>
  </gazebo>
```

加入四轮滑移转向插件：

```xml
  <gazebo>
    <plugin name="skid_steer_drive_controller" filename="libgazebo_ros_skid_steer_drive.so">
      <robotNamespace>/</robotNamespace>
      <leftFrontJoint>left_wheel_joint</leftFrontJoint>
      <rightFrontJoint>right_wheel_joint</rightFrontJoint>
      <leftRearJoint>left_rear_wheel_joint</leftRearJoint>
      <rightRearJoint>right_rear_wheel_joint</rightRearJoint>
      <wheelSeparation>${2 * wheel_y}</wheelSeparation>
      <wheelDiameter>${2 * wheel_radius}</wheelDiameter>
      <torque>15</torque>
      <commandTopic>cmd_vel</commandTopic>
      <odometryTopic>odom</odometryTopic>
      <odometryFrame>odom</odometryFrame>
      <robotBaseFrame>base_footprint</robotBaseFrame>
      <broadcastTF>true</broadcastTF>
      <updateRate>50</updateRate>
    </plugin>
  </gazebo>
```

该插件订阅 `/cmd_vel`，自动计算四个轮子的速度。

加入相机插件：

```xml
  <gazebo reference="camera_link">
    <sensor type="camera" name="front_camera">
      <update_rate>20</update_rate>
      <camera name="front">
        <horizontal_fov>1.047</horizontal_fov>
        <image>
          <width>640</width>
          <height>480</height>
          <format>R8G8B8</format>
        </image>
        <clip><near>0.05</near><far>20</far></clip>
      </camera>
      <plugin name="camera_controller" filename="libgazebo_ros_camera.so">
        <robotNamespace>/</robotNamespace>
        <cameraName>camera</cameraName>
        <imageTopicName>image_raw</imageTopicName>
        <cameraInfoTopicName>camera_info</cameraInfoTopicName>
        <frameName>camera_optical_link</frameName>
      </plugin>
    </sensor>
  </gazebo>
```

相机最终发布：

```text
/camera/image_raw
/camera/camera_info
```

### 6.11 每次修改模型后都要执行的检查

```bash
cd ~/robot_course/catkin_ws

rosrun xacro xacro \
  src/embodied_robot_demo/urdf/embodied_robot.urdf.xacro \
  > /tmp/embodied_robot.urdf

check_urdf /tmp/embodied_robot.urdf
```

不要等全部模型写完后再检查。错误越早发现，越容易定位。

---

## 7. 第六步：创建 RViz 模型检查功能

### 7.1 创建 `display.launch`

文件：

```text
launch/display.launch
```

内容：

```xml
<?xml version="1.0"?>
<launch>
  <param name="robot_description"
         command="$(find xacro)/xacro '$(find embodied_robot_demo)/urdf/embodied_robot.urdf.xacro'"/>

  <node pkg="joint_state_publisher_gui" type="joint_state_publisher_gui"
        name="joint_state_publisher_gui"/>
  <node pkg="robot_state_publisher" type="robot_state_publisher"
        name="robot_state_publisher"/>
  <node pkg="rviz" type="rviz" name="rviz"
        args="-d $(find embodied_robot_demo)/config/display.rviz"/>
</launch>
```

它完成：

1. 将 Xacro 展开后放入 ROS 参数 `/robot_description`。
2. 启动关节滑块 GUI。
3. 发布 TF。
4. 启动 RViz。

### 7.2 创建 `display.rviz`

最简单的方法不是手写 RViz 配置，而是：

1. 先临时启动 RViz：

   ```bash
   rosrun rviz rviz
   ```

2. 将 Fixed Frame 改为：

   ```text
   base_footprint
   ```

3. 点击 `Add`，添加：

   ```text
   RobotModel
   Grid
   ```

4. 在 RViz 菜单选择：

   ```text
   File -> Save Config As
   ```

5. 保存到：

   ```text
   ~/robot_course/catkin_ws/src/embodied_robot_demo/config/display.rviz
   ```

这一步说明 `display.rviz` 是由 RViz 图形界面保存的配置，而不是 Catkin 自动生成。

### 7.3 运行 RViz 检查

```bash
source /opt/ros/noetic/setup.bash
source ~/robot_course/catkin_ws/devel/setup.bash
roslaunch embodied_robot_demo display.launch
```

检查：

- 四个轮子位于底盘四角。
- 灰色机械臂底座与第一橙色连杆没有间隙。
- 两段橙色连杆可通过滑块弯曲。
- 顶部显示固定两指夹爪。
- 黑色相机位于底盘前端。

RViz 不计算轮地摩擦，因此拖动车轮关节滑块不会让车辆移动。

---

## 8. 第七步：创建机械臂控制器配置

创建：

```text
config/controllers.yaml
```

内容：

```yaml
joint_state_controller:
  type: joint_state_controller/JointStateController
  publish_rate: 50

joint1_position_controller:
  type: effort_controllers/JointPositionController
  joint: arm_joint_1
  pid: {p: 120.0, i: 0.5, d: 12.0}

joint2_position_controller:
  type: effort_controllers/JointPositionController
  joint: arm_joint_2
  pid: {p: 90.0, i: 0.4, d: 9.0}
```

### 8.1 控制器解释

- `joint_state_controller` 发布当前关节状态。
- `joint1_position_controller` 控制肩关节目标角度。
- `joint2_position_controller` 控制肘关节目标角度。
- PID 参数决定响应速度、误差和阻尼。

控制 Topic 为：

```text
/joint1_position_controller/command
/joint2_position_controller/command
```

四轮不使用这份 YAML 控制，因为四轮由 Gazebo skid-steer 插件直接根据 `/cmd_vel` 驱动。

---

## 9. 第八步：创建 Gazebo 场景

创建：

```text
worlds/simple_room.world
```

### 9.1 先建立最小世界

```xml
<?xml version="1.0"?>
<sdf version="1.6">
  <world name="simple_room">
    <gravity>0 0 -9.81</gravity>
    <physics type="ode">
      <real_time_update_rate>1000</real_time_update_rate>
      <max_step_size>0.001</max_step_size>
    </physics>

    <include>
      <uri>model://ground_plane</uri>
    </include>
    <include>
      <uri>model://sun</uri>
    </include>
  </world>
</sdf>
```

此时世界只有地面和光源。

### 9.2 加入墙体

在 `<world>` 内加入一个静态墙体：

```xml
    <model name="back_wall">
      <static>true</static>
      <pose>2.5 0 0.5 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>0.1 5 1</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>0.1 5 1</size></box></geometry>
          <material>
            <ambient>0.7 0.7 0.7 1</ambient>
            <diffuse>0.7 0.7 0.7 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
```

按照相同方式创建 `left_wall` 和 `right_wall`，分别放在：

```text
左墙 pose：0 2.5 0.5 0 0 0
右墙 pose：0 -2.5 0.5 0 0 0
墙体尺寸：5 0.1 1
```

### 9.3 加入红色视觉目标

```xml
    <model name="red_target">
      <static>true</static>
      <pose>1.7 0 0.3 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>0.35 0.35 0.6</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>0.35 0.35 0.6</size></box></geometry>
          <material>
            <ambient>1 0 0 1</ambient>
            <diffuse>1 0 0 1</diffuse>
            <specular>0.1 0.1 0.1 1</specular>
          </material>
        </visual>
      </link>
    </model>
```

红色目标使用简单纯色，是为了让 B 的 HSV 视觉检测稳定运行。

### 9.4 检查世界 XML

```bash
xmllint --noout \
  ~/robot_course/catkin_ws/src/embodied_robot_demo/worlds/simple_room.world
```

---

## 10. 第九步：创建 Gazebo 启动文件

创建：

```text
launch/gazebo_demo.launch
```

内容：

```xml
<?xml version="1.0"?>
<launch>
  <arg name="gui" default="true"/>
  <arg name="paused" default="false"/>
  <arg name="use_sim_time" default="true"/>
  <arg name="x" default="0.0"/>
  <arg name="y" default="0.0"/>
  <arg name="z" default="0.02"/>

  <param name="use_sim_time" value="$(arg use_sim_time)"/>
  <param name="robot_description"
         command="$(find xacro)/xacro '$(find embodied_robot_demo)/urdf/embodied_robot.urdf.xacro'"/>

  <include file="$(find gazebo_ros)/launch/empty_world.launch">
    <arg name="world_name" value="$(find embodied_robot_demo)/worlds/simple_room.world"/>
    <arg name="gui" value="$(arg gui)"/>
    <arg name="paused" value="$(arg paused)"/>
    <arg name="use_sim_time" value="$(arg use_sim_time)"/>
  </include>

  <node pkg="gazebo_ros" type="spawn_model" name="spawn_embodied_robot"
        args="-urdf -param robot_description -model embodied_robot -x $(arg x) -y $(arg y) -z $(arg z)"
        output="screen"/>

  <rosparam file="$(find embodied_robot_demo)/config/controllers.yaml"
            command="load"/>

  <node pkg="controller_manager" type="spawner"
        name="arm_controller_spawner"
        args="joint_state_controller joint1_position_controller joint2_position_controller"
        output="screen"/>

  <node pkg="robot_state_publisher" type="robot_state_publisher"
        name="robot_state_publisher" output="screen">
    <param name="publish_frequency" value="50.0"/>
  </node>
</launch>
```

### 10.1 启动顺序解释

该 launch 文件会自动完成：

1. 展开 Xacro。
2. 将 URDF 写入 `/robot_description`。
3. 启动 `simple_room.world`。
4. 将机器人生成到 Gazebo。
5. 加载机械臂控制器参数。
6. 启动机械臂控制器。
7. 启动机器人 TF 发布器。

---

## 11. 第十步：第一次完整编译和 Gazebo 验证

### 11.1 安装声明的依赖

```bash
cd ~/robot_course/catkin_ws
rosdep install --from-paths src --ignore-src -r -y
```

### 11.2 编译

```bash
conda deactivate 2>/dev/null || true
source /opt/ros/noetic/setup.bash
cd ~/robot_course/catkin_ws
catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3
source devel/setup.bash
```

此时 `catkin_make` 编译的是刚刚逐步建立的源码，而不是一个凭空出现的文件夹。

### 11.3 启动 Gazebo

```bash
roslaunch embodied_robot_demo gazebo_demo.launch
```

### 11.4 检查四轮稳定性

观察至少三分钟：

- 四轮均接触地面。
- 底盘保持水平。
- 小车不前倾。
- 机械臂不持续剧烈振荡。

### 11.5 测试底盘

```bash
timeout 2s rostopic pub -r 10 /cmd_vel geometry_msgs/Twist \
"linear: {x: 0.2, y: 0.0, z: 0.0}
angular: {x: 0.0, y: 0.0, z: 0.0}"
```

停车：

```bash
rostopic pub -1 /cmd_vel geometry_msgs/Twist \
"linear: {x: 0.0, y: 0.0, z: 0.0}
angular: {x: 0.0, y: 0.0, z: 0.0}"
```

### 11.6 测试机械臂

```bash
rostopic pub -1 /joint1_position_controller/command std_msgs/Float64 "data: 0.6"
rostopic pub -1 /joint2_position_controller/command std_msgs/Float64 "data: -0.8"
```

### 11.7 测试相机

```bash
rqt_image_view
```

选择：

```text
/camera/image_raw
```

---

## 12. 第十一步：B 创建控制与多模态文件

至此，A 已经构建了可独立运行的 Gazebo 移动操作机器人。B 接着在同一个 ROS 包内加入控制与交互程序。

### 12.1 创建语音依赖文件

文件：

```text
requirements-voice.txt
```

内容：

```text
vosk==0.3.45
sounddevice==0.4.6
```

### 12.2 创建控制 API

文件：

```text
scripts/robot_control_api.py
```

该节点应逐步实现：

1. 创建 `/cmd_vel` 发布器。
2. 创建两个机械臂控制器 Topic 发布器。
3. 实现速度与关节限幅。
4. 实现定时运动。
5. 实现动作结束停车。
6. 实现节点退出停车。
7. 实现机械臂 home 和挥手。

需要提供的方法：

```python
move_forward(speed, duration)
move_backward(speed, duration)
turn_left(speed, duration)
turn_right(speed, duration)
stop()
set_arm(joint1, joint2, wait_time)
arm_home()
arm_wave(cycles)
```

完整实现位于当前项目：

```text
catkin_ws/src/embodied_robot_demo/scripts/robot_control_api.py
```

教学时应按照上述功能顺序逐个实现，每增加一个方法就单独测试，不应直接复制后完全不解释。

### 12.3 创建视觉节点

文件：

```text
scripts/vision_node.py
```

实现顺序：

1. 订阅 `/camera/image_raw`。
2. 使用 `cv_bridge` 转为 OpenCV BGR 图像。
3. 将 BGR 转为 HSV。
4. 使用两个红色 HSV 区间创建掩膜。
5. 使用形态学操作减少噪声。
6. 找到最大红色轮廓。
7. 面积达到阈值时发布 `/vision/red_target = True`。
8. 绘制检测框。

### 12.4 创建语音节点

文件：

```text
scripts/voice_node.py
```

实现顺序：

1. 加载 Vosk 中文模型。
2. 打开麦克风。
3. 将音频数据送入识别器。
4. 将识别文本归一化。
5. 只接受规定命令。
6. 发布 `/voice/command`。

### 12.5 创建任务编排节点

文件：

```text
scripts/task_orchestrator.py
```

实现顺序：

1. 导入 `RobotControlAPI`。
2. 订阅 `/vision/red_target`。
3. 订阅 `/voice/command`。
4. 发布 `/task/status`。
5. 收到“开始任务”后等待视觉结果。
6. 检测到目标后前进、停车、挥手、回 home。
7. 收到“停止”后中止当前任务。
8. 使用独立任务线程，避免订阅回调被长动作阻塞。

### 12.6 创建多模态启动文件

文件：

```text
launch/multimodal_demo.launch
```

内容：

```xml
<?xml version="1.0"?>
<launch>
  <arg name="gui" default="true"/>
  <arg name="show_vision_window" default="false"/>
  <arg name="auto_start" default="false"/>

  <include file="$(find embodied_robot_demo)/launch/gazebo_demo.launch">
    <arg name="gui" value="$(arg gui)"/>
  </include>

  <node pkg="embodied_robot_demo" type="vision_node.py"
        name="vision_node" output="screen">
    <param name="show_window" value="$(arg show_vision_window)"/>
    <param name="minimum_area" value="800.0"/>
  </node>

  <node pkg="embodied_robot_demo" type="task_orchestrator.py"
        name="task_orchestrator" output="screen">
    <param name="auto_start" value="$(arg auto_start)"/>
    <param name="vision_timeout" value="10.0"/>
  </node>
</launch>
```

语音节点运行于独立 venv，因此不强制写入该 launch 文件。

### 12.7 设置脚本权限

```bash
chmod +x ~/robot_course/catkin_ws/src/embodied_robot_demo/scripts/*.py
```

### 12.8 重新编译

```bash
cd ~/robot_course/catkin_ws
catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3
source devel/setup.bash
```

---

## 13. 每个文件到底是如何产生的

| 文件或目录 | 产生方式 | 负责人 |
|---|---|---|
| `catkin_ws/src/` | `mkdir -p` 创建 | A |
| `catkin_ws/src/CMakeLists.txt` | 首次初始化 Catkin 工作空间时自动生成 | Catkin |
| `embodied_robot_demo/CMakeLists.txt` | `catkin_create_pkg` 生成模板，人工修改 | A |
| `embodied_robot_demo/package.xml` | `catkin_create_pkg` 生成模板，人工修改 | A |
| `config/ launch/ scripts/ urdf/ worlds/` | `mkdir -p` 创建 | A |
| `urdf/embodied_robot.urdf.xacro` | A 分阶段人工编写 | A |
| `config/controllers.yaml` | A 人工编写 | A |
| `config/display.rviz` | RViz 图形界面保存 | A |
| `worlds/simple_room.world` | A 人工编写 | A |
| `launch/display.launch` | A 人工编写 | A |
| `launch/gazebo_demo.launch` | A 人工编写 | A |
| `requirements-voice.txt` | B 人工编写 | B |
| `scripts/*.py` | B 逐个功能实现 | B |
| `launch/multimodal_demo.launch` | B 人工编写 | B |
| `catkin_ws/build/` | `catkin_make` 自动生成 | Catkin |
| `catkin_ws/devel/` | `catkin_make` 自动生成 | Catkin |

本教程对 A 负责的包骨架、模型、场景、控制器和启动文件给出了可逐步构建的具体内容。四个 Python 节点属于 B 的独立实现任务，本教程给出了每个节点的功能拆分和实现顺序，最终实现以 `embodied_robot_demo/scripts/` 中对应源码为准。报告中必须据实写明 A、B 分工，不能把 B 的代码描述成 A 独立完成。

---

## 14. 推荐的教学演示顺序

面向听众时，不要一开始就展示完整项目并运行。推荐按以下顺序讲解：

1. 展示空的 `catkin_ws/src/`。
2. 使用 `catkin_create_pkg` 创建包骨架。
3. 说明 `package.xml` 和 `CMakeLists.txt`。
4. 只创建蓝色底盘并执行 `check_urdf`。
5. 添加四个轮子并再次检查。
6. 添加机械臂底座和两段连杆。
7. 添加固定两指夹爪。
8. 添加相机。
9. 使用 RViz 检查模型。
10. 创建 Gazebo 场景。
11. 添加四轮驱动、相机和机械臂控制器。
12. 在 Gazebo 中测试底盘、机械臂和相机。
13. B 逐步添加控制 API。
14. B 添加视觉节点。
15. B 添加语音节点。
16. B 添加任务编排。
17. 运行完整多模态任务。

这种顺序能让听众看到系统如何从一个蓝色盒子逐步变成移动操作机器人。

---

## 15. A 写实验报告时应记录什么

A 不应只写“复制代码后执行 `catkin_make`”。应记录：

### 15.1 ROS 包建立过程

- 为什么创建 Catkin 工作空间。
- `catkin_create_pkg` 生成了什么。
- 为什么还要修改 `package.xml` 和 `CMakeLists.txt`。
- `catkin_make` 生成了什么。

### 15.2 模型迭代过程

建议保存以下阶段截图：

```text
01_only_base.png
02_four_wheels.png
03_first_arm_link.png
04_two_link_arm.png
05_fixed_gripper.png
06_camera.png
07_complete_rviz_model.png
08_complete_gazebo_scene.png
```

### 15.3 模型问题与修复

应真实记录已经发现的问题：

1. 初版两轮底盘因为机械臂较高而前倾。
2. 将底盘修改为四轮滑移转向结构。
3. 初版机械臂底座和第一连杆存在 `0.02 m` 间隙。
4. 将 `arm_joint_1` 高度从 `0.06 m` 改为 `0.04 m`。
5. 初版末端使用灰色球体，不像机械臂末端。
6. 将灰色球替换为固定开口两指夹爪。

这些问题和修复比“第一次就全部成功”的虚假过程更有技术价值。

---

## 16. 最终验收

### 16.1 文件检查

```bash
find ~/robot_course/catkin_ws/src/embodied_robot_demo \
  -maxdepth 3 -type f | sort
```

### 16.2 构建检查

```bash
cd ~/robot_course/catkin_ws
catkin_make -DPYTHON_EXECUTABLE=/usr/bin/python3
source devel/setup.bash
rospack find embodied_robot_demo
```

### 16.3 模型检查

```bash
rosrun xacro xacro \
  src/embodied_robot_demo/urdf/embodied_robot.urdf.xacro \
  > /tmp/embodied_robot.urdf
check_urdf /tmp/embodied_robot.urdf
```

### 16.4 RViz 检查

```bash
roslaunch embodied_robot_demo display.launch
```

### 16.5 Gazebo 检查

```bash
roslaunch embodied_robot_demo gazebo_demo.launch
```

### 16.6 完整多模态检查

```bash
roslaunch embodied_robot_demo multimodal_demo.launch
```

最终应能够说明：

- 哪些文件由命令自动生成。
- 哪些文件由 A 人工设计。
- 哪些文件由 B 人工实现。
- `catkin_make` 为什么必须在源码存在后执行。
- ROS 包如何从空目录逐步构建并运行。
