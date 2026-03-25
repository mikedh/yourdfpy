"""Serialize and reconstruct URDF Robot models to/from GLB files."""

import io
from dataclasses import fields, is_dataclass

import numpy as np
import trimesh

from .urdf import (
    Actuator,
    Calibration,
    Collision,
    Color,
    Cylinder,
    Box,
    Dynamics,
    Geometry,
    Inertial,
    Joint,
    Limit,
    Link,
    Material,
    Mesh,
    Mimic,
    Robot,
    SafetyController,
    Sphere,
    Texture,
    Transmission,
    TransmissionJoint,
    URDF,
    Visual,
)

_REGISTRY: dict[str, type] = {
    cls.__name__: cls
    for cls in [
        Actuator,
        Calibration,
        Collision,
        Color,
        Cylinder,
        Box,
        Dynamics,
        Geometry,
        Inertial,
        Joint,
        Limit,
        Link,
        Material,
        Mesh,
        Mimic,
        Robot,
        SafetyController,
        Sphere,
        Texture,
        Transmission,
        TransmissionJoint,
        Visual,
    ]
}


def _to_dict(obj: object) -> object:
    """Serialize a dataclass tree to plain dicts, tagging types for reconstruction."""
    if is_dataclass(obj) and not isinstance(obj, type):
        result: dict = {"_type": type(obj).__name__}
        for f in fields(obj):
            result[f.name] = _to_dict(getattr(obj, f.name))
        return result
    if isinstance(obj, np.ndarray):
        return {"_ndarray": obj.tolist()}
    if isinstance(obj, list):
        return [_to_dict(v) for v in obj]
    return obj


def _from_dict(data: object) -> object:
    """Reconstruct a dataclass tree from tagged dicts produced by `_to_dict`."""
    if isinstance(data, dict):
        if "_ndarray" in data:
            return np.array(data["_ndarray"])
        if "_type" in data:
            target: type = _REGISTRY[data["_type"]]
            kwargs: dict = {k: _from_dict(v) for k, v in data.items() if k != "_type"}
            return target(**kwargs)
    if isinstance(data, list):
        return [_from_dict(v) for v in data]
    return data


def robot_to_dict(robot: Robot) -> dict:
    """Serialize a Robot to a dict suitable for GLTF extras."""
    return _to_dict(robot)


def from_glb(data: bytes) -> list[URDF]:
    """Load URDFs from a GLB that has Robot definitions in scene extras.

    Parameters
    ----------
    data
        GLB bytes (from URDF.to_glb()).

    Returns
    -------
    list[URDF]
        URDF models reconstructed from the GLB.
    """
    scene: trimesh.Scene = trimesh.load(io.BytesIO(data), file_type="glb")
    results: list[URDF] = []
    for rd in scene.metadata.get("robots", []):
        robot: Robot = _from_dict(rd)
        urdf: URDF = URDF(robot=robot, build_scene_graph=False, load_meshes=False)
        urdf._scene = scene
        results.append(urdf)
    return results
