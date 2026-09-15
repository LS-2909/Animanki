#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,json,random,sqlite3,string,subprocess,tempfile,time,zipfile
FIELD_KEYS=["anime","titre_original","studio","compositeur_ost","oeuvre_originale","saison","annee_sortie","createur_original","nombre_episodes","opening_1","opening_2","ending_1","ending_2","affiche","realisateur","scenario"]
DECK_BY_ORD={0:(1787225000001,"Titre de l'anime"),1:(1787225000002,"Studio"),2:(1787225000004,"Œuvre originale"),3:(1787225000005,"Année"),4:(1787225000006,"Compositeur OST")}
def rv(d,i):
 v=s=0
 while 1:
  b=d[i];i+=1;v|=(b&127)<<s
  if b<128:return v,i
  s+=7
def ev(v):
 r=bytearray()
 while 1:
  b=v&127;v>>=7;r.append(b|(128 if v else 0))
  if not v:return bytes(r)
def parts(raw):
 i=0;o=[]
 while i<len(raw):
  st=i;k,i=rv(raw,i);fn,wt=k>>3,k&7
  if wt==0:_,en=rv(raw,i)
  elif wt==1:en=i+8
  elif wt==2:ln,p=rv(raw,i);en=p+ln
  elif wt==5:en=i+4
  else:raise ValueError(wt)
  o.append((fn,wt,raw[st:en]));i=en
 return o
def getstr(raw,fn):
 for f,w,ch in parts(raw):
  if f==fn and w==2:
   i=0;_,i=rv(ch,i);ln,i=rv(ch,i);return ch[i:i+ln].decode()
 return ""
def setfield(raw,fn,val,wt=2):
 if wt==2:b=val.encode();rep=ev((fn<<3)|2)+ev(len(b))+b
 else:rep=ev((fn<<3)|0)+ev(val)
 o=[];done=False
 for f,w,ch in parts(raw):
  if f==fn:
   if not done:o.append(rep);done=True
  else:o.append(ch)
 if not done:o.append(rep)
 return b''.join(o)
def migrate_seed(cur,mid):
 # Add the two metadata fields if the historical seed lacks them.
 fs=cur.execute("select ord,name,config from fields where ntid=? order by ord",(mid,)).fetchall();names=[x[1] for x in fs];cfg=fs[-1][2]
 for name in ("Realisateur","Scenario"):
  if name not in names:cur.execute("insert into fields(ntid,ord,name,config) values(?,?,?,?)",(mid,len(names),name,cfg));names.append(name)
 # Old seed ords: 0 title,1 studio,2 creator,3 work,4 year,5 composer. Remove creator and compact ords.
 if cur.execute("select 1 from templates where ntid=? and ord=5",(mid,)).fetchone():
  cur.execute("delete from cards where nid in(select id from notes where mid=?) and ord=2",(mid,));cur.execute("delete from templates where ntid=? and ord=2",(mid,))
  for old,new in ((3,2),(4,3),(5,4)):
   cur.execute("update cards set ord=? where nid in(select id from notes where mid=?) and ord=?",(new,mid,old));cur.execute("update templates set ord=? where ntid=? and ord=?",(new,mid,old))
 # Director is context on every front, never a dedicated card.
 for o,name,cfg in cur.execute("select ord,name,config from templates where ntid=? order by ord",(mid,)).fetchall():
  raw=bytes(cfg);q=getstr(raw,1)
  if "{{Realisateur}}" not in q:q += '<div class="director">Réalisateur : {{Realisateur}}</div>'
  raw=setfield(raw,1,q);raw=setfield(raw,5,DECK_BY_ORD[o][0],0)
  cur.execute("update templates set config=?,mtime_secs=?,usn=-1 where ntid=? and ord=?",(raw,int(time.time()),mid,o))
def ensure_decks(cur,parent):
 row=cur.execute("select name,common,kind from decks where id=?",(parent,)).fetchone();pn,common,kind=row
 for o,(did,label) in DECK_BY_ORD.items():
  name=pn+'\x1f'+label;r=cur.execute("select id from decks where id=? or name=?",(did,name)).fetchone()
  if r:cur.execute("update decks set name=?,mtime_secs=?,usn=-1 where id=?",(name,int(time.time()),r[0]))
  else:cur.execute("insert into decks(id,name,mtime_secs,usn,common,kind) values(?,?,?,?,?,?)",(did,name,int(time.time()),-1,common,kind))
def add_note(cur,note,mid):
 now=int(time.time());nid=max(int(time.time()*1000),cur.execute("select coalesce(max(id),0)+10 from notes").fetchone()[0],cur.execute("select coalesce(max(id),0)+10 from cards").fetchone()[0]);guid=''.join(random.choice(string.ascii_letters+string.digits) for _ in range(10));v=[str(note.get(k,'') or '') for k in FIELD_KEYS];f='\x1f'.join(v);cs=int(hashlib.sha1(v[0].encode()).hexdigest()[:8],16);tags=' '+' '.join(note.get('tags',['animation_japonaise']))+' '
 cur.execute("insert into notes values(?,?,?,?,?,?,?,?,?,?,?)",(nid,guid,mid,now,-1,tags,f,v[0],cs,0,''));due=cur.execute("select coalesce(max(due),0) from cards").fetchone()[0]
 for o in range(5):cur.execute("insert into cards values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(nid+o+1,nid,DECK_BY_ORD[o][0],o,now,-1,0,0,due+o+1,0,0,0,0,0,0,0,0,''))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--database',default='database.json');ap.add_argument('--seed',default='template/Animanki_V8_seed.apkg.b64');ap.add_argument('--output',default='output/Animanki_Ajout.apkg');ap.add_argument('--all',action='store_true');a=ap.parse_args();dp=Path(a.database);data=json.loads(dp.read_text('utf-8'));sel=[n for n in data['notes'] if a.all or not n.get('exported',False)]
 if not sel:raise SystemExit('Aucune nouvelle note à exporter.')
 with tempfile.TemporaryDirectory() as x:
  p=Path(x);import base64;seed=p/'seed.apkg';seed.write_bytes(base64.b64decode(Path(a.seed).read_text('ascii')));zipfile.ZipFile(seed).extractall(p);seed.unlink();z=p/'collection.anki21b';d=p/'collection.anki21';subprocess.run(['zstd','-d','-q',str(z),'-o',str(d)],check=True);q=sqlite3.connect(d);q.create_collation('unicase',lambda a,b:(a.casefold()>b.casefold())-(a.casefold()<b.casefold()));c=q.cursor();m=data['model_id'];migrate_seed(c,m);ensure_decks(c,data['deck_id'])
  c.execute('delete from revlog');c.execute('delete from cards');c.execute('delete from notes');c.execute('delete from graves')
  for n in sel:add_note(c,n,m)
  q.commit();q.close();z.unlink();subprocess.run(['zstd','-q','-19',str(d),'-o',str(z)],check=True);d.unlink();Path(a.output).parent.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED) as w:
   for f in p.iterdir():w.write(f,f.name)
 for n in sel:n['exported']=True
 dp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');print(f'{len(sel)} note(s) exportée(s) vers {a.output}')
if __name__=='__main__':main()
