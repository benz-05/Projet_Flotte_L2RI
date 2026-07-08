"""Programme principal : démonstration complète du Sujet D.

Lance : python main.py

Ce script joue tous les scénarios attendus par le sujet :
  1. Création d'une flotte mixte (>= 8 véhicules, 3 types).
  2. Cycle complet de location (réservation, départ, retour, tarif).
  3. Détection des véhicules à entretenir.
  4. Rapport de disponibilité à une date donnée.
  5. Bonus : pénalité de retard.
  6. Persistance JSON / CSV / SQLite.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

from src.base_donnees import BaseDonnees
from src.enums import CategorieClient, StatutVehicule
from src.exceptions import FlotteError
from src.flotte import Flotte
from src.persistance_fichiers import (
    charger_json,
    exporter_locations_csv,
    sauvegarder_json,
)
from src.vehicules import Moto, Utilitaire, Voiture

# Configuration du logging (remplace les print de debug).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

DOSSIER_DATA = Path("data")
DOSSIER_DATA.mkdir(exist_ok=True)


def construire_flotte() -> Flotte:
    """Crée une flotte mixte de 9 véhicules (3 types)."""
    flotte = Flotte(nom="Location Dakar Auto")

    vehicules = [
        Voiture("DK-1001-A", "Toyota", "Corolla", 8000, nb_places=5),
        Voiture("DK-1002-A", "Hyundai", "Accent", 22000, nb_places=5),
        Voiture("DK-1003-A", "Peugeot", "5008", 5000, nb_places=7),
        Utilitaire("DK-2001-B", "Renault", "Master", 13000, charge_utile_kg=1500),
        Utilitaire("DK-2002-B", "Ford", "Transit", 4000, charge_utile_kg=1200),
        Moto("DK-3001-C", "Yamaha", "Crux", 9000, cylindree_cc=110),
        Moto("DK-3002-C", "Honda", "CB", 3000, cylindree_cc=250),
        Moto("DK-3003-C", "KTM", "Duke", 16000, cylindree_cc=390),
        Voiture("DK-1004-A", "Kia", "Picanto", 30000, nb_places=5),
    ]
    for v in vehicules:
        flotte.ajouter_vehicule(v)
    return flotte


def demo_locations(flotte: Flotte) -> None:
    """Joue plusieurs locations, dont une avec retard (pénalité)."""
    aujourdhui = date.today()

    # Location classique (particulier).
    flotte.louer(
        "DK-1001-A", "Aminata Ba", CategorieClient.PARTICULIER,
        aujourdhui - timedelta(days=5), aujourdhui - timedelta(days=2),
    )
    flotte.cloturer_location("DK-1001-A", aujourdhui - timedelta(days=2))

    # Location entreprise (remise) rendue EN RETARD -> pénalité.
    flotte.louer(
        "DK-2001-B", "Sonatel SA", CategorieClient.ENTREPRISE,
        aujourdhui - timedelta(days=10), aujourdhui - timedelta(days=6),
    )
    location_retard = flotte.cloturer_location(
        "DK-2001-B", aujourdhui - timedelta(days=3)  # 3 jours de retard
    )
    print(f"\nPénalité de retard (DK-2001-B) : {location_retard.calculer_penalite():,.0f} FCFA")
    print(f"Montant total facturé : {location_retard.montant_total():,.0f} FCFA")

    # Location événementiel en cours.
    flotte.louer(
        "DK-3002-C", "Festival Dakar", CategorieClient.EVENEMENTIEL,
        aujourdhui, aujourdhui + timedelta(days=4),
    )


def afficher_rapports(flotte: Flotte) -> None:
    """Affiche les rapports demandés (disponibilité, entretien, CA)."""
    print("\n=== Véhicules disponibles aujourd'hui ===")
    for v in flotte.vehicules_disponibles():
        print(f"  - {v}")

    print("\n=== Véhicules nécessitant un entretien ===")
    a_entretenir = flotte.vehicules_a_entretenir()
    if not a_entretenir:
        print("  (aucun)")
    for v in a_entretenir:
        print(f"  - {v} ({v.kilometrage} km)")

    print("\n=== Chiffre d'affaires par type ===")
    for type_v, ca in flotte.chiffre_affaires_par_type().items():
        print(f"  - {type_v} : {ca:,.0f} FCFA")


def demo_persistance(flotte: Flotte) -> None:
    """Sauvegarde JSON/CSV, recharge, puis synchronise la base SQLite."""
    chemin_json = DOSSIER_DATA / "flotte.json"
    chemin_csv = DOSSIER_DATA / "locations.csv"

    sauvegarder_json(flotte, chemin_json)
    exporter_locations_csv(flotte, chemin_csv)

    # Rechargement pour prouver que l'import fonctionne.
    flotte_rechargee = charger_json(chemin_json)
    print(f"\nFlotte rechargée depuis JSON : {len(flotte_rechargee.vehicules)} véhicules.")

    # Base SQLite + requêtes métier.
    bdd = BaseDonnees(DOSSIER_DATA / "flotte.db")
    bdd.synchroniser(flotte)

    print("\n=== [SQL] Chiffre d'affaires par type ===")
    for ligne in bdd.chiffre_affaires_par_type():
        print(f"  - {ligne['type_vehicule']} : {ligne['chiffre_affaires']:,.0f} FCFA")

    print("\n=== [SQL] Top clients ===")
    for ligne in bdd.top_clients():
        print(f"  - {ligne['client']} : {ligne['nb_locations']} location(s)")


def main() -> None:
    """Point d'entrée : enchaîne tous les scénarios."""
    try:
        flotte = construire_flotte()
        demo_locations(flotte)
        afficher_rapports(flotte)
        demo_persistance(flotte)
        print("\nDémonstration terminée avec succès.")
    except FlotteError as exc:
        logging.error("Erreur métier : %s", exc)


if __name__ == "__main__":
    main()
