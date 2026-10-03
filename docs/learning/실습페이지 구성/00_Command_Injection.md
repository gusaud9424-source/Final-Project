# 00. Command Injection 실습 페이지 (DVWA 재현)

> 대상: 웹 보안 입문자
> 기준: DVWA(Damn Vulnerable Web Application)의 Command Injection 소스를 그대로 재현
> 작성: 2026-10-03 · 오현명

---

## 1. 한 줄 요약

"IP를 입력하면 ping 해주는" 기능에서, 입력이 `ping` 명령 뒤에 그대로 붙어 실행되기 때문에 셸 명령을 끼워 넣어 서버에서 임의 명령을 실행하는 취약점.

---

## 2. 개념 설명 (비유)

직원에게 "이 주소로 택배 보내줘"라고 쪽지를 주는데, 직원이 쪽지 내용을 **그대로 터미널에 복사해 실행**한다고 하자. 주소 칸에 "서울시… ; 그리고 금고 비밀번호도 알려줘"라고 적으면, 직원은 주소 확인 뒤 이어서 두 번째 지시까지 실행해버린다. 세미콜론(`;`) 하나로 명령이 둘이 된 것이다.

---

## 3. 용어 설명

| 용어 | 뜻 |
|---|---|
| Command Injection | 입력이 OS 명령의 일부로 실행되는 취약점 |
| 셸(shell) | 명령을 실행하는 프로그램(`/bin/sh`) |
| `;` `&&` `\|` | 명령 구분자. 한 줄에 여러 명령을 이어 실행 |
| `/etc/passwd` | 리눅스 계정 목록 파일(유출 시연 대상) |
| 블랙리스트 | 금지 문자 목록 방식. 목록에 없으면 통과 |

---

## 4. DVWA 소스 기준 난이도별 로직

DVWA는 `ping -c 4 <입력>` 을 셸로 실행한다. 단계마다 입력에서 지우는 문자가 달라진다.

| 단계 | DVWA 필터 | 우회 payload |
|---|---|---|
| Low | 없음 | `127.0.0.1; cat /etc/passwd` |
| Medium | `&&`, `;` 제거 | `127.0.0.1 \| cat /etc/passwd` |
| High | `\|\|` `&` `;` `\| `(파이프+공백) `-` `$` `(` `)` `` ` `` 제거 | `127.0.0.1\|cat /etc/passwd` (파이프 뒤 공백 없이) |
| Impossible | `.`으로 쪼개 4옥텟이 모두 숫자인지 검사 | 주입 불가 |

- **Medium 포인트**: `;`·`&&`만 막으므로 파이프(`\|`)로 우회.
- **High 포인트**: 목록에 `\| `(파이프+공백)은 있지만 공백 없는 `\|`는 빠져 있다 → `127.0.0.1\|cat ...`.
- **Impossible**: 숫자 4마디만 허용 → 셸 메타문자 자체가 못 들어감.

---

## 5. 실습 화면 & 동작

- DVWA의 "Ping a device" 화면: **Enter an IP address** 입력 + **Submit**.
- 결과가 `<pre>`에 표시된다. 성공하면 ping 통계 뒤에 `/etc/passwd` 내용(`root:x:0:0:...`)이 덤프된다.
- 성공 판정: 출력에 `root:` 가 포함되면(=passwd 유출) 성공.

### 관련 파일
| 파일 | 역할 |
|---|---|
| `backend/app/practice_builders/command_injection.py` | DVWA 필터 재현, ping 실행, 성공 판정 |
| `sandbox/runner.py` · `sandbox/Dockerfile` | 격리 샌드박스에서 실행(`iputils-ping` 포함) |
| `frontend/src/components/practice/CmdInjectionPractice.vue` | "Ping a device" 화면 |

---

## 6. 방어 (Impossible이 정답)

- 셸에 사용자 입력을 붙이지 말 것.
- 꼭 필요하면 **화이트리스트 검증**(여기선 숫자 4옥텟) 후 인자 배열로 전달.
- 블랙리스트(금지 문자)는 항상 우회로가 남는다(파이프, 공백 유무 등).

---

*DVWA 로직을 Flask/Vue 환경에 재현. © 2026 5팀_Security Learning Platform*
