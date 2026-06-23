# Running the tests

## Unit tests (no RAY-UI required)

```bash
./tools/test_versions.sh
```

## Regression tests — stable vs development RAY-UI

```bash
./tools/test_versions.sh \
    --stable /home/simone/Applications/Ray-UI \
    --dev    /home/simone/Applications/Ray-UI-development
```

## Regression tests — also run multi-energy (slow)

```bash
./tools/test_versions.sh \
    --stable /home/simone/Applications/Ray-UI \
    --dev    /home/simone/Applications/Ray-UI-development \
    --slow
```
