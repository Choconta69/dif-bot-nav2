#!/usr/bin/env python3
"""Compara /odom (ruedas) con /odom_filtered (EKF) durante una trayectoria."""
import math
import time

import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data

# (velocidad lineal m/s, velocidad angular rad/s, duracion s)
PLAN = [(0.2, 0.0, 4.0), (0.0, 0.5, 4.0), (0.2, 0.0, 4.0), (0.0, -0.5, 4.0), (0.2, 0.0, 3.0)]


def yaw(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


class Prueba(Node):
    def __init__(self):
        super().__init__('prueba_ekf', parameter_overrides=[
            Parameter('use_sim_time', Parameter.Type.BOOL, True)])
        self.raw = None
        self.fil = None
        self.create_subscription(Odometry, '/odom', self._raw, qos_profile_sensor_data)
        self.create_subscription(Odometry, '/odom_filtered', self._fil, qos_profile_sensor_data)

    @staticmethod
    def _pose(m):
        return (m.pose.pose.position.x, m.pose.pose.position.y, yaw(m.pose.pose.orientation))

    def _raw(self, m):
        self.raw = self._pose(m)

    def _fil(self, m):
        self.fil = self._pose(m)

    def spin_for(self, secs):
        end = time.time() + secs
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.02)

    def tipo_cmd_vel(self):
        infos = self.get_subscriptions_info_by_topic('/cmd_vel')
        return infos[0].topic_type if infos else None


def main():
    rclpy.init()
    n = Prueba()
    end = time.time() + 20
    while time.time() < end and (n.raw is None or n.fil is None or n.tipo_cmd_vel() is None):
        rclpy.spin_once(n, timeout_sec=0.1)
    if n.raw is None or n.fil is None or n.tipo_cmd_vel() is None:
        raise SystemExit('ERROR: faltan /odom, /odom_filtered o el suscriptor de /cmd_vel')
    stamped = n.tipo_cmd_vel().endswith('TwistStamped')
    pub = n.create_publisher(TwistStamped if stamped else Twist, '/cmd_vel', 10)

    def cmd(v, w):
        if stamped:
            m = TwistStamped()
            m.header.stamp = n.get_clock().now().to_msg()
            m.twist.linear.x = v
            m.twist.angular.z = w
        else:
            m = Twist()
            m.linear.x = v
            m.angular.z = w
        pub.publish(m)

    n.spin_for(1.0)
    r0, f0 = n.raw, n.fil
    # El EKF arranca en cero al lanzarlo; /odom conserva lo acumulado. Se resta el desfase inicial.
    ox, oy, oyaw = r0[0] - f0[0], r0[1] - f0[1], wrap(r0[2] - f0[2])
    print(f'modo: {"ros2_control" if stamped else "plugin_gazebo"}')
    print(f'inicio /odom         : x={r0[0]:.3f} y={r0[1]:.3f} yaw={math.degrees(r0[2]):.1f} deg')
    print(f'inicio /odom_filtered: x={f0[0]:.3f} y={f0[1]:.3f} yaw={math.degrees(f0[2]):.1f} deg')
    if abs(math.degrees(oyaw)) > 2.0:
        print('AVISO: las odometrias no parten del mismo giro; reinicia simulacion y EKF para comparar bien')

    dx, dy, dyaw = [], [], []
    for v, w, dur in PLAN:
        fin = time.time() + dur
        while time.time() < fin:
            cmd(v, w)
            n.spin_for(0.1)
            dx.append(n.raw[0] - n.fil[0] - ox)
            dy.append(n.raw[1] - n.fil[1] - oy)
            dyaw.append(wrap(n.raw[2] - n.fil[2] - oyaw))
    cmd(0.0, 0.0)
    n.spin_for(1.5)
    r, f = n.raw, n.fil

    def rms(a):
        return math.sqrt(sum(x * x for x in a) / len(a))

    print(f'final  /odom         : x={r[0]:.3f} y={r[1]:.3f} yaw={math.degrees(r[2]):.1f} deg')
    print(f'final  /odom_filtered: x={f[0]:.3f} y={f[1]:.3f} yaw={math.degrees(f[2]):.1f} deg')
    print(f'diferencia final     : dx={r[0] - f[0] - ox:.4f} m  dy={r[1] - f[1] - oy:.4f} m  '
          f'dyaw={math.degrees(wrap(r[2] - f[2] - oyaw)):.3f} deg')
    print(f'diferencia maxima    : |dx|={max(map(abs, dx)):.4f} m  |dy|={max(map(abs, dy)):.4f} m  '
          f'|dyaw|={math.degrees(max(map(abs, dyaw))):.3f} deg')
    print(f'diferencia RMS       : dx={rms(dx):.4f} m  dy={rms(dy):.4f} m  dyaw={math.degrees(rms(dyaw)):.3f} deg')
    print(f'muestras: {len(dx)}')
    rclpy.shutdown()


if __name__ == '__main__':
    main()
