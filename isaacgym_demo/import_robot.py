#!/usr/bin/env python3
"""Import the course robot into Isaac Gym and demonstrate physical parameters."""

import math
import os

import numpy as np
from isaacgym import gymapi, gymutil


CUSTOM_PARAMETERS = [
    {"name": "--friction", "type": float, "default": 1.0, "help": "Rigid shape friction"},
    {"name": "--stiffness", "type": float, "default": 200.0, "help": "Arm DOF stiffness"},
    {"name": "--damping", "type": float, "default": 20.0, "help": "Arm DOF damping"},
    {"name": "--duration", "type": float, "default": 20.0, "help": "Headless run duration"},
    {"name": "--num_envs", "type": int, "default": 1, "help": "Number of parallel environments"},
]


def main() -> None:
    args = gymutil.parse_arguments(
        description="Embodied robot URDF import and physical parameter demo",
        custom_parameters=CUSTOM_PARAMETERS,
    )
    gym = gymapi.acquire_gym()

    sim_params = gymapi.SimParams()
    sim_params.dt = 1.0 / 60.0
    sim_params.substeps = 2
    sim_params.up_axis = gymapi.UP_AXIS_Z
    sim_params.gravity = gymapi.Vec3(0.0, 0.0, -9.81)
    sim_params.use_gpu_pipeline = args.use_gpu_pipeline
    sim_params.physx.use_gpu = args.use_gpu
    sim_params.physx.solver_type = 1
    sim_params.physx.num_position_iterations = 4
    sim_params.physx.num_velocity_iterations = 1

    graphics_device_id = -1 if args.headless else args.graphics_device_id
    sim = gym.create_sim(
        args.compute_device_id, graphics_device_id, gymapi.SIM_PHYSX, sim_params
    )
    if sim is None:
        raise RuntimeError("Failed to create Isaac Gym simulation")

    plane = gymapi.PlaneParams()
    plane.normal = gymapi.Vec3(0.0, 0.0, 1.0)
    plane.static_friction = args.friction
    plane.dynamic_friction = max(0.0, args.friction * 0.8)
    gym.add_ground(sim, plane)

    asset_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    asset_file = "embodied_robot.urdf"
    asset_options = gymapi.AssetOptions()
    asset_options.fix_base_link = False
    asset_options.collapse_fixed_joints = True
    asset_options.disable_gravity = False
    asset_options.default_dof_drive_mode = gymapi.DOF_MODE_NONE
    asset_options.armature = 0.01
    asset_options.thickness = 0.002

    asset = gym.load_asset(sim, asset_root, asset_file, asset_options)
    if asset is None:
        raise RuntimeError("Failed to load {}".format(os.path.join(asset_root, asset_file)))

    rigid_body_count = gym.get_asset_rigid_body_count(asset)
    dof_count = gym.get_asset_dof_count(asset)
    dof_names = gym.get_asset_dof_names(asset)
    print("Loaded asset:", asset_file)
    print("Rigid bodies:", rigid_body_count)
    print("DOFs:", dof_count)
    print("DOF names:", dof_names)
    print(
        "Parameters: dt={:.5f}, substeps={}, friction={:.3f}, stiffness={:.1f}, damping={:.1f}".format(
            sim_params.dt, sim_params.substeps, args.friction, args.stiffness, args.damping
        )
    )

    dof_properties = gym.get_asset_dof_properties(asset)
    arm_indices = []
    for index, name in enumerate(dof_names):
        if name.startswith("arm_joint_"):
            arm_indices.append(index)
            dof_properties["driveMode"][index] = gymapi.DOF_MODE_POS
            dof_properties["stiffness"][index] = args.stiffness
            dof_properties["damping"][index] = args.damping
        elif name.endswith("_wheel_joint"):
            dof_properties["driveMode"][index] = gymapi.DOF_MODE_VEL
            dof_properties["stiffness"][index] = 0.0
            dof_properties["damping"][index] = 5.0

    envs = []
    actors = []
    spacing = 2.0
    env_lower = gymapi.Vec3(-spacing, -spacing, 0.0)
    env_upper = gymapi.Vec3(spacing, spacing, spacing)
    envs_per_row = max(1, int(math.sqrt(args.num_envs)))

    for env_index in range(max(1, args.num_envs)):
        env = gym.create_env(sim, env_lower, env_upper, envs_per_row)
        pose = gymapi.Transform()
        pose.p = gymapi.Vec3(0.0, 0.0, 0.02)
        actor = gym.create_actor(env, asset, pose, "embodied_robot_{}".format(env_index), env_index, 1)
        gym.set_actor_dof_properties(env, actor, dof_properties)

        shape_properties = gym.get_actor_rigid_shape_properties(env, actor)
        for shape_property in shape_properties:
            shape_property.friction = args.friction
            shape_property.rolling_friction = 0.02
            shape_property.torsion_friction = 0.02
        gym.set_actor_rigid_shape_properties(env, actor, shape_properties)
        envs.append(env)
        actors.append(actor)

    viewer = None
    if not args.headless:
        viewer = gym.create_viewer(sim, gymapi.CameraProperties())
        if viewer is None:
            raise RuntimeError("Failed to create viewer")
        camera_position = gymapi.Vec3(3.0, -3.0, 2.2)
        camera_target = gymapi.Vec3(0.0, 0.0, 0.5)
        gym.viewer_camera_look_at(viewer, envs[0], camera_position, camera_target)

    targets = np.zeros(dof_count, dtype=np.float32)
    gym.prepare_sim(sim)
    print("Simulation started; arm DOFs will follow sinusoidal position targets")

    while True:
        if viewer is not None and gym.query_viewer_has_closed(viewer):
            break

        simulation_time = gym.get_sim_time(sim)
        if args.headless and simulation_time >= args.duration:
            break

        if arm_indices:
            targets[arm_indices[0]] = 0.65 * math.sin(simulation_time * 1.2)
        if len(arm_indices) > 1:
            targets[arm_indices[1]] = -0.75 + 0.40 * math.sin(simulation_time * 1.8)
        for env, actor in zip(envs, actors):
            gym.set_actor_dof_position_targets(env, actor, targets)

        gym.simulate(sim)
        gym.fetch_results(sim, True)
        if viewer is not None:
            gym.step_graphics(sim)
            gym.draw_viewer(viewer, sim, True)
            gym.sync_frame_time(sim)

    if viewer is not None:
        gym.destroy_viewer(viewer)
    gym.destroy_sim(sim)
    print("Simulation completed")


if __name__ == "__main__":
    main()
