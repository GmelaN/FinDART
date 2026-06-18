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
        HEALTH_URL = 'http://10.1.0.100:8000/api/v1/health'
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
                    set -eu

                    cp "$ENV_FILE" "$ENV_PATH"
                    chmod 600 "$ENV_PATH"
                    test -s "$ENV_PATH"

                    echo ".env prepared"
                    ls -l "$ENV_PATH"
                    '''
                }
            }
        }

        stage('Build Image') {
            steps {
                sh '''
                set -eu

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
                set -eu

                docker compose \
                  -p "$COMPOSE_PROJECT_NAME" \
                  -f "$COMPOSE_FILE" \
                  --env-file "$ENV_PATH" \
                  run --rm --no-deps api python -m compileall app
                '''
            }
        }

        stage('DB Migration') {
            steps {
                sh '''
                set -eu

                docker compose \
                  -p "$COMPOSE_PROJECT_NAME" \
                  -f "$COMPOSE_FILE" \
                  --env-file "$ENV_PATH" \
                  run --rm api alembic upgrade head
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                set -eu

                docker compose \
                  -p "$COMPOSE_PROJECT_NAME" \
                  -f "$COMPOSE_FILE" \
                  --env-file "$ENV_PATH" \
                  up -d --remove-orphans
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                set -eu

                echo "PWD=$PWD"
                ls -l "$ENV_PATH"

                ENV_FILE_ABS="$ENV_PATH"
                case "$ENV_FILE_ABS" in
                  /*) ;;
                  *) ENV_FILE_ABS="$PWD/$ENV_FILE_ABS" ;;
                esac

                set -a
                . "$ENV_FILE_ABS"
                set +a

                for i in $(seq 1 10); do
                    if curl -fsS "$HEALTH_URL"; then
                        exit 0
                    fi

                    echo "Health check retry: $i"
                    sleep 3
                done

                echo "Health check failed: $HEALTH_URL"
                exit 1
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

            sh '''
            docker compose \
              -p "$COMPOSE_PROJECT_NAME" \
              -f "$COMPOSE_FILE" \
              --env-file "$ENV_PATH" \
              ps || true
            '''

            sh '''
            docker compose \
              -p "$COMPOSE_PROJECT_NAME" \
              -f "$COMPOSE_FILE" \
              --env-file "$ENV_PATH" \
              logs --tail=100 api || true
            '''
        }
    }
}
