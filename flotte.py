"""Location et Flotte.

- Location : représente un contrat de location d'un véhicule par un client.
- Flotte : conteneur qui AGRÈGE des véhicules.

AGRÉGATION (Flotte -> Vehicule) :
    Les véhicules sont créés À L'EXTÉRIEUR de la flotte, puis ajoutés via
    ajouter_vehicule(). Si la flotte disparaît, les véhicules pourraient
    exister ailleurs. Leurs cycles de vie sont INDÉPENDANTS.

À comparer avec la COMPOSITION Vehicule -> Entretien, où le véhicule crée
lui-même ses entretiens et où les cycles de vie sont LIÉS.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date

from .enums import CategorieClient, StatutVehicule
from .exceptions import (
    DonneesInvalidesError,
    LocationIntrouvableError,
    VehiculeIndisponibleError,
)
from .vehicules import VehiculeBase

logger = logging.getLogger(__name__)

# Pénalité par jour de retard (FCFA).
PENALITE_RETARD_JOUR = 5000


@dataclass
class Location:
    """Contrat de location d'un véhicule.

    Attributs:
        immatriculation: véhicule loué (référence par sa plaque).
        client: nom du client.
        categorie: catégorie de client (influence le tarif).
        date_debut: date de départ.
        date_fin_prevue: date de retour prévue.
        date_fin_reelle: date de retour réelle (None tant que non clôturée).
        tarif_jour: tarif journalier au moment de la location.
    """

    immatriculation: str
    client: str
    categorie: CategorieClient
    date_debut: date
    date_fin_prevue: date
    tarif_jour: float
    date_fin_reelle: date | None = None

    @property
    def est_active(self) -> bool:
        """True tant que le véhicule n'a pas été rendu."""
        return self.date_fin_reelle is None

    def nb_jours(self) -> int:
        """Nombre de jours facturés (au minimum 1)."""
        fin = self.date_fin_reelle or self.date_fin_prevue
        jours = (fin - self.date_debut).days
        return max(1, jours)

    def calculer_penalite(self) -> float:
        """Calcule la pénalité de retour tardif (fonctionnalité bonus)."""
        if self.date_fin_reelle is None:
            return 0.0
        retard = (self.date_fin_reelle - self.date_fin_prevue).days
        return max(0, retard) * PENALITE_RETARD_JOUR

    def montant_total(self) -> float:
        """Montant total = jours * tarif * coefficient client + pénalité."""
        base = self.nb_jours() * self.tarif_jour * self.categorie.coefficient()
        return round(base + self.calculer_penalite(), 2)

    def to_dict(self) -> dict:
        """Sérialise la location en dictionnaire (JSON)."""
        return {
            "immatriculation": self.immatriculation,
            "client": self.client,
            "categorie": self.categorie.name,
            "date_debut": self.date_debut.isoformat(),
            "date_fin_prevue": self.date_fin_prevue.isoformat(),
            "date_fin_reelle": (
                self.date_fin_reelle.isoformat() if self.date_fin_reelle else None
            ),
            "tarif_jour": self.tarif_jour,
        }

    @staticmethod
    def from_dict(data: dict) -> "Location":
        """Reconstruit une Location depuis un dictionnaire (JSON)."""
        return Location(
            immatriculation=data["immatriculation"],
            client=data["client"],
            categorie=CategorieClient[data["categorie"]],
            date_debut=date.fromisoformat(data["date_debut"]),
            date_fin_prevue=date.fromisoformat(data["date_fin_prevue"]),
            tarif_jour=float(data["tarif_jour"]),
            date_fin_reelle=(
                date.fromisoformat(data["date_fin_reelle"])
                if data.get("date_fin_reelle")
                else None
            ),
        )


@dataclass
class Flotte:
    """Conteneur agrégeant les véhicules et gérant les locations."""

    nom: str = "Flotte principale"
    _vehicules: dict[str, VehiculeBase] = field(default_factory=dict)
    _locations: list[Location] = field(default_factory=list)

    # ----- Gestion du parc (agrégation) -----

    def ajouter_vehicule(self, vehicule: VehiculeBase) -> None:
        """Ajoute un véhicule DÉJÀ CRÉÉ à la flotte (agrégation).

        Raises:
            DonneesInvalidesError: si la plaque est déjà présente.
        """
        if vehicule.immatriculation in self._vehicules:
            raise DonneesInvalidesError(
                f"Le véhicule {vehicule.immatriculation} existe déjà dans la flotte."
            )
        self._vehicules[vehicule.immatriculation] = vehicule
        logger.info("Véhicule ajouté : %s", vehicule.immatriculation)

    def get_vehicule(self, immatriculation: str) -> VehiculeBase:
        """Récupère un véhicule par sa plaque."""
        cle = immatriculation.strip().upper()
        if cle not in self._vehicules:
            raise DonneesInvalidesError(f"Véhicule {cle} introuvable.")
        return self._vehicules[cle]

    @property
    def vehicules(self) -> list[VehiculeBase]:
        """Liste des véhicules de la flotte."""
        return list(self._vehicules.values())

    @property
    def locations(self) -> list[Location]:
        """Liste de toutes les locations (actives et clôturées)."""
        return list(self._locations)

    # ----- Cycle de vie d'une location -----

    def louer(
        self, immatriculation: str, client: str, categorie: CategorieClient,
        date_debut: date, date_fin_prevue: date,
    ) -> Location:
        """Crée une location et passe le véhicule au statut LOUE.

        Raises:
            VehiculeIndisponibleError: si le véhicule n'est pas disponible.
            DonneesInvalidesError: si les dates sont incohérentes.
        """
        if date_fin_prevue <= date_debut:
            raise DonneesInvalidesError(
                "La date de fin prévue doit être postérieure à la date de début."
            )
        vehicule = self.get_vehicule(immatriculation)
        if vehicule.statut is not StatutVehicule.DISPONIBLE:
            raise VehiculeIndisponibleError(
                f"Le véhicule {vehicule.immatriculation} n'est pas disponible "
                f"(statut : {vehicule.statut.value})."
            )
        location = Location(
            immatriculation=vehicule.immatriculation,
            client=client,
            categorie=categorie,
            date_debut=date_debut,
            date_fin_prevue=date_fin_prevue,
            tarif_jour=vehicule.calculer_tarif_jour(),
        )
        vehicule.statut = StatutVehicule.LOUE
        self._locations.append(location)
        logger.info("Location créée : %s -> %s", vehicule.immatriculation, client)
        return location

    def cloturer_location(
        self, immatriculation: str, date_fin_reelle: date | None = None,
    ) -> Location:
        """Clôture la location active d'un véhicule et le rend DISPONIBLE.

        Raises:
            LocationIntrouvableError: si aucune location active n'existe.
        """
        cle = immatriculation.strip().upper()
        for location in self._locations:
            if location.immatriculation == cle and location.est_active:
                location.date_fin_reelle = date_fin_reelle or date.today()
                self.get_vehicule(cle).statut = StatutVehicule.DISPONIBLE
                logger.info("Location clôturée : %s", cle)
                return location
        raise LocationIntrouvableError(
            f"Aucune location active pour le véhicule {cle}."
        )

    # ----- Rapports -----

    def vehicules_disponibles(self, a_la_date: date | None = None) -> list[VehiculeBase]:
        """Retourne les véhicules disponibles à une date donnée."""
        jour = a_la_date or date.today()
        indisponibles = {
            loc.immatriculation
            for loc in self._locations
            if loc.date_debut <= jour <= (loc.date_fin_reelle or loc.date_fin_prevue)
        }
        return [
            v for v in self._vehicules.values()
            if v.immatriculation not in indisponibles
            and v.statut is not StatutVehicule.HORS_SERVICE
        ]

    def vehicules_a_entretenir(self) -> list[VehiculeBase]:
        """Retourne les véhicules nécessitant un entretien."""
        return [v for v in self._vehicules.values() if v.necessite_entretien()]

    def chiffre_affaires_par_type(self) -> dict[str, float]:
        """Calcule le chiffre d'affaires total par type de véhicule."""
        ca: dict[str, float] = {}
        for loc in self._locations:
            vehicule = self._vehicules.get(loc.immatriculation)
            if vehicule is None:
                continue
            type_v = vehicule.type_vehicule
            ca[type_v] = ca.get(type_v, 0.0) + loc.montant_total()
        return ca
