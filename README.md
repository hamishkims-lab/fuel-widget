# 필리핀 유가 위젯 (노션 임베드용)

fuelprice.ph의 가솔린(RON 91)·디젤 평균가를 매일 확인해 작은 카드 페이지로 만들고, GitHub Pages로 공개해 노션에 `/embed` 하는 구조입니다.

```
GitHub Actions (매일 10시 PH) → scrape.py가 fuelprice.ph 읽기 → docs/index.html 갱신
→ GitHub Pages가 docs/를 웹페이지로 게시 → 노션 /embed
```

## 설정 순서 (약 10분)

1. **저장소 만들기**: github.com → New repository → 이름 예: `fuel-widget` → **Public** 선택 → Create.
   (무료 계정은 Public 저장소만 GitHub Pages 사용 가능)
2. **파일 올리기**: 저장소 화면에서 `uploading an existing file` 클릭 → 압축을 푼 폴더 안의 내용 전체
   (`scrape.py`, `README.md`, `docs/`, `.github/`)를 끌어다 놓고 Commit.
   - `.github` 폴더는 숨김 폴더라 탐색기에서 안 보일 수 있습니다. 안 올라갔다면
     Add file → Create new file → 이름에 `.github/workflows/update.yml` 입력 → 내용 붙여넣기.
3. **쓰기 권한 허용**: Settings → Actions → General → Workflow permissions →
   **Read and write permissions** 선택 → Save.
4. **Pages 켜기**: Settings → Pages → Source: *Deploy from a branch* →
   Branch: `main`, 폴더: `/docs` → Save. 1~2분 뒤 주소가 표시됩니다.
   예: `https://<내아이디>.github.io/fuel-widget/`
5. **첫 실행 확인**: Actions 탭 → *Update fuel price* → **Run workflow**. 초록 체크가 뜨면 정상.
6. **노션에 넣기**: 노션 페이지에서 `/embed` → 4번 주소 붙여넣기 → 블록 높이를 카드에 맞게 조절.

## 동작 메모

- 필리핀 유가는 보통 월요일 발표, **화요일 적용**. 매일 확인하되 값이 바뀐 날만 커밋합니다.
- 노션 임베드는 캐시 때문에 갱신이 몇 분~수 시간 늦게 보일 수 있습니다. 새로고침하면 반영됩니다.
- Actions가 빨간 X로 실패하면: 사이트 구조 변경(“가격 카드를 찾지 못했습니다”) 또는 접속 차단입니다.
  이 경우 기존 카드는 그대로 유지되고 덮어쓰지 않습니다.
- 60일간 저장소에 활동이 없으면 GitHub가 예약 실행을 멈춥니다. 가격이 바뀌면 자동 커밋이 생기므로 보통 문제 없지만,
  멈췄다면 Actions 탭에서 다시 Enable 하면 됩니다.
- 실행 시각 변경: `.github/workflows/update.yml`의 `cron` 값 (UTC 기준, PH = UTC+8).
- 등유·LPG 추가: `scrape.py`의 `FUELS`에 `"Kerosene": "Kerosene"` 등을 추가.
