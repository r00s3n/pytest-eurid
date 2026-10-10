import xml.etree.ElementTree as ET

import pytest

from eurid_epp.client import EPPClient, render_template
from eurid_epp.config import load_config

NS = {"e": "urn:ietf:params:xml:ns:epp-1.0"}


@pytest.fixture(scope="session")
def config():
    cfg = load_config()
    if not cfg["host"]:
        pytest.skip("EPP_HOST not set in ENV_FILE")
    return cfg


@pytest.fixture
def credentials(config):
    if not config["user"] or not config["pwd"]:
        pytest.skip("Please provide values for EPP_USER & EPP_PWD in ENV_FILE")
    return config


def result_code(xml):
    return ET.fromstring(xml).find(".//e:result", NS).get("code")


@pytest.fixture
def connect(config):
    """Factory: returns a connected client (greeting not yet read); closes on teardown."""
    clients = []

    def _connect(ipv6=False):
        client = EPPClient(config["host"], config["port"], ipv6=ipv6)
        client.connect()
        clients.append(client)
        return client

    yield _connect
    for c in clients:
        c.close()


@pytest.fixture
def session(credentials, connect):
    """Connected client with greeting consumed and a successful login."""
    client = connect()
    client.receive()
    client.send(render_template("session/login.xml",
                                REGISTRAR_ALIAS=credentials["user"],
                                PASSWORD=credentials["pwd"]))
    response = client.receive()
    assert result_code(response) == "1000", response
    return client
