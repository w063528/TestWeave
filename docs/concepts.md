# TestWeave Concepts

이 문서는 TestWeave 엔진에서 사용하는 핵심 개념과 데이터 모델을 정의합니다. TestWeave는 스펙 파일을 읽어 테스트 케이스를 생성하고, 이를 여러 테스트 주기(Test Cycle)에서 실행하여 결과를 기록하는 **로컬-퍼스트** 테스트 관리 엔진입니다. 명확한 용어 정의는 사용자가 사양-작성부터 실행·보고까지 일관된 작업 흐름을 유지하는 데 도움이 됩니다.

## 주요 엔티티

TestWeave에서 관리되는 요소는 다음 네 가지입니다.

| 엔티티 | 설명 |
|---|---|
| **Test Suite** | 하나의 스펙 파일(.feature, .md, .csv 등)에 포함된 테스트 케이스 집합 |
| **Test Case** | 사용자 행동과 기대 결과를 설명하는 테스트 시나리오 |
| **Test Cycle** | 특정 버전 또는 릴리즈에서 실행되는 테스트 실행 단위 |
| **Test Result** | 테스트 실행 결과 기록 |

## 데이터 관계

Test Suite → Test Case → Test Cycle → Test Result

TestSuite (1) —— contains —— (many) TestCase  
TestCase (many) —— belongs to —— (many) TestCycle  
TestCycle (1) —— has —— (many) TestResult —— belongs to —— (1) TestCase  

## ID 규칙

Suite ID  
스펙 파일 경로

TCID  
SuiteID + 시나리오 순번

Example

specs/login.feature:2

Cycle ID  
timestamp + version

Example

2026-03-05_v1.0.0

## Test Case 속성

- title
- description
- precondition
- steps
- expected result
- priority
- status

## Test Result 상태

Not Run  
Pass  
Fail  
Blocked

## 기본 워크플로우

1. Spec Scan  
스펙 파일(.feature .md .csv 등)을 읽어 Test Suite 생성

2. Test Cycle 생성  
테스트 실행 단위 생성

3. Manual Execution  
테스터가 실행 결과 입력

4. Report Export  
HTML / CSV 리포트 생성

## Local-First 원칙

TestWeave는 SaaS가 아닌 **로컬-퍼스트 테스트 관리 엔진**입니다.

- 모든 테스트 데이터는 로컬에 저장
- 외부 서버 의존 없음
- Git으로 공유 가능

## Future Expansion

- Test Case Versioning
- Template
- Tag system
- Collaboration
- Issue Tracker Integration
