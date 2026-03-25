"""
Conftest for yourdfpy tests.

Patches URDF.load so every test that loads a URDF also validates
that the full Robot survives a GLB roundtrip.
"""

import pytest

from yourdfpy import urdf
from yourdfpy.glb import from_glb


def _check_glb_roundtrip(urdf_model):
    """Assert full Robot survives a GLB export/import cycle."""
    glb_data = urdf_model.to_glb()
    assert isinstance(glb_data, bytes)
    assert len(glb_data) > 0
    reconstructed = from_glb(glb_data)
    assert len(reconstructed) == 1
    assert urdf_model.robot == reconstructed[0].robot


@pytest.fixture(autouse=True)
def glb_roundtrip_on_load(monkeypatch):
    """Wrap URDF.load so every call also runs a GLB roundtrip check."""
    original_load = urdf.URDF.load

    @staticmethod
    def load_and_check(*args, **kwargs):
        model = original_load(*args, **kwargs)
        _check_glb_roundtrip(model)
        return model

    monkeypatch.setattr(urdf.URDF, "load", load_and_check)
