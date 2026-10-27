from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_compose():
    return yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))


def environment_map(service):
    values = service["environment"]
    if isinstance(values, dict):
        return values
    return dict(item.split("=", 1) for item in values)


def test_compose_defines_exactly_two_symmetric_services():
    compose = load_compose()

    assert set(compose["services"]) == {"alice", "bob"}
    assert compose["services"]["alice"]["build"] == "."
    assert compose["services"]["bob"]["build"] == "."


def test_both_pages_are_published_on_distinct_host_ports():
    services = load_compose()["services"]

    assert services["alice"]["ports"] == ["8080:8000"]
    assert services["bob"]["ports"] == ["8081:8000"]


def test_services_use_dns_names_instead_of_fixed_ips():
    services = load_compose()["services"]
    alice_env = environment_map(services["alice"])
    bob_env = environment_map(services["bob"])

    assert alice_env["PEER_URL"] == "http://bob:8000"
    assert bob_env["PEER_URL"] == "http://alice:8000"
    assert alice_env["ROLE"] == "Alice"
    assert bob_env["ROLE"] == "Bob"
    assert "ipv4_address" not in services["alice"]
    assert "ipv4_address" not in services["bob"]


def test_both_services_share_only_the_private_quanta_network():
    compose = load_compose()
    services = compose["services"]

    assert services["alice"]["networks"] == ["quanta"]
    assert services["bob"]["networks"] == ["quanta"]
    assert compose["networks"]["quanta"]["driver"] == "bridge"
