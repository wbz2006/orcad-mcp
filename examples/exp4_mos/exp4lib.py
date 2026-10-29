# -*- coding: utf-8 -*-
"""Experiment 4 (MOSFET amplifier) project skeleton.

Creates exp4.opj in D:\\Users\\Download\\try.  Simulations are run with
hand-written .cir netlists via psp_cmd; the Capture design is the printable
schematic source of truth.
"""
import os

PROJ_DIR = r"D:\Users\Download\try"
DSN_NAME = "exp4"


def make_opj() -> str:
    return f'''(ExpressProject "exp4"
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
  (Folder "Outputs")
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


def generate_all() -> None:
    os.makedirs(PROJ_DIR, exist_ok=True)
    with open(os.path.join(PROJ_DIR, f"{DSN_NAME}.opj"), "w", encoding="latin-1") as f:
        f.write(make_opj())
    print("project skeleton written to", PROJ_DIR)


if __name__ == "__main__":
    generate_all()
