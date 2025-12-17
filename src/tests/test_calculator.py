from pathlib import Path

from gateway.core.calculator import Calculator


def test_calculator_ldap_rules_with_globals():
    # Localise le fichier de règles depuis la racine du projet
    root = Path(__file__).resolve().parents[1]
    rules_path = root / "config" / "rules.yaml"

    calc = Calculator.from_file(rules_path)

    attrs = {
        "firstname": "Jean",
        "lastname": "Dupont",
        "email": "j.dupont@sae.com",
    }

    out = calc.calculate(source_attributes=attrs, account_id="jdupont", targets=["LDAP"])  # restreint à LDAP

    assert "LDAP" in out
    ldap = out["LDAP"]

    # Vérifie rendu multi-pass (mail/dn dépendent de login)
    assert ldap["login"] == "jean.dupont"
    assert ldap["cn"] == "Jean Dupont"
    assert ldap["mail"] == "jean.dupont@sae.com"  # global.domain
    assert ldap["dn"].lower() == "uid=jean.dupont,dc=sae,dc=com"


def test_calculator_limits_to_requested_targets():
    root = Path(__file__).resolve().parents[1]
    rules_path = root / "config" / "rules.yaml"

    calc = Calculator.from_file(rules_path)

    attrs = {"firstname": "Alice", "lastname": "Martin", "email": "a.martin@sae.com"}
    out = calc.calculate(source_attributes=attrs, account_id="amartin", targets=["SQL"])  # seulement SQL

    assert set(out.keys()) == {"SQL"}
    sql = out["SQL"]
    assert sql["username"] == "amartin"
    assert sql["role"] == "APP_USER"
