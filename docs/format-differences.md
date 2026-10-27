# CMS 2018 vs CMS 2021 car mods: observed differences

This compares exactly two cars, so treat it as a starting point rather than a complete specification.

- **CMS 2018:** 1951 Holden FX Coupe Utility (Workshop item folder `1203793941`)
- **CMS 2021:** 1969 Camaro RS SS (Workshop item `2689830628`)

Everything under "Verified" was read directly from those files with the tools in this repo. Everything under "Not yet known" is open.

## Folder layout

Both mods are a folder holding a `.cms` bundle plus plain-text files:

| File | CMS 2018 car | CMS 2021 car |
| --- | --- | --- |
| `car_NAME.cms` (Unity bundle) | yes | yes |
| `config.txt`, `bodyconfig.txt`, `parts.txt`, `name.txt` | yes | yes |
| `PartThumb/` part images | yes | yes |
| `upload_config.txt`, `upload_preview.png` (Workshop uploader files) | yes | yes |
| `config1.txt`, `bodyconfig1.txt` (extra variant) | no | yes |
| `.meta` files next to the bundle (`car_NAME.cms.meta`, `PartThumb.meta`) | yes | no (only inside `Materials/`) |

The CMS 2021 sample also ships `Materials/`, `Textures/` and `RustMaps/` folders. These may be source files for the uploader rather than something the game needs; that is not confirmed.

## Verified: the `.cms` bundle

| | CMS 2018 car | CMS 2021 car |
| --- | --- | --- |
| Signature | `SnityFS` | `UnityFS` |
| Bundle format version | 6 | 7 |
| Unity version | 2017.1.0f3 | 2021.1.20f1 |
| Compression | LZ4HC | LZ4HC |
| Recorded size equals file size | yes | yes |

The CMS 2018 bundle's header parses cleanly apart from the first letter of the signature, which suggests the change is deliberate rather than corruption. A standard `UnityFS` signature is what tools such as UnityPy expect.

## Verified: what is inside the bundles

Both bundles were opened with UnityPy on a GitHub runner (the CMS 2018 one using a copy with the signature fixed, see `cms_tools/fix_signature.py`) and read without errors.

| Object type | CMS 2018 car | CMS 2021 car |
| --- | --- | --- |
| GameObject / Transform | 24 | 44 |
| Mesh (each with MeshFilter, MeshRenderer, MeshCollider) | 23 | 43 |
| Material | 63 | 66 |
| Texture2D | 24 | 33 |
| Shader | 1 | 1 |
| Animator, Avatar | 1 each | 0 |
| MonoBehaviour (scripts), TextAsset | 0 | 0 |

- Neither bundle contains scripts, so there is no code to port between Unity versions. The car's behaviour comes from the text files.
- Both use the same texture format codes (10 and 12).
- Both contain GameObjects named after every part in their `parts.txt`, plus `model`, `body`, `collider` and `details`.
- **The shaders differ.** Every material in the CMS 2018 car uses Unity's built-in `Standard` shader (63 materials). Every material in the CMS 2021 car uses `HDRP/Lit` (66 materials), so CMS 2021 appears to use Unity's High Definition Render Pipeline. Unity's `Standard` shader is normally not supported by HDRP, where such materials usually show up pink. This has not been confirmed in CMS 2021.
- The CMS 2018 car has a gauge needle object (`wskazowka`) and a `GAUGE_NEEDLE` material. The CMS 2021 car has `speed` and `tach` objects, alongside its `[dials]` config section. How these relate is not yet verified.

## Verified: `config.txt`

Output of `python -m cms_tools.diff_configs` with A = CMS 2018 and B = CMS 2021. Values are not compared, only which sections and keys exist.

**Sections only in CMS 2021:** `10_bonusParts`, `carLight#` (numbered, `carLight0`, `carLight1`), `carLightBasic`, `dials`.

| Section | Only in CMS 2018 | Only in CMS 2021 |
| --- | --- | --- |
| `[0_main]` | | `carBrand`, `scale` |
| `[1_other]` | `finalDriveRatio`, `rpmAngle`, `rpmFactor`, `speedoAngle`, `speedoFactor` | `allowedColors`, `brakeMod`, `engineTorqueMod`, `engineWeight`, `gearsFinalRatioMod`, `liveries`, `thumbnailColor` |
| `[2_suspension]` | | `frontStiffness`, `rearStiffness` |
| `[6_engine]` | | `swapoptions` |
| `[8_logic]` | | `carValue` |

The new `[dials]` section in CMS 2021 holds the gauge settings (`dialname`, `rpm_max`, `rpm_max_angle`, `speed_max_kph`, `speed_max_angle`, and others). The CMS 2018 gauge keys in `[1_other]` (`rpmAngle`, `rpmFactor`, `speedoAngle`, `speedoFactor`) have no direct counterpart.

Other differences noticed while reading both files:

- `allowedPlaces` entries in the CMS 2021 car can carry a number (`Order.16`); the CMS 2018 car uses plain names.
- `frontWheelMaxSize` is `5` in the CMS 2018 car and `0.385` in the CMS 2021 car. This could be a change of units or just a difference between the two cars; with one car each, it cannot be told apart.

## Not yet known

- Whether CMS 2021 loads a CMS 2018 car at all, with or without the signature change. Nothing here has been run in the game.
- Whether the `Standard`-shader materials really show up pink in CMS 2021, as expected for HDRP.
- How to convert the materials. The likely route is re-creating them as `HDRP/Lit` in a Unity 2021.1.20f1 HDRP project and rebuilding the bundle. That needs the Unity editor; the Python tools here cannot do it.
- How the CMS 2018 gauge keys and `wskazowka` needle map onto the CMS 2021 `[dials]` values and `speed` / `tach` objects.
- Which of the new CMS 2021 keys are required and which have safe defaults.
- Whether `bodyconfig.txt` and `parts.txt` need changes. The files looked structurally similar in these two cars, but that was not checked in detail.

## Suggested first experiment

1. Make a copy of the CMS 2018 car folder.
2. Run `python -m cms_tools.fix_signature` on its `.cms` file and use the fixed copy.
3. Put the folder where CMS 2021 expects mods and see whether the car appears.
4. If it loads but misbehaves, add the missing `config.txt` sections one at a time, using the CMS 2021 car's values as a model, and note what each change does.
5. If the car appears with pink or broken materials, the shader difference above is the next problem to solve.
