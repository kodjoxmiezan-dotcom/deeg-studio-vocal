"""Conclusion intégrale du module 1 avec la voix de référence DEEG B."""
from __future__ import annotations

import json
import os
from pathlib import Path
import torch
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
import optimiser_tanguy as opt

QUESTIONS = [
    "Quelles situations relèvent des rôles sociaux de genre ou d’inégalités de traitement ?",
    "Quels obstacles limitent la participation et la réussite de certains élèves ?",
    "Quelles premières mesures l’établissement pourrait-il adopter pour devenir plus équitable et inclusif ?",
]

def main():
    # Une synthèse par question, puis pauses authentiques de lecture dans la vidéo.
    # Conserver les 3 questions mot pour mot avec leurs accents.
    opt.OUTPUT = opt.ROOT / "sorties-questions-module1"
    opt.OUTPUT.mkdir(parents=True, exist_ok=True)
    speed = opt.valid_speed(os.getenv("DEEG_SPEED", "85"))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model="v3")
    profile = next(p for p in opt.PROFILES if p["id"] == "B_institutionnel")
    manifest = []
    for no, q in enumerate(QUESTIONS, 1):
        # output paths are created by the existing comparison generator
        original_id=profile["id"]
        profile["id"]=f"question_{no}"
        try:
            report=opt.make_audio(model, torch, q, profile, speed, device)
        finally:
            profile["id"]=original_id
        report["question"]=q
        manifest.append(report)
    (opt.OUTPUT / "questions_integrales.txt").write_text("\n\n".join(QUESTIONS)+"\n", encoding="utf-8")
    (opt.OUTPUT / "questions_rapport.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Trois questions produites séparément pour permettre le montage et les silences.", flush=True)

if __name__ == "__main__":
    main()
