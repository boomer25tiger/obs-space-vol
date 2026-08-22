"""S20, DECISIONS item 139. Render Table 1 from the paper/k_table.csv artifact.
The S19 rewrite added the paper/session label columns but dropped `margin`,
leaving each determination asserted rather than evidenced. This renders all six
columns. It reads the CSV; it does not regenerate it (build_ktable.py does that,
and predates the label columns)."""
import os,pandas as pd
R=os.path.dirname(os.path.abspath(__file__))
T=pd.read_csv(os.path.join(R,"k_table.csv"))
HYPH={"INDETERMINATE":"INDETER\\-MINATE","UNTESTED":"UN\\-TESTED"}
def esc(s):
    s=str(s)
    for a,b in (("\\","\\textbackslash "),("&","\\&"),("%","\\%"),("_","\\_"),
                ("#","\\#"),("$","\\$"),("|","$|$")):
        s=s.replace(a,b)
    for a,b in HYPH.items():
        s=s.replace(a,b)
    return s
RAG=lambda w: r">{\raggedright\arraybackslash}p{"+w+"}"
o=[r"\begin{table}[!ht]\centering\footnotesize",
   r"\setlength{\tabcolsep}{4pt}\renewcommand{\arraystretch}{1.15}",
   r"\setlength{\abovetopsep}{6pt}",
   r"\caption{Kill conditions and their determinations.\protect\footnotemark{} Generated"
   r" from the determination artifacts listed in \texttt{paper/k\_table.csv}; the margin"
   r" column gives the measured quantity against its pre-registered threshold, and the"
   r" final column records whether the application was selected before or after the"
   r" first-order criterion was articulated.}\label{tab:kill}",
   r"\begin{tabular}{@{}ll" + RAG("3.3cm") + RAG("3.0cm") + RAG("4.3cm") + "c@{}}",r"\toprule",
   r"Paper & Session & Content & Determination & Margin & Selected \\",r"\midrule"]
for _,r in T.iterrows():
    o.append(" & ".join(esc(r[c]) for c in
        ("paper_label","session_label","content","determination","margin","chosen"))
        +r" \\"+f"  % source: {r.artifact} [{r.key}]")
o+=[r"\bottomrule",r"\end{tabular}",r"\end{table}",
    r"\footnotetext{The session record uses overlapping labels. Item~61 relabelled the"
    r" MCS-composition condition K2 while the specification already used K2 for grid"
    r" invariance, and two distinct conditions were both called K3. The paper renumbers"
    r" K1--K13 in the order shown; the repository retains the original labels, given here"
    r" in the second column.}"]
open(os.path.join(R,"sections/05_conditions_table.tex"),"w").write("\n".join(o)+"\n")
print(f"rendered {len(T)} rows, 6 columns; margin non-empty in {int(T.margin.notna().sum())}")
