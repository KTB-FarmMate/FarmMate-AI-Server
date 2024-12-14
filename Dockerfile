# Python 3.10-slim 이미지를 기반으로 시작
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 시스템 패키지 설치
RUN apt-get update
RUN apt-get install -y --no-install-recommends curl build-essential

# 패키지별 설치 (각 패키지는 별도의 RUN 명령어로 설치)
RUN pip install --no-cache-dir annotated-types==0.7.0
RUN pip install --no-cache-dir anyio==4.6.2.post1
RUN pip install --no-cache-dir certifi==2024.8.30
RUN pip install --no-cache-dir charset-normalizer==3.4.0
RUN pip install --no-cache-dir click==8.1.7
RUN pip install --no-cache-dir colorama==0.4.6
RUN pip install --no-cache-dir distro==1.9.0
RUN pip install --no-cache-dir exceptiongroup==1.2.2
RUN pip install --no-cache-dir fastapi==0.115.2
RUN pip install --no-cache-dir h11==0.14.0
RUN pip install --no-cache-dir httpcore==1.0.6
RUN pip install --no-cache-dir httpx==0.27.2
RUN pip install --no-cache-dir idna==3.10
RUN pip install --no-cache-dir iniconfig==2.0.0
RUN pip install --no-cache-dir jiter==0.6.1
RUN pip install --no-cache-dir openai==1.55.1
RUN pip install --no-cache-dir packaging==24.1
RUN pip install --no-cache-dir pip==24.2
RUN pip install --no-cache-dir pluggy==1.5.0
RUN pip install --no-cache-dir pydantic==2.9.2
RUN pip install --no-cache-dir pydantic_core==2.23.4
RUN pip install --no-cache-dir pydantic-settings==2.5.2
RUN pip install --no-cache-dir pytest==8.3.3
RUN pip install --no-cache-dir pytest-asyncio==0.24.0
RUN pip install --no-cache-dir pytest-mock==3.14.0
RUN pip install --no-cache-dir python-dotenv==1.0.1
RUN pip install --no-cache-dir requests==2.32.3
RUN pip install --no-cache-dir setuptools==75.1.0
RUN pip install --no-cache-dir sniffio==1.3.1
RUN pip install --no-cache-dir starlette==0.40.0
RUN pip install --no-cache-dir tomli==2.0.2
RUN pip install --no-cache-dir tqdm==4.66.5
RUN pip install --no-cache-dir typing_extensions==4.12.2
RUN pip install --no-cache-dir urllib3==2.2.3
RUN pip install --no-cache-dir uvicorn==0.32.0
RUN pip install --no-cache-dir wheel==0.44.0
RUN pip install --no-cache-dir beautifulsoup4==4.12.3

# 깃 레포지토리에서 프로젝트 파일을 복사
COPY . .

# 애플리케이션 포트를 외부에 노출
EXPOSE 8000

# Uvicorn 서버를 시작
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
