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

