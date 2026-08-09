#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, json, random, sqlite3, string, subprocess, tempfile, time, zipfile

FIELD_KEYS = [
    "anime","titre_original","studio","compositeur_ost","oeuvre_originale","saison",
    "annee_sortie","createur_original","nombre_episodes","opening_1","opening_2",
    "ending_1","ending_2","affiche"
]

def add_note(cur, note, model_id, deck_id):
    now_s = int(time.time())
    now_ms = int(time.time()*1000)
    max_note = cur.execute("SELECT COALESCE(MAX(id),0) FROM notes").fetchone()[0]
    max_card = cur.execute("SELECT COALESCE(MAX(id),0) FROM cards").fetchone()[0]
    nid = max(now_ms, max_note+10, max_card+10)
    guid = "".join(random.choice(string.ascii_letters+string.digits) for _ in range(10))
    values = [str(note.get(k,"") or "") for k in FIELD_KEYS]
    flds = "\x1f".join(values)
    csum = int(hashlib.sha1(values[0].encode("utf-8")).hexdigest()[:8],16)
    tags = " " + " ".join(note.get("tags",["animation_japonaise"])) + " "
    cur.execute(
        """INSERT INTO notes(id,guid,mid,mod,usn,tags,flds,sfld,csum,flags,data)
           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (nid,guid,model_id,now_s,-1,tags,flds,values[0],csum,0,"")
    )
    max_due = cur.execute("SELECT COALESCE(MAX(due),0) FROM cards").fetchone()[0]
    for ord_ in range(5):
        cur.execute(
            """INSERT INTO cards(id,nid,did,ord,mod,usn,type,queue,due,ivl,factor,
               reps,lapses,left,odue,odid,flags,data)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (nid+ord_+1,nid,deck_id,ord_,now_s,-1,0,0,max_due+ord_+1,
             0,0,0,0,0,0,0,0,"")
        )

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--database",default="database.json")
    ap.add_argument("--seed",default="template/Animanki_V8_seed.apkg.b64")
    ap.add_argument("--output",default="output/Animanki_Ajout.apkg")
    ap.add_argument("--all",action="store_true",help="exporte toutes les notes, pas seulement exported=false")
    args=ap.parse_args()

    db_path=Path(args.database)
    seed_path=Path(args.seed)
    out_path=Path(args.output)
    data=json.loads(db_path.read_text("utf-8"))
    selected=[n for n in data["notes"] if args.all or not n.get("exported",False)]
    if not selected:
        raise SystemExit("Aucune nouvelle note à exporter.")

    out_path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        td=Path(tmp)
        if seed_path.suffix == ".b64":
            import base64
            seed_apkg = td / "seed.apkg"
            seed_apkg.write_bytes(base64.b64decode(seed_path.read_text("ascii")))
        else:
            seed_apkg = seed_path
        with zipfile.ZipFile(seed_apkg) as z:z.extractall(td)
        comp=td/"collection.anki21b"
        db=td/"collection.anki21"
        subprocess.run(["zstd","-d","-q",str(comp),"-o",str(db)],check=True)
        con=sqlite3.connect(db);cur=con.cursor()
        for note in selected:
            add_note(cur,note,data["model_id"],data["deck_id"])
        cur.execute("UPDATE col SET mod=? WHERE id=1",(int(time.time()*1000),))
        con.commit();con.close()
        comp.unlink()
        subprocess.run(["zstd","-q","-19",str(db),"-o",str(comp)],check=True)
        db.unlink()
        with zipfile.ZipFile(out_path,"w",zipfile.ZIP_DEFLATED) as z:
            for p in td.iterdir():z.write(p,p.name)

    for note in selected:
        note["exported"]=True
    db_path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"{len(selected)} note(s) exportée(s) vers {out_path}")

if __name__=="__main__":
    main()
