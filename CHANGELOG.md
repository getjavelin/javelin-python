<a name="unreleased"></a>
## [Unreleased]


<a name="v0.2.21"></a>
## [v0.2.21] - 2025-02-03
### Bug Fixes
- take both bedrock & bedrock-runtime client
- Update client URL scheme: use scheme from self.base_url instead of hardcoding 'https'
- fixed a few bugs

### DevOps
- Update CHANGELOG for v0.2.20

### Features
- 1. added logic to look for model_arn if profile_arn is not found. Fail silently in case of error (this needs to be enhanced to add async tracing). 2. added logic to pass a default_route_name for bedrock models optionally when registering bedrock_client, 3. added logic to always etract the model and set the x-javlein-model header (needed for model_spec in case if are not rewriting the url and we get an arn instead of model id
- register_bedrock now supports arn
- Integrating LangGraph agents with Javelin route with proper comments and short documentaiton of implementation

### Pull Requests
- Merge pull request [#119](https://github.com/getjavelin/javelin-python/issues/119) from getjavelin/spg
- Merge pull request [#118](https://github.com/getjavelin/javelin-python/issues/118) from getjavelin/spg
- Merge pull request [#116](https://github.com/getjavelin/javelin-python/issues/116) from getjavelin/langraph-javelin-branch
- Merge pull request [#117](https://github.com/getjavelin/javelin-python/issues/117) from getjavelin/cicd-changelog


<a name="v0.2.20"></a>
## [v0.2.20] - 2025-01-31
### Bug Fixes
- release version build break
- parse newly updated streaming responses
- support CRUD operation secret
- supporing the bot commit message pr checks
- revert changes for javelin-api-key
- update key field api_key_value field

### DevOps
- Patching the pr issue status change pipeline
- Patching the pr issue status change pipeline
- Adding pipeline for PR issue status update
- Bumping the version of slack plugins and patching the pipeline
- Patching the PR checks pipeline
- Adding lint checks in the PR checks pipeline
- Patching the testing pipeline
- Patching the testing pipeline
- Patching the Trivy Scan Pipeline
- Patching the Changelog PR commit message
- Adding the trivy scan
- Adding the trivy scan
- Patching the pipeline with a dynamic variable for devops repo branch
- Patching the cicd pipeline for PR checks
- Patching the pipeline to use ubuntu-24.04 OS in action
- Update CHANGELOG for v0.2.19

### Features
- setting up boto3 client with javelin for runtime-operation. scope custom header registration to Bedrock runtime operations only
- Adding example files for Azure OpenAI and Javelin stream/non-stream tests In Python and JS code
- Enhance CrewwAI and Javelin integration with refined workflow
- Adding usage guide for RAG with Javelin

### Pull Requests
- Merge pull request [#115](https://github.com/getjavelin/javelin-python/issues/115) from getjavelin/fix_streaming_responses
- Merge pull request [#114](https://github.com/getjavelin/javelin-python/issues/114) from getjavelin/issue-20-boto-helper-sdk-integration
- Merge pull request [#113](https://github.com/getjavelin/javelin-python/issues/113) from getjavelin/invoke-converse-branch
- Merge pull request [#112](https://github.com/getjavelin/javelin-python/issues/112) from getjavelin/crew-javelin-branch
- Merge pull request [#111](https://github.com/getjavelin/javelin-python/issues/111) from getjavelin/rag-javelin-branch
- Merge pull request [#110](https://github.com/getjavelin/javelin-python/issues/110) from getjavelin/fix_streaming_responses
- Merge pull request [#109](https://github.com/getjavelin/javelin-python/issues/109) from getjavelin/cicd-patch
- Merge pull request [#108](https://github.com/getjavelin/javelin-python/issues/108) from getjavelin/cicd-patch
- Merge pull request [#106](https://github.com/getjavelin/javelin-python/issues/106) from getjavelin/cicd-patch
- Merge pull request [#105](https://github.com/getjavelin/javelin-python/issues/105) from getjavelin/ISSUE-15
- Merge pull request [#103](https://github.com/getjavelin/javelin-python/issues/103) from getjavelin/cicd-patch
- Merge pull request [#98](https://github.com/getjavelin/javelin-python/issues/98) from getjavelin/cicd-patch
- Merge pull request [#97](https://github.com/getjavelin/javelin-python/issues/97) from getjavelin/cicd-patch
- Merge pull request [#96](https://github.com/getjavelin/javelin-python/issues/96) from getjavelin/cicd-patch
- Merge pull request [#95](https://github.com/getjavelin/javelin-python/issues/95) from getjavelin/cicd-patch
- Merge pull request [#94](https://github.com/getjavelin/javelin-python/issues/94) from getjavelin/cicd-patch
- Merge pull request [#93](https://github.com/getjavelin/javelin-python/issues/93) from getjavelin/cicd-patch
- Merge pull request [#92](https://github.com/getjavelin/javelin-python/issues/92) from getjavelin/cicd-patch
- Merge pull request [#91](https://github.com/getjavelin/javelin-python/issues/91) from getjavelin/cicd-patch
- Merge pull request [#90](https://github.com/getjavelin/javelin-python/issues/90) from getjavelin/ISSUE-89
- Merge pull request [#88](https://github.com/getjavelin/javelin-python/issues/88) from getjavelin/cicd-changelog


<a name="v0.2.19"></a>
## [v0.2.19] - 2024-12-05
### DevOps
- Update CHANGELOG for v0.2.18

### Pull Requests
- Merge pull request [#82](https://github.com/getjavelin/javelin-python/issues/82) from getjavelin/cicd-changelog


<a name="v0.2.18"></a>
## [v0.2.18] - 2024-12-04
### Bug Fixes
- add security filters field in route config

### Pull Requests
- Merge pull request [#84](https://github.com/getjavelin/javelin-python/issues/84) from getjavelin/ISSUE-83


<a name="v0.2.17"></a>
## [v0.2.17] - 2024-12-03
### DevOps
- Update CHANGELOG for v0.2.16

### Pull Requests
- Merge pull request [#80](https://github.com/getjavelin/javelin-python/issues/80) from getjavelin/cicd-changelog


<a name="v0.2.16"></a>
## [v0.2.16] - 2024-12-03
### Bug Fixes
- handle empty input/output rules in ModelSpec initialization ([#79](https://github.com/getjavelin/javelin-python/issues/79))
- support for traces in SDK

### DevOps
- Swagger Sync ([#59](https://github.com/getjavelin/javelin-python/issues/59))
- Update CHANGELOG for v0.2.15

### Pull Requests
- Merge pull request [#75](https://github.com/getjavelin/javelin-python/issues/75) from getjavelin/ISSUE-71
- Merge pull request [#74](https://github.com/getjavelin/javelin-python/issues/74) from getjavelin/cicd-changelog


<a name="v0.2.15"></a>
## [v0.2.15] - 2024-11-17
### Bug Fixes
- call reload API after every updation/deletion

### DevOps
- Update CHANGELOG for v0.2.14

### Pull Requests
- Merge pull request [#72](https://github.com/getjavelin/javelin-python/issues/72) from getjavelin/ISSUE-272
- Merge pull request [#69](https://github.com/getjavelin/javelin-python/issues/69) from getjavelin/cicd-changelog


<a name="v0.2.14"></a>
## [v0.2.14] - 2024-11-11
### DevOps
- Fixing the PR checks issue for PR merge commit msg
- Adding changelog PR for release

### Pull Requests
- Merge pull request [#66](https://github.com/getjavelin/javelin-python/issues/66) from getjavelin/cicd-patch


<a name="v0.2.13"></a>
## [v0.2.13] - 2024-11-11
### Bug Fixes
- Patching the commit message check
- Patching the commit message check

### DevOps
- Adding changelogs for the module
- Adding the PR checks

### Features
- add example to create embeddings for rag ([#64](https://github.com/getjavelin/javelin-python/issues/64))

### Pull Requests
- Merge pull request [#65](https://github.com/getjavelin/javelin-python/issues/65) from getjavelin/cicd-patch
- Merge pull request [#63](https://github.com/getjavelin/javelin-python/issues/63) from getjavelin/cicd-patch
- Merge pull request [#62](https://github.com/getjavelin/javelin-python/issues/62) from getjavelin/cicd-patch
- Merge pull request [#47](https://github.com/getjavelin/javelin-python/issues/47) from getjavelin/blog
- Merge pull request [#56](https://github.com/getjavelin/javelin-python/issues/56) from getjavelin/38-sync-models-between-javelin-admin-and-javelin-python
- Merge pull request [#58](https://github.com/getjavelin/javelin-python/issues/58) from getjavelin/examples
- Merge pull request [#55](https://github.com/getjavelin/javelin-python/issues/55) from getjavelin/38-sync-models-between-javelin-admin-and-javelin-python
- Merge pull request [#54](https://github.com/getjavelin/javelin-python/issues/54) from getjavelin/examples


<a name="v0.2.12"></a>
## [v0.2.12] - 2024-10-21
### Pull Requests
- Merge pull request [#50](https://github.com/getjavelin/javelin-python/issues/50) from getjavelin/ISSUE-5


<a name="v0.2.11"></a>
## [v0.2.11] - 2024-10-09
### Pull Requests
- Merge pull request [#46](https://github.com/getjavelin/javelin-python/issues/46) from getjavelin/14-javelin-cli-for-all-admin-capabilities


<a name="v0.2.10"></a>
## [v0.2.10] - 2024-10-09

<a name="v0.2.9"></a>
## [v0.2.9] - 2024-10-09
### Pull Requests
- Merge pull request [#41](https://github.com/getjavelin/javelin-python/issues/41) from getjavelin/38-sync-models-between-javelin-admin-and-javelin-python
- Merge pull request [#39](https://github.com/getjavelin/javelin-python/issues/39) from getjavelin/15-add-validation-like-pydantic-in-javelin-python
- Merge pull request [#37](https://github.com/getjavelin/javelin-python/issues/37) from getjavelin/cicd-patch


<a name="v0.2.8"></a>
## [v0.2.8] - 2024-10-02
### Features
- add javelin_sdk_app.py under examples

### Pull Requests
- Merge pull request [#36](https://github.com/getjavelin/javelin-python/issues/36) from getjavelin/cicd-patch
- Merge pull request [#35](https://github.com/getjavelin/javelin-python/issues/35) from getjavelin/feature-add-javelin-sdk-app


<a name="v0.2.7"></a>
## [v0.2.7] - 2024-10-01
### Pull Requests
- Merge pull request [#34](https://github.com/getjavelin/javelin-python/issues/34) from getjavelin/cicd-patch
- Merge pull request [#33](https://github.com/getjavelin/javelin-python/issues/33) from getjavelin/cicd-patch


<a name="v0.2.6"></a>
## [v0.2.6] - 2024-09-30
### Bug Fixes
- cache javelin credential data
- javelin auth
- exception handling
- Update template commands
- updated models insync with javelin-core and javelin-admin
- create/update for Provider, Route and Secret
- Secret Management
- return empty list if an error occurs or no secrets are found
- Dependabot alerts
- Known security vulnerabilities detected
- support setting the base_url from an environment variable with a fallback to javelin dev environment
- rename directory to javelin_cli
- changed command argument from read to get
- set indent to 2
- Updated for Gateway
- updated base url to https://api-dev.javelin.live
- provider functions

### Features
- Refactor example routes and improve error handling ([#31](https://github.com/getjavelin/javelin-python/issues/31))
- Mask sensitive fields in secrets and improve secret listing output
- updated commands for secret
- updated commands for provider, route
- Updated Gateway commands
- CLI for Javelin SDK
- CLI for Javelin SDK
- Update Gateway example
- Updated with Gateway
- update models with Gateway

### Pull Requests
- Merge pull request [#29](https://github.com/getjavelin/javelin-python/issues/29) from getjavelin/20-sdk-enhancements
- Merge pull request [#25](https://github.com/getjavelin/javelin-python/issues/25) from getjavelin/fix-code-scanning-alert
- Merge pull request [#24](https://github.com/getjavelin/javelin-python/issues/24) from getjavelin/20-sdk-enhancements
- Merge pull request [#23](https://github.com/getjavelin/javelin-python/issues/23) from getjavelin/20-sdk-enhancements
- Merge pull request [#22](https://github.com/getjavelin/javelin-python/issues/22) from getjavelin/20-sdk-enhancements
- Merge pull request [#21](https://github.com/getjavelin/javelin-python/issues/21) from getjavelin/20-sdk-enhancements
- Merge pull request [#12](https://github.com/getjavelin/javelin-python/issues/12) from getjavelin/dependabot/pip/black-24.3.0
- Merge pull request [#7](https://github.com/getjavelin/javelin-python/issues/7) from getjavelin/dependabot/pip/zipp-3.19.1
- Merge pull request [#6](https://github.com/getjavelin/javelin-python/issues/6) from getjavelin/dependabot/pip/certifi-2024.7.4
- Merge pull request [#3](https://github.com/getjavelin/javelin-python/issues/3) from getjavelin/dependabot/pip/jinja2-3.1.4
- Merge pull request [#5](https://github.com/getjavelin/javelin-python/issues/5) from getjavelin/dependabot/pip/urllib3-2.2.2
- Merge pull request [#4](https://github.com/getjavelin/javelin-python/issues/4) from getjavelin/dependabot/pip/requests-2.32.0
- Merge pull request [#13](https://github.com/getjavelin/javelin-python/issues/13) from getjavelin/dependabot/pip/pydantic-1.10.13


<a name="v0.2.5"></a>
## [v0.2.5] - 2024-01-05
### Bug Fixes
- **(javelin-sdk):** Changed message to Access denied from Invalid API key


<a name="v0.2.4"></a>
## [v0.2.4] - 2023-12-15
### Features
- **(javelin_sdk):** tested and updated exceptions


<a name="v0.2.3"></a>
## [v0.2.3] - 2023-12-14

<a name="v0.2.2"></a>
## [v0.2.2] - 2023-12-14

<a name="v0.2.1"></a>
## [v0.2.1] - 2023-12-14

<a name="v0.2.0"></a>
## [v0.2.0] - 2023-12-06

<a name="v0.1.8"></a>
## [v0.1.8] - 2023-09-04

<a name="v0.1.7"></a>
## [v0.1.7] - 2023-09-04

<a name="v0.1.5"></a>
## v0.1.5 - 2023-09-04

[Unreleased]: https://github.com/getjavelin/javelin-python/compare/v0.2.21...HEAD
[v0.2.21]: https://github.com/getjavelin/javelin-python/compare/v0.2.20...v0.2.21
[v0.2.20]: https://github.com/getjavelin/javelin-python/compare/v0.2.19...v0.2.20
[v0.2.19]: https://github.com/getjavelin/javelin-python/compare/v0.2.18...v0.2.19
[v0.2.18]: https://github.com/getjavelin/javelin-python/compare/v0.2.17...v0.2.18
[v0.2.17]: https://github.com/getjavelin/javelin-python/compare/v0.2.16...v0.2.17
[v0.2.16]: https://github.com/getjavelin/javelin-python/compare/v0.2.15...v0.2.16
[v0.2.15]: https://github.com/getjavelin/javelin-python/compare/v0.2.14...v0.2.15
[v0.2.14]: https://github.com/getjavelin/javelin-python/compare/v0.2.13...v0.2.14
[v0.2.13]: https://github.com/getjavelin/javelin-python/compare/v0.2.12...v0.2.13
[v0.2.12]: https://github.com/getjavelin/javelin-python/compare/v0.2.11...v0.2.12
[v0.2.11]: https://github.com/getjavelin/javelin-python/compare/v0.2.10...v0.2.11
[v0.2.10]: https://github.com/getjavelin/javelin-python/compare/v0.2.9...v0.2.10
[v0.2.9]: https://github.com/getjavelin/javelin-python/compare/v0.2.8...v0.2.9
[v0.2.8]: https://github.com/getjavelin/javelin-python/compare/v0.2.7...v0.2.8
[v0.2.7]: https://github.com/getjavelin/javelin-python/compare/v0.2.6...v0.2.7
[v0.2.6]: https://github.com/getjavelin/javelin-python/compare/v0.2.5...v0.2.6
[v0.2.5]: https://github.com/getjavelin/javelin-python/compare/v0.2.4...v0.2.5
[v0.2.4]: https://github.com/getjavelin/javelin-python/compare/v0.2.3...v0.2.4
[v0.2.3]: https://github.com/getjavelin/javelin-python/compare/v0.2.2...v0.2.3
[v0.2.2]: https://github.com/getjavelin/javelin-python/compare/v0.2.1...v0.2.2
[v0.2.1]: https://github.com/getjavelin/javelin-python/compare/v0.2.0...v0.2.1
[v0.2.0]: https://github.com/getjavelin/javelin-python/compare/v0.1.8...v0.2.0
[v0.1.8]: https://github.com/getjavelin/javelin-python/compare/v0.1.7...v0.1.8
[v0.1.7]: https://github.com/getjavelin/javelin-python/compare/v0.1.5...v0.1.7
