# Gestion d'une flotte de véhicules en location (Sujet D)

Projet de fin de semestre — **POO & Persistance des données** — L2 RI, ISI Dakar.

Une société de location gère une flotte hétérogène (voitures, utilitaires,
motos), avec des contrats de location, un suivi de maintenance, et un besoin
de connaître la disponibilité de chaque véhicule à tout moment.

## Fonctionnalités

- Flotte mixte de véhicules (3 types : voiture, utilitaire, moto).
- Cycle complet d'une location : réservation, départ, retour, calcul du tarif
  selon la durée et la catégorie de client.
- Détection automatique des véhicules nécessitant un entretien (seuil de km).
- Rapport de disponibilité de la flotte à une date donnée.
- **Bonus** : calcul d'une pénalité en cas de retour tardif.
- Persistance : **JSON** (état complet), **CSV** (locations), **SQLite**
  (2 tables liées, 4 requêtes métier).

## Installation

```bash
git clone <lien-du-depot>
cd flotte
python -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

## Utilisation

Lancer la démonstration complète (crée les fichiers dans `data/`) :

```bash
python main.py
```

Lancer les tests unitaires :

```bash
python -m pytest -v
```

## Structure du projet

```
flotte/
├── main.py                      # Point d'entrée : démonstration des scénarios
├── requirements.txt
├── README.md
├── CONTRIBUTIONS.md
├── data/                        # Fichiers générés (JSON, CSV, base SQLite)
├── src/
│   ├── enums.py                 # StatutVehicule, CategorieClient (2 Enum)
│   ├── exceptions.py            # Exceptions métier personnalisées
│   ├── entretien.py             # Objet Entretien (composition)
│   ├── vehicules.py             # VehiculeBase (ABC) + Voiture/Utilitaire/Moto
│   ├── flotte.py                # Flotte (agrégation) + Location
│   ├── persistance_fichiers.py  # Sauvegarde/chargement JSON, export CSV
│   └── base_donnees.py          # SQLite : 2 tables liées, 4 requêtes métier
└── tests/
    └── test_flotte.py           # Tests unitaires (pytest)
```

## Choix d'architecture

- **Classe abstraite** `VehiculeBase` (ABC) avec 2 méthodes abstraites
  (`calculer_tarif_jour`, `necessite_entretien`), impossible à instancier.
- **3 classes filles** concrètes qui surchargent ces méthodes.
- **2 Enum** : `StatutVehicule`, `CategorieClient`.
- **Agrégation** : `Flotte` contient des `Vehicule` créés à l'extérieur puis
  ajoutés — cycles de vie indépendants.
- **Composition** : chaque `Vehicule` crée et possède ses `Entretien` —
  cycles de vie liés.
- Séparation des responsabilités : métier (`vehicules`, `flotte`), accès aux
  données (`persistance_fichiers`, `base_donnees`), affichage (`main`).
```
