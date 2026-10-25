# DEEG Studio Vocal 🎙️

Studio de synthèse vocale en français pour la formation DEEG, indépendant de l’application pédagogique.

## Démarrage rapide (GitHub Actions)

1. Ouvrez l’onglet **Actions** puis **Studio vocal DEEG**.
2. Cliquez sur **Run workflow** ; choisissez `edge`, la voix `fr-FR-HenriNeural` et la vitesse `85`.
3. Laissez le champ texte vide pour utiliser `narrations/texte.txt`, ou collez un court passage.
4. Après réussite, ouvrez l’exécution et téléchargez **Artifacts → narration-deeg-…** : les fichiers MP3, WAV, SRT, texte et rapport JSON sont inclus.

Une modification de `narrations/texte.txt` dans GitHub déclenche aussi la génération automatiquement.

## Moteurs de synthèse

| Moteur | Exemple de voix | Audio | Sous-titres | Connexion |
| --- | --- | --- | --- | --- |
| **Edge TTS** | `fr-FR-HenriNeural` | MP3 + WAV | minutage fourni par le moteur | Internet requis |
| **Piper TTS** | `fr_FR-tom-medium` | MP3 + WAV | estimation à vérifier | modèle téléchargé avant usage, puis possible hors ligne |

**Important :** ce projet ne reproduit **pas** la voix Tanguy de HeyGen. L’accès Edge TTS utilise le service en ligne de Microsoft Edge via une bibliothèque communautaire non officielle ; disponibilité et restrictions peuvent évoluer.

La vitesse initiale est de **85 %**, proche de notre rythme pédagogique choisi pour DEEG. Elle se règle entre 60 et 130 %.

## Modifier les textes depuis ChatGPT

Demandez dans ChatGPT : « Dans mon dépôt GitHub `kodjoxmiezan-dotcom/deeg-studio-vocal`, remplace `narrations/texte.txt` par [votre texte] ». Le commit peut déclencher GitHub Actions. Les fichiers générés apparaissent dans les *Artifacts* de l'exécution.

## Utilisation sur ordinateur

Installez Python 3.11 ou plus récent et FFmpeg :

```bash
python -m pip install -r requirements-edge.txt
python scripts/generer.py
```

Pour Piper, installez `requirements-piper.txt` et sélectionnez `DEEG_ENGINE=piper` et `DEEG_VOICE=fr_FR-tom-medium`. Le téléchargement initial du modèle nécessite Internet ; consultez les licences propres à chaque modèle vocal.

## Sécurité et confidentialité

Ce dépôt est **public** : ne publiez ni mots de passe, ni données d’élèves, ni textes confidentiels. Les exécuteurs standards GitHub Actions sont gratuits pour les dépôts publics, conformément aux conditions GitHub. Les résultats sont conservés temporairement comme *Artifacts* (7 jours dans cette configuration).

## Références

- [Piper TTS](https://github.com/OHF-Voice/piper1-gpl)
- [Edge TTS](https://github.com/rany2/edge-tts)
- [GitHub Actions](https://docs.github.com/en/actions)
