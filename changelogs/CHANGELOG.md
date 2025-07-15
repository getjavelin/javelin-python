<a name="unreleased"></a>
## [Unreleased]


<a name="v0.2.38"></a>
## [v0.2.38] - 2025-07-14
### Bug Fixes
- lint issues ([#204](https://github.com/getjavelin/javelin-python/issues/204))
- Update README.md

### DevOps
- Update WEEKLY-CHANGELOG for v0.0.3-weekly
- Update WEEKLY-CHANGELOG for v0.0.2-weekly
- Update WEEKLY-CHANGELOG for v0.0.1-weekly
- Adding the new pipeline for weekly changelog cron
- Fixing the pipeline trigger issue

### Pull Requests
- Merge pull request [#201](https://github.com/getjavelin/javelin-python/issues/201) from getjavelin/cicd-patch
- Merge pull request [#200](https://github.com/getjavelin/javelin-python/issues/200) from getjavelin/ankumar-patch-1
- Merge pull request [#199](https://github.com/getjavelin/javelin-python/issues/199) from getjavelin/cicd-patch


<a name="v0.2.37"></a>
## [v0.2.37] - 2025-05-30
### Bug Fixes
- update route models ([#198](https://github.com/getjavelin/javelin-python/issues/198))

### DevOps
- Patching the cicd and release pipeline

### Pull Requests
- Merge pull request [#197](https://github.com/getjavelin/javelin-python/issues/197) from getjavelin/cicd-patch


<a name="v0.2.36"></a>
## [v0.2.36] - 2025-05-28
### DevOps
- disabling the edited option in the PR checks
- Update CHANGELOG for v0.2.35

### Features
- update universal endpoint scripts ([#195](https://github.com/getjavelin/javelin-python/issues/195))

### Pull Requests
- Merge pull request [#190](https://github.com/getjavelin/javelin-python/issues/190) from getjavelin/cicd-changelog
- Merge pull request [#194](https://github.com/getjavelin/javelin-python/issues/194) from getjavelin/cicd-patch


<a name="v0.2.35"></a>
## [v0.2.35] - 2025-05-08
### Bug Fixes
- upgrade Python version and OpenTelemetry dependencies ([#191](https://github.com/getjavelin/javelin-python/issues/191))
- updated west region to east-1 for bedrock clint ([#192](https://github.com/getjavelin/javelin-python/issues/192))

### Features
- img gen support for unified endpoints ([#193](https://github.com/getjavelin/javelin-python/issues/193))


<a name="v0.2.34"></a>
## [v0.2.34] - 2025-05-02
### Bug Fixes
- update SDK calls to prevent failures in E2E pipeline ([#179](https://github.com/getjavelin/javelin-python/issues/179))

### DevOps
- Removing the changelog configs from code repo
- Update CHANGELOG for v0.2.33

### Features
- add standalone guardrail methods and enforce strict model validation ([#189](https://github.com/getjavelin/javelin-python/issues/189))
- add tool/function calling test scripts for all LLM providers except openai via Javelin ([#182](https://github.com/getjavelin/javelin-python/issues/182))
- added multi-agent coordination example for OpenAI and Gemini via Javelin (research → summary → report) ([#186](https://github.com/getjavelin/javelin-python/issues/186))
- Added agent example for openai-agents ([#185](https://github.com/getjavelin/javelin-python/issues/185))
- Added examples for anthropic api call-chat and function calling ([#183](https://github.com/getjavelin/javelin-python/issues/183))

### Pull Requests
- Merge pull request [#188](https://github.com/getjavelin/javelin-python/issues/188) from getjavelin/cicd-patch
- Merge pull request [#176](https://github.com/getjavelin/javelin-python/issues/176) from getjavelin/cicd-changelog


<a name="v0.2.33"></a>
## [v0.2.33] - 2025-04-07
### Bug Fixes
- remove duplicate event register. ([#178](https://github.com/getjavelin/javelin-python/issues/178))


<a name="v0.2.32"></a>
## [v0.2.32] - 2025-04-04
### Bug Fixes
- Update README formatting for provider and agent examples
- pip install instructions and update author/homepage in pyproject.toml
- update base url to use environment variables

### DevOps
- Update CHANGELOG for v0.2.31

### Pull Requests
- Merge pull request [#174](https://github.com/getjavelin/javelin-python/issues/174) from getjavelin/update_baseurl
- Merge pull request [#175](https://github.com/getjavelin/javelin-python/issues/175) from getjavelin/fix-install-readme-and-metadata
- Merge pull request [#166](https://github.com/getjavelin/javelin-python/issues/166) from getjavelin/cicd-changelog


<a name="v0.2.31"></a>
## [v0.2.31] - 2025-04-03
### Bug Fixes
- correct AWS Bedrock integration doc link in README
- Update README.md
- broken filepaths in readme
- use api_key and provider_name in secret create request

### Pull Requests
- Merge pull request [#173](https://github.com/getjavelin/javelin-python/issues/173) from getjavelin/fix-readme-bedrock-link
- Merge pull request [#172](https://github.com/getjavelin/javelin-python/issues/172) from getjavelin/patch-main-commit-msg
- Merge pull request [#168](https://github.com/getjavelin/javelin-python/issues/168) from getjavelin/rsharath-patch-1
- Merge pull request [#169](https://github.com/getjavelin/javelin-python/issues/169) from getjavelin/fix_readme
- Merge pull request [#167](https://github.com/getjavelin/javelin-python/issues/167) from getjavelin/fix/secret-service-api-key-provider


<a name="v0.2.30"></a>
## [v0.2.30] - 2025-03-20
### Bug Fixes
- merge issues ([#165](https://github.com/getjavelin/javelin-python/issues/165))
- move example scripts to right folders ([#164](https://github.com/getjavelin/javelin-python/issues/164))
- Resolved merge conflicts in examples/bedrock_client.py
- LangChain OpenAI base URL & Bedrock API message format ([#161](https://github.com/getjavelin/javelin-python/issues/161))
- streaming+univ endpoints via sdk ([#155](https://github.com/getjavelin/javelin-python/issues/155))
- cleanup accidental file checkin ([#159](https://github.com/getjavelin/javelin-python/issues/159))

### DevOps
- Adding reusable pipeline
- Adding support for reusable workflow in PR pipelines
- Update CHANGELOG for v0.2.29

### Features
- Updated Bedrock and OpenAI clients with tracing and refactored request handling
- Updated the code for general routs testing ([#156](https://github.com/getjavelin/javelin-python/issues/156))
- Code for function calling using 01/o3 models ([#152](https://github.com/getjavelin/javelin-python/issues/152))

### Pull Requests
- Merge pull request [#163](https://github.com/getjavelin/javelin-python/issues/163) from getjavelin/feature/openai-register
- Merge pull request [#162](https://github.com/getjavelin/javelin-python/issues/162) from getjavelin/cicd-patch
- Merge pull request [#158](https://github.com/getjavelin/javelin-python/issues/158) from getjavelin/cicd-patch
- Merge pull request [#151](https://github.com/getjavelin/javelin-python/issues/151) from getjavelin/cicd-changelog


<a name="v0.2.29"></a>
## [v0.2.29] - 2025-02-26
### Bug Fixes
- resolve merge conflicts
- update readme
- add readme
- openai compatible univ endpoints
- isort and black command to format the files
- support embedding in openai compatible sdk
- add support for univ endpoints in javelin sdk
- apply formatting and linting fixes
- apply formatting and linting fixes
- apply formatting and linting fixes
- revert changes in pre commit config
- linting issues
- linting issues
- resolve conflicts
- clean make file
- format files before building
- linting issues
- fixed javelin universal rout and updated agentic code using javelin unified rout
- javelin configuration setup changed
- fixed rout name
- handle empty stream_response_path list to avoid index error
- load dot env
- integrate modelspecs 2.0
- Fixed agents examples in seperate /agents
- Removed rout from javelin config
- No open ai credentials passed

### DevOps
- Update CHANGELOG for v0.2.28

### Features
- Updated providers features branch
- Added langchain respected providers , having .py file with seperate functionalities
- added universal endpoint files

### Pull Requests
- Merge pull request [#149](https://github.com/getjavelin/javelin-python/issues/149) from getjavelin/univ_endpoints
- Merge pull request [#148](https://github.com/getjavelin/javelin-python/issues/148) from getjavelin/ISSUE-31
- Merge pull request [#141](https://github.com/getjavelin/javelin-python/issues/141) from getjavelin/fix-rout-branch
- Merge pull request [#145](https://github.com/getjavelin/javelin-python/issues/145) from getjavelin/univ_endpoints
- Merge pull request [#144](https://github.com/getjavelin/javelin-python/issues/144) from getjavelin/fix_linting_issues
- Merge pull request [#142](https://github.com/getjavelin/javelin-python/issues/142) from getjavelin/javelin-rout-f
- Merge pull request [#140](https://github.com/getjavelin/javelin-python/issues/140) from getjavelin/fix-rout-branch
- Merge pull request [#139](https://github.com/getjavelin/javelin-python/issues/139) from getjavelin/null-branch
- Merge pull request [#138](https://github.com/getjavelin/javelin-python/issues/138) from getjavelin/modelspecs2.0
- Merge pull request [#137](https://github.com/getjavelin/javelin-python/issues/137) from getjavelin/feature-update-branch
- Merge pull request [#136](https://github.com/getjavelin/javelin-python/issues/136) from getjavelin/modelspecs2.0
- Merge pull request [#130](https://github.com/getjavelin/javelin-python/issues/130) from getjavelin/cicd-changelog
- Merge pull request [#133](https://github.com/getjavelin/javelin-python/issues/133) from getjavelin/new-feature


<a name="v0.2.28"></a>
## [v0.2.28] - 2025-02-11
### Features
- Refactor JavelinClient initialization, improve tracing with OpenTelemetry status handling, and simplify OpenAI base URL logic

### Pull Requests
- Merge pull request [#135](https://github.com/getjavelin/javelin-python/issues/135) from getjavelin/feature/openai-register


<a name="v0.2.27"></a>
## [v0.2.27] - 2025-02-11
### Features
- Integrate OpenTelemetry tracing with OpenAI, Gemini, and Azure OpenAI support

### Pull Requests
- Merge pull request [#131](https://github.com/getjavelin/javelin-python/issues/131) from getjavelin/feature/openai-register


<a name="v0.2.26"></a>
## [v0.2.26] - 2025-02-06
### Bug Fixes
- Removing the code and moving to other repo

### DevOps
- Update CHANGELOG for v0.2.25

### Features
- Enhance OpenAI client registration with provider handling and model-specific headers
- Enhance OpenAI client registration with provider handling and model-specific headers
- Add /completions, /chat/completions, /embeddings endpoints
- Add register_openai method to JavelinClient
- Implement agent for test case generation, execution, and evaluation

### Pull Requests
- Merge pull request [#129](https://github.com/getjavelin/javelin-python/issues/129) from getjavelin/feature/openai-register
- Merge pull request [#127](https://github.com/getjavelin/javelin-python/issues/127) from getjavelin/feature/openai-register
- Merge pull request [#128](https://github.com/getjavelin/javelin-python/issues/128) from getjavelin/lg-agent-eval-branch
- Merge pull request [#124](https://github.com/getjavelin/javelin-python/issues/124) from getjavelin/lg-agent-eval-branch
- Merge pull request [#125](https://github.com/getjavelin/javelin-python/issues/125) from getjavelin/cicd-changelog


<a name="v0.2.25"></a>
## [v0.2.25] - 2025-02-04
### Features
- Set x-javelin-provider header to base URL

### Pull Requests
- Merge pull request [#126](https://github.com/getjavelin/javelin-python/issues/126) from getjavelin/spg


<a name="v0.2.24"></a>
## [v0.2.24] - 2025-02-04
### Bug Fixes
- chcking for null in javelin-client'

### DevOps
- Update CHANGELOG for v0.2.23

### Features
- added missing regexp
- simplified logic for handling ARN and model identifier

### Pull Requests
- Merge pull request [#123](https://github.com/getjavelin/javelin-python/issues/123) from getjavelin/spg
- Merge pull request [#121](https://github.com/getjavelin/javelin-python/issues/121) from getjavelin/cicd-changelog


<a name="v0.2.23"></a>
## [v0.2.23] - 2025-02-03
### Bug Fixes
- for missing arn proc

### Pull Requests
- Merge pull request [#122](https://github.com/getjavelin/javelin-python/issues/122) from getjavelin/spg


<a name="v0.2.22"></a>
## [v0.2.22] - 2025-02-04
### DevOps
- Update CHANGELOG for v0.2.21

### Pull Requests
- Merge pull request [#120](https://github.com/getjavelin/javelin-python/issues/120) from getjavelin/cicd-changelog


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

[Unreleased]: https://github.com/getjavelin/javelin-python/compare/v0.2.38...HEAD
[v0.2.38]: https://github.com/getjavelin/javelin-python/compare/v0.2.37...v0.2.38
[v0.2.37]: https://github.com/getjavelin/javelin-python/compare/v0.2.36...v0.2.37
[v0.2.36]: https://github.com/getjavelin/javelin-python/compare/v0.2.35...v0.2.36
[v0.2.35]: https://github.com/getjavelin/javelin-python/compare/v0.2.34...v0.2.35
[v0.2.34]: https://github.com/getjavelin/javelin-python/compare/v0.2.33...v0.2.34
[v0.2.33]: https://github.com/getjavelin/javelin-python/compare/v0.2.32...v0.2.33
[v0.2.32]: https://github.com/getjavelin/javelin-python/compare/v0.2.31...v0.2.32
[v0.2.31]: https://github.com/getjavelin/javelin-python/compare/v0.2.30...v0.2.31
[v0.2.30]: https://github.com/getjavelin/javelin-python/compare/v0.2.29...v0.2.30
[v0.2.29]: https://github.com/getjavelin/javelin-python/compare/v0.2.28...v0.2.29
[v0.2.28]: https://github.com/getjavelin/javelin-python/compare/v0.2.27...v0.2.28
[v0.2.27]: https://github.com/getjavelin/javelin-python/compare/v0.2.26...v0.2.27
[v0.2.26]: https://github.com/getjavelin/javelin-python/compare/v0.2.25...v0.2.26
[v0.2.25]: https://github.com/getjavelin/javelin-python/compare/v0.2.24...v0.2.25
[v0.2.24]: https://github.com/getjavelin/javelin-python/compare/v0.2.23...v0.2.24
[v0.2.23]: https://github.com/getjavelin/javelin-python/compare/v0.2.22...v0.2.23
[v0.2.22]: https://github.com/getjavelin/javelin-python/compare/v0.2.21...v0.2.22
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
