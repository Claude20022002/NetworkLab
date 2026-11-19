"""subscriber_node : affiche ce qu'il recoit sur /sensor_data et /commands.

/sensor_data en BEST_EFFORT pour etre compatible avec le publisher.
En Partie B, la gouvernance restreint ce noeud a /sensor_data : on met alors
SUBSCRIBE_COMMANDS=false pour qu'il ne cree pas de reader /commands (interdit)."""
import os
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String
from geometry_msgs.msg import Twist

SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
)


class SubscriberNode(Node):
    def __init__(self):
        super().__init__('subscriber_node')
        self.create_subscription(String, '/sensor_data', self.on_sensor, SENSOR_QOS)
        if os.environ.get('SUBSCRIBE_COMMANDS', 'true').lower() != 'false':
            self.create_subscription(Twist, '/commands', self.on_cmd, 10)

    def on_sensor(self, msg):
        self.get_logger().info('sensor_data <- "%s"' % msg.data)

    def on_cmd(self, msg):
        self.get_logger().info('commands <- linear_x=%.2f angular_z=%.2f'
                               % (msg.linear.x, msg.angular.z))


def main():
    rclpy.init()
    rclpy.spin(SubscriberNode())


if __name__ == '__main__':
    main()
