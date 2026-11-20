# PixVerse — module vidéo du Studio Audiovisuel Éboulé

Le module utilise les endpoints officiels PixVerse API v2 sans modifier les moteurs vocaux et Podcastfy.

## Simulation gratuite et sans clé
Dans GitHub Actions, ouvrir « Studio Audiovisuel Éboulé - PixVerse (simulation par défaut) » puis Run workflow. Garder « operation = simulation ». Choisir texte ou image, les paramètres de durée et de résolution. Le rapport JSON obtenu présente les paramètres et une estimation de crédits, mais ne crée aucune vidéo et n'effectue aucun appel réseau à PixVerse.

## Génération réelle, facultative et payante en crédits
1. Examiner les prix sur https://docs.platform.pixverse.ai/pixverse-api-pricing-2394995m0 et vérifier les conditions de son compte API.
2. Créer une clé sur https://platform.pixverse.ai et la stocker dans GitHub : Settings → Secrets and variables → Actions → New repository secret ; nom PIXVERSE_API_KEY. Ne jamais l'insérer dans un prompt ou un commit.
3. Dans le workflow, choisir « operation = generation », valider « autoriser_credits = true » et indiquer « plafond_indicatif » au moins égal à l'estimation.
4. Contrôler le compte PixVerse. Le plafond sert de barrière locale, mais ne garantit PAS une limite de facture imposée par le fournisseur.
5. Le rapport contient un video_id. L'URL n'est incluse que si « publier_url = true » a été activé.

Barème indicatif documenté pour PixVerse V6 sans audio, novembre 2026 :
360p : 5 crédits/s ; 540p : 7 ; 720p : 9 ; 1080p : 18.
L'application PixVerse et l'API disposent de crédits distincts.

## Texte vers vidéo
Sélectionner « mode = texte », décrire le plan et choisir 16:9 pour les films ou 9:16 pour les vidéos verticales. La création audio native est désactivée, le son pouvant ensuite être créé avec Studio Vocal Éboulé.

## Image vers vidéo
Sélectionner « mode = image » puis renseigner un img_id déjà obtenu dans PixVerse et le prompt d'animation. Le module ne téléverse PAS encore les fichiers images locaux ; il n'est pas possible de fournir simplement un chemin Mac ou une image non hébergée. Pour tes scènes, vérifier l'image maîtresse avant animation.

## Consulter un résultat
Choisir « operation = statut », renseigner le video_id existant et disposer de la clé. Il s'agit seulement d'un appel de consultation, sans création de tâche supplémentaire. L'URL de sortie n'est pas publiée par défaut.

## Confidentialité
Le dépôt est public : prompts et rapports dans les artefacts sont potentiellement consultables. Ne pas soumettre d'images, de vidéos ou de textes confidentiels. Les droits d'utilisation des personnages et images doivent être respectés. La clé reste dans le secret GitHub. Le script ne télécharge pas de MP4 et ne retente jamais automatiquement une création facturable.

## Documentation officielle
- https://docs.platform.pixverse.ai/start-here-2394989m0
- https://docs.platform.pixverse.ai/text-to-video-generation-13016634e0
- https://docs.platform.pixverse.ai/image-to-video-generation-13016633e0
- https://docs.platform.pixverse.ai/query-task-status-43051212e0
- https://docs.platform.pixverse.ai/pixverse-api-pricing-2394995m0
- https://github.com/PixVerseAI/cli
- https://github.com/PixVerseAI/skills
