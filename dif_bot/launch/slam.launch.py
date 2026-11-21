import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_dif_bot = get_package_share_directory('dif_bot')
    pkg_slam_toolbox = get_package_share_directory('slam_toolbox')

    default_params = os.path.join(
        pkg_dif_bot, 'config', 'mapper_params_online_async.yaml'
    )

    slam_params_arg = DeclareLaunchArgument(
        'slam_params_file',
        default_value=default_params,
        description='Ruta al archivo YAML de parametros de slam_toolbox'
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Usar reloj de simulacion'
    )

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_slam_toolbox, 'launch', 'online_async_launch.py')
        ),
        launch_arguments={
            'slam_params_file': LaunchConfiguration('slam_params_file'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }.items()
    )

    return LaunchDescription([
        slam_params_arg,
        use_sim_time_arg,
        slam_launch,
    ])
