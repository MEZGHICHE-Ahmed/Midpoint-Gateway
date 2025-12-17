"""API REST minimale pour tester le Calculator."""

from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from gateway.core.calculator import Calculator

app = FastAPI(title="Gateway IAM - Calculator Test API", version="0.1.0")


# Modèle d'entrée pour POST /calculate
class CalculateRequest(BaseModel):
    """
    Requête pour calculer les attributs par cible.
    
    Exemple:
    {
      "sourceAttributes": {
        "firstname": "Jean",
        "lastname": "Dupont",
        "email": "j.dupont@sae.com"
      },
      "accountId": "jdupont",
      "targets": ["LDAP", "SQL"]
    }
    """
    sourceAttributes: Dict[str, Any]
    accountId: str
    targets: Optional[List[str]] = None  # Si None, calcule pour toutes les cibles


# Initialisation du Calculator au démarrage
@app.on_event("startup")
def load_calculator():
    """Charge les règles depuis config/rules.yaml au démarrage."""
    global calculator
    # Chemin relatif depuis la racine du projet
    rules_path = Path(__file__).resolve().parents[2] / "config" / "rules.yaml"
    if not rules_path.exists():
        raise RuntimeError(f"Fichier de règles introuvable: {rules_path}")
    calculator = Calculator.from_file(rules_path)
    print(f"✓ Règles chargées depuis {rules_path}")


@app.get("/")
def root():
    """Health check."""
    return {"status": "ok", "service": "Gateway IAM Calculator"}


@app.post("/calculate")
def calculate_attributes(req: CalculateRequest) -> Dict[str, Dict[str, Any]]:
    """
    Calcule les attributs par cible selon les règles YAML.
    
    Retourne un dict {target_name: {calculated_attrs}}.
    """
    try:
        result = calculator.calculate(
            source_attributes=req.sourceAttributes,
            account_id=req.accountId,
            targets=req.targets,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de calcul: {str(e)}")


@app.get("/health")
def health():
    """Endpoint de santé (pour K8s/monitoring)."""
    return {"status": "healthy", "calculator": "loaded"}
