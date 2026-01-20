from pecha_api.text_uploader.segments.segment_model import (
    ManifestationModel,
    Segment,
    SegmentModel,
)


def test_segment_models_validate_and_dump():
    model = SegmentModel(
        text_id="t1",
        segments=[
            Segment(content="a", type="source"),
            Segment(content="b", type="source"),
        ],
    )

    dumped = model.model_dump()
    assert dumped["text_id"] == "t1"
    assert dumped["segments"][0] == {"content": "a", "type": "source"}


def test_manifestation_model_defaults_none():
    model = ManifestationModel()
    assert model.job_id is None
    assert model.status is None
    assert model.message is None

