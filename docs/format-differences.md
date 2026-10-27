# CMS 2018 vs CMS 2021 car mods: observed differences

This compares three cars, so treat it as a starting point rather than a complete specification.

- **CMS 2018:** 1951 Holden FX Coupe Utility (Workshop item folder `1203793941`)
- **CMS 2021, Workshop mod:** 1969 Camaro RS SS (Workshop item `2689830628`)
- **CMS 2021, stock game car:** Sixon Cebulion (`car_sixoncebulion.cms`). Only its text config files and the output of local tools are used here; no game files are stored in this repo.

Where a table says "CMS 2021 car" without further detail, it means the Camaro. Everything under "Verified" was read directly from those files with the tools in this repo. Everything under "Not yet known" is open.

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

| | CMS 2018 Holden | CMS 2021 Camaro (Workshop) | CMS 2021 Cebulion (stock) |
| --- | --- | --- | --- |
| Signature | `SnityFS` | `UnityFS` | `UnityFS` |
| Bundle format version | 6 | 7 | 8 |
| Unity version | 2017.1.0f3 | 2021.1.20f1 | 2020.3.41f1 |
| Compression | LZ4HC | LZ4HC | LZ4HC |
| Recorded size equals file size | yes | yes | yes |

The CMS 2018 bundle's header parses cleanly apart from the first letter of the signature, which suggests the change is deliberate rather than corruption. A standard `UnityFS` signature is what tools such as UnityPy expect.

The game's own engine is 2020.3.49f1 (see test results). The stock car was built with 2020.3.41f1, the closest match. The Workshop Camaro was built with a newer editor (2021.1.20f1) than the game runs on, so a different editor version does not by itself rule a bundle out, though whether the Camaro loads has not been tested here.

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
- **The shaders differ.** Every material in the CMS 2018 car uses Unity's built-in `Standard` shader (63 materials). Every material in the CMS 2021 car uses `HDRP/Lit` (66 materials), and the game's own `Player.log` confirms CMS 2021 renders with Unity's High Definition Render Pipeline. Unity's `Standard` shader is normally not supported by HDRP, where such materials usually show up pink. That has not been seen in CMS 2021 yet, because the car has not loaded (see test results).
- A local text scan of the decompressed bundles (`cms_tools/bundle_peek.py`, checked against the UnityPy results above) finds `Standard` in the Holden bundle and `HDRP/Lit` in both the Camaro and the stock Cebulion bundle. So both CMS 2021 cars, including the game's own, ship the `HDRP/Lit` shader. The scan also finds a stray `Standard` string in both CMS 2021 bundles, which UnityPy did not report as a shader for the Camaro, so it is probably unrelated text. Treat the scan's counts as rough.
- All three bundles have the same shape: one serialized data file plus one `.resS` file holding bulk data such as textures.
- The CMS 2018 car has a gauge needle object (`wskazowka`) and a `GAUGE_NEEDLE` material. The CMS 2021 car has `speed` and `tach` objects, alongside its `[dials]` config section. How these relate is not yet verified.

## Verified: `config.txt`

Output of `python -m cms_tools.diff_configs`. Values are not compared, only which sections and keys exist.

**Holden (CMS 2018) against Camaro (CMS 2021 Workshop).** Sections only in the Camaro: `10_bonusParts`, `carLight#` (numbered, `carLight0`, `carLight1`), `carLightBasic`, `dials`.

| Section | Only in Holden | Only in Camaro |
| --- | --- | --- |
| `[0_main]` | | `carBrand`, `scale` |
| `[1_other]` | `finalDriveRatio`, `rpmAngle`, `rpmFactor`, `speedoAngle`, `speedoFactor` | `allowedColors`, `brakeMod`, `engineTorqueMod`, `engineWeight`, `gearsFinalRatioMod`, `liveries`, `thumbnailColor` |
| `[2_suspension]` | | `frontStiffness`, `rearStiffness` |
| `[6_engine]` | | `swapoptions` |
| `[8_logic]` | | `carValue` |

The new `[dials]` section holds the gauge settings (`dialname`, `rpm_max`, `rpm_max_angle`, `speed_max_kph`, `speed_max_angle`, and others). The Holden's gauge keys in `[1_other]` (`rpmAngle`, `rpmFactor`, `speedoAngle`, `speedoFactor`) have no direct counterpart.

**Correction:** an earlier version of these notes treated `finalDriveRatio` as a CMS 2018-only key, because the Camaro lacks it. The stock Cebulion config has `finalDriveRatio=4`, so it still exists in CMS 2021 and is simply optional.

**Stock Cebulion against Camaro.** The stock car has some things the Workshop Camaro lacks: a `[dragstrip]` section of performance data, `bonusPart#` sections, `engineRpmMod` and `finalDriveRatio` in `[1_other]`, `scale` in `[2_suspension]`, and `sound` in `[6_engine]`. The Camaro has `liveries`, which the stock car lacks. Both CMS 2021 configs share the extra sections and keys listed above (`dials`, `carLight#`, and so on), and neither contains the Holden's old gauge keys. Because the Camaro is a published mod that works without the keys the stock car adds, those keys look optional, but nothing has been tested.

Other differences noticed while reading the files:

- `allowedPlaces` differs in both format and names: Holden `Shed,Junkyard,Auction,Salon`, Camaro `Order.16,Shed,Junkyard,Auction`, stock `Order.5,Junkyard,Auction,Barn`. Entries can carry a number (`Order.5`), and names vary (`Shed`, `Barn`, `Salon`). Which names CMS 2021 accepts is not verified.
- `frontWheelMaxSize` is `5` in the Holden and `0.385` / `0.375` in the two CMS 2021 cars. That suggests a change of units rather than a car-specific value, but three cars is not conclusive.
- The Holden config names CMS 2018 part IDs (`engine_i6_old`, `rim_willys`, `seat_atlanta`, `steering_wheel_cape`, `tire_vintage_wall2`). The CMS 2021 configs use other IDs (for example `rim_36`, `seat_7_leather4`, `steering_wheel1`).
- The stock car's `bodyconfig.txt` has a `[tuning]` section mapping parts to variants (such as `hood=hood2`) and a per-variant license plate position section. The Holden's does not.

## Test results

**Game engine (from `Player.log`):** CMS 2021 reports Unity 2020.3.49f1 and Direct3D 11, and its log shows `HDRenderPipeline` calls. The CMS 2021 sample car's bundle was built with Unity 2021.1.20f1, which is newer than the game's own engine, so the editor version used for CMS 2021 mods is not the same as the game's runtime version.

**Test 1 — CMS 2018 Holden, only the bundle signature fixed (`SnityFS` to `UnityFS`), config files unchanged:**
the game froze before reaching the title screen. The last lines of `Player.log` were `[GameDataManager] -> Load()` and `[MenuPressButton] -> LoadData() Waiting for CarBundleLoader. Start: 00:00:03`, and the log ends there. It contains no error or exception lines at all, and it never names the mod, so the log does not say which car or file caused the stall. It does show the game was waiting on the car bundle loader and never got past it. This points at car bundle loading but does not prove the Holden bundle is the cause.

## Not yet known

- Whether CMS 2021 can load a CMS 2018 car at all. Test 1 froze at startup, so the first thing to find out is why.
- Whether the freeze depends on the signature fix. Testing the original, unfixed Holden mod would show this.
- Whether the freeze comes from the bundle or from `config.txt`.
- Whether the `Standard`-shader materials show up pink in CMS 2021, as expected for HDRP. This cannot be seen until a car loads.
- How to convert the materials. The likely route is re-creating them as `HDRP/Lit` in a Unity 2021.1.20f1 HDRP project and rebuilding the bundle. That needs the Unity editor; the Python tools here cannot do it.
- How the CMS 2018 gauge keys and `wskazowka` needle map onto the CMS 2021 `[dials]` values and `speed` / `tach` objects.
- Which of the new CMS 2021 keys are required. The Camaro, a known-shape CMS 2021 config, is the best model for a minimum set, but nothing has been tested.
- Whether CMS 2021 still has the CMS 2018 part IDs that the Holden config names (`engine_i6_old`, `rim_willys`, `seat_atlanta`, `steering_wheel_cape`, `tire_vintage_wall2`, and the exhaust, downpipe and radiator parts). A missing ID could cause problems of its own.
- Whether `bodyconfig.txt` and `parts.txt` need changes. The files looked structurally similar in these two cars, but that was not checked in detail.

## Suggested first experiment

1. Make a copy of the CMS 2018 car folder.
2. Run `python -m cms_tools.fix_signature` on its `.cms` file and use the fixed copy.
3. Put the folder where CMS 2021 expects mods and see whether the car appears.
4. If it loads but misbehaves, add the missing `config.txt` sections one at a time, using the CMS 2021 car's values as a model, and note what each change does.
5. If the car appears with pink or broken materials, the shader difference above is the next problem to solve.
