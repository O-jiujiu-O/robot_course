# 项目目录说明

该目录同时服务于运行、三人并行开发和最终材料汇总。运行源码不能按负责人拆散，否则会破坏 ROS 包和 Isaac Gym 相对路径。

```text
robot/
├── catkin_ws/src/embodied_robot_demo/  # ROS/Gazebo 运行源码，A/B 按文件所有权协作
├── isaacgym_demo/                      # Isaac Gym 运行源码，C 负责
├── docs/                               # 手册、三人章节素材、最终文档与 PPT
├── collaboration/                      # 跨机器交付模板和交付包
├── evidence/                           # 按负责人保存实验依据
├── isaacgym/                           # 各机器本地安装，不参与代码同步
└── envs/                               # 各机器本地环境，不参与代码同步
```

规则：

- `catkin_ws/src/embodied_robot_demo/` 必须保持为一个 ROS 包。
- `isaacgym_demo/assets/embodied_robot.urdf` 与 Gazebo Xacro 描述同一机器人，但由 C 维护 Isaac Gym 版本。
- `docs/team_inputs/person_X/` 保存每个人提交给 C 的文档章节和图表。
- `collaboration/handoffs/person_X/` 保存每次跨机器交付包。
- `evidence/person_X/` 保存各自机器产生的日志、截图和视频。
- 不传递 `catkin_ws/build/`、`catkin_ws/devel/`、`isaacgym/` 或 `envs/`。

