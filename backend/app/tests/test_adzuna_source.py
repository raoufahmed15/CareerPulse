from app.services.adzuna_job_source import AdzunaJobSource


def test_adzuna_source_name():
    source = AdzunaJobSource()

    assert source.name == "adzuna"