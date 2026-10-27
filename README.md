# cms-18-mod-cars-on-cms21

Tooling to study how Car Mechanic Simulator 2018 mod cars differ from Car Mechanic Simulator 2021 cars, with the aim of porting CMS 2018 mods to CMS 2021.

## Status

Early research stage. There is **no working converter yet**, and nothing here has been tested inside the game.

What has been done: one real CMS 2018 car (1951 Holden FX Coupe Utility) and one real CMS 2021 car (1969 Camaro RS SS) were compared. The verified differences are written up in [docs/format-differences.md](docs/format-differences.md). The short version:

- The CMS 2018 `.cms` bundle starts with `SnityFS` instead of `UnityFS`, is bundle format 6 (Unity 2017.1.0f3), and the CMS 2021 one is format 7 (Unity 2021.1.20f1).
- The CMS 2021 `config.txt` has four sections and about a dozen keys that the CMS 2018 one lacks, and the CMS 2018 gauge keys no longer exist.
- Neither bundle contains scripts, and the part layout is similar, but every CMS 2018 material uses Unity's `Standard` shader while every CMS 2021 material uses `HDRP/Lit`. Materials will probably need converting for CMS 2021.

## Tools

All commands run from the repository root. Only `inspect_bundle` needs `pip install -r requirements.txt` (UnityPy); the rest need just Python 3.9+.

| Command | What it does |
| --- | --- |
| `python -m cms_tools.bundle_header FILE...` | Reads a `.cms` bundle header (signature, Unity version, sizes, compression). |
| `python -m cms_tools.bundle_peek FILE...` | Decompresses a bundle locally and lists the files inside, the Unity version and shader names. Standard library only, and nothing is uploaded, so it suits game files you should not publish. |
| `python -m cms_tools.diff_configs A/config.txt B/config.txt` | Lists sections and keys present in one car's config but not the other. |
| `python -m cms_tools.fix_signature CAR.cms [OUT.cms]` | **Experimental.** Writes a copy with `SnityFS` changed to `UnityFS`. Original is never modified. Untested in-game. |
| `python -m cms_tools.inspect_bundle PATH -o report.json` | Lists a bundle's meshes, textures, GameObjects and script data using UnityPy. Not yet run against real bundles. |
| `python -m cms_tools.compare_reports a.json b.json` | Compares two `inspect_bundle` reports. |

Put your own copies of the files you want to study in a local `samples/` folder. It is git-ignored, so game and mod assets are never committed.

`.github/workflows/inspect-bundles.yml` runs `inspect_bundle` on GitHub (where UnityPy installs) for any `.cms` files under `samples/`. Mods belong to their authors, so do not commit them to a public repository.

## Roadmap

1. Test whether CMS 2021 loads a CMS 2018 car after the signature fix, with and without the config changes below.
2. Work out how to convert the `Standard` materials to `HDRP/Lit` (likely in a Unity 2021.1.20f1 HDRP project).
3. Write a config upgrader that adds the CMS 2021 sections and keys, using values confirmed in game.
4. Work out how the CMS 2018 gauge keys map to the CMS 2021 `[dials]` section.
5. Document the working procedure.

## Notes

Mod cars and game files belong to their creators and to Playter. Use only files you are allowed to use, and credit mod authors.
