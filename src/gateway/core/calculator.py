"""Moteur de calcul d'attributs basé sur des règles YAML et templates Jinja2.

Usage minimal:
    from gateway.core.calculator import Calculator
    calc = Calculator.from_file("config/rules.yaml")
    attrs_by_target = calc.calculate(
        source_attributes={"firstname": "Jean", "lastname": "Dupont", "email": "j.dupont@entreprise.com"},
        account_id="jdupont",
        targets=["AD", "SQL", "ODOO"],
    )

Structure attendue du YAML (config/rules.yaml):

targets:
  AD:
    rules:
      login: "{{ (firstname ~ '.' ~ lastname) | lower }}"
      email: "{{ email }}"
  SQL:
    rules:
      username: "{{ accountId }}"
      role: "APP_USER"
  ODOO:
    rules:
      login: "{{ email }}"
      active: true

"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import yaml
from jinja2 import Environment, BaseLoader

from .models import RulesConfig


class Calculator:
    """Interprète des règles YAML pour produire des attributs par cible."""

    def __init__(self, rules: RulesConfig):
        self._rules = rules
        # Environnement Jinja2 minimal avec quelques filtres simples
        self._env = Environment(loader=BaseLoader(), autoescape=False)
        self._env.filters.update({
            "lower": lambda s: s.lower() if isinstance(s, str) else s,
            "upper": lambda s: s.upper() if isinstance(s, str) else s,
            "trim": lambda s: s.strip() if isinstance(s, str) else s,
        })

    @staticmethod
    def from_file(path: Union[str, Path]) -> "Calculator":
        """Construit un Calculator à partir d'un fichier YAML."""
        cfg = Calculator._load_rules_from_file(path)
        return Calculator(cfg)

    @staticmethod
    def _load_rules_from_file(path: Union[str, Path]) -> RulesConfig:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Fichier de règles introuvable: {p}")
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        # Validation minimale via Pydantic
        return RulesConfig(**data)

    def calculate(
        self,
        source_attributes: Dict[str, Any],
        account_id: str,
        targets: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calcule les attributs par cible en appliquant les règles.

        - source_attributes: attributs entrants (depuis MidPoint)
        - account_id: identifiant de compte (utilisable dans les templates)
        - targets: si fourni, restreint le calcul à ces cibles
        """
        all_targets = list((self._rules.targets or {}).keys())
        selected_targets = targets or all_targets

        context = self._build_context(source_attributes, account_id)
        # Injecte les variables globales (si présentes) dans le contexte
        if getattr(self._rules, "global_", None):
            context["global"] = dict(self._rules.global_)
            # Confort: exposer aussi les clés globales à la racine du contexte
            for k, v in self._rules.global_.items():
                if k not in context:
                    context[k] = v
        result: Dict[str, Dict[str, Any]] = {}

        for target in selected_targets:
            target_cfg = (self._rules.targets or {}).get(target)
            if not target_cfg:
                # Cible non configurée: ignorer silencieusement (on pourra logger plus tard)
                continue
            rules = (target_cfg or {}).get("rules", {})
            # Rendu en passes pour permettre des références intra-cible (ex: mail utilise login)
            rendered = self._render_target_rules(rules, context)
            # Ne garder que les clés avec valeurs non None (pour un patch propre)
            result[target] = {
                k: v for k, v in (rendered or {}).items() if v is not None
            }
        
        return result

    def _build_context(self, source_attributes: Dict[str, Any], account_id: str) -> Dict[str, Any]:
        # Contexte exposé aux templates: attributs à plat + alias "source" + accountId
        ctx = dict(source_attributes) if source_attributes else {}
        ctx["source"] = dict(source_attributes) if source_attributes else {}
        ctx["accountId"] = account_id
        return ctx

    def _render_value(self, value: Any, context: Dict[str, Any]) -> Any:
        """Rendu récursif de valeurs: str -> template, dict/list -> récursif, sinon identique."""
        if isinstance(value, str):
            template = self._env.from_string(value)
            return template.render(**context)
        if isinstance(value, dict):
            return {k: self._render_value(v, context) for k, v in value.items()}
        if isinstance(value, list):
            return [self._render_value(v, context) for v in value]
        return value

    def _render_target_rules(self, rules: Dict[str, Any], base_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rend les règles d'une cible en plusieurs passes pour permettre
        des références entre champs (ex: 'mail' qui référence 'login').
        Limite à 3 passes pour éviter les boucles.
        """
        current: Dict[str, Any] = {}
        max_passes = 3
        for _ in range(max_passes):
            ctx = {**base_context, **current}
            rendered = self._render_value(rules, ctx) or {}
            if rendered == current:
                break
            current = rendered
        return current
