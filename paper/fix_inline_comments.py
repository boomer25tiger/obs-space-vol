"""Move any % numbers.csv: comment that sits mid-line to the end of its line.
A mid-line comment silently deletes the remainder of the line in LaTeX, which is
what produced the four dropped-text fragments of DECISIONS item 138."""
import re,sys,glob
CIT=r"(%\s*numbers\.csv:\s*[A-Za-z0-9_\[\]/\.\-]+(?:\s*,\s*[A-Za-z0-9_\[\]/\.\-]+)*(?:\s*=\s*MISSING)?(?:\s+and companions)?)"
def fix(path):
    L=open(path).read().split("\n"); n=0
    for i,l in enumerate(L):
        m=re.search(r"^(.*?)"+CIT+r"\s+(\S.*)$",l)
        # "and companions" is comment prose, not swallowed body text
        if m and len(m.group(3).split())>=2 and m.group(3).strip() not in ("and companions","= MISSING"):
            L[i]=f"{m.group(1)}{m.group(3)} {m.group(2)}"; n+=1
    if n: open(path,"w").write("\n".join(L))
    return n
tot=0
for f in sorted(glob.glob("paper/sections/*.tex"))+["paper/main.tex"]:
    k=fix(f)
    if k: print(f"  {f.split('/')[-1]:24s} {k} moved"); tot+=k
print(f"total moved: {tot}")
