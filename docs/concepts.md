# TestWeave Concepts

이 문서는 TestWeave 엔진에서 사용하는 핵심 개념과 데이터 모델을 정의합니다. TestWeave는 스펙 파일을 읽어 테스트 케이스를 생성하고, 이를 여러 테스트 주기(Test Cycle)에서 실행하여 결과를 기록하는 **로컬‑퍼스트** 테스트 관리 엔진입니다. 명확한 용어 정의는 사용자가 사양‑작성부터 실행·보고까지 일관된 작업 흐름을 유지하는 데 도움이 됩니다.

## 주요 엔티티

TestWeave에서 관리되는 요소는 다음 네 가지입니다.

| 엔티티 | 설명 |
|---|---|
| **Test Suite** | 하나의 스펙 파일(예: Gherkin `.feature`, Markdown `.md`, CSV/Excel 등)에 포함된 테스트 케이스들의 집합입니다. 스캔 대상 파일 하나가 곧 하나의 Test Suite가 되며, 파일 경로가 Suite ID 역할을 합니다. |
| **Test Case** | 사용자 행동과 기대 결과를 설명하는 단일 테스트 시나리오입니다. Test Suite 안에 여러 개의 Test Case가 존재하며, 각 Test Case는 순서에 기반한 **TCID**(예: `login.feature:1`)로 고유하게 식별됩니다. |
| **Test Cycle** (또는 **Test Run**) | 특정 버전·릴리즈·환경에 대해 여러 Test Case를 묶어 실행하는 주기입니다. 테스트 기간과 대상 Test Case 목록을 정의하며, 각 케이스 실행 결과를 추적합니다. 하나의 Test Case는 여러 Test Cycle에서 재사용될 수 있습니다. |
| **Test Result** | Test Cycle에서 특정 Test Case를 실행한 결과입니다. 상태(Not Run/Pass/Fail/Blocked), 실행자, 실행 날짜, 메모, 첨부 파일 등을 포함합니다. Test Result는 Test Case와 Test Cycle의 교차점에 존재하는 엔티티입니다. |

## 데이터 관계

Test Suite → Test Case → Test Cycle → Test Result로 이어지는 계층 구조를 통해 테스트 작업이 조직됩니다.

1. **Test Suite**는 여러 **Test Case**를 포함합니다. 스펙 파일의 각 시나리오가 하나의 Test Case가 됩니다.
2. **Test Cycle**은 실행할 Test Case 목록과 테스트 기간을 정의합니다. 하나의 Cycle에는 여러 Case가 포함될 수 있으며, 하나의 Case는 여러 Cycle에 배정될 수 있습니다.
3. **Test Result**는 Test Cycle과 Test Case 사이의 다대다 관계를 해소하는 조인 엔티티입니다. 각 결과는 고유한 `cycle_id`, `tcid` 조합으로 식별됩니다.

다음 그림은 관계 구조를 요약한 것입니다.

```
TestSuite (1) —— contains —— (many) TestCase
TestCase (many) —— belongs to —— (many) TestCycle
TestCycle (1) —— has —— (many) TestResult —— belongs to —— (1) TestCase
```

## ID 규칙과 명명

* **Suite ID**: 스펙 파일의 경로를 사용합니다. 예: `specs/login.feature`.
* **TCID**: `Suite ID`와 스펙 파일 내 시나리오 순번을 조합한 값입니다. 예: `specs/login.feature:2`는 `login.feature` 파일 두 번째 시나리오를 의미합니다.
* **Cycle ID**: 생성 시점·버전·환경 등으로 구성된 고유 문자열입니다. 예: `2026-03-05_v1.0.0`.

ID는 결과 파일과 보고서에서 일관된 참조를 제공하므로 변경하지 않는 것이 좋습니다. 스펙 파일을 수정하여 시나리오 순서가 바뀌면 TCID가 달라질 수 있으므로, 장기적으로는 파일 내에 `tcid` 태그를 삽입하여 안정성을 높이는 방안을 고려할 수 있습니다.

## 상태와 속성

### Test Case 속성

* **제목**과 **설명**: 테스트 목적과 시나리오 요약.
* **사전 조건(Precondition)**: 테스트 시작 전에 만족돼야 할 조건.
* **단계(Steps)**: 사용자 행동(When/Then) 또는 Given/When/Then 구조로 표현된 실행 단계.
* **기대 결과(Expect)**: 성공 기준.
* **우선순위(Priority)**: `Low`, `Medium`, `High` 등.
* **상태(Status)**: `Active`(사용 중), `Deprecated`(더 이상 사용하지 않음) 등.

### Test Result 상태

* **Not Run** – 아직 실행되지 않은 테스트 케이스.
* **Pass** – 테스트가 기대 결과를 만족함.
* **Fail** – 실행 결과가 기대 결과와 일치하지 않음.
* **Blocked** – 환경 문제, 사전 조건 미충족 등으로 실행할 수 없음.

각 Test Result에는 실행자(테스터), 실행 일시, 메모, 첨부 파일(스크린샷 등)을 기록할 수 있습니다.

## 작업 흐름

1. **스펙 스캔**: 사용자가 지정한 디렉터리를 스캔하여 `.feature`, `.md`, `.csv`, `.xlsx` 등의 파일을 읽고, 각 파일을 Test Suite로 변환합니다. 스캔 과정은 오프라인에서 수행되며, 변환된 Test Case는 로컬 캐시에 저장됩니다【754578316293951†screenshot】.
2. **테스트 주기 생성**: QA 담당자는 새로운 Test Cycle을 만들고 실행 기간(예: 릴리즈 버전, 기간)을 지정한 뒤 실행할 Test Case를 선택합니다. 필요에 따라 각 케이스에 실행 담당자(테스터)를 할당할 수 있습니다【341863036223580†screenshot】.
3. **수동 테스트 실행**: 사용자는 VS Code 확장, CLI 또는 Web UI를 통해 각 Test Case를 하나씩 실행하며 결과(상태, 노트, 첨부)를 입력합니다. TestWeave는 **로컬** 파일에 실행 기록을 저장하므로 외부 서버에 의존하지 않습니다【384828939135081†screenshot】.
4. **보고 및 리뷰**: 테스트가 완료되면 결과를 HTML/CSV 등으로 내보내어 팀과 공유할 수 있습니다. 대시보드에서는 전체/실행됨/Pass/Fail/Blocked 수치를 요약하고, 개별 결과를 열람할 수 있습니다【732006997533607†screenshot】.

## 로컬‑퍼스트 & 보안 원칙

TestWeave는 SaaS나 클라우드 서비스 없이 **로컬‑퍼스트**로 설계되었습니다【384828939135081†screenshot】. 스캔된 스펙, 생성된 Test Suite/Case, 실행 결과와 보고서는 사용자의 PC나 사내 서버에 저장됩니다. 외부 API 호출이나 서버 전송 없이도 모든 기능을 수행할 수 있어 기밀성과 보안성이 높습니다. 필요한 경우 저장 위치(.testweave 디렉터리 등)를 Git에 커밋하여 팀과 공유할 수 있습니다.

## 향후 확장

개념 정의는 프로젝트 진행에 따라 확장될 수 있습니다. 향후 계획된 기능으로는 테스트 케이스 버전 관리, 클론·템플릿, 태그 시스템, 협업 댓글·멘션, 외부 이슈 트래커 연동 등이 있으며【732006997533607†screenshot】, 해당 기능에 대한 데이터 모델은 향후 문서에서 다룰 예정입니다.