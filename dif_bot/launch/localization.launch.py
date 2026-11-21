import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dif_bot = get_package_share_directory('dif_bot')

    default_map = os.path.join(pkg_dif_bot, 'maps', 'mapa_dif_bot.yaml')
    default_amcl = os.path.join(pkg_dif_bot, 'config', 'amcl.yaml')

    map_arg = DeclareLaunchArgument(
        'map',
        default_value=default_map,
        description='Ruta completa al archivo YAML del mapa'
    )

    params_arg = DeclareLaunchArgument(
        'params_file',
        default_value=default_amcl,
        description='Ruta completa al archivo de parametros de AMCL'
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Usar reloj de simulacion'
    )

    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            {'yaml_filename': LaunchConfiguration('map')}
        ]
    )

    amcl_node = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[
            LaunchConfiguration('params_file'),
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            {'autostart': True},
            {'node_names': ['map_server', 'amcl']}
        ]
    )

    return LaunchDescription([
        map_arg,
        params_arg,
        use_sim_time_arg,
        map_server_node,
        amcl_node,
        lifecycle_manager_node,
    ])
