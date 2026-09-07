# Upload Project #2

1. Extract `Infrastructure_Dependency_Analyzer.zip`.
2. Open the included `infrastructure-dependency-analyzer` folder.
3. Open `examples/interactive-report.html` to try the demo.
4. In GitHub, create a **Public** repository named `infrastructure-dependency-analyzer`.
5. Description: `Offline infrastructure dependency analysis with business-impact scenarios, recovery planning checks, and an interactive report.`
6. Leave GitHub’s starter README, .gitignore, and license options off; these files are already supplied.
7. Choose **uploading an existing file**. Drag the CONTENTS of the extracted project folder into GitHub. The list should show `analyzer.py` and `README.md` without an extra project-folder prefix. Preserve the examples and tests folders.
8. Commit with `Add infrastructure dependency analyzer`.
9. If `.github/workflows/test.yml` was omitted by the upload, use **Add file → Create new file**, enter that exact path, and paste the workflow below. Commit directly to main.
10. Open **Actions** and inspect the four test jobs. If no run appears, select **Python tests → Run workflow → main → Run workflow**.

```yaml
name: Python tests
on:
  push:
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.10', '3.11', '3.12', '3.13']
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: ${{ matrix.python-version }}
      - name: Run tests
        run: python -m unittest discover -s tests -v
```

Paste each `uses:` value exactly. For example, `actions/actions` is not the checkout repository.

Suggested topics: `python`, `infrastructure`, `business-continuity`, `dependency-analysis`, `it-operations`, `disaster-recovery`.

After publication, share the repository URL to add it to your OSU portfolio. GitHub will show HTML source; to run the offline demo, download the repository ZIP, extract it, and open the HTML locally. Publishing a GitHub Pages demo is a separate optional step.
