# Nouvelle voix vidéo DEEG — novembre 2026

Ce guide accompagne le profil `profils_vocaux/voix_video_2026.json`.
La voix de cette vidéo est conservée comme **référence privée** et utilisée
par Chatterbox Multilingual V3 pour conditionner les nouvelles narrations.
**Aucun modèle de poids n'est réentraîné** : la ressemblance doit être jugée
par l'écoute du premier fichier synthétisé.

## Source et préparation

La vidéo originale fournie dure **20,01 secondes** ; sa version de 60 secondes
est une répétition trois fois du même enregistrement. Utiliser l'original de
20 secondes, et non la boucle. Un extrait de **10 secondes** suffit pour
l'essai du moteur. La référence doit, idéalement, contenir une seule voix,
sans musique ni bruit de fond.

Le script `scripts/preparer_reference_video.py` extrait un WAV mono 24 kHz,
puis contrôle la durée, le volume et l'écrêtage. Il ne peut **ni retirer
automatiquement une musique de fond ni garantir l'identité de la voix**.
Écouter l'extrait avant de le retenir.

## Lancer l'essai sécurisé avec GitHub Actions

1. Conserver l'audio **hors de ce dépôt public**. Héberger la source originale
   de 20 secondes en téléchargement direct HTTPS privé, idéalement avec un
   lien à durée de vie limitée. Vérifier l'autorisation de reproduction vocale.
2. Ouvrir **Settings → Secrets and variables → Actions → New repository secret**.
   Nom : `DEEG_VIDEO_VOICE_REFERENCE_URL`. Valeur : URL HTTPS directe vers
   la source privée. Ne jamais coller ce lien dans le README, une issue ou
   une exécution de workflow visible publiquement.
3. Après fusion de la proposition de modification, ouvrir
   **Actions → DEEG - Profil vocal depuis video (prive) → Run workflow**.
4. Renseigner une courte phrase en français, vitesse `85`, début
   `0`. Cocher la confirmation d'autorisation.
5. En cas de réussite, télécharger dans **Artifacts** :
   `essai-nouvelle-voix-deeg-…`. Il contient MP3, WAV, texte de synthèse
   et rapport. **Aucune voix source n'y est jointe.**
6. Écouter la synthèse pour valider le timbre, la prononciation, le
   débit et les intonations institutionnelles. Si nécessaire, essayer un
   extrait commençant à `5` ou à `10` secondes.

Le moteur de synthèse utilise le script déjà présent
`scripts/cloner_voix.py`. Les autres voix, notamment la voix B et
les travaux antérieurs, ne sont pas modifiées. Pour faire de cette voix
la nouvelle voix principale des modules, une étape ultérieure de
validation puis d'intégration aux pipelines de production sera nécessaire.

## Confidentialité et limites

- Utiliser uniquement une voix créée par vous ou employée avec
  l'autorisation nécessaire ; si la voix appartient à une personne,
  obtenir son consentement explicite.
- Le dépôt est public, mais le contenu de la référence n'est jamais
  ajouté au contrôle de version ni aux artefacts.
- Le workflow nécessite une référence HTTPS privée configurée en secret.
  Le connecteur GitHub ne permet pas de renseigner ce secret à votre place.
- Les calculs Chatterbox peuvent être lents et éventuellement échouer
  sur un exécuteur GitHub Actions sans GPU. Le fonctionnement du moteur
  n'est pas garanti par les seuls tests du préparateur.

## Méthode directe sur ordinateur : aucun secret GitHub

Pour produire une nouvelle voix **sans exposer votre vidéo** et sans renseigner
le secret GitHub `DEEG_VIDEO_VOICE_REFERENCE_URL`, une commande locale est
maintenant disponible. Le modèle Chatterbox doit être téléchargé une première
fois depuis Internet ; il n'est pas intégré au dépôt.

**Pré-requis** : Python 3.11, FFmpeg, Git, mémoire suffisante et accès Internet
pour la première installation. Sur Mac, ouvrez le Terminal à la racine du dépôt :

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-clonage.txt
python scripts/produire_voix_video_locale.py \
    --source "/chemin/vers/gemini_generated_video_24930477.mp4" \
    --diagnostic
```

Le diagnostic contrôle la source et l'extrait de 10 secondes sans charger le
modèle IA. Pour créer une narration en français, après confirmation de votre
autorisation de reproduire la voix :

```bash
python scripts/produire_voix_video_locale.py \
    --source "/chemin/vers/gemini_generated_video_24930477.mp4" \
    --texte "Bienvenue dans ATHÉNÉE. Ensemble, renforçons nos pratiques pédagogiques." \
    --vitesse 85 --debut 0 --autorisation
```

Fichiers produits dans `sorties-video-local/` :
- `DEEG_voix_video.wav`
- `DEEG_voix_video.mp3`
- `DEEG_voix_video.srt` : sous-titres approximatifs à vérifier
- `texte_narre.txt`, `rapport.json`

Vous pouvez également lancer `outils/lancer_voix_video_mac.command` depuis
la racine du dépôt en lui donnant en argument le chemin local de la vidéo ;
il demande la confirmation d'autorisation et installe les dépendances
lors de la première utilisation.

**Limites vérifiables** : les tests automatisés contrôlent la préparation
audio, la confidentialité des chemins et les sorties simulées. Ils ne
prouvent pas la ressemblance du timbre ni la réussite de l'inférence réelle
sur votre matériel. Sans téléchargement du modèle Chatterbox, la
génération ne peut pas s'exécuter. Le dossier `sorties-video-local/`
est exclu de Git pour éviter les publications accidentelles.
