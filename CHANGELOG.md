# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project mostly adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/compare/2.0.0...main)

### Fixed
- Clipping bug in greenness computation is fixed now by removing the necessity to clip again on artifact creation ([#109](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/109))

### Changed
- Polygon Paths and Line Paths are now only separated where functionally necessary, in other places they are kept together.

## [2.0.0](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/releases/2.0.0) - 2025-11-10

### Changed

- Added more tests for separate OSM Parking requests ([#40](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/40))
- Added commit hash to docker files and ci for development environment builds ([#83](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/83))
- Added pytest-coverage to project and ci ([#82](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/82))
- Update ruff config and pre-commit-hooks for dev setup ([#54](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/82))
- Remove Kaniko from build processs ([#95](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/95))
- Add teaser to plugin and restore the previous purpose
- Update the colors of surface types in hiBike to match hiWalk ([#94](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/94))
- Tests for ohsome filter functions now rely on validation of their grammar by ohsome-filter-to-sql instead of approving filters in plain text ([#100]((https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/100)))
- Move PathCategoryFilters from a class to a module ([#98](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/98))
- Harden maxspeed filters and move them to a separate function ([#99](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/99))
- Handle maxspeed tags in mph ([#103](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/103))
- Added "shared with cars of unknown speed" category to path categories ([#86](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/86))
- Added 'maxspeed:backward' tag to maxspeed filters ([#102](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/102))
- Update the colors of surface types in hiBike to match hiWalk ([#94](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/94))
- Update result size (paths count) check method and directly request ohsome element count api([#104](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/104))
- Remove network requests from dooring risk tests
- Remove netwokr requests from smoothness test
- Refactor to match standard plugin layout ([#87](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/87))

### Added
- Port Detour Factors from Hiwalk ([#96])(https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/96)
- Add greenness(naturalness) indicator into hiBike ([#38](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/38))
- Add histogram for greenness and summary chart for path categories ([#97](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/97))

## [1.1.5](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/releases/1.1.5) - 2025-06-04

### Changed

- Updated climatoology to 6.4.2

## [1.1.4](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/releases/1.1.4)

### Changed
- Now public transport platforms are consistently categorized as "Requires dismounting" ([#74](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/74))
- To avoid cluttering map display and distracting from gaps in the public cycling path network, hiBike now excludes indoor paths from data requested from OSM and hides from view all paths with restricted public access ((#73)[https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/73])
- Change color maps for legends ([#75](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/75))
- Make path category labeling more consistent with hiWalk
- Update general methodology ([#76](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/76))

### Fixed
- Computation now also works if there are no polygon paths in the area ([#77](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/77))
- Fix invalid path geometries ([#84](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/84))

## [1.1.3](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/releases/1.1.3)

### Changed
- New icon simplified icon
- More concise description of the assessment tool

## [1.1.0](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/releases/1.1.0)

### Changed
- Tool name from 'Bikeability' to 'hiBike' ([#65](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/65))
- Description of the dooring risk ([#58](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/58))
- Description of the surface types ([#62](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/62))
- Classify paths with restricted access as "not bikeable" so that they are displayed in the map of bikeable path categories ([#63](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/63))

- Updated Climatoology to 6.4.0
- Include demo_input_parameters in operator worker file


### Added
- Functionality to re-categorise geometries that match with zebra crossing nodes to require
  dismounting([#22](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/22))
- Check to ensure that the number of path segments in the AOI does not exceed 500,000 ([#67](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/67))

### Removed
- Unused user input parameters ([#48](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/48))

## [1.0.0](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/releases/1.0.0)

### Removed

- Removed legacy feature "boost_route_members" ([#37](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/37))

### Changed

- Modified ohsome filters to keep information on ways with restricted access and footpaths without designated bike access ([#19](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/19))


- Refactored operator_worker.py to outsource the functions for calculating indicators [(!26)](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/merge_requests/26)
- Refactored utils.py to outsource classes and functions for specific indicators to indicator files [(!28)](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/merge_requests/28)
- `get_qualitative_color()` is now category agnostic, as long as the unknown/missing data category has the value `'unknown'` [(!28)](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/merge_requests/28)
- Updated to climatoology 6.0.2

### Added

- Added smoothness indicator ([#35](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/35))
- Added surface type indicator ([#34](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/34))
- Added dooring risk indicator ([#32](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/32))
- Added shadow PathCategories and mechanisms to ignore these categories for artifact building ([#19](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/19)).

## [Demo](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/compare/main...demo?from_project_id=914&straight=true)

### Changed
- First full set of bikeable path categories based on the share with other road users ([#7](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/7), [#17](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/17), [#20](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/20), [#25](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/25))

### Added
- Description of the plugin and path category indicator ([#9](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/9), [#15](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/issues/15))



## [Dummy](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/tree/e125efcd136567c554ee7bbf6f67c8366aae9a55) 2024-10-02

### Changed

- Complete revision of repository to create a dummy based on the walkability functionality.

