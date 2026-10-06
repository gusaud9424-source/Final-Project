# 02. 로고 SVG 개념 설명 (좌표계 · path · mask · currentColor · 컴포넌트 재사용)

> 대상: 웹 개발을 처음 배우는 입문자
> 목표: SecuQuest 로고가 이미지 파일이 아니라 "코드로 그린 그림(SVG)"이라는 점, 방패 모양과 S 글자 구멍이 어떻게 만들어지는지, 색과 크기가 어떻게 정해지는지를 코드 한 줄씩 이해한다.
> 작성: 2026-10-06 · 오현명
> 함께 볼 문서: `01_로고변경.md` (작업 기록)

---

## 1. 요약

- 로고는 PNG 같은 이미지 파일이 아니라 **SVG 코드**다. 확대해도 깨지지 않고, 색을 CSS 로 바꿀 수 있다.
- 방패 모양은 **점 5개를 잇는 path(선 그리기 명령)** 한 줄로 그린다. CSS3 로고 비율(가로:세로 ≈ 0.88)이라 기존보다 가로가 넓다.
- S 글자는 칠하는 게 아니라 **mask(마스크)로 방패에 구멍을 뚫어** 만든다. 구멍으로 뒤 배경이 보인다.
- S 는 헤더 "SecuQuest" 와 같은 **Pretendard 700** 글꼴, 방패 높이의 약 45% 크기다.
- 색은 `currentColor` + 디자인 토큰 `var(--sq-color-accent)` 로 정해 hex 를 직접 쓰지 않는다.
- 로고는 `BrandMark.vue` 컴포넌트 하나로 만들어 **헤더와 인증 화면에서 재사용**한다. 한 곳만 고치면 둘 다 바뀐다.

---

## 2. 개념 설명 (비유)

### 2-1. 전체 그림: 색종이 + 칼틀

```
 ① 도화지 크기 정하기        ② 파란 색종이(방패) 오리기      ③ S 모양 칼틀로 구멍 뚫기       ④ 결과
   viewBox="30 0 452 512"     path: 점 5개를 이어 방패        mask: 흰 바탕 + 검은 S           방패에 S 구멍,
   (모눈종이 좌표)             fill = currentColor(파랑)       → 검은 부분만 투명               뒤 배경이 비침
```

- **도화지(viewBox)**: 모눈종이에 좌표를 정한다. 실제 화면 크기(42×48px)와 상관없이 이 좌표로 그림을 그린다.
- **색종이(path)**: 꼭짓점 5개를 이어 방패를 오린다.
- **칼틀(mask)**: 흰색 부분은 남기고 검은색 부분은 투명하게 만드는 틀. 검은 S 를 올려 S 모양 구멍을 뚫는다.
- 구멍을 뚫었기 때문에 배경이 흰색이든 다른 색이든 **S 가 항상 자연스럽게** 보인다.

### 2-2. 이미지 파일(PNG) 대신 SVG 를 쓰는 이유

| 비교 | PNG(점으로 된 그림) | SVG(코드로 된 그림) |
|---|---|---|
| 확대 | 계단처럼 깨짐 | 항상 선명 |
| 색 바꾸기 | 그림 파일을 새로 만들어야 함 | CSS 한 줄 |
| 글꼴 맞추기 | 그림에 박혀 있음 | 화면 글꼴(Pretendard)을 그대로 사용 |
| 파일 크기 | 해상도에 비례 | 코드 몇 줄 |

---

## 3. 용어 설명

| 용어 | 쉬운 뜻 |
|---|---|
| SVG | Scalable Vector Graphics. 점·선·면을 좌표로 적어 그리는 그림 형식 |
| 벡터 / 비트맵 | 좌표·수식으로 그린 그림(확대해도 선명) / 작은 점(픽셀)을 모은 그림(확대하면 깨짐) |
| viewBox | SVG 안의 좌표계. `x y 너비 높이` 순서. 여기서는 `30 0 452 512` |
| width · height | 화면에 실제로 보이는 크기(px). 여기서는 42 × 48 |
| path | 선을 그리는 SVG 요소. `d` 속성에 그리기 명령을 적는다 |
| `M` · `L` · `Z` | path 명령. `M` = 펜을 여기로 옮김, `L` = 여기까지 직선, `Z` = 처음 점으로 닫기 |
| fill | 도형 안을 칠하는 색 |
| mask | 흰색=보임, 검은색=투명으로 만드는 틀 |
| `maskUnits="userSpaceOnUse"` | 마스크 크기를 viewBox 좌표 그대로 쓰겠다는 설정 |
| `<defs>` | 바로 그리지 않고 "정의만" 해 두는 영역 (mask 를 여기에 둔다) |
| `text-anchor="middle"` | 글자를 x 좌표의 가운데에 맞춤 |
| baseline | 글자가 올라앉는 기준선. `y="372"` 는 S 의 기준선 위치 |
| currentColor | 부모 요소의 CSS `color` 값을 그대로 쓰는 키워드 |
| 디자인 토큰 | 색 등 디자인 값을 이름 붙인 CSS 변수 (`--sq-color-accent`) |
| 컴포넌트 | 화면 조각을 재사용할 수 있게 묶은 단위 (`BrandMark.vue`) |
| `useId` | Vue 3.5 기능. 컴포넌트마다 겹치지 않는 고유 id 를 만든다 |
| `aria-label` · `role="img"` | 화면 낭독기(시각장애인용)에 "SecuQuest 로고"라고 알려주는 속성 |
| Pretendard | 프로젝트 기본 한글 글꼴 |

---

## 4. 구조와 코드

### 4-1. 전체 코드

```vue
<!-- frontend/src/components/brand/BrandMark.vue -->
<svg class="sq-brand-mark" width="42" height="48" viewBox="30 0 452 512"
     role="img" aria-label="SecuQuest 로고">                            <!-- ① 크기와 좌표계 -->
  <defs>
    <mask :id="maskId" maskUnits="userSpaceOnUse" x="30" y="0" width="452" height="512">
      <rect x="30" y="0" width="452" height="512" fill="white" />   <!-- ② 흰 바탕 = 전부 보임 -->
      <text class="sq-brand-mark__letter" x="256" y="372"
            text-anchor="middle" fill="black">S</text>              <!-- ③ 검은 S = 구멍 -->
    </mask>
  </defs>
  <path fill="currentColor" :mask="`url(#${maskId})`"
        d="M71 460 L30 0 L482 0 L441 460 L256 512 Z" />             <!-- ④ 방패 + 마스크 적용 -->
</svg>
```

### 4-2. 줄별 의미

| # | 코드 | 의미 | 없으면 생기는 일 |
|---|---|---|---|
| ① | `width="42" height="48"` | 화면에 보이는 크기 | 브라우저 기본 크기(300×150)로 크게 보임 |
| ① | `viewBox="30 0 452 512"` | 좌표 x=30~482, y=0~512 를 42×48 에 맞춰 축소 | 좌표 그대로 그려져 로고가 잘리거나 엄청 커짐 |
| ② | 흰 `rect` | 마스크 전체를 "보임"으로 | 방패 전체가 투명해져 안 보임 |
| ③ | 검은 `text` S | S 부분만 "투명" | 구멍 없이 파란 방패만 보임 |
| ③ | `x="256"` + `text-anchor="middle"` | S 를 방패 가로 가운데에 | S 가 한쪽으로 치우침 |
| ③ | `y="372"` | S 기준선 위치 (방패 위쪽 넓은 부분의 가운데쯤) | S 가 위아래로 어긋남 |
| ④ | `fill="currentColor"` | 부모 `color` 값으로 칠함 | 색을 바꾸려면 SVG 코드를 직접 고쳐야 함 |
| ④ | `:mask="url(#…)"` | 위 마스크를 방패에 적용 | S 구멍이 생기지 않음 |

### 4-3. 방패 모양 path 읽기

```
d = "M71 460  L30 0  L482 0  L441 460  L256 512  Z"

      (30,0) ●───────────────────● (482,0)        M71 460 : 왼쪽 아래(71,460)에서 시작
              \                 /                 L30 0   : 왼쪽 위로
               \               /                  L482 0  : 오른쪽 위로 (윗변)
       (71,460) ●             ● (441,460)         L441 460: 오른쪽 아래로
                  \         /                     L256 512: 아래 꼭짓점(가운데)
                    ● (256,512)                   Z       : 시작점으로 닫기
```

- 위가 넓고 아래로 갈수록 살짝 좁아지다가 가운데 뾰족한 점으로 모이는 **CSS3 로고 방패** 모양이다.
- 가로 452 : 세로 512 ≈ **0.88** 이라 예전 로고(40×48)보다 가로가 넓다.

### 4-4. 글꼴과 크기, 색

```css
.sq-brand-mark { color: var(--sq-color-accent); }   /* currentColor 가 이 파란색이 됨 */

.sq-brand-mark__letter {
  font-family: var(--sq-font-family);  /* Pretendard — 헤더 "SecuQuest" 와 같은 글꼴 */
  font-weight: 700;                    /* 헤더 타이틀과 같은 굵기 */
  font-size: 360px;                    /* viewBox 좌표 기준 → 방패 높이(512)의 약 45% */
}
```

```
 var(--sq-color-accent) ──▶ .sq-brand-mark 의 color ──▶ path 의 currentColor ──▶ 방패 색
 (토큰 파일에만 색 값)        (CSS)                       (SVG)
```

- `font-size: 360px` 은 실제 화면 360px 이 아니라 **viewBox 좌표 단위**다. 전체가 42×48 로 축소되므로 화면에서는 작게 보인다.
- S 를 path 로 직접 그리지 않고 글꼴 글자로 쓴 이유: 옆의 "SecuQuest" 글자와 **같은 글꼴**이어야 로고와 이름이 한 덩어리로 보인다.

### 4-5. 고유 id 가 필요한 이유 (`useId`)

```javascript
const maskId = `sq-brand-mask-${useId()}`;   // 예: sq-brand-mask-v-0-1
```

- mask 는 `id` 로 연결된다(`url(#id)`). 한 페이지에 로고가 두 개 있는데 id 가 같으면, 두 번째 로고가 첫 번째 마스크를 쓰거나 꼬일 수 있다.
- 로고 인스턴스마다 다른 id 를 만들어 이 문제를 막는다.

### 관련 파일

| 파일 | 역할 |
|---|---|
| `frontend/src/components/brand/BrandMark.vue` | 로고 SVG 컴포넌트 |
| `frontend/src/components/layout/AppHeader.vue` | 헤더에서 `<BrandMark />` 사용 |
| `frontend/src/components/auth/AuthCard.vue` | 인증 카드에서 `<BrandMark />` 사용 (높이 40px 로 조정) |
| `frontend/src/assets/design-tokens.css` | `--sq-color-accent`, `--sq-font-family` |

---

## 5. 동작 흐름 (화면에 그려지기까지)

```
1. 헤더가 <BrandMark /> 를 그림 → useId 로 마스크 id 생성
2. 브라우저가 viewBox(452×512 좌표)를 42×48px 로 축소할 준비
3. <defs> 의 마스크 정의: 흰 사각형 + 검은 S (Pretendard 700, 360 단위)
4. path 로 방패를 그리고 currentColor(= --sq-color-accent 파랑)로 칠함
5. 마스크 적용 → S 부분만 투명 → 헤더 배경이 S 모양으로 비침
```

---

## 6. 주의점과 한계

- **Pretendard 글꼴이 아직 안 불러와졌으면** 잠깐 다른 글꼴로 S 가 보일 수 있다(글꼴은 CDN 에서 불러옴).
- S 위치(`y="372"`)와 크기(`360`)는 눈으로 맞춘 값이다. 글꼴을 바꾸면 다시 맞춰야 한다.
- 이 방패 모양은 W3C CSS3 공개 마크에서 영감을 받아 S 로 재해석한 SecuQuest 자체 마크다(README Attribution 참고).

---

## 7. 핵심 정리

- 로고는 **SVG 코드**: viewBox 좌표계 → path 로 방패 → mask 로 S 구멍.
- S 는 헤더와 같은 **Pretendard 700**, 방패 높이의 약 45%.
- 색은 **currentColor + 디자인 토큰**, 컴포넌트 하나를 헤더·인증 화면이 **재사용**한다.
- 발표용 한 문장: **"로고는 코드로 그린 SVG라서 확대해도 선명하고, 방패에 마스크로 S 구멍을 뚫어 배경과 자연스럽게 어울리며, 색은 디자인 토큰 하나로 관리한다."**

---

## 8. 검증 (이 문서의 근거)

- 코드: `frontend/src/components/brand/BrandMark.vue`
- 확인 기록: `01_로고변경.md` 8절 (대시보드 헤더 4배 확대로 로고 S 와 타이틀 S 글꼴 일치 확인, 사용자 확인 완료)

---

*© 2026 5팀_Security Learning Platform (부트캠프 캡스톤 학습용)*
