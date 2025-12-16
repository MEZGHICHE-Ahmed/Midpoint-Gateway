# Gateway IAM - Provisionnement Multi-Cibles

Passerelle de provisionnement pour orchestrer les opérations sur AD/LDAP, SQL, Odoo, etc. depuis MidPoint.

## Architecture

```
gateway/
├── core/           # Logique métier principale
│   ├── models.py       # Contrats (Request/Result)
│   ├── calculator.py   # Moteur de calcul d'attributs
│   ├── orchestrator.py # Service de provisionnement multi-cibles
│   └── provisioner.py  # Orchestrateur principal
├── connectors/     # Connecteurs vers systèmes cibles
│   ├── base.py         # Interface commune
│   ├── ldap.py         # Connecteur LDAP/AD
│   └── sql.py          # Connecteur SQL
├── api/            # API REST
│   └── http.py         # Endpoints FastAPI
config/             # Fichiers de configuration
└── rules.yaml      # Règles de calcul d'attributs
tests/              # Tests unitaires
```

## Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Démarrage (à venir)

```bash
uvicorn gateway.api.http:app --reload
```

## Développement progressif

1. ✅ Structure de base
2. ⏳ Modèles de données (ProvisionRequest, ProvisionResult)
3. ⏳ Calculator (moteur de règles simple)
4. ⏳ Connecteurs (BaseConnector + stubs)
5. ⏳ ProvisioningService (orchestration)
6. ⏳ Provisioner (logique principale)
7. ⏳ API REST (endpoint /provision)
