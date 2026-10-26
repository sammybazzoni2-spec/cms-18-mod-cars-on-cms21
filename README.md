# cms-18-mod-cars-on-cms21

Tooling to study how Car Mechanic Simulator 2018 mod cars are put together, so they can be ported to Car Mechanic Simulator 2021.

## Status

Early scaffold. There is **no working converter yet**. What exists is the groundwork for finding out what a port needs:

- `cms_tools/inspect_bundle.py` reads a Unity asset bundle (or a folder of them) with [UnityPy](https://github.com/K0lb3/UnityPy) and writes a JSON report: Unity version, object types, meshes, textures, GameObjects, and the data fields of scripts and text assets.
- `cms_tools/compare_reports.py` diffs two of those reports, for example a CMS 2018 car against a CMS 2021 car.

These scripts have not yet been run against real CMS bundles. Expect to adjust them once you see what the files actually contain.

## Why a plain "load" isn't enough

Both games use Unity, but they are built with different Unity versions and the car data layout differs between them. A CMS 2018 car generally has to be converted (bundle rebuilt, car config rewritten), not just dropped into the CMS 2021 mods folder. The comparison report is meant to show exactly which parts differ.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Put your own copies of the files you want to study in a local `samples/` folder (it is git-ignored, so game and mod assets are never committed).

```bash
# 1. Inspect a CMS 2018 mod car and a CMS 2021 car
python -m cms_tools.inspect_bundle samples/cms18_car -o reports/cms18.json
python -m cms_tools.inspect_bundle samples/cms21_car -o reports/cms21.json

# 2. See what differs
python -m cms_tools.compare_reports reports/cms18.json reports/cms21.json
```

## Roadmap

1. Run the inspector on real CMS 2018 and CMS 2021 cars and record the differences in `docs/`.
2. Work out how CMS 2021 discovers and registers custom cars.
3. Write a converter for the pieces that differ (car config, naming, paths), starting with the simplest car.
4. Test in-game and document the result.

## Notes

Mod cars and game files belong to their creators and to Playter. Use only files you are allowed to use, and credit mod authors.
