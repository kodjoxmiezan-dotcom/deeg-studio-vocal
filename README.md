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


## Essai de reproduction de la voix Tanguy (expérimental)

Ce module utilise [Chatterbox Multilingual V3](https://github.com/resemble-ai/chatterbox), avec la **voix Tanguy de HeyGen comme référence** uniquement si l'utilisateur dispose d'une autorisation explicite de la réutiliser en dehors de HeyGen. Il ne s'agit pas d'un modèle réentraîné : Chatterbox conditionne chaque génération sur un échantillon de voix.

**La référence vocale ne doit pas être envoyée dans ce dépôt public.** Le workflow la récupère à l'aide d'un secret GitHub nommé `DEEG_TANGUY_REFERENCE_URL`. Il suffit d'utiliser le lien HTTPS direct de l'enregistrement autorisé, puis de procéder ainsi :

1. Ouvrez **Settings → Secrets and variables → Actions → New repository secret**.
2. **Name :** `DEEG_TANGUY_REFERENCE_URL` ; **Secret :** le lien HTTPS de l'enregistrement Tanguy.
3. Ouvrez **Actions → Essai de voix de reference DEEG → Run workflow**.
4. Gardez **vitesse 85** et **début référence 23 secondes** si le fichier contient la narration complète de 72,7 secondes. Pour un court extrait préparé de 10 secondes, choisissez début **0**.
5. Après une exécution réussie, téléchargez le fichier **essai-voix-tanguy-deeg-…** sous *Artifacts*. Il contient uniquement le MP3 et le WAV générés, le texte de la synthèse et le rapport, **jamais l'extrait vocal de référence**.

⚠️ **Limite de calcul :** le modèle français V3 comporte environ 500 millions de paramètres. Sur l'exécuteur GitHub gratuit **sans GPU**, les dépendances et les modèles sont volumineux, et la synthèse peut être très lente, échouer pour manque de mémoire ou dépasser la limite de durée. Le workflow est donc **manuel uniquement**, pour un essai très court. Une machine avec GPU est recommandée pour la production des longs modules.

**Confidentialité :** ne collez jamais le lien de référence dans un fichier public ou le texte d'un workflow. Ne publiez pas de voix clonée prétendant être un enregistrement authentique d'une personne. Le résultat peut différer de Tanguy, même avec une référence autorisée.



## Comparatif d'optimisation de la voix de référence (26 octobre 2026)

Le workflow manuel **Essai de voix de reference DEEG** génère désormais **deux variantes sur le même texte** (vitesse 85 % par défaut), à partir d'extraits différents de la référence privée :

- **A_fidelite** : priorité à la stabilité du timbre, extrait explicatif, `cfg_weight=0.48` et `exaggeration=0.38`.
- **B_institutionnel** : expressivité réduite pour un ton pédagogique posé, extrait plus calme, `cfg_weight=0.30` et `exaggeration=0.26`.

Les sorties audio sont `A_fidelite.mp3/.wav` et `B_institutionnel.mp3/.wav`, accompagnées du rapport comparatif. Le texte d'essai par défaut est : « Chaque matin, les élèves arrivent à l'école. Filles et garçons s'y retrouvent. Ont-ils les mêmes chances ? »

Les variantes sont des hypothèses de réglages ; **leur ressemblance exacte n'est pas démontrée**. La sélection du profil définitif dépend de l'écoute par le responsable DEEG. La référence audio n'est jamais publiée dans le dépôt ni dans les artefacts.

