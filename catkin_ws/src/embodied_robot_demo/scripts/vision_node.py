#!/usr/bin/env python3
"""Detect the largest red object in the Gazebo camera image."""

import cv2
import numpy as np
import rospy
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
from std_msgs.msg import Bool


class RedTargetDetector:
    def __init__(self) -> None:
        self.bridge = CvBridge()
        self.minimum_area = float(rospy.get_param("~minimum_area", 800.0))
        self.show_window = bool(rospy.get_param("~show_window", True))
        self.detected_pub = rospy.Publisher("/vision/red_target", Bool, queue_size=10)
        self.image_sub = rospy.Subscriber(
            "/camera/image_raw", Image, self.on_image, queue_size=1, buff_size=2**24
        )
        rospy.loginfo(
            "Red target detector ready; minimum_area=%.1f show_window=%s",
            self.minimum_area,
            self.show_window,
        )

    def on_image(self, message: Image) -> None:
        try:
            frame = self.bridge.imgmsg_to_cv2(message, desired_encoding="bgr8")
        except CvBridgeError as error:
            rospy.logerr_throttle(5.0, "cv_bridge conversion failed: %s", error)
            return

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_red_1 = np.array([0, 100, 80], dtype=np.uint8)
        upper_red_1 = np.array([10, 255, 255], dtype=np.uint8)
        lower_red_2 = np.array([170, 100, 80], dtype=np.uint8)
        upper_red_2 = np.array([180, 255, 255], dtype=np.uint8)
        mask = cv2.bitwise_or(
            cv2.inRange(hsv, lower_red_1, upper_red_1),
            cv2.inRange(hsv, lower_red_2, upper_red_2),
        )

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected = False
        largest_area = 0.0
        if contours:
            largest = max(contours, key=cv2.contourArea)
            largest_area = float(cv2.contourArea(largest))
            if largest_area >= self.minimum_area:
                detected = True
                x, y, width, height = cv2.boundingRect(largest)
                cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)

        label = "RED TARGET: {} area={:.0f}".format(
            "FOUND" if detected else "NOT FOUND", largest_area
        )
        cv2.putText(frame, label, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        self.detected_pub.publish(Bool(detected))

        if self.show_window:
            cv2.imshow("red_target_detector", frame)
            cv2.waitKey(1)


def main() -> None:
    rospy.init_node("vision_node")
    RedTargetDetector()
    rospy.spin()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
