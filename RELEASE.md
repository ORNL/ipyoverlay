# Publishing Checklist

1. Run `pytest`
2. Update version in `ipyoverlay/__init__.py`
3. Update changelog (`CHANGELOG.md`)
4. Generate documentation in `sphinx` directory with `make html` (if doc updates)
5. Modfiy `sphinx/source/_static/switcher.json` and add a new entry for the version/update version of current stable (if doc updates)
6. Apply documentation `make apply-docs` (if doc updates)
7. Commit
8. Push to github
9. Publish to pypi (`make publish`)
10. Tag release on github
