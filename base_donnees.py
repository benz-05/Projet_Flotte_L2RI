"""Persistance en base de données SQLite.

Le sujet impose :
- au moins 2 tables liées par une clé étrangère,
- au moins 4 requêtes métier (pas de simple SELECT *).

Schéma :
    vehicules(immatriculation PK, type, marque, modele, kilometrage, statut)
    locations(id PK, immatriculation FK -> vehicules, client, categorie,
              date_debut, date_fin_prevue, date_fin_reelle, tarif_jour)

Toutes les connexions utilisent 'with' pour garantir la fermeture propre
(aucune fuite de ressource).
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from .flotte import Flotte

logger = logging.getLogger(__name__)


class BaseDonnees:
    """Gère la base SQLite de la flotte."""

    def __init__(self, chemin: str | Path = "data/flotte.db") -> None:
        self.chemin = str(chemin)
        self._creer_tables()

    def _connexion(self) -> sqlite3.Connection:
        """Ouvre une connexion avec clés étrangères activées."""
        cnx = sqlite3.connect(self.chemin)
        cnx.execute("PRAGMA foreign_keys = ON;")
        cnx.row_factory = sqlite3.Row
        return cnx

    def _creer_tables(self) -> None:
        """Crée les deux tables liées si elles n'existent pas."""
        with self._connexion() as cnx:
            cnx.execute("""
                CREATE TABLE IF NOT EXISTS vehicules (
                    immatriculation TEXT PRIMARY KEY,
                    type            TEXT NOT NULL,
                    marque          TEXT NOT NULL,
                    modele          TEXT NOT NULL,
                    kilometrage     INTEGER NOT NULL,
                    statut          TEXT NOT NULL
                );
            """)
            cnx.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    immatriculation TEXT NOT NULL,
                    client          TEXT NOT NULL,
                    categorie       TEXT NOT NULL,
                    date_debut      TEXT NOT NULL,
                    date_fin_prevue TEXT NOT NULL,
                    date_fin_reelle TEXT,
                    tarif_jour      REAL NOT NULL,
                    FOREIGN KEY (immatriculation)
                        REFERENCES vehicules (immatriculation)
                );
            """)
        logger.info("Tables SQLite prêtes (%s)", self.chemin)

    def synchroniser(self, flotte: Flotte) -> None:
        """Écrit tout l'état de la flotte dans la base (remplace l'existant)."""
        with self._connexion() as cnx:
            cnx.execute("DELETE FROM locations;")
            cnx.execute("DELETE FROM vehicules;")
            for v in flotte.vehicules:
                cnx.execute(
                    "INSERT INTO vehicules VALUES (?, ?, ?, ?, ?, ?);",
                    (v.immatriculation, v.type_vehicule, v.marque,
                     v.modele, v.kilometrage, v.statut.name),
                )
            for loc in flotte.locations:
                cnx.execute(
                    """INSERT INTO locations
                       (immatriculation, client, categorie, date_debut,
                        date_fin_prevue, date_fin_reelle, tarif_jour)
                       VALUES (?, ?, ?, ?, ?, ?, ?);""",
                    (loc.immatriculation, loc.client, loc.categorie.name,
                     loc.date_debut.isoformat(), loc.date_fin_prevue.isoformat(),
                     loc.date_fin_reelle.isoformat() if loc.date_fin_reelle else None,
                     loc.tarif_jour),
                )
        logger.info("Base synchronisée avec la flotte.")

    # ----- 4 requêtes métier (jointures, agrégats, filtres) -----

    def vehicules_disponibles(self) -> list[sqlite3.Row]:
        """Requête 1 : véhicules au statut DISPONIBLE."""
        with self._connexion() as cnx:
            return cnx.execute(
                "SELECT immatriculation, marque, modele FROM vehicules "
                "WHERE statut = 'DISPONIBLE' ORDER BY marque;"
            ).fetchall()

    def chiffre_affaires_par_type(self) -> list[sqlite3.Row]:
        """Requête 2 : CA par type de véhicule (jointure + agrégat).

        Montant simplifié = nb_jours * tarif_jour, calculé en SQL.
        """
        with self._connexion() as cnx:
            return cnx.execute("""
                SELECT v.type AS type_vehicule,
                       ROUND(SUM(
                           MAX(1, julianday(COALESCE(l.date_fin_reelle,
                               l.date_fin_prevue)) - julianday(l.date_debut))
                           * l.tarif_jour
                       ), 2) AS chiffre_affaires
                FROM locations l
                JOIN vehicules v ON v.immatriculation = l.immatriculation
                GROUP BY v.type
                ORDER BY chiffre_affaires DESC;
            """).fetchall()

    def historique_entretien_par_vehicule(self, immatriculation: str) -> list[sqlite3.Row]:
        """Requête 3 : toutes les locations d'un véhicule donné (filtre).

        (Sert d'historique d'utilisation par véhicule.)
        """
        with self._connexion() as cnx:
            return cnx.execute(
                "SELECT client, date_debut, date_fin_prevue, tarif_jour "
                "FROM locations WHERE immatriculation = ? "
                "ORDER BY date_debut DESC;",
                (immatriculation.strip().upper(),),
            ).fetchall()

    def top_clients(self, limite: int = 3) -> list[sqlite3.Row]:
        """Requête 4 : clients ayant loué le plus de véhicules (agrégat + tri)."""
        with self._connexion() as cnx:
            return cnx.execute(
                "SELECT client, COUNT(*) AS nb_locations "
                "FROM locations GROUP BY client "
                "ORDER BY nb_locations DESC LIMIT ?;",
                (limite,),
            ).fetchall()
