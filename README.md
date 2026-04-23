# English Tutor - Railway 배포 버전

어디서나 PC 없이도 스마트폰으로 접속 가능한 영어 회화 튜터입니다.

## 사전 준비
- GitHub 계정 (https://github.com)
- Railway 계정 (https://railway.app)
- Anthropic API 키 (https://console.anthropic.com)

## 배포 순서

### 1단계 - GitHub에 코드 올리기
1. github.com 로그인
2. New repository 생성 (이름: english-tutor, Public)
3. 아래 명령 실행:

  git init
  git add .
  git commit -m "첫 배포"
  git branch -M main
  git remote add origin https://github.com/[내ID]/english-tutor.git
  git push -u origin main

### 2단계 - Railway 배포
1. railway.app 접속
2. "Deploy from GitHub repo" 선택
3. english-tutor 저장소 선택 후 Deploy

### 3단계 - API 키 환경변수 설정
1. Railway 프로젝트 > Variables 탭
2. New Variable 추가:
   Name:  ANTHROPIC_API_KEY
   Value: sk-ant-실제키입력
3. 저장 후 자동 재배포

### 4단계 - 도메인 확인
1. Settings > Domains > Generate Domain
2. https://english-tutor-xxxx.railway.app 주소 생성
3. 스마트폰으로 접속!

## 스마트폰 앱처럼 설치 (안드로이드 Chrome)
1. 위 주소 접속
2. 메뉴(점 3개) > "홈 화면에 추가"
3. 앱 아이콘으로 바로 실행 가능!

## Railway 요금
- 무료 플랜: 월 $5 크레딧 제공
- 소규모 개인 앱은 무료로 운영 가능

## 보안 주의
- API 키는 Railway 환경변수에만 입력하세요
- .env 파일은 .gitignore에 포함되어 GitHub에 올라가지 않습니다
