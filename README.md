# Animanki

Base maître pour générer des paquets d'ajout Anki compatibles avec le modèle Japanimation V8.

## Principe

Le deck Anki principal reste dans Anki avec toute sa progression. Ce dépôt conserve uniquement la définition du modèle V8 et la base des saisons déjà enregistrées.

À chaque nouvel anime, on ajoute une entrée à `database.json`, puis on génère un petit `.apkg` d'ajout contenant uniquement la nouvelle note et ses 5 cartes.

## Champs V8

Anime, Titre original, Studio, Compositeur OST, Œuvre originale, Saison, Période de diffusion, Créateur original, Nombre d'épisodes, Opening 1, Opening 2, Ending 1, Ending 2, Affiche.

Les champs Opening/Ending sont conservés dans la note mais ne génèrent pas de cartes dédiées.
