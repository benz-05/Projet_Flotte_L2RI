"""Hiérarchie de véhicules : classe abstraite + 3 classes filles concrètes.

Points POO couverts ici (exigés par le sujet) :
- Classe abstraite VehiculeBase (ABC) avec 2 méthodes abstraites.
- 3 classes filles concrètes : Voiture, Utilitaire, Moto (surcharge).
- COMPOSITION : chaque Vehicule crée et possède ses propres Entretien.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import date

from .entretien import Entretien
from .enums import StatutVehicule
from .exceptions import DonneesInvalidesError

logger = logging.getLogger(__name__)

# Seuil de kilométrage au-delà duquel un entretien est recommandé.
SEUIL_KM_ENTRETIEN = 15000


class VehiculeBase(ABC):
    """Classe abstraite représentant un véhicule de la flotte.

    On ne peut PAS instancier VehiculeBase directement (c'est une ABC).
    Toute classe fille DOIT implémenter calculer_tarif_jour() et
    necessite_entretien(), sinon Python refuse de l'instancier.
    """

    def __init__(
        self,
        immatriculation: str,
        marque: str,
        modele: str,
        kilometrage: int,
        statut: StatutVehicule = StatutVehicule.DISPONIBLE,
    ) -> None:
        """Initialise les attributs communs à tous les véhicules.

        Args:
            immatriculation: plaque du véhicule (identifiant unique).
            marque: marque (Toyota, Renault...).
            modele: modèle.
            kilometrage: kilométrage courant.
            statut: statut de disponibilité (par défaut DISPONIBLE).

        Raises:
            DonneesInvalidesError: si l'immatriculation est vide ou le
                kilométrage négatif.
        """
        if not immatriculation or not immatriculation.strip():
            raise DonneesInvalidesError("L'immatriculation ne peut pas être vide.")
        if kilometrage < 0:
            raise DonneesInvalidesError("Le kilométrage ne peut pas être négatif.")

        self.immatriculation = immatriculation.strip().upper()
        self.marque = marque
        self.modele = modele
        self.kilometrage = kilometrage
        self.statut = statut
        # COMPOSITION : le véhicule possède sa propre liste d'entretiens.
        self._entretiens: list[Entretien] = []

    # ----- Méthodes abstraites : contrat imposé aux classes filles -----

    @abstractmethod
    def calculer_tarif_jour(self) -> float:
        """Retourne le tarif de location par jour (en FCFA)."""
        raise NotImplementedError

    @abstractmethod
    def necessite_entretien(self) -> bool:
        """Indique si le véhicule a besoin d'un entretien."""
        raise NotImplementedError

    # ----- Comportement commun (composition des entretiens) -----

    def ajouter_entretien(
        self, description: str, cout: float, kilometrage: int,
        date_entretien: date | None = None,
    ) -> Entretien:
        """Crée et rattache un entretien à CE véhicule (composition).

        C'est le véhicule qui construit l'objet Entretien : leurs cycles
        de vie sont liés. Si le véhicule est supprimé, ses entretiens le
        sont aussi.
        """
        if cout < 0:
            raise DonneesInvalidesError("Le coût d'un entretien ne peut être négatif.")
        entretien = Entretien(
            date_entretien=date_entretien or date.today(),
            description=description,
            cout=cout,
            kilometrage=kilometrage,
        )
        self._entretiens.append(entretien)
        logger.info("Entretien ajouté au véhicule %s : %s", self.immatriculation, description)
        return entretien

    @property
    def entretiens(self) -> list[Entretien]:
        """Liste (lecture seule) des entretiens du véhicule."""
        return list(self._entretiens)

    @property
    @abstractmethod
    def type_vehicule(self) -> str:
        """Nom lisible du type de véhicule (utilisé pour l'affichage/BDD)."""
        raise NotImplementedError

    def __str__(self) -> str:
        return (
            f"{self.type_vehicule} {self.marque} {self.modele} "
            f"[{self.immatriculation}] - {self.statut.value}"
        )


class Voiture(VehiculeBase):
    """Voiture particulière. Tarif basé sur le nombre de places."""

    TARIF_BASE = 20000  # FCFA / jour

    def __init__(self, immatriculation, marque, modele, kilometrage,
                 nb_places: int = 5, statut=StatutVehicule.DISPONIBLE) -> None:
        super().__init__(immatriculation, marque, modele, kilometrage, statut)
        self.nb_places = nb_places

    @property
    def type_vehicule(self) -> str:
        return "Voiture"

    def calculer_tarif_jour(self) -> float:
        """Tarif = base + supplément si plus de 5 places."""
        supplement = 3000 if self.nb_places > 5 else 0
        return self.TARIF_BASE + supplement

    def necessite_entretien(self) -> bool:
        """Entretien nécessaire tous les 15 000 km."""
        return self.kilometrage >= SEUIL_KM_ENTRETIEN


class Utilitaire(VehiculeBase):
    """Véhicule utilitaire (camionnette). Tarif basé sur la charge utile."""

    TARIF_BASE = 30000

    def __init__(self, immatriculation, marque, modele, kilometrage,
                 charge_utile_kg: float = 1000.0, statut=StatutVehicule.DISPONIBLE) -> None:
        super().__init__(immatriculation, marque, modele, kilometrage, statut)
        self.charge_utile_kg = charge_utile_kg

    @property
    def type_vehicule(self) -> str:
        return "Utilitaire"

    def calculer_tarif_jour(self) -> float:
        """Tarif = base + 5 FCFA par kg de charge utile."""
        return self.TARIF_BASE + self.charge_utile_kg * 5

    def necessite_entretien(self) -> bool:
        """Les utilitaires sont plus sollicités : seuil abaissé à 12 000 km."""
        return self.kilometrage >= 12000


class Moto(VehiculeBase):
    """Moto. Tarif basé sur la cylindrée."""

    TARIF_BASE = 10000

    def __init__(self, immatriculation, marque, modele, kilometrage,
                 cylindree_cc: int = 125, statut=StatutVehicule.DISPONIBLE) -> None:
        super().__init__(immatriculation, marque, modele, kilometrage, statut)
        self.cylindree_cc = cylindree_cc

    @property
    def type_vehicule(self) -> str:
        return "Moto"

    def calculer_tarif_jour(self) -> float:
        """Tarif = base + 20 FCFA par cc au-delà de 125 cc."""
        supplement = max(0, self.cylindree_cc - 125) * 20
        return self.TARIF_BASE + supplement

    def necessite_entretien(self) -> bool:
        """Entretien moto tous les 8 000 km."""
        return self.kilometrage >= 8000
