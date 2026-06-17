pipeline {
    agent { label 'findart-public' }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        COMPOSE_PROJECT_NAME = 'findart'
        COMPOSE_FILE = 'docker-compose.yml'
        ENV_PATH = '.env'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Prepare Env') {
            steps {
                echo 'Preparing .env file'
        
                withCredentials([file(credentialsId: 'FinDART-dotenv', variable: 'ENV_FILE')]) {
                    sh '''
                    set -u
        
                    echo "Current user: $(id)"
                    echo "Workspace: $PWD"
                    echo "ENV_FILE path: $ENV_FILE"
                    echo "ENV_PATH: $ENV_PATH"
        
                    if [ ! -r "$ENV_FILE" ]; then
                        echo "ERROR: ENV_FILE is not readable"
                        ls -l "$ENV_FILE" || true
                        exit 1
                    fi
        
                    echo "Credential file metadata:"
                    ls -l "$ENV_FILE"
        
                    ENV_SIZE=$(wc -c < "$ENV_FILE" || echo 0)
                    echo "Credential file size: ${ENV_SIZE} bytes"
        
                    if [ "$ENV_SIZE" -eq 0 ]; then
                        echo "ERROR: Jenkins credential file is empty"
                        exit 1
                    fi
        
                    cp "$ENV_FILE" "$ENV_PATH"
                    chmod 600 "$ENV_PATH"
        
                    if [ ! -s "$ENV_PATH" ]; then
                        echo "ERROR: .env was not created or is empty"
                        ls -l "$ENV_PATH" || true
                        exit 1
                    fi
        
                    echo ".env prepared successfully"
                    ls -l "$ENV_PATH"
                    '''
                }
            }
        }
         stage('Build Image') {
            steps {
                sh '''
                docker compose \
                  -p "$COMPOSE_PROJECT_NAME" \
                  -f "$COMPOSE_FILE" \
                  --env-file "$ENV_PATH" \
                  build api
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                docker run --rm --env-file "$ENV_PATH" findart-api:latest python -m compileall app
                '''
            }
        }

        stage('DB Migration') {
            steps {
                sh '''
                docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" --env-file "$ENV_PATH" run --rm api alembic upgrade head
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" --env-file "$ENV_PATH" up -d --remove-orphans
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                set -a
                . "$ENV_PATH"
                set +a
        
                sleep 5
                curl -fsS "$HEALTH_URL"
                '''
            }
        }
    }

    post {
        success {
            echo 'finDART deployment succeeded.'
        }

        failure {
            echo 'finDART deployment failed.'
            sh 'docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" --env-file "$ENV_PATH" ps || true'
            sh 'docker logs findart-api --tail=100 || true'
        }
    }
}
