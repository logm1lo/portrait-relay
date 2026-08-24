"""Immutable model manifest for bundled download workflows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

MODEL_REPOSITORY = "hacksider/deep-live-cam"
MODEL_REVISION = "581e70b61240b7928404c17900437f47cfe94133"


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """Integrity and policy data for one downloadable model file."""

    name: str
    size: int
    sha256: str
    license_note: str
    source: str = MODEL_REPOSITORY
    revision: str = MODEL_REVISION
    allow_download: bool = True

    @property
    def url(self) -> str:
        """Return an immutable Hugging Face revision URL."""

        return f"https://huggingface.co/{self.source}/resolve/{self.revision}/{self.name}"


_INSIGHTFACE = "InsightFace model; noncommercial research use only"
_GFPGAN = "GFPGAN model; third-party model terms apply"
_GPEN = "GPEN weight provenance requires manual verification"

MODEL_SPECS: Mapping[str, ModelSpec] = MappingProxyType(
    {
        spec.name: spec
        for spec in (
            ModelSpec(
                "inswapper_128.onnx",
                554253681,
                "e4a3f08c753cb72d04e10aa0f7dbe3deebbf39567d4ead6dce08e98aa49e16af",
                _INSIGHTFACE,
            ),
            ModelSpec(
                "inswapper_128_fp16.onnx",
                277680638,
                "6d51a9278a1f650cffefc18ba53f38bf2769bf4bbff89267822cf72945f8a38b",
                _INSIGHTFACE,
            ),
            ModelSpec(
                "gfpgan-1024.onnx",
                365875079,
                "ee8dd6415e388b3a410689d5d9395a2bf50b5973b588421ebfa57bc266f19e24",
                _GFPGAN,
            ),
            ModelSpec(
                "GPEN-BFR-256.onnx",
                75715262,
                "aa5bd3ab238640a378c59e4a560f7a7150627944cf2129e6311ae4720e833271",
                _GPEN,
                allow_download=False,
            ),
            ModelSpec(
                "GPEN-BFR-512.onnx",
                284244491,
                "bf80acb8e91ba8852e3f012505be2c3b6cd6b3eed5ec605e3db87863c4e74d4e",
                _GPEN,
                allow_download=False,
            ),
            ModelSpec(
                "buffalo_l/buffalo_l/1k3d68.onnx",
                143607619,
                "df5c06b8a0c12e422b2ed8947b8869faa4105387f199c477af038aa01f9a45cc",
                _INSIGHTFACE,
            ),
            ModelSpec(
                "buffalo_l/buffalo_l/2d106det.onnx",
                5030888,
                "f001b856447c413801ef5c42091ed0cd516fcd21f2d6b79635b1e733a7109dbf",
                _INSIGHTFACE,
            ),
            ModelSpec(
                "buffalo_l/buffalo_l/det_10g.onnx",
                16923827,
                "5838f7fe053675b1c7a08b633df49e7af5495cee0493c7dcf6697200b85b5b91",
                _INSIGHTFACE,
            ),
            ModelSpec(
                "buffalo_l/buffalo_l/genderage.onnx",
                1322532,
                "4fde69b1c810857b88c64a335084f1c3fe8f01246c9a191b48c7bb756d6652fb",
                _INSIGHTFACE,
            ),
            ModelSpec(
                "buffalo_l/buffalo_l/w600k_r50.onnx",
                174383860,
                "4c06341c33c2ca1f86781dab0e829f88ad5b64be9fba56e56bc9ebdefc619e43",
                _INSIGHTFACE,
            ),
        )
    }
)


def get_model_spec(name: str) -> ModelSpec | None:
    """Return the normalized model specification if it is approved."""

    return MODEL_SPECS.get(name.replace("\\", "/"))
