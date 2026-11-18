"""EXPERT PREPA CM2 - Monte des lots audio 2 minutes par voix.
Le statut technique n'est PAS une validation de prononciation.
"""
import json, subprocess, tempfile, urllib.request
from pathlib import Path
from pydub import AudioSegment, silence

TARGET=120000
OUTPUT=Path("sorties-exp-prepa")
OUTPUT.mkdir(exist_ok=True)

def probe(p):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(p)],text=True).strip())

def run(*args):
    subprocess.run([str(x) for x in args],check=True)

def pauses(audio,extra):
    if extra<=0:return audio
    silence_threshold=max(-48.0,min(-28.0,audio.dBFS-18))
    gaps=silence.detect_silence(audio,min_silence_len=200,silence_thresh=silence_threshold,seek_step=30)
    gaps=[(b-a,a,b) for a,b in gaps if a>900 and b<len(audio)-900]
    if len(gaps)<4:
        gaps=silence.detect_silence(audio,min_silence_len=130,silence_thresh=silence_threshold+3,seek_step=25)
        gaps=[(b-a,a,b) for a,b in gaps if a>900 and b<len(audio)-900]
    if not gaps:return audio+AudioSegment.silent(duration=extra,frame_rate=audio.frame_rate)
    choice=sorted(gaps,reverse=True)[:min(24,len(gaps))]
    positions=sorted((a+b)//2 for _,a,b in choice)
    each,rest=divmod(extra,len(positions))
    result=AudioSegment.empty();last=0
    for i,pos in enumerate(positions):
        result+=audio[last:pos]
        result+=AudioSegment.silent(duration=each+(1 if i<rest else 0),frame_rate=audio.frame_rate)
        last=pos
    return result+audio[last:]

def main():
    reports=[];errors=[]
    for manifest in sorted(Path("experts_prepa_cm2_audio").glob("lot_*.json")):
        group=json.loads(manifest.read_text(encoding="utf8"))
        for item in group:
            code=item["id"];voice=item["voix"];url=item["url"]
            name=f"{code}_{voice}_DICTEE_2MIN.mp3"
            if (OUTPUT/name).exists():continue
            try:
                if not url.startswith("https://resource2.heygen.ai/"):
                    raise ValueError("URL non autorisée")
                with tempfile.TemporaryDirectory() as temp:
                    t=Path(temp);original=t/"original.wav";intermediate=t/"etire.wav"
                    with urllib.request.urlopen(url,timeout=180) as r, original.open("wb") as f:
                        import shutil;shutil.copyfileobj(r,f)
                    d=probe(original)
                    if not 20<d<240:raise ValueError(f"Durée originale suspecte: {d:.1f}")
                    # Débit posé; le temps supplémentaire est distribué entre les silences.
                    gap=min(30000,max(6000,int(TARGET-d*1000*1.15)))
                    vocal=(TARGET-gap)/1000.0
                    tempo=max(0.6,min(1.1,d/vocal))
                    run("ffmpeg","-y","-v","error","-i",original,"-af",f"atempo={tempo:.7f}",
                        "-ar","24000","-ac","1",intermediate)
                    audio=AudioSegment.from_wav(intermediate)
                    if len(audio)>TARGET:
                        tempo*=len(audio)/TARGET
                        run("ffmpeg","-y","-v","error","-i",original,"-af",f"atempo={tempo:.7f}",
                            "-ar","24000","-ac","1",intermediate)
                        audio=AudioSegment.from_wav(intermediate)
                    audio=pauses(audio,max(0,TARGET-len(audio)))
                    audio=audio[:TARGET]
                    if len(audio)<TARGET:
                        audio+=AudioSegment.silent(duration=TARGET-len(audio),frame_rate=audio.frame_rate)
                    audio.export(OUTPUT/name,format="mp3",bitrate="96k")
                    final_d=probe(OUTPUT/name)
                    if abs(final_d-120)>0.25:raise ValueError("Durée finale incorrecte")
                    reports.append({"id":code,"voix":voice,"fichier":name,"original_s":round(d,2),
                                    "final_s":round(final_d,2),"tempo":round(tempo,4),
                                    "statut":"TECHNIQUE_OK_AUDIO_A_ECOUTER"})
                    print("OK",name,round(final_d,2),flush=True)
            except Exception as e:
                errors.append({"id":code,"voix":voice,"erreur":str(e)})
                print("ERREUR",name,e,flush=True)
    (OUTPUT/"RAPPORT_CONTROLE_TECHNIQUE.json").write_text(
        json.dumps({"audios":reports,"erreurs":errors,
                    "avertissement":"Les mots de ponctuation, dont virgule, exigent une vérification à l'écoute pour chaque voix et chaque dictée."},
                    indent=2,ensure_ascii=False),encoding="utf8")
    if errors:raise SystemExit(f"{len(errors)} échecs; ne pas diffuser le lot aux élèves")

if __name__=="__main__":main()
