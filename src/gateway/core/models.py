"""Modèles de données pour le provisionnement."""

from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class OperationType(str, Enum):
    """Types d'opérations supportées."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ProvisionRequest(BaseModel):
    """
    Requête de provisionnement reçue de MidPoint.
    
    Exemple:
        {
            "operation": "create",
            "targetSystems": ["AD", "SQL", "ODOO"],
            "accountId": 1,
            "sourceAttributes": {
                "firstname": "Jean",
                "lastname": "Dupont",
                "email": "j.dupont@entreprise.com",
                "department": "Finance",
                "job": "Employee"
            }
        }
    """
    operation: OperationType
    targetSystems: List[str]
    accountId: int
    sourceAttributes: Dict[str, Any]
    correlationId: Optional[str] = Field(default_factory=lambda: None)


class TargetResult(BaseModel):
    """
    Résultat du provisionnement pour une cible spécifique.
    
    Exemple:
        {
            "target": "AD",
            "operation": "create",
            "status": "SUCCESS",
            "calculatedAttributes": {
                "login": "jean.dupont",
                "email": "j.dupont@entreprise.com"
            },
            "message": "User created in AD",
            "duration_ms": 245
        }
    """
    target: str
    operation: OperationType
    status: str  # "SUCCESS", "FAILED", "SKIPPED", etc.
    calculatedAttributes: Dict[str, Any]
    message: str
    duration_ms: float
    error: Optional[str] = None


class ProvisionResult(BaseModel):
    """
    Résultat final du provisionnement retourné à MidPoint.
    
    Exemple:
        {
            "status": "SUCCESS",
            "calculatedAttributes": {
                "AD": {"login": "jean.dupont", ...},
                "SQL": {"username": "jdupont", ...},
                "ODOO": {"login": "j.dupont@entreprise.com", ...}
            },
            "targetResults": [...],
            "message": "Provisioning done in AD, SQL and Odoo",
            "timestamp": "2025-12-16T10:30:00Z",
            "correlationId": "..."
        }
    """
    status: str  # "SUCCESS", "PARTIAL_SUCCESS", "FAILED"
    calculatedAttributes: Dict[str, Dict[str, Any]]  # {target: {attrs}}
    targetResults: List[TargetResult]
    message: str
    timestamp: datetime
    correlationId: Optional[str] = None


class RulesConfig(BaseModel):
        """
        Configuration des règles de calcul d'attributs par cible.

        Schéma YAML attendu:
            global:                      # optionnel, variables globales utilisables dans les templates
                domain: "sae.com"
                base_dn: "dc=SAE,dc=com"
            targets:
                LDAP:
                    rules:
                        login: "{{ (firstname ~ '.' ~ lastname) | lower }}"
                        mail:  "{{ login }}@{{ global.domain }}"
                        dn:    "uid={{ login }},{{ global.base_dn }}"
                    object_classes: [inetOrgPerson]    # libre, pour usage par le connecteur
                    server: { host: localhost, port: 389 }  # libre, pour usage par le connecteur
                SQL:
                    rules:
                        username: "{{ accountId }}"
                        role: "APP_USER"
        """
        targets: Dict[str, Dict[str, Any]]  # {target_name: {rules: ...}}
        # 'global' est un mot réservé en Python; on l'expose sous 'global_' avec un alias YAML 'global'
        global_: Optional[Dict[str, Any]] = Field(default=None, alias="global")
