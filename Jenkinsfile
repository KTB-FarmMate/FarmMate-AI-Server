 pipeline {
    agent {
        label 'farmmate-ai-agent'
    }

    environment {
        REPO = 'KTB-FarmMate/FarmMate-AI-Server'
        ECR_REPO = '211125697339.dkr.ecr.ap-northeast-2.amazonaws.com/farmmate-ai'
        ECR_CREDENTIALS_ID = 'ecr:ap-northeast-2:farmmate-ecr'
        SSH_CREDENTIALS_ID = 'EC2_ssh_key'
        ENVIRONMENT_KEY = 'ai_environment_key'
    }

    stages {
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
        stage('Download Environment') {
            steps {
                withAWS(credentials: "${ECR_CREDENTIALS_ID}", region: 'ap-northeast-2') {
                    sh '''
                        aws s3 cp "${ENVIRONMENT_KEY}" .env
                        chmod 600 .env
                    '''
                }
            }
        }
        stage('Deploy to EC2') {
            steps {
                withCredentials([string(credentialsId: 'ai-server', variable: 'EC2_INSTANCE_IP')]) {
                    script {
                        // SSH를 통해 EC2에 연결하고, ECR 이미지를 가져와 실행
                        sshagent([SSH_CREDENTIALS_ID]) {
                            // .env 파일을 EC2로 전송
                            sh """
                            scp -o StrictHostKeyChecking=no .env ec2-user@${EC2_INSTANCE_IP}:/home/ec2-user/.env
                            """

                            
                            sh """
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
        }
        
        stage('Cleanup Local Docker Images') {
            steps {
                script {
                    // 로컬 Docker 이미지를 삭제하는 단계
                    sh "docker rmi ${ECR_REPO}:latest || true"
                }
            }
        }
    }
    post {
        success {
            echo 'Build and integration successful, proceeding with deployment.'
        }
        failure {
            echo 'Build failed, keeping the current deployment as it is.'
        }
        always {
            // Cleanup: 로컬 Docker 시스템을 정리
            sh 'docker system prune -f'
        }
    }
}
