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
| **Voix vidéo DEEG** | `deeg_voix_video_2026_11` | MP3 + WAV | estimation à vérifier | Chatterbox V3, référence privée HTTPS requise |

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

## Nouvelle voix issue d'une vidéo (novembre 2026)

Un profil distinct est prêt pour un essai de synthèse vocale conditionnée sur un extrait privé de 10 secondes, sans modifier les voix des modules existants. Consultez [le guide d'intégration](GUIDE_REFERENCE_VIDEO.md) avant de configurer le secret `DEEG_VIDEO_VOICE_REFERENCE_URL` et de lancer le workflow **DEEG - Profil vocal depuis video (prive)**. Cette procédure ne constitue pas un réentraînement de modèle.

### Utiliser cette voix dans le Studio vocal principal

Le moteur `voix_video` est également disponible sous **Actions → Studio vocal DEEG → Run workflow**.
Après avoir configuré le secret `DEEG_VIDEO_VOICE_REFERENCE_URL` décrit dans le guide,
choisir **moteur : voix_video**, saisir une phrase de **500 caractères maximum**, conserver
la vitesse **85**, le début de référence **0**, puis confirmer l'autorisation de reproduire
cette voix. Une exécution réussie remet **MP3, WAV et SRT** (sous-titrage estimé).
La référence originale n'est ni commitée ni jointe aux fichiers générés.

Cet ajout ne modifie pas le fonctionnement des moteurs existants `edge` et `piper`.

## Générer une voix directement depuis la vidéo sur votre ordinateur

La nouvelle commande `scripts/produire_voix_video_locale.py` utilise directement
la vidéo ou un fichier audio local : **aucun lien de téléchargement ni secret
GitHub n'est nécessaire**. Elle réalise d'abord l'extraction privée de dix
secondes, puis la synthèse Chatterbox V3 (après installation initiale du moteur).
Un diagnostic sans modèle est disponible avec `--diagnostic`.

Lancez `outils/lancer_voix_video_mac.command` avec le chemin de la vidéo,
ou suivez le [guide détaillé](GUIDE_REFERENCE_VIDEO.md#méthode-directe-sur-ordinateur--aucun-secret-github).
Les résultats sont exportés dans `sorties-video-local/` et sont ignorés par Git.
La reproduction d'une voix nécessite l'autorisation appropriée.

## Interface graphique locale (français)

Le Studio Vocal DEEG dispose également d'une **interface dans votre navigateur**,
sans envoyer la voix de référence sur un serveur distant. Sur un ordinateur
équipé de Python 3.11 et FFmpeg :

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-interface.txt
python -m pip install -r requirements-clonage.txt
python scripts/interface_studio.py
```

Sur Mac, exécutez `outils/ouvrir_studio_mac.command` (prérequis Python 3.11
et FFmpeg). L'interface s'ouvre à `http://127.0.0.1:7860`.
Lancez **Vérifier la référence**, renseignez un texte français, confirmez
les droits de reproduction vocale et cliquez sur **Générer la narration**.
Écoutez le résultat puis téléchargez les MP3, WAV, SRT et rapport de diagnostic.
L'interface ne partage pas son accès à Internet : elle écoute sur
`127.0.0.1` et la fonctionnalité de partage Gradio est désactivée.

**Important** : les fichiers sont générés uniquement si les dépendances et
les poids Chatterbox Multilingual V3 sont installés et que l'ordinateur
dispose de suffisamment de mémoire. La première utilisation nécessite
une connexion pour installer le modèle. Les sous-titres sont estimatifs.
