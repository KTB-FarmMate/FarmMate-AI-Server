pipeline {
    agent {
        label 'farmmate-ai-agent'
    }

    environment {
        REPO = 'KTB-FarmMate/FarmMate-AI-Server'
        ECR_REPO = '211125697339.dkr.ecr.ap-northeast-2.amazonaws.com/farmmate-ai'
        ECR_CREDENTIALS_ID = 'ecr:ap-northeast-2:farmmate-ecr'
        SSH_CREDENTIALS_ID = 'EC2_ssh_key'
    }

    stages {
        stage('Start Alert'){
            steps {
                slackSend (
                 channel: '#ai-server-alert',
                 color: '#141414',
                 message: "🚀 [${env.JOB_NAME}] 작업이 시작되었습니다!\n" +
                        "- 빌드 번호: #${env.BUILD_NUMBER}\n" +
                        "- 브랜치: ${env.GIT_BRANCH}\n" + 
                        "- 시작 시간: ${new Date().format('yyyy-MM-dd HH:mm:ss')}"
                )
            }
        }
        stage('Checkout') {
            steps {
                // Git 소스 코드를 체크아웃하는 단계
                git branch: 'dev', url: "https://github.com/${REPO}.git", credentialsId: 'farmmate-github-key'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Docker 이미지를 빌드하는 단계
                    dockerImage = docker.build("${ECR_REPO}:latest", ".")
                }
            }
        }

        stage('Push to ECR') {
            steps {
                script {
                    // ECR에 Docker 이미지를 푸시하는 단계
                    docker.withRegistry("https://${ECR_REPO}", "${ECR_CREDENTIALS_ID}") {
                        dockerImage.push('latest')
                    }
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                withCredentials([
                    string(credentialsId: 'ai-server', variable: 'EC2_INSTANCE_IP')
                ]) {
                    sshagent([SSH_CREDENTIALS_ID]) {
                        sh """
                        # EC2에서 Docker 컨테이너 실행 시 env-file 포함
                        ssh -o StrictHostKeyChecking=no ec2-user@${EC2_INSTANCE_IP} '
                        aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin ${ECR_REPO}
                        docker pull ${ECR_REPO}:latest
                        docker stop ai_server || true
                        docker rm ai_server || true
                        docker run -d --env-file /home/ec2-user/.env --name ai_server -p 8000:8000 ${ECR_REPO}:latest
                        docker system prune -f
                        docker image prune -f
                        '
                        """
                    }
                }
            }
        }

        stage('Health Check') {
            steps {
                withCredentials([
                    string(credentialsId: 'ai-server', variable: 'EC2_INSTANCE_IP')
                ]) {
                    script {
                        def healthUrl = "http://${EC2_INSTANCE_IP}:8000/health"
                        def maxRetries = 10          // 최대 재시도 횟수
                        def waitSeconds = 10         // 재시도 간 대기 시간 (초)
                        def initialWait = 30         // 초기 대기 시간 (초)
                        def success = false          // Health Check 성공 여부
        
                        echo "Initial wait for ${initialWait} seconds to allow container to start..."
                        sleep(time: initialWait, unit: 'SECONDS') // 초기 대기 시간
        
                        for (int i = 1; i <= maxRetries; i++) {
                            echo "Health check attempt ${i} of ${maxRetries}"
                            
                            // curl 명령어를 사용하여 /health 체크
                            def response = sh(
                                script: "curl -s -o /dev/null -w '%{http_code}' ${healthUrl}",
                                returnStdout: true
                            ).trim()
        
                            if (response == '200') {
                                success = true
                                break
                            } else {
                                sleep(waitSeconds) // 재시도 전 대기
                            }
                        }
        
                        if (!success) {
                            error "Health check failed after ${maxRetries} attempts."
                        } else {
                            echo "Deployment verified successfully via Health Check."
                        }
                    }
                }
            }
        }

        stage('Cleanup Local Docker Images') {
            steps {
                sh "docker rmi ${ECR_REPO}:latest || true"
            }
        }
    }

    post {
        success {
            slackSend (
                 channel: '#ai-server-alert',
                 color: 'good',
                 message: "✅ [${env.JOB_NAME}] 작업이 성공적으로 완료되었습니다!\n" +
                          "- 빌드 번호: #${env.BUILD_NUMBER}\n" +
                          "- 완료 시간: ${new Date().format('yyyy-MM-dd HH:mm:ss')}\n" +
                          "- 자세히 보기: ${env.BUILD_URL}"
            )
        }
        unstable {
            slackSend (
                 channel: '#ai-server-alert',
                 color: 'warning',
                 message: "⚠️ [${env.JOB_NAME}] 작업이 완료되었지만 일부 테스트가 실패했습니다.\n" +
                          "- 빌드 번호: #${env.BUILD_NUMBER}\n" +
                          "- 로그 확인: ${env.BUILD_URL}"
            )
        }
        failure {
            slackSend (
                 channel: '#ai-server-alert',
                 color: 'danger',
                 message: "❌ [${env.JOB_NAME}] 작업이 실패했습니다.\n" +
                          "- 빌드 번호: #${env.BUILD_NUMBER}\n" +
                          "- 에러 로그: [여기서 확인](${env.BUILD_URL}/console)\n" +
                          "- 담당자 확인 부탁드립니다."
            )
        }
        always {
            // Cleanup: 로컬 Docker 시스템을 정리 
            sh 'docker system prune -f'
        }
    }
}
