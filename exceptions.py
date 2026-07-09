"""Exceptions personnalisées (métier) du projet.

Le sujet impose AU MOINS 2 exceptions personnalisées.
On en définit plusieurs pour couvrir les cas d'erreur propres au domaine
de la location de véhicules. Elles héritent toutes d'une exception racine
FlotteError, ce qui permet d'attraper "toutes les erreurs métier" d'un coup
si besoin (except FlotteError).
"""


class FlotteError(Exception):
    """Classe racine de toutes les exceptions métier du projet."""


class VehiculeIndisponibleError(FlotteError):
    """Levée quand on tente de louer un véhicule qui n'est pas disponible."""


class DonneesInvalidesError(FlotteError):
    """Levée quand une entrée utilisateur / une donnée est invalide."""


class LocationIntrouvableError(FlotteError):
    """Levée quand on tente de clôturer une location qui n'existe pas."""
