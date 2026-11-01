"""Synthese par clips : module 3 DEEG voix B, references privees locales uniquement."""
from __future__ import annotations
import os, json, subprocess, pathlib
import torch, torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

TEXTS=json.loads("[\"Module deux. Cadre normatif et institutionnel en matière de genre et d’éducation.\",\"Lors d’une réunion pédagogique, l’équipe examine plusieurs situations préoccupantes.\",\"Quatre situations scolaires appellent des décisions justes et protectrices.\",\"Une écolière risque de devoir abandonner l’école.\",\"Sa famille a décidé d’organiser son mariage.\",\"Cette décision met en péril la poursuite de ses études.\",\"En sciences, des garçons sont plus souvent sollicités.\",\"Plusieurs filles souhaitent participer, mais sont peu interrogées.\",\"L’inégalité de participation devient visible dans la classe.\",\"Un garçon rencontre une difficulté pendant un exercice.\",\"Il voudrait demander de l’aide, mais redoute les moqueries.\",\"Par crainte d’être jugé, il garde le silence.\",\"Un autre enfant rencontre un obstacle dans son parcours scolaire.\",\"Son dossier ne contient pas d’acte de naissance.\",\"Cette absence complique sa scolarité.\",\"En réunion, l’équipe reconnaît qu’il faut agir.\",\"Mais quels textes garantissent les droits de ces élèves ?\",\"Ensemble, ils s’engagent à agir dans le respect des droits des élèves.\",\"Quels droits sont menacés dans ces différentes situations ?\",\"Quels textes internationaux, régionaux et ivoiriens peuvent être mobilisés ?\",\"Quelles mesures concrètes l’établissement doit-il prendre pour protéger les élèves et prévenir les discriminations ?\"]")
root=pathlib.Path(__file__).resolve().parents[1]
reference=root/".modeles"/"tanguy_pose.wav"
if not reference.is_file(): raise FileNotFoundError("Reference vocale B absente")
part=int(os.environ.get("M02_PART","1"))
if part not in (1,2,3): raise ValueError("M02_PART attendu 1, 2 ou 3")
start=(part-1)*7
end=min(start+7,len(TEXTS))
out=root/"sorties-module2"/f"partie_{part}"
out.mkdir(parents=True,exist_ok=True)
device="cuda" if torch.cuda.is_available() else "cpu"
torch.set_num_threads(4)
model=ChatterboxMultilingualTTS.from_pretrained(device=device,t3_model="v3")
model.prepare_conditionals(str(reference),exaggeration=0.26)
manifest=[]
for k in range(start,end):
    idx=k+1
    torch.manual_seed(2200+idx)
    message=TEXTS[k]
    print(f"DEEG B module2 clip {idx:02d}/21 : {message}",flush=True)
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
