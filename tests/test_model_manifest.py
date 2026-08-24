from portrait_relay.models import MODEL_REVISION, MODEL_SPECS, get_model_spec


def test_manifest_uses_immutable_revision_and_sha256() -> None:
    assert len(MODEL_REVISION) == 40
    assert MODEL_SPECS
    for name, spec in MODEL_SPECS.items():
        assert MODEL_REVISION in spec.url
        assert spec.url.startswith("https://huggingface.co/")
        assert len(spec.sha256) == 64
        assert spec.size > 0
        assert get_model_spec(name.replace("/", "\\")) == spec


def test_gpen_models_are_manual_only() -> None:
    gpen_specs = [spec for name, spec in MODEL_SPECS.items() if "GPEN" in name]

    assert gpen_specs
    assert all(spec.allow_download is False for spec in gpen_specs)
