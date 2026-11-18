cmake_minimum_required(VERSION 3.8)
project(dif_bot)

find_package(ament_cmake REQUIRED)

install(DIRECTORY urdf launch config worlds rviz
  DESTINATION share/${PROJECT_NAME})

ament_package()
