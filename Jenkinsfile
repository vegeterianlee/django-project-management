// Jenkinsfile
pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'docker.io'
        IMAGE_NAME = 'dsct/daesan-pms'
        GITLAB_REPO = 'https://gitlab.com/ds-it-team/daesan-pms-server.git'
        K8S_BRANCH = 'main'
        K8S_NAMESPACE = 'pms-web'
        INFRA_DEPLOYED = 'false'
    }

    stages {
        // ============================================
        // 1. 체크아웃
        // ============================================
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                    env.IMAGE_TAG = "${env.GIT_COMMIT_SHORT}-${env.BUILD_NUMBER}"
                    env.FULL_IMAGE_TAG = "${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.IMAGE_TAG}"
                    env.LATEST_IMAGE_TAG = "${DOCKER_REGISTRY}/${IMAGE_NAME}:latest"
                }
            }
        }

        // ============================================
        // 2. 배포 설정 파싱
        // ============================================
        stage('Parse Deploy Config') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'dockerhub-username', variable: 'DOCKERHUB_USERNAME'),
                        string(credentialsId: 'dockerhub-password', variable: 'DOCKERHUB_PASSWORD'),
                        string(credentialsId: 'kubeconfig-data', variable: 'KUBECONFIG_DATA')
                    ]) {
                        env.DOCKERHUB_USERNAME = "${DOCKERHUB_USERNAME}"
                        env.DOCKERHUB_PASSWORD = "${DOCKERHUB_PASSWORD}"
                        env.KUBECONFIG_DATA = "${KUBECONFIG_DATA}"
                    }
                }
            }
        }

        // ============================================
        // 3. kubeconfig 설정
        // ============================================
        stage('Configure kubeconfig') {
            steps {
                script {
                    sh """
                        mkdir -p \$HOME/.kube
                        echo "${env.KUBECONFIG_DATA}" | base64 -d > \$HOME/.kube/config
                        chmod 600 \$HOME/.kube/config

                        # k3s 클러스터 연결 확인
                        kubectl cluster-info
                        kubectl get nodes
                    """
                }
            }
        }

        // ============================================
        // 4. 네임스페이스 생성
        // ============================================
        stage('Create Namespace') {
            steps {
                script {
                    sh """
                        kubectl create namespace ${env.K8S_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
                    """
                }
            }
        }

        // ============================================
        // 5. 인프라 배포 (MySQL, Redis, Nginx)
        // ============================================
        stage('Deploy Infrastructure') {
            steps {
                script {
                    // 인프라가 이미 배포되어 있는지 확인
                    def mysqlExists = sh(
                        script: "kubectl get statefulset pms-v3-mysql -n ${env.K8S_NAMESPACE} 2>/dev/null || echo 'not-found'",
                        returnStdout: true
                    ).trim()

                    if (mysqlExists == 'not-found') {
                        echo "Deploying infrastructure (MySQL, Redis, Nginx)..."

                        // MySQL StatefulSet 배포
                        sh """
                            kubectl apply -f k8s/base/mysql-statefulset.yaml -n ${env.K8S_NAMESPACE}
                            kubectl wait --for=condition=ready pod/pms-v3-mysql-0 -n ${env.K8S_NAMESPACE} --timeout=300s || true
                        """

                        // Redis StatefulSet 배포
                        sh """
                            kubectl apply -f k8s/base/redis-statefulset.yaml -n ${env.K8S_NAMESPACE}
                            kubectl wait --for=condition=ready pod/pms-v3-redis-0 -n ${env.K8S_NAMESPACE} --timeout=300s || true
                        """

                        // Nginx Deployment 배포
                        sh """
                            kubectl apply -f k8s/base/nginx-deployment.yaml -n ${env.K8S_NAMESPACE}
                            kubectl wait --for=condition=available deployment/pms-v3-nginx -n ${env.K8S_NAMESPACE} --timeout=300s || true
                        """

                        env.INFRA_DEPLOYED = 'true'
                    } else {
                        echo "Infrastructure already deployed. Skipping..."
                        env.INFRA_DEPLOYED = 'false'
                    }
                }
            }
        }

        // ============================================
        // 6. Docker 로그인
        // ============================================
        stage('Docker Login') {
            steps {
                script {
                    sh """
                        echo "${env.DOCKERHUB_PASSWORD}" | docker login ${env.DOCKER_REGISTRY} \
                            -u "${env.DOCKERHUB_USERNAME}" \
                            --password-stdin
                    """
                }
            }
        }

        // ============================================
        // 7. Docker Buildx 설정
        // ============================================
        stage('Set up Docker Buildx') {
            steps {
                script {
                    sh '''
                        docker buildx version || docker buildx install
                        docker buildx create --use --name builder --driver docker-container || true
                        docker buildx inspect --bootstrap
                    '''
                }
            }
        }

        // ============================================
        // 8. Docker 이미지 빌드 및 푸시 (캐싱 포함)
        // ============================================
        stage('Build and Push with Cache') {
            steps {
                script {
                    sh """
                        docker buildx build \
                            --platform linux/amd64 \
                            --push \
                            --tag ${env.FULL_IMAGE_TAG} \
                            --tag ${env.LATEST_IMAGE_TAG} \
                            --cache-from type=registry,ref=${DOCKER_REGISTRY}/${IMAGE_NAME}:buildcache \
                            --cache-to type=registry,ref=${DOCKER_REGISTRY}/${IMAGE_NAME}:buildcache,mode=max \
                            --build-arg BUILDKIT_INLINE_CACHE=1 \
                            .
                    """
                }
            }
        }

        // ============================================
        // 9. 이전 배포 버전 저장 (롤백용)
        // ============================================
        stage('Save Previous Version') {
            steps {
                script {
                    try {
                        env.PREVIOUS_IMAGE = sh(
                            script: """
                                kubectl get deployment web -n ${env.K8S_NAMESPACE} \
                                    -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo ""
                            """,
                            returnStdout: true
                        ).trim()
                        echo "Previous image: ${env.PREVIOUS_IMAGE}"
                    } catch (Exception e) {
                        env.PREVIOUS_IMAGE = ""
                        echo "No previous deployment found"
                    }
                }
            }
        }

        // ============================================
        // 10. k8s 매니페스트 업데이트 및 커밋
        // ============================================
        stage('Update K8s Manifest') {
            steps {
                script {
                    sh """
                        git config user.name "Jenkins"
                        git config user.email "jenkins@example.com"

                        # kustomization.yaml의 이미지 태그 업데이트
                        sed -i 's|newTag:.*|newTag: ${env.IMAGE_TAG}|g' k8s/overlays/prod/kustomization.yaml
                        sed -i 's|newName:.*|newName: ${env.DOCKER_REGISTRY}/${env.IMAGE_NAME}|g' k8s/overlays/prod/kustomization.yaml

                        git add k8s/overlays/prod/kustomization.yaml
                        git commit -m "Update image tag to ${env.IMAGE_TAG} [skip ci]"
                        git push origin ${env.K8S_BRANCH}
                    """
                }
            }
        }

        // ============================================
        // 11. 애플리케이션 배포 확인 (ArgoCD 대기)
        // ============================================
        stage('Wait for ArgoCD Deployment') {
            steps {
                script {
                    echo "Waiting for ArgoCD to deploy the application..."
                    // ArgoCD가 배포를 완료할 때까지 대기 (선택사항)
                    // 또는 ArgoCD가 자동으로 처리하도록 함
                }
            }
        }
    }

    post {
        success {
            echo "✅ Build successful! Image: ${env.FULL_IMAGE_TAG}"
            echo "Infrastructure deployed: ${env.INFRA_DEPLOYED}"
            echo "ArgoCD will automatically deploy the updated manifest."
        }
        failure {
            echo "❌ Build failed!"
            script {
                // 실패 시 인프라 상태 확인
                sh """
                    echo "=== Infrastructure Status ==="
                    kubectl get statefulset -n ${env.K8S_NAMESPACE}
                    kubectl get deployment -n ${env.K8S_NAMESPACE}
                    kubectl get pods -n ${env.K8S_NAMESPACE}
                """
            }
        }
    }
}