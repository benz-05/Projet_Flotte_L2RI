"""Objet Entretien : un enregistrement de maintenance d'un véhicule.

Un Entretien est un SOUS-OBJET d'un véhicule. C'est de la COMPOSITION :
un Entretien n'a aucun sens tout seul, il "appartient" à un véhicule et
disparaît avec lui. C'est le véhicule lui-même qui crée ses Entretien
(voir methode Vehicule.ajouter_entretien()).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Entretien:
    """Représente une opération d'entretien effectuée sur un véhicule.

    Attributs:
        date_entretien: date de l'intervention.
        description: nature de l'entretien (vidange, freins, révision...).
        cout: coût de l'intervention en FCFA.
        kilometrage: kilométrage du véhicule au moment de l'entretien.
    """

    date_entretien: date
    description: str
    cout: float
    kilometrage: int

    def to_dict(self) -> dict:
        """Convertit l'entretien en dictionnaire (pour l'export JSON)."""
        return {
            "date_entretien": self.date_entretien.isoformat(),
            "description": self.description,
            "cout": self.cout,
            "kilometrage": self.kilometrage,
        }

    @staticmethod
    def from_dict(data: dict) -> "Entretien":
        """Reconstruit un Entretien à partir d'un dictionnaire (import JSON)."""
        return Entretien(
            date_entretien=date.fromisoformat(data["date_entretien"]),
            description=data["description"],
            cout=float(data["cout"]),
            kilometrage=int(data["kilometrage"]),
        )
