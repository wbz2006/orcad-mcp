"""Experiment 3 (BJT common-emitter amp) project file generator.

生成 Capture 工程骨架:exp3.opj(PSpice 工程类型 + 两个仿真 profile)、
bias/tran 两个 .sim profile、BF=70 模型库。
"""

import os

PROJ_DIR = r"D:\Users\Download\exp3_BJT_CE"
DSN_NAME = "exp3"
PSPICE_DIR = r"C:\OrCAD\OrCAD_16.6_Lite\tools\capture\library\pspice"
CAPSYM = r"C:\OrCAD\OrCAD_16.6_Lite\tools\capture\library\capsym.olb"

CLASS_ID = "{09528990-3187-11D2-BC7B-00A0C90CBF91}"  # PSpice profile class GUID(与官方工程一致)


def sim_template(profile_name: str, connectivity: str, analysis_block: str) -> str:
    """按官方 tran.sim 的 18 段模板生成 .sim;analysis_block 决定哪段 enabled."""
    secs = {
        0: ("+0 0 0 0 \n+0 \"5ms\" \n+1 \"\" \n+2 \"0\" \n+3 \"1u\" \n+4 \"\" \n+5 \"\" \n+6 \"\" ", 0),
        1: ("+0 0 1\n+0 \"2\" \n+1 \"10khz\" \n+2 \"15khz\" \n+3 \"\" \n+4 \"\" \n+5 \"\" ", 0),
        2: ("+0 0\n+0 \"\" \n+1 \"\" \n+2 \"\" \n+3 \"\" \n+4 \"\" \n+5 \"\" \n+6 \"\" \n+7 \"\" ", 0),
        3: ("+0 0 0\n+0 \"\" \n+1 \"\" \n+2 \"\" ", 0),
    }
    secs[analysis_block[0]] = analysis_block[1]
    out = [f"@OrCAD Simulation Server Version: 1.0\n", f"\n@Settings: 0 1\n", "@General:\n",
           f"ProfileName= \"{profile_name}\" \n",
           f"ProfileFile= \"{profile_name}.sim\" \n",
           f"Connectivity= \"{connectivity}.net\" \n",
           f"NetlistFile= \"{profile_name}.cir\" \n",
           f"DataFile= \"{profile_name}.dat\" \n",
           f"OutFile= \"{profile_name}.out\" \n",
           "Notes=\n@#$BEGINNOTES\n@#$ENDNOTES\n@End General\n"]
    for i in range(18):
        body, en = secs.get(i, ("", 0))
        if i == 4:
            body = "+0 0 1 0 0 0 0 0 0 0 1\n+0 \"\" \n+1 \"\" \n+2 \"\" \n+3 \"\" \n+4 \"\" \n+5 \"\" \n+6 \"\" \n+7 \"\" \nLoadFile 0 \"\" \nSaveFile 0 \"\" "
        elif i == 11:
            body = "+ 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 \n+ 0 0 0 0 0 0 0 0 0"
        elif i == 13:
            body = "+0 1 1 1"
        elif i == 14:
            body = "+1 1 1 \"*\" "
        out.append(f"@Analysis: {i} {en}\n" + (body + "\n" if body else "") + "@End Analysis\n")
    return "".join(out)


def bias_block():
    # @Analysis: 3 1 → Bias Point enabled
    return (3, ("+0 0 0\n+0 \"\" \n+1 \"\" \n+2 \"\" ", 1))


def tran_block():
    # @Analysis: 0 1 → Time Domain enabled: run to 5ms, max step 1u
    return (0, ("+0 0 0 0 \n+0 \"5ms\" \n+1 \"\" \n+2 \"0\" \n+3 \"1u\" \n+4 \"\" \n+5 \"\" \n+6 \"\" ", 1))


def profile_entry(sim_rel: str, display: str) -> str:
    return (f'      (File.PSpice.{CLASS_ID}\n'
            f'         "{sim_rel}"\n'
            f'        (DisplayName "{display}")\n'
            f'        (Type "PSpice Profile"))\n')


def make_opj(active: str | None = "bias") -> str:
    mdl = os.path.join(PROJ_DIR, "q2n3904_bf70.lib")
    active_line = (f'\n      (ActiveProfile "{active}")') if active else ""
    return f'''(ExpressProject "exp3"
  (ProjectVersion "19981106")
  (ProjectType "Analog or A/D Mixed Mode")
  (Folder "Design Resources"
    (Folder "Library")
    (NoModify)
    (File ".\\{DSN_NAME}.dsn"
      (Type "Schematic Design"))
    (BuildFileAddedOrDeleted "x")
    (CompileFileAddedOrDeleted "x")
    (PSPICE_Regenerate_Netlist_Flag "TRUE")
    (RootChangedForceReNetlist "x"))
  (Folder "Outputs"
    (File ".\\{DSN_NAME}-pspicefiles\\bias\\bias.out"
      (Type "Report"))
    (File ".\\{DSN_NAME}-pspicefiles\\tran\\tran.out"
      (Type "Report")))
  (Folder "PSpice Resources"
    (Folder "Simulation Profiles"
{profile_entry(f'.\\{DSN_NAME}-pspicefiles\\bias\\bias.sim', 'Bias')}{profile_entry(f'.\\{DSN_NAME}-pspicefiles\\tran\\tran.sim', 'Tran')}{active_line}
    (Folder "Model Libraries"
      (File "{mdl}"
        (Type "PSpice Library"))
      (Sort User))
    (Folder "Stimulus Files"
      (Sort User))
    (Folder "Include Files"
      (Sort User)))
  (GlobalState
    (FileView
      (Path "Design Resources")
      (Path "Design Resources" ".\\{DSN_NAME}.dsn")
      (Path "Design Resources" ".\\{DSN_NAME}.dsn" "SCHEMATIC1")
      (Path "Design Resources" ".\\{DSN_NAME}.dsn" "Design Cache"))
    (HierarchyView)
    (Doc
      (Type "COrCapturePMDoc")
      (Frame
        (Placement "44 0 1 -1 -1 -1 -1 0 700 0 500"))
      (Tab 0))))
'''


def bf70_lib() -> str:
    return """* Q2N3904 with BF (beta) changed to 70; other parameters identical to eval.lib
.MODEL Q2N3904 NPN(Is=6.734f Xti=3 Eg=1.11 Vaf=74.03 Bf=70 Ne=1.259
+		Ise=6.734f Ikf=66.78m Xtb=1.5 Br=.7371 Nc=2 Isc=0 Ikr=0 Rc=1
+		Cjc=3.638p Mjc=.3085 Vjc=.75 Fc=.5 Cje=4.493p Mje=.2593 Vje=.75
+		Tr=239.5n Tf=301.2p Itf=.4 Vtf=4 Xtf=2 Rb=10)
"""


def generate_all(active: str | None = "bias") -> None:
    os.makedirs(PROJ_DIR, exist_ok=True)
    pf = os.path.join(PROJ_DIR, f"{DSN_NAME}-pspicefiles")
    os.makedirs(os.path.join(pf, "bias"), exist_ok=True)
    os.makedirs(os.path.join(pf, "tran"), exist_ok=True)
    with open(os.path.join(PROJ_DIR, "q2n3904_bf70.lib"), "w", encoding="latin-1") as f:
        f.write(bf70_lib())
    with open(os.path.join(pf, "bias", "bias.sim"), "w", encoding="latin-1") as f:
        f.write(sim_template("Bias", DSN_NAME, bias_block()))
    with open(os.path.join(pf, "tran", "tran.sim"), "w", encoding="latin-1") as f:
        f.write(sim_template("Tran", DSN_NAME, tran_block()))
    with open(os.path.join(PROJ_DIR, f"{DSN_NAME}.opj"), "w", encoding="latin-1") as f:
        rel = (".\\" + DSN_NAME + "-pspicefiles\\" + active + "\\" + active + ".sim") if active else None
        f.write(make_opj(rel))
    print("project skeleton written to", PROJ_DIR)


if __name__ == "__main__":
    import sys
    a = sys.argv[1] if len(sys.argv) > 1 else "bias"
    generate_all(None if a == "none" else a)
