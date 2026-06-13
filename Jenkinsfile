pipeline {
    agent { label 'findart-public' }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        COMPOSE_PROJECT_NAME = 'findart'
        COMPOSE_FILE = 'docker-compose.yml'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Image') {
            steps {
                sh '''
                docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" --env-file /opt/findart/.env build api
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                docker run --rm --env-file /opt/findart/.env findart-api:latest python -m compileall app
                '''
            }
        }

        stage('DB Migration') {
            steps {
                sh '''
                docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" --env-file /opt/findart/.env run --rm api alembic upgrade head
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" --env-file /opt/findart/.env up -d --remove-orphans
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                set -a
                . /opt/findart/.env
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
            sh 'docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" --env-file /opt/findart/.env ps || true'
            sh 'docker logs findart-api --tail=100 || true'
        }
    }
}
