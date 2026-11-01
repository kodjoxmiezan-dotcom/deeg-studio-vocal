"""Synthese par clips : module 3 DEEG voix B, references privees locales uniquement."""
from __future__ import annotations
import os, json, subprocess, pathlib
import torch, torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

TEXTS=json.loads("[\"Module trois. Approche transformatrice de genre.\",\"Dans cette école primaire, filles et garçons suivent les mêmes cours.\",\"Pourtant, en mathématiques et en sciences, les garçons sont davantage interrogés.\",\"Ils occupent aussi plus souvent les fonctions de responsabilité.\",\"À l’inverse, plusieurs filles restent peu sollicitées.\",\"Les encouragements semblent eux aussi inégalement répartis.\",\"Peu à peu, certaines filles doutent de leurs capacités.\",\"Pourtant, certaines souhaitent déjà poursuivre des activités scientifiques.\",\"Mais les attentes sociales influencent déjà les projets qu’on juge faits pour les filles ou pour les garçons.\",\"Ces attentes se prolongent jusque dans certaines familles.\",\"L’école a déjà mis en place des cours de remédiation.\",\"Elle distribue aussi des trousses d’hygiène adaptées à des besoins réels.\",\"Ces mesures répondent à des difficultés bien réelles.\",\"Mais la répartition de la parole n’a pas changé.\",\"Les pratiques d’encouragement et de responsabilité continuent de poser question.\",\"L’équipe éducative doit donc examiner les causes de ces écarts.\",\"Personnes, relations, communauté et institution sont concernées.\",\"Comment passer d’actions ponctuelles à une transformation durable ?\",\"Pourquoi des inégalités persistent-elles malgré l’égalité formelle d’accès ?\",\"Quelles normes, quels acteurs et quels rapports de pouvoir entretiennent la situation ?\",\"Quelles actions permettraient d’agir simultanément sur les personnes, les relations, la communauté et l’institution ?\"]")
root=pathlib.Path(__file__).resolve().parents[1]
reference=root/".modeles"/"tanguy_pose.wav"
if not reference.is_file(): raise FileNotFoundError("Reference vocale B absente")
part=int(os.environ.get("M03_PART","1"))
if part not in (1,2,3): raise ValueError("M03_PART attendu 1, 2 ou 3")
start=(part-1)*7
end=min(start+7,len(TEXTS))
out=root/"sorties-module3"/f"partie_{part}"
out.mkdir(parents=True,exist_ok=True)
device="cuda" if torch.cuda.is_available() else "cpu"
torch.set_num_threads(4)
model=ChatterboxMultilingualTTS.from_pretrained(device=device,t3_model="v3")
model.prepare_conditionals(str(reference),exaggeration=0.26)
manifest=[]
for k in range(start,end):
    idx=k+1
    torch.manual_seed(3200+idx)
    message=TEXTS[k]
    print(f"DEEG B clip {idx:02d}/21 : {message}",flush=True)
    with torch.inference_mode():
        x=model.generate(message,language_id="fr",exaggeration=0.26,cfg_weight=0.30,temperature=0.68,repetition_penalty=1.16)
    raw=out/f"clip_{idx:02d}_brut.wav"
    wav=out/f"clip_{idx:02d}.wav"
    mp3=out/f"clip_{idx:02d}.mp3"
    torchaudio.save(str(raw),x.detach().cpu(),model.sr)
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),"-af","atempo=0.850,highpass=f=65,loudnorm=I=-18:TP=-2.5:LRA=11","-ac","1","-ar","48000",str(wav)],check=True)
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(wav),"-codec:a","libmp3lame","-q:a","3",str(mp3)],check=True)
    raw.unlink(missing_ok=True)
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(wav)],capture_output=True,text=True,check=True)
    manifest.append(dict(clip=idx,text=message,wav=wav.name,mp3=mp3.name,duration_seconds=float(p.stdout.strip()),profile="B_institutionnel",speed_percent=85,language="fr",engine="Chatterbox Multilingual V3"))
    print(f"clip {idx:02d} pret",flush=True)
(out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print("FIN, reference vocale non exportee",flush=True)
