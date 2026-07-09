"""Enumérations métier du projet de gestion de flotte.

Les Enum permettent de représenter un ensemble FINI de valeurs possibles.
On évite ainsi les chaînes de caractères "magiques" (ex: "loue", "Loué", "LOUE"...)
qui sont sources d'erreurs. Ici, une seule valeur canonique par statut.
"""

from enum import Enum


class StatutVehicule(Enum):
    """Statut de disponibilité d'un véhicule dans la flotte."""

    DISPONIBLE = "Disponible"
    LOUE = "Loué"
    EN_MAINTENANCE = "En maintenance"
    HORS_SERVICE = "Hors service"


class CategorieClient(Enum):
    """Catégorie du client qui loue un véhicule.

    La catégorie influence le tarif appliqué (coefficient multiplicateur).
    """

    PARTICULIER = "Particulier"
    ENTREPRISE = "Entreprise"
    EVENEMENTIEL = "Événementiel"

    def coefficient(self) -> float:
        """Retourne le coefficient tarifaire lié à la catégorie de client."""
        coefficients = {
            CategorieClient.PARTICULIER: 1.0,
            CategorieClient.ENTREPRISE: 0.9,      # remise entreprise
            CategorieClient.EVENEMENTIEL: 1.2,    # majoration événementiel
        }
        return coefficients[self]
