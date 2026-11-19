"""publisher_node : simule un robot qui publie /sensor_data et /commands.

Deux modes (variable d'environnement ROBOT_MODE) pour la Partie B / fingerprinting :
  - navigating (defaut) : flux dense et IRREGULIER (capteur ~20 Hz avec gigue,
    commandes 2 Hz) -> imite un robot en deplacement (scans LiDAR, consignes).
  - idle              : flux rare et REGULIER (statut 1 Hz) -> robot a l'arret.

/sensor_data est en QoS BEST_EFFORT (choix naturel d'un flux capteur) : cela
reflete un robot reel et rend l'injection reseau de la Partie A observable
cote subscriber. /commands reste en RELIABLE (defaut)."""
import os
import random
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


class PublisherNode(Node):
    def __init__(self):
        super().__init__('publisher_node')
        self.mode = os.environ.get('ROBOT_MODE', 'navigating').lower()
        # En Partie B, le noeud capteur est restreint par la gouvernance a /sensor_data
        # (PUBLISH_COMMANDS=false) : il ne publie donc PAS /commands.
        self.pub_commands = os.environ.get('PUBLISH_COMMANDS', 'true').lower() != 'false'
        self.sensor_pub = self.create_publisher(String, '/sensor_data', SENSOR_QOS)
        if self.pub_commands:
            self.cmd_pub = self.create_publisher(Twist, '/commands', 10)

        if self.mode == 'idle':
            # Robot a l'arret : un statut regulier a 1 Hz, pas de commandes.
            self.create_timer(1.0, self.publish_sensor)
        else:
            # Robot en deplacement : capteur dense et irregulier + commandes.
            self.create_timer(0.05, self.publish_sensor_jitter)  # 20 Hz moyen, irregulier
            if self.pub_commands:
                self.create_timer(0.5, self.publish_command)     # 2 Hz
        self.get_logger().info('publisher_node mode="%s" commands=%s'
                               % (self.mode, self.pub_commands))

    def _sensor_msg(self):
        msg = String()
        # Largeur fixe "temperature: 24.5, pressure: 1012.9" (valeurs sur 4 et 6 car.)
        msg.data = 'temperature: %.1f, pressure: %.1f' % (
            24.5 + random.uniform(-0.2, 0.2), 1013.2 + random.uniform(-0.5, 0.5))
        return msg

    def publish_sensor(self):
        self.sensor_pub.publish(self._sensor_msg())

    def publish_sensor_jitter(self):
        # Publie avec probabilite -> espacement inter-paquets irregulier (gigue).
        if random.random() < 0.6:
            self.sensor_pub.publish(self._sensor_msg())

    def publish_command(self):
        cmd = Twist()
        cmd.linear.x = 0.5
        cmd.angular.z = 0.1
        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    rclpy.spin(PublisherNode())


if __name__ == '__main__':
    main()
