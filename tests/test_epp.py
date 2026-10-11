import xml.etree.ElementTree as ET
from datetime import datetime

import pytest

from eurid_epp.client import render_template
from tests.conftest import NS, result_code


def check_greeting(client):
    """Read the greeting and check the server id (as epp.robot does)."""
    sv_id = ET.fromstring(client.receive()).find(".//e:svID", NS).text
    assert sv_id == "eurid.eu"


def login(client, config):
    client.send(render_template("session/login.xml",
                                REGISTRAR_ALIAS=config["user"],
                                PASSWORD=config["pwd"]))
    response = client.receive()
    code = result_code(response)
    if code != "1000":
        print(response)
    assert code == "1000", response


@pytest.mark.smoke
def test_connect_to_epp_server_ipv4(connect):
    """Connect to the EPP server and read the greeting message"""
    client = connect()
    check_greeting(client)


@pytest.mark.smoke
def test_connect_to_epp_server_ipv6(connect):
    """Connect to the EPP server over IPv6 and read the greeting message"""
    client = connect(ipv6=True)
    check_greeting(client)


@pytest.mark.smoke
def test_successfully_login_to_epp_server_ipv4(connect, credentials):
    """Connect to the EPP server and login"""
    client = connect()
    check_greeting(client)
    login(client, credentials)


@pytest.mark.smoke
def test_successfully_login_to_epp_server_ipv6(connect, credentials):
    """Connect to the EPP server over IPv6 and login"""
    client = connect(ipv6=True)
    check_greeting(client)
    login(client, credentials)


@pytest.mark.smoke
def test_successfully_update_registrant_contact_in_epp_ipv4(connect, credentials):
    """Connect, login, read the registrant contact, rename it and put the original name back"""
    client = connect()
    check_greeting(client)
    login(client, credentials)

    contact = credentials["registrar_contact"]
    if not contact:
        pytest.skip("Please provide value for REGISTRAR_CONTACT in ENV_FILE")

    # Contact info
    client.send(render_template("contact/contact_info.xml", CONTACT_ALIAS=contact))
    response = client.receive()
    code = result_code(response)
    if code != "1000":
        print(response)
    assert code == "1000", response
    name = ET.fromstring(response).find(".//{*}postalInfo/{*}name").text

    # Contact update
    new_name = f"{name} - smoketest - {datetime.now():%Y%m%d %H:%M:%S}"
    client.send(render_template("contact/contact_update.xml",
                                CONTACT_ALIAS=contact, CONTACT_NAME=new_name))
    response = client.receive()
    code = result_code(response)
    if code != "1000":
        print(response)
    assert code == "1000", response

    # Put back original name
    client.send(render_template("contact/contact_update.xml",
                                CONTACT_ALIAS=contact, CONTACT_NAME=name))
    response = client.receive()
    code = result_code(response)
    if code != "1000":
        print(response)
    assert code == "1000", response
