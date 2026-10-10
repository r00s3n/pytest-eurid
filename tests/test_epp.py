import xml.etree.ElementTree as ET
from datetime import datetime

import pytest

from eurid_epp.client import render_template
from tests.conftest import NS, result_code


def greeting_sv_id(client):
    return ET.fromstring(client.receive()).find(".//e:svID", NS).text


@pytest.mark.smoke
def test_connect_ipv4(connect):
    assert greeting_sv_id(connect()) == "eurid.eu"


@pytest.mark.no_ipv6_available_in_office
def test_connect_ipv6(connect):
    assert greeting_sv_id(connect(ipv6=True)) == "eurid.eu"


@pytest.mark.smoke
def test_login_ipv4(session):
    # the session fixture asserts a 1000 login response
    pass


@pytest.mark.smoke
def test_update_registrant_contact_ipv4(session, config):
    contact = config["registrar_contact"]
    if not contact:
        pytest.skip("Please provide value for REGISTRAR_CONTACT in ENV_FILE")

    session.send(render_template("contact/contact_info.xml", CONTACT_ALIAS=contact))
    response = session.receive()
    assert result_code(response) == "1000", response
    name = ET.fromstring(response).find(".//{*}postalInfo/{*}name").text

    new_name = f"{name} - smoketest - {datetime.now():%Y%m%d %H:%M:%S}"
    try:
        session.send(render_template("contact/contact_update.xml",
                                     CONTACT_ALIAS=contact, CONTACT_NAME=new_name))
        response = session.receive()
        assert result_code(response) == "1000", response
    finally:
        # put the original name back
        session.send(render_template("contact/contact_update.xml",
                                     CONTACT_ALIAS=contact, CONTACT_NAME=name))
        restore = session.receive()
    assert result_code(restore) == "1000", restore
