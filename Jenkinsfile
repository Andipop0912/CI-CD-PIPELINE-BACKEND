pipeline {
    agent any

    parameters {
        string(
            name: 'BACKEND_SERVER_IP',
            defaultValue: '32.199.159.187',
            description: 'Public IP of Backend EC2'
        )

        string(
            name: 'DEPLOY_DIR',
            defaultValue: '/home/ubuntu/backend-app',
            description: 'Backend deployment directory'
        )
    }

    environment {
        SSH_CREDENTIALS = 'backend-server-ssh'
        VENV_DIR = 'venv'
    }

    stages {

        stage('Checkout Code') {
            steps {
                echo 'Checking out backend code...'
                checkout scm
            }
        }

        stage('Deploy to Backend Server') {
            steps {
                echo "Backend Server IP: ${params.BACKEND_SERVER_IP}"
                echo "Deployment Directory: ${params.DEPLOY_DIR}"

                sshagent(credentials: [env.SSH_CREDENTIALS]) {

                    sh """
                        echo "Creating deployment directory..."

                        ssh -o StrictHostKeyChecking=no ubuntu@${params.BACKEND_SERVER_IP} \
                        "mkdir -p ${params.DEPLOY_DIR}"

                        echo "Copying backend files..."

                        scp -o StrictHostKeyChecking=no \
                        app.py \
                        requirements.txt \
                        backend_version.txt \
                        ubuntu@${params.BACKEND_SERVER_IP}:${params.DEPLOY_DIR}/
                    """
                }
            }
        }

        stage('Setup Virtual Environment') {
            steps {

                sshagent(credentials: [env.SSH_CREDENTIALS]) {

                    sh """
                        ssh -o StrictHostKeyChecking=no ubuntu@${params.BACKEND_SERVER_IP} '

                        set -e

                        cd ${params.DEPLOY_DIR}

                        if [ ! -d ${VENV_DIR} ]; then
                            python3 -m venv ${VENV_DIR}
                        fi

                        . ${VENV_DIR}/bin/activate

                        pip install --upgrade pip

                        pip install -r requirements.txt

                        '
                    """
                }
            }
       }

	stage('Stop Existing Backend') {
    steps {
        sshagent(credentials: ['env.SSH_CREDENTIALS']) {
            sh '''
                ssh -o StrictHostKeyChecking=no ubuntu@32.199.159.187 "
                    pkill -f app.py 2>/dev/null || true
                    sleep 1
                    echo 'Backend stopped (or was not running).'
                "
            '''
        }
    }
}

        stage('Start Backend') {
    steps {
        sshagent(credentials: ['env.SSH_CREDENTIALS']) {
            sh '''
                ssh -o StrictHostKeyChecking=no ubuntu@32.199.159.187 "
                    cd /home/ubuntu/backend-app
                    source venv/bin/activate
                    nohup python3 app.py > app.log 2>&1 &
                    echo 'Backend started with PID: '$!
                "
            '''
        }
    }
}

	stage('Health Check') {
    steps {
        sh 'sleep 3'  // Give app time to boot
        sshagent(credentials: ['env.SSH_CREDENTIALS']) {
            sh '''
                ssh -o StrictHostKeyChecking=no ubuntu@32.199.159.187 "
                    pgrep -f app.py && echo 'App is running!' || echo 'WARNING: App not found!'
                "
            '''
        }
    }
}

        stage('Read Backend Version') {
            steps {

                sshagent(credentials: [env.SSH_CREDENTIALS]) {

                    sh """
                        ssh -o StrictHostKeyChecking=no ubuntu@${params.BACKEND_SERVER_IP} '

                        echo "Backend Version:"
                        cat ${params.DEPLOY_DIR}/backend_version.txt

                        '
                    """
                }
            }
        }
    }

    post {

        success {
            echo '✅ Backend deployment completed successfully!'
        }

        failure {
            echo '❌ Backend deployment failed!'
        }

        always {
            cleanWs()
        }
    }
}
