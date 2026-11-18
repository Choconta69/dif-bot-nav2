# dif_bot

Robot diferencial (IMU, lidar 2D y camara de profundidad opcional) para simulacion en Gazebo con ROS 2 Kilted.
Soporta dos modos de control sobre el mismo URDF: plugin `DiffDrive` de Gazebo o `ros2_control`.
Proyecto final de Robotica Movil Autonoma (Escuela Colombiana de Ingenieria Julio Garavito).

## Uso
```bash
colcon build --symlink-install --packages-select dif_bot && source install/setup.bash

# Modo 1: plugin DiffDrive de Gazebo
ros2 launch dif_bot sim.launch.py use_ros2_control:=false
# Modo 2: ros2_control (diff_drive_controller)
ros2 launch dif_bot sim.launch.py use_ros2_control:=true

# Teleoperacion
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
Argumentos: `use_camera` (false), `gui` (false: Gazebo solo servidor), `rviz` (true), `world`.

## Estructura
- `dif_bot/urdf/robot.urdf.xacro`: robot e interruptores `use_ros2_control` y `use_camera`.
- `dif_bot/urdf/gz_control.xacro` y `ros2_control.xacro`: los dos modos de control.
- `dif_bot/urdf/sensors.xacro`: IMU, lidar y camara (esta ultima condicional).
- `dif_bot/config/`: bridges `ros_gz_bridge` y controladores de `ros2_control`.
- `dif_bot/worlds/dif_bot_world.sdf`: sala de 8 x 6 m con tres obstaculos.

## Cambios respecto al robot del laboratorio anterior
- `wheel_separation` corregido de 0.4 a **0.36 m** (las ruedas estan en y = +-0.18 m).
- Sensores con `gz_frame_id` para que los mensajes lleguen con el frame del URDF (`lidar_link`, `imu_link`).
- Camara opcional y de menor resolucion (320x240 a 15 Hz); `visualize` desactivado en los sensores.
- Sistemas `Sensors` e `Imu` movidos al mundo, donde corresponden.
