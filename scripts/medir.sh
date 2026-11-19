#!/bin/bash
source /opt/ros/kilted/setup.bash; source ~/nav_ws/install/setup.bash
OUT=~/medicion_$(date +%H%M%S).txt
{
echo "== hora: $(date)"
echo "== modo: $(timeout 8 ros2 control list_controllers 2>/dev/null | grep -q diff_drive && echo ros2_control || echo plugin_gazebo)"
echo "== nodos que publican /odom:"; ros2 topic info /odom -v | grep -E "Node name|Endpoint type"
echo "== estadisticas de Gazebo:"; timeout 8 gz topic -e -t /stats -n 1
echo "== frecuencia /odom (20 s):"; timeout 20 ros2 topic hz /odom --window 100 2>&1 | tail -3
echo "== top:"; top -b -n 1 | head -15
} 2>&1 | tee $OUT
echo "guardado en $OUT"
