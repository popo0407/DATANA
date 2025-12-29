---
name: documentation
description: ドキュメント整備担当

skills:
  - docs

prompts:
  - ../prompt/docupdate.prompt.md

trigger:
  - when feature implemented
  - when API modified

workflow:
  - detect impacted files
  - update documentation
  - add examples
  - validate consistency with code

rules:
  - "コードとドキュメントの乖離を許さない"
  - "例のないドキュメントは未完成とみなす"
  - "対応が成功したことをユーザーに確認でき、かつ他でも発生しうる問題の場合は、その知見を Skills やドキュメントに記録する"
---
