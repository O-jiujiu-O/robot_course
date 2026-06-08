#!/usr/bin/env python3
"""Coordinate voice commands, visual detection, base motion, and arm motion."""

import threading
from typing import Callable

import rospy
from std_msgs.msg import Bool, String

from robot_control_api import RobotControlAPI


class TaskOrchestrator:
    def __init__(self) -> None:
        self.robot = RobotControlAPI()
        self.vision_timeout = float(rospy.get_param("~vision_timeout", 10.0))
        self.target_visible = False
        self.target_update_time = rospy.Time(0)
        self.abort_event = threading.Event()
        self.execution_lock = threading.Lock()
        self.status_pub = rospy.Publisher("/task/status", String, queue_size=10, latch=True)
        self.vision_sub = rospy.Subscriber("/vision/red_target", Bool, self.on_vision)
        self.voice_sub = rospy.Subscriber("/voice/command", String, self.on_command)
        self.publish_status("IDLE")

        if bool(rospy.get_param("~auto_start", False)):
            rospy.Timer(rospy.Duration(3.0), self.auto_start, oneshot=True)

    def publish_status(self, status: str) -> None:
        rospy.loginfo("Task status: %s", status)
        self.status_pub.publish(String(status))

    def on_vision(self, message: Bool) -> None:
        self.target_visible = bool(message.data)
        self.target_update_time = rospy.Time.now()

    def auto_start(self, _event) -> None:
        self.start_worker(self.run_main_task)

    def on_command(self, message: String) -> None:
        command = message.data.strip()
        rospy.loginfo("Received command: %s", command)

        if command == "停止":
            self.abort_event.set()
            self.robot.stop()
            self.publish_status("TASK_ABORTED")
            return

        command_actions = {
            "开始任务": self.run_main_task,
            "前进": lambda: self.run_single_action(
                "MOVE_FORWARD", lambda: self.robot.move_forward(0.15, 2.0, self.is_aborted)
            ),
            "后退": lambda: self.run_single_action(
                "MOVE_BACKWARD", lambda: self.robot.move_backward(0.15, 2.0, self.is_aborted)
            ),
            "左转": lambda: self.run_single_action(
                "TURN_LEFT", lambda: self.robot.turn_left(0.4, 1.5, self.is_aborted)
            ),
            "右转": lambda: self.run_single_action(
                "TURN_RIGHT", lambda: self.robot.turn_right(0.4, 1.5, self.is_aborted)
            ),
            "挥手": lambda: self.run_single_action(
                "ARM_WAVE", lambda: self.robot.arm_wave(2, self.is_aborted)
            ),
        }
        action = command_actions.get(command)
        if action is None:
            rospy.logwarn("Unknown command ignored: %s", command)
            return
        self.start_worker(action)

    def start_worker(self, action: Callable[[], None]) -> None:
        if self.execution_lock.locked():
            rospy.logwarn("A task is already running; command ignored")
            return
        self.abort_event.clear()
        threading.Thread(target=self.run_locked, args=(action,), daemon=True).start()

    def run_locked(self, action: Callable[[], None]) -> None:
        with self.execution_lock:
            try:
                action()
            except Exception as error:
                self.robot.stop()
                self.publish_status("TASK_ERROR")
                rospy.logerr("Task failed: %s", error)

    def is_aborted(self) -> bool:
        return self.abort_event.is_set() or rospy.is_shutdown()

    def run_single_action(self, status: str, action: Callable[[], bool]) -> None:
        self.publish_status(status)
        succeeded = action()
        if self.is_aborted() or not succeeded:
            self.publish_status("TASK_ABORTED")
        else:
            self.publish_status("TASK_COMPLETED")

    def wait_for_target(self) -> bool:
        deadline = rospy.Time.now() + rospy.Duration(self.vision_timeout)
        rate = rospy.Rate(20)
        while not self.is_aborted() and rospy.Time.now() < deadline:
            reading_is_fresh = (rospy.Time.now() - self.target_update_time) < rospy.Duration(1.0)
            if self.target_visible and reading_is_fresh:
                return True
            rate.sleep()
        return False

    def run_main_task(self) -> None:
        self.publish_status("WAITING_FOR_VISION")
        if not self.wait_for_target():
            if self.is_aborted():
                self.publish_status("TASK_ABORTED")
            else:
                self.publish_status("TARGET_NOT_FOUND")
            return

        self.publish_status("TARGET_FOUND")
        if not self.robot.move_forward(0.15, 2.0, self.is_aborted):
            self.publish_status("TASK_ABORTED")
            return
        self.robot.stop()

        if not self.robot.arm_wave(2, self.is_aborted):
            self.publish_status("TASK_ABORTED")
            return
        self.robot.arm_home(self.is_aborted)
        self.publish_status("TASK_ABORTED" if self.is_aborted() else "TASK_COMPLETED")


def main() -> None:
    rospy.init_node("task_orchestrator")
    orchestrator = TaskOrchestrator()
    rospy.on_shutdown(orchestrator.robot.stop)
    rospy.spin()


if __name__ == "__main__":
    main()
