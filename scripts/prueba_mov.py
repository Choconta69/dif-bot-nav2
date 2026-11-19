#!/usr/bin/env python3
"""Prueba de movimiento de dif_bot. Detecta el modo por el tipo de /cmd_vel."""
import time

import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data

V = 0.2       # m/s
T_PUB = 5.0   # s publicando
T_WAIT = 3.0  # s sin publicar


class Prueba(Node):
    def __init__(self):
        super().__init__('prueba_mov', parameter_overrides=[
            Parameter('use_sim_time', Parameter.Type.BOOL, True)])
        self.odom = None
        self.create_subscription(Odometry, '/odom', self._cb, qos_profile_sensor_data)

    def _cb(self, m):
        self.odom = (m.header.stamp.sec + m.header.stamp.nanosec * 1e-9,
                     m.pose.pose.position.x, m.twist.twist.linear.x)

    def spin_for(self, secs):
        end = time.time() + secs
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.02)

    def esperar(self, cond, secs, msg):
        end = time.time() + secs
        while time.time() < end and not cond():
            rclpy.spin_once(self, timeout_sec=0.1)
        if not cond():
            raise SystemExit(msg)

    def tipo_cmd_vel(self):
        infos = self.get_subscriptions_info_by_topic('/cmd_vel')
        return infos[0].topic_type if infos else None


def main():
    rclpy.init()
    n = Prueba()
    n.esperar(lambda: n.odom is not None, 20, 'ERROR: no llega /odom')
    n.esperar(lambda: n.tipo_cmd_vel() is not None, 20, 'ERROR: nadie escucha /cmd_vel')
    tipo = n.tipo_cmd_vel()
    stamped = tipo.endswith('TwistStamped')
    pub = n.create_publisher(TwistStamped if stamped else Twist, '/cmd_vel', 10)

    def cmd(v):
        if stamped:
            m = TwistStamped()
            m.header.stamp = n.get_clock().now().to_msg()
            m.twist.linear.x = v
        else:
            m = Twist()
            m.linear.x = v
        pub.publish(m)

    print(f'modo: {"ros2_control" if stamped else "plugin_gazebo"}  (tipo /cmd_vel: {tipo})')
    n.spin_for(1.0)
    t0, x0, _ = n.odom
    print(f'x inicial: {x0:.3f} m')

    fin = time.time() + T_PUB
    vs = []
    while time.time() < fin:
        cmd(V)
        n.spin_for(0.05)
        vs.append(n.odom[2])
    t1, x1, _ = n.odom

    n.spin_for(T_WAIT)  # sin publicar nada
    t2, x2, v2 = n.odom

    dt = t1 - t0
    mitad = vs[len(vs) // 2:]
    print(f'publicando {T_PUB:.0f} s reales = {dt:.2f} s de simulacion '
          f'(factor ~{dt / T_PUB:.2f})')
    print(f'distancia mientras publicaba: {x1 - x0:.3f} m  (esperado ~{V * dt:.2f} m)')
    print(f'velocidad media reportada (2a mitad): {sum(mitad) / len(mitad):.3f} m/s')
    print(f'{T_WAIT:.0f} s SIN publicar: velocidad = {v2:.3f} m/s, avance extra = {x2 - x1:.3f} m')
    print('veredicto: ' + ('SE DETIENE SOLO' if abs(v2) < 0.02 else 'NO SE DETIENE SOLO (mantiene la ultima orden)'))

    cmd(0.0)       # parada de seguridad
    n.spin_for(1.0)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
