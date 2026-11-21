import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dif_bot = get_package_share_directory('dif_bot')
    default_wp = os.path.join(pkg_dif_bot, 'config', 'waypoints.yaml')

    wp_arg = DeclareLaunchArgument(
        'waypoints_file',
        default_value=default_wp,
        description='Ruta al archivo YAML de waypoints'
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Usar reloj de simulacion'
    )

    mission_node = Node(
        package='dif_bot',
        executable='mission_commander.py',
        name='dif_bot_mission_commander',
        output='screen',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            {'waypoints_file': LaunchConfiguration('waypoints_file')},
        ]
    )

    return LaunchDescription([
        wp_arg,
        use_sim_time_arg,
        mission_node,
    ])
