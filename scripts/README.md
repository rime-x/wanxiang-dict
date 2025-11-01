# add_auxcodes script

This folder contains a small utility to append auxiliary codes from `fuzhuma/moqi/moqima_41448.txt` into the pinyin field of `dicts/wanxiang/dicts/chars.dict.yaml`.

Usage examples

- Dry-run (show unified diff):

```bash
python scripts/add_auxcodes.py --moqi fuzhuma/moqi/moqima_41448.txt --file dicts/wanxiang/dicts/chars.dict.yaml --dry-run
```

- Apply changes in-place and keep a timestamped backup:

```bash
python scripts/add_auxcodes.py --moqi fuzhuma/moqi/moqima_41448.txt --file dicts/wanxiang/dicts/chars.dict.yaml --backup --inplace
```

Batch processing (process all dicts in the same folder as `chars.dict.yaml` and write outputs to repo-root `auxified/moqi` folder):

```bash
python scripts/add_auxcodes.py --moqi fuzhuma/moqi/moqima_41448.txt --dir dicts/wanxiang/dicts --out-dir auxified/moqi --dry-run
```

The above will write output files (when not using `--dry-run`) to `./auxified/moqi/<original-filename>` under the current working directory. If you prefer to overwrite the originals, use `--inplace` (optionally with `--backup`).

GitHub Actions

The workflow `.github/workflows/add-auxcodes.yml` runs a dry-run and, on manual dispatch or when on `main`, applies changes and commits them.
