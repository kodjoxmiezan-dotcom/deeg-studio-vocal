"""Pilote EXPERT PRÉPA CM2 : dictée lente et ponctuation lue.
Utilise la synthèse Edge TTS déjà choisie dans Studio Vocal DEEG.
"""
from pathlib import Path
import subprocess, wave, json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'sorties-dictee-cm2'
OUT.mkdir(parents=True,exist_ok=True)
VOICE='fr-FR-HenriNeural'
TITLE='La journée des nouveaux élèves'
ORIGINAL=('Dès la rentrée, Awa accueille une camarade dans la cour. '
          'Sa gentillesse inspire toute la classe. '
          'À la fin de la journée, une véritable amitié est née. '
          'Le maître félicite les enfants pour leur générosité.')
PHRASES=[
'Dès la rentrée, virgule, Awa accueille une camarade dans la cour. Point.',
'Sa gentillesse inspire toute la classe. Point.',
'À la fin de la journée, virgule, une véritable amitié est née. Point.',
'Le maître félicite les enfants pour leur générosité. Point.',
]
def run(*args):
    subprocess.run(list(args),check=True)
def synth(name,text,rate=60):
    mp3=OUT/f'{name}.mp3'; wav=OUT/f'{name}.wav'
    run('edge-tts','--voice',VOICE,f'--rate={rate-100:+d}%',
        '--text',text,'--write-media',str(mp3))
    run('ffmpeg','-y','-v','error','-i',str(mp3),'-ac','1',
        '-ar','24000','-c:a','pcm_s16le',str(wav))
    return wav
def silence(name,seconds):
    file=OUT/name
    with wave.open(str(file),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000)
        w.writeframes(b'\\x00\\x00'*int(24000*seconds))
    return file
def assemble(files,target):
    playlist=OUT/'playlist.txt'
    playlist.write_text(''.join("file '"+str(p.absolute())+"'\\n" for p in files),encoding='utf-8')
    raw=OUT/'assembled.wav'
    run('ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(playlist),
        '-ac','1','-ar','24000','-c:a','pcm_s16le',str(raw))
    run('ffmpeg','-y','-v','error','-i',str(raw),'-codec:a','libmp3lame',
        '-b:a','96k',str(target))
    raw.unlink(missing_ok=True);playlist.unlink(missing_ok=True)
def main():
    passage=' '.join(PHRASES)
    intro=synth('consigne','EXPERT PRÉPA. Dictée CM2. La journée des nouveaux élèves. '
                'Quand je dis virgule, écris une virgule. Quand je dis point, écris un point. '
                'Écoute d’abord le texte en entier.',78)
    lecture=synth('lecture_integrale_tres_lente',passage,60)
    consigne=synth('consigne_phrase','Maintenant, écris chaque phrase. Elle sera lue trois fois. '
                   'Tu peux mettre le lecteur en pause quand tu veux.',78)
    noms=['Première','Deuxième','Troisième','Quatrième']
    labels=[synth(f'annonce_{i+1:02}',f'{noms[i]} phrase.',75) for i in range(4)]
    phrases=[synth(f'phrase_{i+1:02}',p,69) for i,p in enumerate(PHRASES)]
    fin=synth('consigne_relecture','Voici la relecture complète. Vérifie les accents, '
              'les accords, les majuscules et la ponctuation.',78)
    relecture=synth('relecture_finale',passage,68)
    p4=silence('pause_04s.wav',4);p10=silence('pause_10s.wav',10)
    seq=[intro,lecture,p4,consigne,p4]
    for label,p in zip(labels,phrases):
        seq.append(label)
        for i in range(3):
            seq.append(p);seq.append(p4 if i<2 else p10)
    seq.extend([fin,p4,relecture])
    assemble(seq,OUT/'EXPERT_PREPA_CM2_S01_A_MODELE_COMPLET.mp3')
    (OUT/'TEXTE_REFERENCE_ENSEIGNANT.txt').write_text(TITLE+'\\n\\n'+ORIGINAL+'\\n',encoding='utf-8')
    (OUT/'parametres.json').write_text(json.dumps({
        'moteur':'Studio vocal DEEG / Edge TTS','voix':VOICE,
        'lecture_complete_pct':60,'phrases_pct':69,'repetitions':3,
        'pause_entre_repetitions_s':4,'pause_entre_phrases_s':10,
        'ponctuation':'virgule et point annonces oralement'},ensure_ascii=False,indent=2))
    print('Fichier produit',OUT/'EXPERT_PREPA_CM2_S01_A_MODELE_COMPLET.mp3')
if __name__=='__main__':main()
