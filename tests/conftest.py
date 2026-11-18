import json
from pathlib import Path

import pytest


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def nuscenes_fixture(tmp_path: Path) -> tuple[Path, dict[str, list[str]]]:
    root = tmp_path / "nuscenes"
    metadata = root / "v1.0-test-fixture"
    metadata.mkdir(parents=True)

    scenes = []
    samples = []
    sample_data = []
    annotations = []
    instances = []
    categories = [
        {"token": "category-car", "name": "vehicle.car"},
        {"token": "category-person", "name": "human.pedestrian.adult"},
    ]
    sensors = [
        {"token": "sensor-lidar", "channel": "LIDAR_TOP"},
        {"token": "sensor-camera", "channel": "CAM_FRONT"},
    ]
    calibrated = [
        {"token": "cal-lidar", "sensor_token": "sensor-lidar"},
        {"token": "cal-camera", "sensor_token": "sensor-camera"},
    ]
    ego_poses = []

    train_names = [f"scene-train-{index}" for index in range(4)]
    val_names = [f"scene-val-{index}" for index in range(2)]
    scene_names = train_names + val_names
    for scene_index, scene_name in enumerate(scene_names):
        scene_token = f"scene-token-{scene_index}"
        scenes.append(
            {
                "token": scene_token,
                "name": scene_name,
                "description": "Night rain" if scene_index == 0 else "Day drive",
            }
        )
        instances.extend(
            [
                {
                    "token": f"instance-car-{scene_index}",
                    "category_token": "category-car",
                },
                {
                    "token": f"instance-person-{scene_index}",
                    "category_token": "category-person",
                },
            ]
        )
        for frame_index in range(2):
            sample_token = f"sample-{scene_index}-{frame_index}"
            samples.append(
                {
                    "token": sample_token,
                    "scene_token": scene_token,
                    "timestamp": scene_index * 10_000 + frame_index,
                }
            )
            pose_token = f"pose-{scene_index}-{frame_index}"
            ego_poses.append({"token": pose_token, "translation": [0.0, 0.0, 0.0]})
            sample_data.append(
                {
                    "token": f"lidar-{sample_token}",
                    "sample_token": sample_token,
                    "calibrated_sensor_token": "cal-lidar",
                    "ego_pose_token": pose_token,
                    "filename": f"samples/LIDAR_TOP/{sample_token}.bin",
                    "is_key_frame": True,
                }
            )
            lidar_payload = root / f"samples/LIDAR_TOP/{sample_token}.bin"
            lidar_payload.parent.mkdir(parents=True, exist_ok=True)
            lidar_payload.touch()
            if not (scene_index == 0 and frame_index == 1):
                sample_data.append(
                    {
                        "token": f"camera-{sample_token}",
                        "sample_token": sample_token,
                        "calibrated_sensor_token": "cal-camera",
                        "ego_pose_token": pose_token,
                        "filename": f"samples/CAM_FRONT/{sample_token}.jpg",
                        "is_key_frame": True,
                    }
                )
                camera_payload = root / f"samples/CAM_FRONT/{sample_token}.jpg"
                camera_payload.parent.mkdir(parents=True, exist_ok=True)
                camera_payload.touch()
            annotations.extend(
                [
                    {
                        "token": f"ann-car-{sample_token}",
                        "sample_token": sample_token,
                        "instance_token": f"instance-car-{scene_index}",
                        "translation": [10.0, 0.0, 0.0],
                    },
                    {
                        "token": f"ann-person-{sample_token}",
                        "sample_token": sample_token,
                        "instance_token": f"instance-person-{scene_index}",
                        "translation": [45.0, 0.0, 0.0],
                    },
                ]
            )

    tables = {
        "scene.json": scenes,
        "sample.json": samples,
        "sample_data.json": sample_data,
        "sensor.json": sensors,
        "calibrated_sensor.json": calibrated,
        "sample_annotation.json": annotations,
        "instance.json": instances,
        "category.json": categories,
        "ego_pose.json": ego_poses,
    }
    for filename, value in tables.items():
        _write_json(metadata / filename, value)

    return root, {"train": train_names, "val": val_names}
