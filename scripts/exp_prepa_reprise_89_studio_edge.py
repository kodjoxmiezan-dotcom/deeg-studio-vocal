"""EXPERT PRÉPA CM2: complément des dictées manquantes dans Studio Vocal DEEG.
Deux voix Edge natives du dépôt, clairement identifiées comme VOIX DE SECOURS.
AUCUNE prétention de reproduire les timbres HeyGen déjà retenus.

Les noms des signes de ponctuation sont synthétisés séparément, puis réutilisés
tels quels. Cela limite les variations, mais ne remplace pas l'écoute humaine.
"""
from __future__ import annotations
import argparse
import asyncio
import csv
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from pydub import AudioSegment
import edge_tts

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experts_prepa_cm2_audio" / "SOURCES_CATALOGUE_108.csv"
MISSING = ROOT / "experts_prepa_cm2_audio" / "MANQUANTS_89.csv"
OUT = ROOT / "sorties-cm2-studio-secours"
CACHE = OUT / ".cache"
OUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
VOICES = {"H": "fr-FR-HenriNeural", "F": "fr-FR-DeniseNeural"}
# Les voix ci-dessus sont françaises (France), et NON les deux voix HeyGen retenues.
PUNCT = {
    ",": "virgule", ".": "point", "?": "point d'interrogation",
    "!": "point d'exclamation", ":": "deux-points",
    ";": "point-virgule", "«": "ouvrez les guillemets",
    "»": "fermez les guillemets", "…": "points de suspension"
}
PUNCT_RE = re.compile(r"([,.;:!?«»…])")
SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜ«])")
SILENT = AudioSegment.silent(duration=200, frame_rate=24000)
MAX_RETRIES = 3

def load_records():
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        catalog = {r["id"]: r for r in csv.DictReader(f)}
    with MISSING.open(encoding="utf-8-sig", newline="") as f:
        missing = list(csv.DictReader(f, delimiter=";"))
    selected = []
    for r in missing:
        label = r["Voix"]
        code = "H" if label == "Masculine personnalisée" else "F" if label == "Féminine Sabine" else None
        if code is None or r["ID"] not in catalog:
            raise ValueError("Entrée manquante inconnue: " + repr(r))
        selected.append((catalog[r["ID"]], code))
    if len(selected) != 89 or len({(r["id"], code) for r,code in selected}) != 89:
        raise ValueError("Liste des 89 reprises incorrecte ou doublons")
    if len(catalog) != 108:
        raise ValueError("Le catalogue doit contenir 108 dictées")
    return catalog, selected

def normalize(s):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip()

def sentences(text):
    result = [x.strip() for x in SENT_RE.split(text) if x.strip()]
    if not result or normalize(" ".join(result)) != normalize(text):
        raise ValueError("Découpage des phrases non fidèle")
    return result

def spoken_fragments(sentence):
    parts = PUNCT_RE.split(sentence)
    output = []
    reconstructed = ""
    for part in parts:
        if not part:
            continue
        reconstructed += part
        if part in PUNCT:
            output.append(("punct", PUNCT[part], part))
        elif part.strip():
            output.append(("text", part.strip(), ""))
    if reconstructed != sentence:
        raise ValueError("Une portion du texte a été perdue")
    return output

async def synth(voice, text, rate="-15%"):
    # Cache vocal : ne jamais mélanger deux voix ou deux vitesses.
    key = hashlib.sha256((voice + "\n" + rate + "\n" + text).encode("utf-8")).hexdigest()
    file = CACHE / (key + ".mp3")
    if not file.exists():
        for retry in range(MAX_RETRIES):
            try:
                temp = CACHE / (key + ".part.mp3")
                await edge_tts.Communicate(text, voice, rate=rate).save(str(temp))
                if not temp.is_file() or temp.stat().st_size < 900:
                    raise RuntimeError("Audio de synthèse vide")
                temp.replace(file)
                break
            except Exception:
                if retry == MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2 ** retry)
    audio = AudioSegment.from_file(file, format="mp3")
    if len(audio) < 160:
        raise RuntimeError("Durée vocale trop courte: " + text)
    return audio.set_frame_rate(24000).set_channels(1).set_sample_width(2)

def pause(ms):
    return AudioSegment.silent(duration=int(ms), frame_rate=24000).set_channels(1).set_sample_width(2)

async def build_sentence(sentence, voice):
    output = AudioSegment.empty()
    trace = []
    for kind, value, character in spoken_fragments(sentence):
        if kind == "text":
            chunk = await synth(voice, value, "-16%")
            output += chunk
            output += pause(120)
        else:
            # Clip isolé unique « virgule », « point », etc. : ne pas laisser le TTS
            # avaler la fin du mot quand il suit immédiatement la phrase.
            chunk = await synth(voice, value + ".", "-24%")
            output += pause(130) + chunk + pause(240)
            trace.append({"signe": character, "nom": value, "clip_ms": len(chunk)})
    return output, trace

async def build(record, code):
    voice = VOICES[code]
    title, original = record["titre"], record["texte"]
    segments = sentences(original)
    rendered = []
    expected = []
    for sentence in segments:
        audio, events = await build_sentence(sentence, voice)
        rendered.append(audio)
        expected.extend(events)
    if not rendered:
        raise ValueError("Aucune phrase")
    # L'enregistrement est complet : lecture entière une fois, phrase par phrase
    # trois fois, relecture finale. Aucune annonce de « première phrase ».
    intro = await synth(voice, "EXPERT PRÉPA. Dictée. " + title + ". Écoute le texte entier.", "-16%")
    consigne = await synth(voice, "Écris maintenant. Utilise la pause du lecteur si nécessaire.", "-16%")
    end = await synth(voice, "Relis ton travail. Vérifie les accords, les accents et la ponctuation.", "-16%")
    parts = [intro, pause(650)]
    for block in rendered:
        parts.extend([block, pause(220)])
    parts.extend([pause(1200), consigne, pause(500)])
    for i, block in enumerate(rendered):
        for rep in range(3):
            parts.append(block)
            parts.append(pause(750 if rep < 2 else 1550))
    parts.extend([end, pause(400)])
    for block in rendered:
        parts.extend([block, pause(160)])
    # Répartition des éventuelles secondes restantes entre les pauses naturelles.
    total = sum(len(s) for s in parts)
    target = 120000
    if total < target:
        extra = target - total
        positions = [i for i,p in enumerate(parts) if len(p) in (220, 500, 650, 750, 1200, 1550, 400, 160)]
        if positions:
            q, r = divmod(extra, len(positions))
            for idx,p_index in enumerate(positions):
                parts[p_index] = parts[p_index] + pause(q + (1 if idx < r else 0))
        else:
            parts.append(pause(extra))
    audio = AudioSegment.empty()
    for part in parts:
        audio += part
    # Ne jamais accélérer exagérément ni couper une fin pour viser 2 minutes.
    target_file = OUT / f"{record['id']}_{code}_STUDIO_DEEG_SECOURS.mp3"
    audio.export(target_file, format="mp3", bitrate="96k")
    result = {
        "id": record["id"], "titre": title, "voix": code,
        "moteur": "Studio DEEG / Edge TTS",
        "voix_technique": voice, "voix_anterieure_preservee": False,
        "statut": "PRODUIT_TECHNIQUEMENT_NON_VALIDE_A_L_ECOUTE",
        "fichier": target_file.name, "duree_s": round(len(audio) / 1000, 2),
        "phrases": len(segments), "repetitions_par_phrase": 3,
        "ponctuation_par_lecture": expected,
        "points_attention": ["Vérifier le mot virgule EN ENTIER", "Vérifier les chiffres et noms propres",
                             "Voix de secours française, pas une voix ivoirienne"],
        "sha256": hashlib.sha256(target_file.read_bytes()).hexdigest()
    }
    return result

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=6)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    if not (0 <= args.shard < args.shards):
        raise ValueError("Index de lot invalide")
    catalog, selected = load_records()
    jobs = [(r,code) for i,(r,code) in enumerate(selected) if i % args.shards == args.shard]
    if args.limit:
        jobs = jobs[:args.limit]
    results = []
    failures = []
    for idx,(record,code) in enumerate(jobs, start=1):
        try:
            result = await build(record,code)
            results.append(result)
            print(f"OK {idx}/{len(jobs)} : {record['id']} / {code} : {result['duree_s']} s", flush=True)
        except Exception as e:
            failures.append({"id": record["id"], "voix": code, "erreur": str(e)})
            print(f"ERREUR {record['id']} / {code} : {e}", file=sys.stderr, flush=True)
    report = {"shard": args.shard, "total_attendu": len(jobs),
              "produits": len(results), "erreurs": failures, "pistes": results,
              "AVERTISSEMENT": "Voix de secours Edge; vérifier à l'écoute tous les signes; ne pas diffuser aux élèves."}
    (OUT / f"CONTROLE_LOT_{args.shard:02d}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if failures:
        raise SystemExit(f"{len(failures)} erreurs dans ce lot")

if __name__ == "__main__":
    asyncio.run(main())
