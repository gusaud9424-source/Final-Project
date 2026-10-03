# 06. File Upload 실습 페이지 (DVWA 재현)

> 기준: DVWA upload 소스 재현 · 2026-10-03 오현명

## 1. 한 줄 요약
업로드 검사가 허술하고 저장 위치가 실행 가능할 때, 웹셸(명령 실행 파일)을 올려 서버에서 원격 코드 실행(RCE)하는 취약점.

## 2. 개념 (비유)
택배 보관함에 "상자만" 넣어야 하는데 경비(검사)가 허술하면 침입자가 상자로 위장해 들어와 건물을 돌아다닌다. (1)위험 파일이 통과하고 (2)실행 위치에 저장될 때 터짐 → 둘 다 막아야 함.

## 3. 용어
| 용어 | 뜻 |
|---|---|
| 웹셸 | 업로드되어 서버에서 명령을 실행하는 악성 파일 |
| RCE | 원격 코드 실행(가장 위험) |
| MIME(Content-Type) | 요청이 알려주는 파일 종류(image/jpeg 등) |
| 매직바이트 | 파일 앞의 형식 서명(GIF는 `GIF89a`) |
| 폴리글랏 | 이미지이자 코드로 동시에 유효한 파일 |

## 4. DVWA 소스 기준 난이도
실행 모델: 파일명에 `.sh`/`.php` 포함 시 서버가 실행(경로 오설정 모사). 성공 = 실행되어 flag 출력.

| 단계 | DVWA 검사 | 우회 |
|---|---|---|
| Low | 없음 | `shell.sh` + `cat /tmp/flag.txt` |
| Medium | **Content-Type(MIME)** image/jpeg·png 검사 | DevTools/Burp로 `mimetype`을 `image/jpeg`로 위조 |
| High | 확장자(jpg/png/gif) + 매직바이트(getimagesize) | 폴리글랏: `shell.sh.gif`, 내용 `GIF89a;`\n`cat /tmp/flag.txt` |
| Impossible | 재인코딩 + 실행 불가 격리 | 불가 |

- **Medium**: 파일명·내용이 아니라 **요청의 Content-Type만** 검사 → 위조로 우회.
- **High**: 이미지 매직바이트로 시작해야 → 앞에 `GIF89a` 붙인 폴리글랏.

## 5. 화면 & 동작
- DVWA "Choose an image to upload" 재현: 파일명+내용 입력, 전송될 Content-Type 표시, Upload.
- 판정: 업로드물이 샌드박스에서 실행돼 flag 출력 시 성공.

### 관련 파일
`backend/app/practice_builders/file_upload.py`, `sandbox/runner.py`, `frontend/.../FileUploadPractice.vue`

## 6. 방어
화이트리스트 확장자 + 실제 내용 검사 + 무작위 파일명 + **실행 권한 없는 별도 스토리지**(여러 겹).

*DVWA 로직 재현(스택상 PHP→sh, 격리 샌드박스 실행). © 2026 5팀_Security Learning Platform*
