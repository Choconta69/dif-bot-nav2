"""Simulacion de dif_bot en Gazebo.

Argumentos:
  use_ros2_control:=false|true   Modo de control (plugin DiffDrive de Gazebo / ros2_control)
  use_camera:=false|true         Incluir la camara de profundidad (pesada)
  gui:=false|true                Mostrar la ventana de Gazebo (por defecto solo servidor)
  rviz:=true|false               Abrir RViz
  world:=<ruta .sdf>             Mundo de Gazebo
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            OpaqueFunction, RegisterEventHandler,
                            SetEnvironmentVariable)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _flag(context, name):
    return LaunchConfiguration(name).perform(context).strip().lower() == 'true'


def launch_setup(context, *args, **kwargs):
    pkg = get_package_share_directory('dif_bot')
    use_ros2_control = _flag(context, 'use_ros2_control')
    use_camera = _flag(context, 'use_camera')
    gui = _flag(context, 'gui')
    rviz = _flag(context, 'rviz')
    world = LaunchConfiguration('world').perform(context)

    xacro_file = os.path.join(pkg, 'urdf', 'robot.urdf.xacro')
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file,
                 ' use_ros2_control:=', 'true' if use_ros2_control else 'false',
                 ' use_camera:=', 'true' if use_camera else 'false']),
        value_type=str)

    # Gazebo: sin GUI se lanza solo el servidor (-s), mucho mas liviano
    gz_args = '-r -v 2 ' + ('' if gui else '-s ') + world
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': gz_args}.items())

    robot_state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
        output='screen')

    spawn = Node(
        package='ros_gz_sim', executable='create',
        arguments=['-name', 'dif_bot', '-topic', 'robot_description', '-z', '0.17'],
        output='screen')

    bridge_common = Node(
        package='ros_gz_bridge', executable='parameter_bridge', name='bridge_common',
        parameters=[{'config_file': os.path.join(pkg, 'config', 'bridge_common.yaml'),
                     'use_sim_time': True}],
        output='screen')

    actions = [gz_sim, robot_state_publisher, spawn, bridge_common]

    if use_ros2_control:
        # Los controladores se cargan cuando el robot ya fue creado en Gazebo
        jsb = Node(
            package='controller_manager', executable='spawner',
            arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
            output='screen')
        dd = Node(
            package='controller_manager', executable='spawner',
            arguments=['diff_drive_controller', '--controller-manager', '/controller_manager',
                       '--controller-ros-args',
                       '-r /diff_drive_controller/cmd_vel:=/cmd_vel '
                       '-r /diff_drive_controller/odom:=/odom '
                       '-r /diff_drive_controller/tf_odometry:=/tf'],
            output='screen')
        actions += [
            RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=[jsb])),
            RegisterEventHandler(OnProcessExit(target_action=jsb, on_exit=[dd])),
        ]
    else:
        actions.append(Node(
            package='ros_gz_bridge', executable='parameter_bridge', name='bridge_gz_control',
            parameters=[{'config_file': os.path.join(pkg, 'config', 'bridge_gz_control.yaml'),
                         'use_sim_time': True}],
            output='screen'))

    if rviz:
        actions.append(Node(
            package='rviz2', executable='rviz2', name='rviz2',
            arguments=['-d', os.path.join(pkg, 'rviz', 'dif_bot.rviz')],
            parameters=[{'use_sim_time': True}], output='screen'))

    return actions


def generate_launch_description():
    pkg = get_package_share_directory('dif_bot')
    return LaunchDescription([
        # RViz y la GUI de Gazebo fallan bajo Wayland sin esto
        SetEnvironmentVariable('QT_QPA_PLATFORM', 'xcb'),
        DeclareLaunchArgument('use_ros2_control', default_value='false'),
        DeclareLaunchArgument('use_camera', default_value='false'),
        DeclareLaunchArgument('gui', default_value='false'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('world', default_value=os.path.join(pkg, 'worlds', 'dif_bot_world.sdf')),
        OpaqueFunction(function=launch_setup),
    ])
