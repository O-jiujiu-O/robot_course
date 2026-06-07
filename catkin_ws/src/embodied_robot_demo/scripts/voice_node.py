#!/usr/bin/env python3
"""Offline Chinese command recognition using Vosk and a microphone."""

import json
import os
import queue
import sys

import rospy
from std_msgs.msg import String


KNOWN_COMMANDS = (
    "开始任务",
    "停止",
    "前进",
    "后退",
    "左转",
    "右转",
    "挥手",
)


def normalize_command(text: str) -> str:
    compact = text.replace(" ", "")
    aliases = {
        "开始": "开始任务",
        "启动任务": "开始任务",
        "停下": "停止",
        "停车": "停止",
        "向前": "前进",
        "向后": "后退",
    }
    for command in KNOWN_COMMANDS:
        if command in compact:
            return command
    for alias, command in aliases.items():
        if alias in compact:
            return command
    return ""


def main() -> None:
    rospy.init_node("voice_node")
    command_pub = rospy.Publisher("/voice/command", String, queue_size=10)
    model_path = os.path.expanduser(
        rospy.get_param("~model_path", "~/robot_course/vosk-model-cn")
    )
    sample_rate = int(rospy.get_param("~sample_rate", 16000))
    device = rospy.get_param("~device", None)

    try:
        import sounddevice as sd
        from vosk import KaldiRecognizer, Model
    except ImportError as error:
        rospy.logfatal(
            "Voice dependencies are missing: %s. Activate the dedicated voice venv "
            "and install vosk and sounddevice.",
            error,
        )
        sys.exit(2)

    if not os.path.isdir(model_path):
        rospy.logfatal("Vosk model directory does not exist: %s", model_path)
        sys.exit(2)

    audio_queue = queue.Queue()

    def audio_callback(indata, frames, time_info, status) -> None:
        del frames, time_info
        if status:
            rospy.logwarn_throttle(2.0, "Microphone status: %s", status)
        audio_queue.put(bytes(indata))

    model = Model(model_path)
    recognizer = KaldiRecognizer(model, sample_rate)
    rospy.loginfo("Voice node ready; commands: %s", ", ".join(KNOWN_COMMANDS))

    try:
        with sd.RawInputStream(
            samplerate=sample_rate,
            blocksize=8000,
            device=device,
            dtype="int16",
            channels=1,
            callback=audio_callback,
        ):
            while not rospy.is_shutdown():
                try:
                    audio = audio_queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                if recognizer.AcceptWaveform(audio):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "")
                    command = normalize_command(text)
                    if command:
                        rospy.loginfo("Voice recognized: %s -> %s", text, command)
                        command_pub.publish(String(command))
                    elif text:
                        rospy.loginfo("Ignored speech: %s", text)
    except Exception as error:
        rospy.logfatal("Voice input failed: %s", error)
        sys.exit(3)


if __name__ == "__main__":
    main()

