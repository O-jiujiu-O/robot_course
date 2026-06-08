#!/usr/bin/env python3
"""Reusable, bounded control API for the Gazebo mobile manipulator."""

import threading
from typing import Callable, Optional

import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64


AbortCheck = Optional[Callable[[], bool]]


class RobotControlAPI:
    LINEAR_LIMIT = 0.4
    ANGULAR_LIMIT = 0.8
    JOINT1_LIMIT = (-1.2, 1.2)
    JOINT2_LIMIT = (-1.5, 1.5)

    def __init__(self) -> None:
        self._cmd_vel = rospy.Publisher("/cmd_vel", Twist, queue_size=10)
        self._joint1 = rospy.Publisher(
            "/joint1_position_controller/command", Float64, queue_size=10
        )
        self._joint2 = rospy.Publisher(
            "/joint2_position_controller/command", Float64, queue_size=10
        )
        self._publish_lock = threading.Lock()
        rospy.on_shutdown(self.stop)
        rospy.sleep(0.5)

    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, float(value)))

    @staticmethod
    def _aborted(abort_check: AbortCheck) -> bool:
        return bool(abort_check and abort_check())

    def _timed_velocity(
        self,
        linear_x: float,
        angular_z: float,
        duration: float,
        abort_check: AbortCheck = None,
    ) -> bool:
        linear_x = self._clamp(linear_x, -self.LINEAR_LIMIT, self.LINEAR_LIMIT)
        angular_z = self._clamp(angular_z, -self.ANGULAR_LIMIT, self.ANGULAR_LIMIT)
        duration = max(0.0, float(duration))

        command = Twist()
        command.linear.x = linear_x
        command.angular.z = angular_z
        end_time = rospy.Time.now() + rospy.Duration(duration)
        rate = rospy.Rate(20)

        try:
            while not rospy.is_shutdown() and rospy.Time.now() < end_time:
                if self._aborted(abort_check):
                    rospy.logwarn("Motion aborted")
                    return False
                with self._publish_lock:
                    self._cmd_vel.publish(command)
                rate.sleep()
            return not self._aborted(abort_check)
        finally:
            self.stop()

    def move_forward(
        self, speed: float = 0.15, duration: float = 2.0, abort_check: AbortCheck = None
    ) -> bool:
        rospy.loginfo("move_forward speed=%.3f duration=%.2f", speed, duration)
        return self._timed_velocity(abs(speed), 0.0, duration, abort_check)

    def move_backward(
        self, speed: float = 0.15, duration: float = 2.0, abort_check: AbortCheck = None
    ) -> bool:
        rospy.loginfo("move_backward speed=%.3f duration=%.2f", speed, duration)
        return self._timed_velocity(-abs(speed), 0.0, duration, abort_check)

    def turn_left(
        self, speed: float = 0.4, duration: float = 1.5, abort_check: AbortCheck = None
    ) -> bool:
        rospy.loginfo("turn_left speed=%.3f duration=%.2f", speed, duration)
        return self._timed_velocity(0.0, abs(speed), duration, abort_check)

    def turn_right(
        self, speed: float = 0.4, duration: float = 1.5, abort_check: AbortCheck = None
    ) -> bool:
        rospy.loginfo("turn_right speed=%.3f duration=%.2f", speed, duration)
        return self._timed_velocity(0.0, -abs(speed), duration, abort_check)

    def stop(self) -> None:
        command = Twist()
        with self._publish_lock:
            for _ in range(3):
                self._cmd_vel.publish(command)

    def set_arm(
        self,
        joint1: float,
        joint2: float,
        wait_time: float = 1.0,
        abort_check: AbortCheck = None,
    ) -> bool:
        joint1 = self._clamp(joint1, *self.JOINT1_LIMIT)
        joint2 = self._clamp(joint2, *self.JOINT2_LIMIT)
        rospy.loginfo("set_arm joint1=%.3f joint2=%.3f", joint1, joint2)

        end_time = rospy.Time.now() + rospy.Duration(max(0.0, wait_time))
        rate = rospy.Rate(20)
        while not rospy.is_shutdown() and rospy.Time.now() < end_time:
            if self._aborted(abort_check):
                return False
            self._joint1.publish(Float64(joint1))
            self._joint2.publish(Float64(joint2))
            rate.sleep()
        return not self._aborted(abort_check)

    def arm_home(self, abort_check: AbortCheck = None) -> bool:
        return self.set_arm(0.0, 0.0, 1.2, abort_check)

    def arm_wave(self, cycles: int = 2, abort_check: AbortCheck = None) -> bool:
        cycles = max(1, min(5, int(cycles)))
        if not self.set_arm(0.35, -0.75, 0.8, abort_check):
            return False
        for _ in range(cycles):
            if not self.set_arm(0.85, -0.35, 0.6, abort_check):
                return False
            if not self.set_arm(-0.35, -0.85, 0.6, abort_check):
                return False
        return not self._aborted(abort_check)


def run_demo() -> None:
    rospy.init_node("robot_control_api_demo")
    robot = RobotControlAPI()
    rospy.loginfo("Starting bounded RobotControlAPI demonstration")
    robot.move_forward(0.15, 2.0)
    robot.turn_left(0.4, 1.5)
    robot.arm_wave(2)
    robot.arm_home()
    robot.stop()
    rospy.loginfo("RobotControlAPI demonstration completed")


if __name__ == "__main__":
    try:
        run_demo()
    except rospy.ROSInterruptException:
        pass
