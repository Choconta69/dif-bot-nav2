import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    cfg = os.path.join(get_package_share_directory('dif_bot'), 'config', 'ekf.yaml')
    return LaunchDescription([
        DeclareLaunchArgument('config', default_value=cfg,
                              description='Archivo de configuracion del EKF'),
        Node(package='robot_localization', executable='ekf_node',
             name='ekf_filter_node', output='screen',
             parameters=[LaunchConfiguration('config'), {'use_sim_time': True}],
             remappings=[('odometry/filtered', '/odom_filtered')]),
    ])
