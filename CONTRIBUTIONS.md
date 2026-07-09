# Contributions au projet

## Membres du groupe
- Magne Ndiaye 
- Rokhayatou Laye Yade
- Cecilia Ruth Mbogo Gnamalengoungou

## Répartition du travail

| Membre | Modules / classes développés | Contribution estimée |
|--------|-------------------------------|----------------------|
| Magne Ndiaye | `vehicules.py` (ABC + classes filles), `entretien.py` | 40% |
| Rokhayatou Laye Yade | `flotte.py` (Flotte, Location), `main.py` | 35% |
| Cecilia Ruth Mbogo Gnamalengoungou | `persistance_fichiers.py`, `base_donnees.py`, tests | 25% |

## Répartition par phase

| Phase | Responsable principal |
|-----------------------------------|------------------------|
| Conception (diagramme de classes) | Magne Ndiaye |
| Implémentation POO |Magne Ndiaye |
| Persistance fichiers (JSON/CSV) | Cecilia Ruth Mbogo Gnamalengoungou |
| Persistance SQL | Cecilia Ruth Mbogo Gnamalengoungou |
| Tests / gestion des exceptions | Rokhayatou Laye Yade |
| README / documentation | Rokhayatou Laye Yade |

## Difficultés rencontrées et résolution

1. **Reconstruire le bon type de véhicule depuis JSON.** Le JSON stocke tous
   les véhicules à plat. On a ajouté un champ `type` sérialisé pour recréer
   la bonne classe fille au chargement (`_dict_to_vehicule`). — Membre 3.

2. **Distinguer agrégation et composition dans le code.** Résolu en faisant
   créer les `Entretien` par le véhicule lui-même (composition) alors que les
   véhicules sont créés à l'extérieur puis ajoutés à la flotte (agrégation).
   — Membre 1.
