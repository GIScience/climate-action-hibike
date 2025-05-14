# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project mostly adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://gitlab.heigit.org/climate-action/plugins/bikeability/-/compare/1.1.3...main)

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

