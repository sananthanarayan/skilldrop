from unittest import mock

from src.ingest import reader


class FakePayload:
    def chunks(self):
        return [b"a", b"b"]


def test_read_stream_yields_chunks():
    fake_client = mock.Mock()
    fake_client.fetch.return_value = FakePayload()
    with mock.patch("quillstream.Client", return_value=fake_client):
        assert list(reader.read_stream("qs://example/feed")) == [b"a", b"b"]
