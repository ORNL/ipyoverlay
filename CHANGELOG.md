# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.2.0] - 2024-07-29

### Added
* `add_child_at_mpl_point()` function to simplify needing to separately call three
  different functions to add a child, get pixel converted mpl data locs, and
  then connect the new child 
* `display_output()` function to support creating an ipywidgets `Output` and
  rendering any displayable such as a static matplotlib figure with a single call

### Fixed
* Missing top level module imports
* Connection to matplotlib ipympl canvas not always using the instance within the
  container




## [0.1.0] - 2024-06-27

First open source release!
