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

        stage('Deploy to Instances') {
            parallel {
                stage('Deploy to AI1') {
                    steps {
                        script {
                            deployToInstance('ai-server', 'server-ai1')
                        }
                    }
                }
                stage('Deploy to AI2') {
                    steps {
                        script {
                            deployToInstance('ai-server2', 'server-ai2')
                        }
                    }
                }
            }
        }

        stage('Health Check') {
            parallel {
                stage('Health Check AI1') {
                    steps {
                        script {
                            performHealthCheck('ai-server', 'AI1')
                        }
                    }
                }
                stage('Health Check AI2') {
                    steps {
                        script {
                            performHealthCheck('ai-server2', 'AI2')
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

def deployToInstance(instanceCredentialsId, logStream) {
    withCredentials([
        string(credentialsId: instanceCredentialsId, variable: 'EC2_INSTANCE_IP')
    ]) {
        sshagent([env.SSH_CREDENTIALS_ID]) {
            sh """
            ssh -o StrictHostKeyChecking=no ec2-user@${EC2_INSTANCE_IP} '
            aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin ${ECR_REPO}
            docker pull ${ECR_REPO}:latest
            docker stop ai_server || true
            docker rm ai_server || true
            docker run -d --env-file /home/ec2-user/.env --name ai_server \
                -p 8000:8000 ${ECR_REPO}:latest
            docker system prune -f
            docker image prune -f
            '
            """
        }
    }
}

def performHealthCheck(credentialsId, instanceLabel) {
    withCredentials([
        string(credentialsId: credentialsId, variable: 'EC2_INSTANCE_IP')
    ]) {
        script {
            def healthUrl = "http://${EC2_INSTANCE_IP}:8000/health"
            def maxRetries = 10
            def waitSeconds = 10
            def initialWait = 30
            def success = false

            echo "Initial wait for ${initialWait} seconds to allow container to start..."
            sleep(time: initialWait, unit: 'SECONDS')

            for (int i = 1; i <= maxRetries; i++) {
                echo "Health check attempt ${i} of ${maxRetries} for ${instanceLabel}"
                def response = sh(
                    script: "curl -s -o /dev/null -w '%{http_code}' ${healthUrl}",
                    returnStdout: true
                ).trim()

                if (response == '200') {
                    success = true
                    break
                } else {
                    echo "Health check failed on attempt ${i}. Retrying in ${waitSeconds} seconds..."
                    sleep(waitSeconds)
                }
            }

            if (!success) {
                error "Health check failed for ${instanceLabel} after ${maxRetries} attempts."
            } else {
                echo "Deployment verified successfully via Health Check for ${instanceLabel}."
            }
        }
    }
}
