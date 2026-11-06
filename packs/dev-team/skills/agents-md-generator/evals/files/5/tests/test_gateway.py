import socket

import pytest


@pytest.mark.hardware
def test_gateway_responds():
    with socket.create_connection(("10.20.0.15", 5020), timeout=300) as s:
        s.sendall(b"PING\n")
        assert s.recv(4) == b"PONG"
