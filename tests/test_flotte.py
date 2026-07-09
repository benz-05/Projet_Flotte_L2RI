"""Tests unitaires du projet (lancer avec : python -m pytest -v).

Ces tests vérifient les règles métier principales et la gestion des
exceptions personnalisées.
"""

from datetime import date, timedelta

import pytest

from src.enums import CategorieClient, StatutVehicule
from src.exceptions import (
    DonneesInvalidesError,
    LocationIntrouvableError,
    VehiculeIndisponibleError,
)
from src.flotte import Flotte
from src.vehicules import Moto, Utilitaire, Voiture, VehiculeBase


def test_vehicule_abstrait_non_instanciable():
    """On ne doit pas pouvoir instancier la classe abstraite."""
    with pytest.raises(TypeError):
        VehiculeBase("DK-0000-A", "X", "Y", 0)  # type: ignore


def test_immatriculation_vide_leve_exception():
    with pytest.raises(DonneesInvalidesError):
        Voiture("", "Toyota", "Yaris", 1000)


def test_tarifs_specifiques():
    """Chaque type de véhicule calcule son propre tarif."""
    voiture = Voiture("DK-1-A", "Toyota", "Corolla", 0, nb_places=7)
    utilitaire = Utilitaire("DK-2-B", "Renault", "Master", 0, charge_utile_kg=1000)
    moto = Moto("DK-3-C", "KTM", "Duke", 0, cylindree_cc=390)
    assert voiture.calculer_tarif_jour() == 23000       # 20000 + 3000
    assert utilitaire.calculer_tarif_jour() == 35000     # 30000 + 1000*5
    assert moto.calculer_tarif_jour() == 10000 + 265 * 20


def test_necessite_entretien():
    assert Moto("DK-3-C", "KTM", "Duke", 8000).necessite_entretien() is True
    assert Voiture("DK-1-A", "Toyota", "Yaris", 1000).necessite_entretien() is False


def test_composition_entretien():
    """Le véhicule crée et possède ses entretiens (composition)."""
    voiture = Voiture("DK-1-A", "Toyota", "Corolla", 16000)
    voiture.ajouter_entretien("Vidange", 25000, 16000)
    assert len(voiture.entretiens) == 1
    assert voiture.entretiens[0].description == "Vidange"


def test_louer_vehicule_indisponible():
    """On ne peut pas louer deux fois le même véhicule."""
    flotte = Flotte()
    flotte.ajouter_vehicule(Voiture("DK-1-A", "Toyota", "Corolla", 0))
    debut, fin = date.today(), date.today() + timedelta(days=2)
    flotte.louer("DK-1-A", "Client 1", CategorieClient.PARTICULIER, debut, fin)
    with pytest.raises(VehiculeIndisponibleError):
        flotte.louer("DK-1-A", "Client 2", CategorieClient.PARTICULIER, debut, fin)


def test_cloture_sans_location():
    flotte = Flotte()
    flotte.ajouter_vehicule(Moto("DK-3-C", "Honda", "CB", 0))
    with pytest.raises(LocationIntrouvableError):
        flotte.cloturer_location("DK-3-C")


def test_penalite_retard():
    """Un retour tardif génère une pénalité."""
    flotte = Flotte()
    flotte.ajouter_vehicule(Voiture("DK-1-A", "Toyota", "Corolla", 0))
    debut = date.today() - timedelta(days=10)
    fin_prevue = date.today() - timedelta(days=5)
    flotte.louer("DK-1-A", "Client", CategorieClient.PARTICULIER, debut, fin_prevue)
    loc = flotte.cloturer_location("DK-1-A", date.today() - timedelta(days=2))
    assert loc.calculer_penalite() == 3 * 5000  # 3 jours de retard


def test_coefficient_categorie():
    assert CategorieClient.ENTREPRISE.coefficient() == 0.9
    assert CategorieClient.EVENEMENTIEL.coefficient() == 1.2


def test_dates_incoherentes():
    flotte = Flotte()
    flotte.ajouter_vehicule(Voiture("DK-1-A", "Toyota", "Corolla", 0))
    jour = date.today()
    with pytest.raises(DonneesInvalidesError):
        flotte.louer("DK-1-A", "Client", CategorieClient.PARTICULIER, jour, jour)
