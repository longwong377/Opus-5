BABYLON 5 -- a 1:1 simulation of the station. 8,047 m. Season 2-3.

Open the `game` folder and double-click Babylon5.exe.

NEW GAME puts you on the transport deck at customs with an identicard, which is
the only thing standing between you and being put back on a ship.

KEEP THIS FOLDER TOGETHER. `game` is the engine and the code. `station` is the
world -- meshes, collision shells, the arrival sequence, the crowd, audio. The
world is read from disk at runtime rather than packed inside the executable,
because it is generated rather than authored and it is about 6 GB. Moving the
.exe somewhere else on its own will not work.

If the title screen says NO WORLD ON DISK, the `station` folder did not come
with this copy.

WHAT TO EXPECT, honestly. The station streams around you: 907 cells, 363
residents with names, jobs and timetables, spin gravity of 0.76 g at the outer
ring. 242 of those 907 cells are over their triangle budget, the worst by 5.3x,
and this was built on a machine with no graphics card at all -- so nobody has
ever measured a frame rate. If it runs badly, that is the known cause and it is
fixable.

Windows will warn you that it does not recognise the publisher. It is an
unsigned executable built by GitHub Actions from public source; the workflow
that produced it is .github/workflows/windows-build.yml in the repository.
