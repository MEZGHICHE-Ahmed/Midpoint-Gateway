"""Tests des modèles de données."""

import pytest
from datetime import datetime
from gateway.core.models import (
    OperationType,
    ProvisionRequest,
    TargetResult,
    ProvisionResult,
    RulesConfig,
)


def test_provision_request_creation():
    """Test création d'une ProvisionRequest valide."""
    req = ProvisionRequest(
        operation=OperationType.CREATE,
        targetSystems=["AD", "SQL"],
        accountId="jdupont",
        sourceAttributes={
            "firstname": "Jean",
            "lastname": "Dupont",
            "email": "j.dupont@example.com",
        },
    )
    
    assert req.operation == OperationType.CREATE
    assert req.accountId == "jdupont"
    assert req.sourceAttributes["firstname"] == "Jean"
    assert len(req.targetSystems) == 2


def test_target_result_creation():
    """Test création d'un TargetResult."""
    result = TargetResult(
        target="AD",
        operation=OperationType.CREATE,
        status="SUCCESS",
        calculatedAttributes={"login": "jean.dupont"},
        message="User created",
        duration_ms=150.5,
    )
    
    assert result.target == "AD"
    assert result.status == "SUCCESS"
    assert result.calculatedAttributes["login"] == "jean.dupont"


def test_provision_result_creation():
    """Test création d'une ProvisionResult."""
    target_results = [
        TargetResult(
            target="AD",
            operation=OperationType.CREATE,
            status="SUCCESS",
            calculatedAttributes={"login": "jean.dupont"},
            message="User created",
            duration_ms=100.0,
        ),
        TargetResult(
            target="SQL",
            operation=OperationType.CREATE,
            status="SUCCESS",
            calculatedAttributes={"username": "jdupont"},
            message="User created",
            duration_ms=50.0,
        ),
    ]
    
    result = ProvisionResult(
        status="SUCCESS",
        calculatedAttributes={
            "AD": {"login": "jean.dupont"},
            "SQL": {"username": "jdupont"},
        },
        targetResults=target_results,
        message="Provisioning done in AD and SQL",
        timestamp=datetime.now(),
    )
    
    assert result.status == "SUCCESS"
    assert len(result.targetResults) == 2
    assert "AD" in result.calculatedAttributes


def test_rules_config_creation():
    """Test création d'une RulesConfig."""
    config = RulesConfig(
        targets={
            "AD": {
                "rules": {
                    "login": "${firstname}.${lastname}",
                    "email": "${email}",
                }
            },
            "SQL": {
                "rules": {
                    "username": "${accountId}",
                    "role": "APP_USER",
                }
            },
        }
    )
    
    assert "AD" in config.targets
    assert "SQL" in config.targets
    assert config.targets["AD"]["rules"]["login"] == "${firstname}.${lastname}"
