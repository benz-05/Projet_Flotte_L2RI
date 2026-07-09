"""Persistance en fichiers : JSON (état complet) et CSV (locations).

Ce module sépare la logique d'accès aux données (fichiers) de la logique
métier (classes Vehicule/Flotte). C'est la "séparation des responsabilités"
demandée par le sujet.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

from .enums import StatutVehicule
from .exceptions import DonneesInvalidesError
from .flotte import Flotte, Location
from .vehicules import Moto, Utilitaire, VehiculeBase, Voiture

logger = logging.getLogger(__name__)


def _vehicule_to_dict(v: VehiculeBase) -> dict:
    """Sérialise un véhicule (attributs communs + spécifiques + entretiens)."""
    base = {
        "type": v.type_vehicule,
        "immatriculation": v.immatriculation,
        "marque": v.marque,
        "modele": v.modele,
        "kilometrage": v.kilometrage,
        "statut": v.statut.name,
        "entretiens": [e.to_dict() for e in v.entretiens],
    }
    if isinstance(v, Voiture):
        base["nb_places"] = v.nb_places
    elif isinstance(v, Utilitaire):
        base["charge_utile_kg"] = v.charge_utile_kg
    elif isinstance(v, Moto):
        base["cylindree_cc"] = v.cylindree_cc
    return base


def _dict_to_vehicule(data: dict) -> VehiculeBase:
    """Reconstruit le bon type de véhicule à partir du champ 'type'."""
    type_v = data["type"]
    statut = StatutVehicule[data["statut"]]
    commun = dict(
        immatriculation=data["immatriculation"],
        marque=data["marque"],
        modele=data["modele"],
        kilometrage=data["kilometrage"],
        statut=statut,
    )
    if type_v == "Voiture":
        vehicule: VehiculeBase = Voiture(nb_places=data.get("nb_places", 5), **commun)
    elif type_v == "Utilitaire":
        vehicule = Utilitaire(charge_utile_kg=data.get("charge_utile_kg", 1000.0), **commun)
    elif type_v == "Moto":
        vehicule = Moto(cylindree_cc=data.get("cylindree_cc", 125), **commun)
    else:
        raise DonneesInvalidesError(f"Type de véhicule inconnu : {type_v}")

    from .entretien import Entretien  # import local pour éviter les cycles
    for e in data.get("entretiens", []):
        vehicule._entretiens.append(Entretien.from_dict(e))
    return vehicule


def sauvegarder_json(flotte: Flotte, chemin: str | Path) -> None:
    """Sauvegarde l'état complet de la flotte (véhicules + locations) en JSON."""
    donnees = {
        "nom": flotte.nom,
        "vehicules": [_vehicule_to_dict(v) for v in flotte.vehicules],
        "locations": [loc.to_dict() for loc in flotte.locations],
    }
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=4)
    logger.info("Flotte sauvegardée dans %s", chemin)


def charger_json(chemin: str | Path) -> Flotte:
    """Recharge une flotte complète depuis un fichier JSON.

    Raises:
        DonneesInvalidesError: si le fichier est absent ou mal formé.
    """
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            donnees = json.load(f)
    except FileNotFoundError as exc:
        raise DonneesInvalidesError(f"Fichier introuvable : {chemin}") from exc
    except json.JSONDecodeError as exc:
        raise DonneesInvalidesError(f"JSON invalide dans {chemin}") from exc

    flotte = Flotte(nom=donnees.get("nom", "Flotte principale"))
    for v_data in donnees.get("vehicules", []):
        flotte.ajouter_vehicule(_dict_to_vehicule(v_data))
    for loc_data in donnees.get("locations", []):
        flotte._locations.append(Location.from_dict(loc_data))
    logger.info("Flotte chargée depuis %s", chemin)
    return flotte


def exporter_locations_csv(
    flotte: Flotte, chemin: str | Path, actives_seulement: bool = False,
) -> None:
    """Exporte les contrats de location dans un fichier CSV.

    Args:
        actives_seulement: si True, n'exporte que les locations en cours.
    """
    locations = flotte.locations
    if actives_seulement:
        locations = [loc for loc in locations if loc.est_active]

    with open(chemin, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "immatriculation", "client", "categorie", "date_debut",
            "date_fin_prevue", "date_fin_reelle", "nb_jours",
            "penalite", "montant_total",
        ])
        for loc in locations:
            writer.writerow([
                loc.immatriculation, loc.client, loc.categorie.value,
                loc.date_debut.isoformat(), loc.date_fin_prevue.isoformat(),
                loc.date_fin_reelle.isoformat() if loc.date_fin_reelle else "",
                loc.nb_jours(), loc.calculer_penalite(), loc.montant_total(),
            ])
    logger.info("Locations exportées vers %s (%d lignes)", chemin, len(locations))
