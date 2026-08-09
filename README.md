# Animanki

Base maître de ton deck Anki **Animanki V8**.

## État synchronisé

- **22 notes** actuellement présentes dans Anki.
- **110 cartes** (5 cartes par note).
- Modèle Anki V8 figé.
- `database.json` est désormais la source de vérité.
- `template/Animanki_V8_seed.apkg.b64` contient uniquement le modèle/deck V8, sans notes ni progression.

## Workflow

Tu peux maintenant dire à ChatGPT :

> Ajoute Kaiju No. 8 Saison 2

ChatGPT :
1. vérifie les informations de l'anime ;
2. ajoute une entrée dans `database.json` avec `exported: false` ;
3. génère un petit `.apkg` depuis le seed V8 ;
4. passe l'entrée à `exported: true` après génération ;
5. te fournit uniquement le paquet d'ajout.

Tu importes ce petit paquet dans ton Animanki existant. Tes anciennes cartes et leur progression ne sont pas reconstruites.

## Fichiers

- `database.json` — base de toutes les saisons synchronisées.
- `model_v8.json` — IDs, champs et cartes du modèle figé.
- `template/Animanki_V8_seed.apkg.b64` — seed V8 encodé en Base64 sans notes.
- `build_incremental.py` — générateur local de paquets d'ajout.
- `output/` — destination par défaut des nouveaux `.apkg`.

## Génération locale

Prérequis : Python 3 et `zstd`.

```bash
python build_incremental.py
```

Le script prend seulement les notes avec `"exported": false`.

## Règle importante

Ne change pas les identifiants `model_id` et `deck_id`. Ils permettent aux nouveaux paquets de s'intégrer au même type de note V8 dans Anki.
