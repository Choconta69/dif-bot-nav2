#!/usr/bin/env python3
import math
import os
import time
import yaml

from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from std_srvs.srv import Trigger


def yaw_to_quaternion(yaw: float):
    return math.sin(yaw / 2.0), math.cos(yaw / 2.0)


class AutonomousMissionNode(BasicNavigator):
    def __init__(self):
        super().__init__(node_name='dif_bot_mission_commander')
        self.mission_requested = False
        self.mission_running = False

        pkg_share = get_package_share_directory('dif_bot')
        default_wp_file = os.path.join(pkg_share, 'config', 'waypoints.yaml')
        self.declare_parameter('waypoints_file', default_wp_file)

        self.srv = self.create_service(
            Trigger,
            '/iniciar_mision',
            self.start_mission_callback
        )
        self.get_logger().info(
            'Nodo de mision listo. Llama al servicio /iniciar_mision para comenzar.'
        )

    def start_mission_callback(self, request, response):
        if self.mission_running:
            response.success = False
            response.message = 'Ya hay una mision autonoma en ejecucion.'
            return response

        self.mission_requested = True
        response.success = True
        response.message = 'Solicitud recibida: iniciando patrullaje por waypoints.'
        return response

    def load_waypoints(self):
        wp_path = self.get_parameter('waypoints_file').get_parameter_value().string_value
        with open(wp_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        frame_id = data.get('frame_id', 'map')
        poses = []
        names = []

        for wp in data.get('waypoints', []):
            pose = PoseStamped()
            pose.header.frame_id = frame_id
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position.x = float(wp['x'])
            pose.pose.position.y = float(wp['y'])
            pose.pose.position.z = 0.0
            qz, qw = yaw_to_quaternion(float(wp.get('yaw', 0.0)))
            pose.pose.orientation.z = qz
            pose.pose.orientation.w = qw
            poses.append(pose)
            names.append(wp.get('name', f'Waypoint_{len(names)+1}'))

        return data.get('mission_name', 'Mision'), names, poses

    def execute_mission(self):
        self.mission_running = True
        self.mission_requested = False

        mission_name, names, poses = self.load_waypoints()
        self.get_logger().info(
            f'=== Iniciando "{mission_name}" con {len(poses)} waypoints ==='
        )
        self.waitUntilNav2Active()

        completed = 0
        for idx, (wp_name, goal_pose) in enumerate(zip(names, poses), start=1):
            goal_pose.header.stamp = self.get_clock().now().to_msg()
            self.get_logger().info(
                f'[{idx}/{len(poses)}] Navegando hacia {wp_name} '
                f'(x={goal_pose.pose.position.x:.2f}, y={goal_pose.pose.position.y:.2f})'
            )
            self.goToPose(goal_pose)

            last_log = time.time()
            while not self.isTaskComplete():
                feedback = self.getFeedback()
                if feedback and (time.time() - last_log) >= 2.0:
                    self.get_logger().info(
                        f'  -> Distancia restante a {wp_name}: '
                        f'{feedback.distance_remaining:.2f} m'
                    )
                    last_log = time.time()

            result = self.getResult()
            if result == TaskResult.SUCCEEDED:
                completed += 1
                self.get_logger().info(f'[OK] Waypoint alcanzado: {wp_name}')
            elif result == TaskResult.CANCELED:
                self.get_logger().warn(f'[CANCELADO] Mision cancelada en {wp_name}')
                break
            else:
                self.get_logger().error(f'[FALLO] No se pudo alcanzar {wp_name}')

        self.get_logger().info(
            f'=== Mision finalizada: {completed}/{len(poses)} waypoints completados ==='
        )
        self.mission_running = False


def main():
    rclpy.init()
    node = AutonomousMissionNode()
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
            if node.mission_requested and not node.mission_running:
                node.execute_mission()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
