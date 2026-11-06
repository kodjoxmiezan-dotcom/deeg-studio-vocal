"""Synthese par clips : module 4 DEEG voix B, references privees locales uniquement."""
from __future__ import annotations
import os, json, subprocess, pathlib
import torch, torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

TEXTS=["Tout commence dès la maternelle.","Au primaire, les besoins se précisent.","Au CAFOP, les futurs enseignants se forment.","Au collège, chaque décision compte.","Monsieur Dago reprend l’ancien budget avec ses collègues. Mais reflète-t-il réellement les besoins des élèves ?","Les comptes semblent équilibrés. Mais les chiffres ne montrent pas toutes les inégalités.","En sciences, les garçons manipulent les instruments. Les filles, elles, attendent encore leur tour.","Awa en parle à madame Diarra : être inscrite ne signifie pas participer à égalité.","Le surveillant remet un registre : plusieurs filles quittent le collège en cours de cycle. Pourquoi ?","Awa montre des portes de sanitaires défectueuses. L’intimité des élèves est-elle suffisamment protégée ?","En réunion, madame Coulibaly demande la parole. Des besoins restent absents du budget. Qui les écoute ?","L’intendante compare le budget aux relevés d’absences et de participation. Ces informations influencent-elles vraiment les dépenses ?","Monsieur Dago suspend sa signature. Avant de décider, il reste des écarts à comprendre.","Quelles disparités de participation, de maintien scolaire et d’accès aux équipements restent invisibles dans le budget de cet établissement ?","Quels élèves, personnels et autres acteurs faudrait-il consulter pour comprendre les besoins réels ?","Comment réviser les priorités et les décisions budgétaires pour garantir une gestion plus équitable et sensible au genre ?","Pour réduire les inégalités, chaque action compte !"]
root=pathlib.Path(__file__).resolve().parents[1]
reference=root/".modeles"/"tanguy_pose.wav"
if not reference.is_file(): raise FileNotFoundError("Reference vocale B absente")
part=int(os.environ.get("M04_PART","1"))
if part not in (1,2,3): raise ValueError("M04_PART attendu 1, 2 ou 3")
start=(part-1)*7
end=min(start+7,len(TEXTS))
out=root/"sorties-module4"/f"partie_{part}"
out.mkdir(parents=True,exist_ok=True)
device="cuda" if torch.cuda.is_available() else "cpu"
torch.set_num_threads(4)
model=ChatterboxMultilingualTTS.from_pretrained(device=device,t3_model="v3")
model.prepare_conditionals(str(reference),exaggeration=0.26)
manifest=[]
for k in range(start,end):
    idx=k+1
    torch.manual_seed(4200+idx)
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
