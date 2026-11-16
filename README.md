# openarabee-web

The website of [OpenArabee](https://github.com/OpenArabee/openarabee-core), served by GitHub Pages at
[openarabee.com](https://openarabee.com).

Right now this is a single hand-written start page (`index.html`). In Phase 1d of the
[project charter](https://github.com/OpenArabee/openarabee-core/blob/main/docs/charter.md) it becomes a
site generated from the dataset, with one page per root.

## Rules

- No cookies, no trackers, nothing loaded from other servers (fonts, scripts, analytics).
- Every linguistic value shown on the site comes from `openarabee-core`, with its source and status.
  The example on the start page is bāb 1 of `reference/abwab.bina-35.json`.
- No numbers or claims that the project has not computed itself (charter §9).
- Changes go through a branch and a pull request; the owner merges.

## Generated pages

`abwab.html` is generated from the reference tables: `python tools/build_abwab.py ../openarabee-core`
(a checkout of `openarabee-core` at `main`). Regenerate it whenever the tables change; never edit it by hand.

## Publishing

GitHub Pages: *Settings → Pages → Deploy from a branch → `main` / root*. The file `CNAME` sets the
custom domain. `.nojekyll` switches off GitHub's Jekyll build, so files are served as they are.

## Licences

Code: MIT (`LICENSE`). Texts: CC BY 4.0. For the logo see `assets/README.md` in `openarabee-core`.
