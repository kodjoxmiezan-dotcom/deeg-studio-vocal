# Studio Vocal Éboulé 🎙️

Studio de synthèse vocale et de narration en français pour les productions pédagogiques **DEEG**, **EXPERT PRÉPA** et les autres projets Éboulé.

Le dépôt GitHub conserve l'identifiant technique `deeg-studio-vocal` afin de préserver ses liens et automatisations existants. Le **nom public du studio** est désormais **Studio Vocal Éboulé**. Les noms des fichiers audio, identifiants et secrets techniques DEEG restent inchangés pour assurer la compatibilité.

## Démarrage rapide (GitHub Actions)

1. Ouvrez l’onglet **Actions** puis **Studio Vocal Éboulé**.
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

## Nouveau catalogue des voix françaises (novembre 2026)

Le fichier [`profils_vocaux/catalogue.json`](profils_vocaux/catalogue.json) décrit **10 profils** : cinq voix Edge TTS, quatre voix Piper et le profil vidéo DEEG expérimental. Un profil n'est **pas** un modèle IA téléchargé ou une voix déjà approuvée. Les nouvelles voix doivent être testées à l'écoute.

### Lancer une narration depuis un navigateur — sans rien installer sur Mac

1. Ouvrir **Actions → Studio Vocal Éboulé → Run workflow**.
2. Choisir `moteur = edge` ou `piper`, puis la **voix_catalogue** correspondante.
3. Coller le texte dans `texte`, régler la vitesse (85 % conseillé), puis lancer.
4. Télécharger les fichiers MP3, WAV et SRT sous les **Artifacts** de l'exécution.

Si `voix_catalogue = automatique`, l'ancien champ libre `voix` reste utilisé. Pour Piper, un nom de voix Edge dans le champ libre revient à l'ancienne voix Piper Tom. Une présélection incompatible avec le moteur est rejetée explicitement.

| Moteur | Voix présélectionnées | État |
| --- | --- | --- |
| Edge TTS | Henri, Denise, Éloïse, Rémy multilingue, Vivienne multilingue | Nouvelles voix à écouter |
| Piper TTS | Tom, Siwis, UPMC, Gilles | Télécharger les modèles à l'exécution ; licences distinctes |
| Chatterbox V3 | Voix vidéo DEEG | Référence privée et autorisation requises ; expérimental |

### Comparer les cinq voix Edge avec le même texte

Ouvrir **Actions → DEEG - Comparatif de 5 voix francaises → Run workflow**. Entrer un court passage sans informations personnelles. Ce workflow produit cinq artefacts séparés, chacun avec MP3, WAV, SRT et rapport. Écouter chaque MP3 avant de retenir une voix pour DEEG ou EXPERT PRÉPA CM2.

Ce comparatif utilise le service Edge TTS via une bibliothèque non officielle : il peut échouer si le service modifie son accès ou ses conditions. Aucune génération n'est garantie avant une exécution réussie. Les fichiers sont conservés sept jours.

**Sécurité et droits :** ne pas publier de référence vocale privée ou de données d'élèves. Vérifier les droits et licences de chaque modèle avant une utilisation publique. La variante B des narrations DEEG existantes n'est pas modifiée.

### Contrôle automatique du catalogue

Le workflow **Audit catalogue vocal DEEG** exécute les tests Python sur toute modification proposée au catalogue ou aux scripts associés. Les tests ne prétendent pas démontrer une bonne qualité vocale : ils vérifient la sélection, les identifiants et la rétrocompatibilité.

## Essai séparé de Kokoro 82M — moteur expérimental

Kokoro constitue un **quatrième moteur** à essayer, distinct des moteurs Edge, Piper et Chatterbox. Sa voix française présélectionnée est `ff_siwis`. L'essai est disponible **en ligne par GitHub Actions** et n'exige aucune installation sur le Mac. Il ne remplace pas les voix DEEG actuellement utilisées et n'active aucune reproduction de voix personnelle.

1. Ouvrir **Actions → EXPERIMENTAL - Kokoro 82M voix francaise → Run workflow**.
2. Fournir un passage français court (800 caractères maximum) et choisir la vitesse, par défaut 85 %.
3. Après réussite, ouvrir l'artefact `kokoro-ff-siwis-...` et écouter le MP3 ; le WAV, les sous-titres SRT *estimés* et le rapport JSON sont également fournis.

La première exécution télécharge les poids du modèle sur un exécuteur GitHub, ce qui peut être lent ou échouer. Cet essai n'est pas validé pour une utilisation de production tant que la synthèse, l'intonation, les coûts et les droits de diffusion n'ont pas été contrôlés. Kokoro-82M est publié sous licence Apache-2.0 : [fiche du modèle](https://huggingface.co/hexgrad/Kokoro-82M). Le pilote est isolé dans `scripts/essai_kokoro_fr.py` et `requirements-kokoro.txt`.

## 🎙️ Podcastfy — créer un podcast à deux voix en français

Cette fonctionnalité utilise le vrai moteur open source [Podcastfy.ai](https://github.com/souzatharsis/podcastfy) (licence Apache-2.0), avec **Microsoft Edge TTS** pour lire le dialogue en français. **Aucun abonnement ni clé API n'est nécessaire en mode dialogue.** Les éventuels quotas et limitations du service Edge peuvent évoluer.

### Démarrer gratuitement depuis le navigateur

1. Ouvrir **Actions → Studio Vocal Éboulé - Créer un podcast (Podcastfy) → Run workflow**.
2. Conserver `mode = dialogue`. Laisser le champ `dialogue` vide pour l'exemple prêt à produire.
3. Choisir deux voix françaises différentes, par défaut Denise (animatrice) et Henri (expert).
4. Cliquer sur **Run workflow** et télécharger l'artefact `studio-eboule-podcastfy-...` après réussite : MP3, WAV, transcription, SRT estimé et rapport technique.

Pour rédiger un épisode à partir de ton propre dialogue, utilise une alternance stricte :

```text
ANIMATRICE: Bonjour à toutes et à tous. Quel est notre sujet aujourd'hui ?
EXPERT: Nous allons expliquer les principes d'une école inclusive.
ANIMATRICE: Pourquoi ce sujet est-il important ?
EXPERT: Parce que tous les enfants doivent avoir leur chance d'apprendre.
```

Sur une seule ligne dans GitHub Actions, remplace les retours à la ligne par ` | ` entre les répliques. Le fichier public d'exemple est [`podcasts/exemple_dialogue.txt`](podcasts/exemple_dialogue.txt). Les noms `ANIMATEUR`, `EXPERTE`, `INVITÉ` sont également acceptés.

### Mode IA facultatif : transformer un texte source en podcast

Pour générer le dialogue automatiquement avec **Gemini**, il faut configurer le secret GitHub `PODCAST_GEMINI_API_KEY`, choisir `mode = ia_gemini`, ajouter le contenu source (ou utiliser l'exemple), puis cocher `autoriser_api`. Sans secret ni autorisation explicite, ce mode refuse de démarrer. La clé est uniquement utilisée pour la génération du dialogue ; **Edge produit toujours la voix**.

**Attention au coût :** Gemini peut proposer des quotas gratuits selon ton offre, ton modèle et ta région, mais la gratuité n'est pas garantie. Ce module ne déclenche **aucun abonnement ou achat** ; vérifie tes paramètres de facturation avant d'activer l'option.

### Confidentialité, qualité et limites

- Le dépôt est **public** : les textes soumis à GitHub Actions, les journaux d'exécution et les artefacts ne constituent pas un environnement privé. Ne jamais transmettre de données d'élèves, de documents confidentiels ou d'enregistrements vocaux sensibles.
- Les sous-titres SRT sont **estimés** à partir de la durée ; vérifier le minutage avant le montage.
- Les dialogues IA doivent être relus et validés avant diffusion. Cette première intégration accepte du texte saisi ; l'import de PDF et de liens web pourra être ajouté ensuite.
- Aucun changement aux moteurs de synthèse ou aux workflows existants de DEEG et EXPERT PRÉPA.

Dépendance optionnelle : `requirements-podcastfy.txt` ; code d'intégration : `scripts/podcastfy_studio.py` ; tests : `tests/test_podcastfy_studio.py`.

## 🎬 PixVerse — vidéo IA (pilotage optionnel)

Le studio possède maintenant un **connecteur PixVerse API v2** pour préparer des scènes « texte → vidéo » ou « image → vidéo ». Ce connecteur est séparé de Podcastfy, Edge, Piper, Chatterbox et Kokoro.

**Démarrage gratuit :** ouvrir **Actions → Studio Audiovisuel Éboulé - PixVerse (simulation par défaut) → Run workflow**, conserver `operation = simulation`, décrire la scène et consulter le rapport JSON. Cette opération **ne génère pas de vidéo** et ne débite **aucun crédit**.

La création réelle demande une clé `PIXVERSE_API_KEY` placée dans les secrets du dépôt, `operation = generation`, l'autorisation explicite des crédits et un plafond de coût indicatif supérieur ou égal au barème officiel. **Le plafond local n'est pas un plafond de facturation garanti par PixVerse.** Le modèle V6 sans audio est seul disponible dans ce premier module.

Pour les images, PixVerse exige un `img_id` obtenu après téléversement préalable dans sa plateforme. La fonction de téléversement depuis le Mac ou Google Flow n'est pas encore incluse. Les vidéos créées restent sur PixVerse ; le workflow ne télécharge pas automatiquement les MP4 et ne publie pas les liens privés sans option explicite.

Consulter le [**guide complet PixVerse**](pixverse/README.md) et la [**liste des onze solutions audiovisuelles**](INTEGRATIONS_AUDIOVISUEL.md).

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

Le moteur `voix_video` est également disponible sous **Actions → Studio Vocal Éboulé → Run workflow**.
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

Le Studio Vocal Éboulé dispose également d'une **interface dans votre navigateur**,
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


### Vérifier et écouter la référence avant la synthèse

Dans l'interface locale, sélectionnez la vidéo d'origine puis utilisez
**▶ Écouter les 10 secondes choisies**. Le studio extrait uniquement les dix
secondes demandées et les lit dans le navigateur local : cela facilite le
choix d'un passage clair, sans musique et avec une seule voix.

La prévisualisation est conservée seulement sur l'ordinateur, sous
`sorties-video-local/reference_previsualisation.wav` (dossier ignoré par Git).
L'ancien aperçu est supprimé avant chaque nouvel essai, même si la nouvelle
extraction échoue. Les tests automatiques contrôlent ce comportement.
