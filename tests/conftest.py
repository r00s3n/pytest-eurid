import html
import urllib.request
import xml.dom.minidom
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
def connect(config, request):
    """Factory: returns a connected client (greeting not yet read); closes on teardown."""
    clients = []

    def _connect(ipv6=False):
        transcript = request.node.__dict__.setdefault("epp_transcript", [])
        client = EPPClient(config["host"], config["port"], ipv6=ipv6, transcript=transcript)
        client.connect()
        clients.append(client)
        return client

    yield _connect
    for c in clients:
        c.close()


def _pretty(xml_text):
    try:
        pretty = xml.dom.minidom.parseString(xml_text.encode()).toprettyxml(indent="  ")
        return "\n".join(line for line in pretty.splitlines() if line.strip())
    except Exception:
        return xml_text


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    # attach all EPP messages exchanged so far to the HTML report (setup phase included,
    # as pytest-html only shows details of the call phase for passing tests)
    transcript = item.__dict__.get("epp_transcript", [])
    if transcript:
        from pytest_html import extras

        parts = [f"<b>{html.escape(d)}</b>\n{html.escape(_pretty(x))}" for d, x in transcript]
        report.extras = getattr(report, "extras", []) + [
            extras.html("<pre>" + "\n\n".join(parts) + "</pre>")
        ]


def _public_ip(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.read().decode().strip()
    except Exception:
        return "not available"


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Show the public IPv4/IPv6 address of this computer in the report's environment table."""
    from pytest_metadata.plugin import metadata_key

    meta = config.stash[metadata_key]
    meta["Public IPv4"] = _public_ip("https://api.ipify.org")
    meta["Public IPv6"] = _public_ip("https://api6.ipify.org")
