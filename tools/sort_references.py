#!/usr/bin/env python3
"""Sort the unsorted reference dump into the subject/sector folders.

Mapping is explicit rather than heuristic: every file is placed deliberately,
and anything unmatched is reported rather than silently left behind.
"""
import os
import shutil
import subprocess
import sys

ROOT = "/home/user/Opus-5/reference"
DUMP = os.path.join(ROOT, "20-unsorted-dump")

# (destination folder, [filenames or directory names relative to the dump])
PLAN = [
    ("01-station-exterior", [
        "exterior more.jpg", "screenshot more exterior.jpeg",
        "screenshot 1 ship and background.jpeg", "view.jpg",
        "sleeping-in-light-05.jpg", "welcome to babylon 5.webp",
        "Cobra Bays with starfurries.webp",
    ]),
    ("02-station-cutaways-and-plans", [
        "Exterior map.jpg", "Interior map.jpg", "other map.png",
        "other map 2.jpg", "other map 4.jpg",
        "b5-schematics-from-the-security-manual-v0-u8879zcrf36h1.webp",
        "b5-schematics-from-the-security-manual-v0-m4rs80drf36h1 more.webp",
        "inside.jpg",
    ]),
    ("03-sector-blue", [
        "comand and contorl.webp", "CC looking out.jpeg", "more cc looking out.jpeg",
        "war room.webp", "dock.webp", "Minbari Flyer 969 in docking bay 17.webp",
        "Babylon_5_2-22_29a.jpg", "Babylon_5_2-22_33a.jpg",
        "Babylon_5_2-22_34b.jpg", "Babylon_5_2-22_35a.jpg",
    ]),
    ("04-sector-red", [
        "zocalo.webp", "more zocalo.png", "example of hallway opening into zocalo.jpeg",
        "concourse looking into hallway.jpeg", "Casino.webp", "Fresh air.webp",
        "Earhart's.webp", "Doug's Dugout.webp", "Darkstar_logo.webp",
        "more gkar and londo with concourse curving up.jpeg",
    ]),
    ("05-sector-green", [
        "council chambers.webp", "conference aerea.webp", "rotunda.webp",
        "corridor in alien sector.webp",
    ]),
    ("07-sector-grey", ["grey level 1.webp"]),
    ("09-garden-core-and-transit", [
        "The Gardens.webp", "The_Gardens01.webp", "garden.png",
        "central corridor.webp", "delen and sheridan in elevator.jpeg",
    ]),
    ("11-props-and-technology", ["Props, written alien script, signs, and Symbols"]),
    ("12-starfury", ["Starfury", "Starfury.jpg", "earth alliance fighter.jpeg"]),
    ("13-other-ships", ["kosh's transport.webp"]),
    ("14-characters-and-uniforms", [
        "uniforms", "Sheridan", "Security", "Talia Winters", "Ranger", "Technomage",
    ]),
    ("15-races-and-makeup", ["Vorlon", "Narn", "Pak'ma'ra"]),
    ("16-signage-typography-ui", [
        "babylon 5 shield.webp", "earthforce logo.webp", "faction symbols.png",
    ]),
]


def git_mv(src, dst):
    r = subprocess.run(["git", "mv", "-k", src, dst], cwd="/home/user/Opus-5",
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.move(src, dst)


def main():
    moved = 0
    for dest, names in PLAN:
        dpath = os.path.join(ROOT, dest)
        os.makedirs(dpath, exist_ok=True)
        for name in names:
            src = os.path.join(DUMP, name)
            if not os.path.exists(src):
                print(f"MISSING: {name}", file=sys.stderr)
                continue
            if os.path.isdir(src):
                # Flatten one level: move the directory's contents, keep the
                # directory name as a filename prefix so provenance survives.
                for f in sorted(os.listdir(src)):
                    git_mv(os.path.join(src, f), os.path.join(dpath, f))
                    moved += 1
                os.rmdir(src)
            else:
                git_mv(src, os.path.join(dpath, name))
                moved += 1

    leftover = [f for f in sorted(os.listdir(DUMP)) if f != ".gitkeep"]
    print(f"moved {moved} files")
    if leftover:
        print(f"unsorted remaining ({len(leftover)}):")
        for f in leftover:
            print(f"  {f}")


if __name__ == "__main__":
    main()
