pipeline {
    agent any

    // Parameters: values set once, picked automatically on webhook trigger
    parameters {
        string(name: 'BACKEND_SERVER_IP', defaultValue: '<backend-server-ip>', description: 'Public IP of backend EC2 server')
        string(name: 'DEPLOY_DIR', defaultValue: '/home/ubuntu/backend-app', description: 'Directory on backend server to deploy app')
    }

    environment {
        PYTHON = "/usr/bin/python3"
        VENV_DIR = "venv"
        SSH_CREDENTIALS = 'backend-server-ssh' // Jenkins SSH credentials ID for backend server
    }

    stages {

        stage('Checkout Code') {
            steps {
                echo "Checking out backend code from GitHub..."
                checkout scm
            }
        }

        stage('Deploy to Backend Server') {
            steps {
                sshagent (credentials: [env.SSH_CREDENTIALS]) {
                    sh '''
                        echo "Creating deployment directory if it doesn't exist..."
                        ssh -o StrictHostKeyChecking=no ubuntu@${BACKEND_SERVER_IP} "mkdir -p ${DEPLOY_DIR}"

                        echo "Copying backend code to backend server..."
                        scp -o StrictHostKeyChecking=no app.py backend_version.txt requirements.txt ubuntu@${BACKEND_SERVER_IP}:${DEPLOY_DIR}/
                    '''
                }
            }
        }
        
        stage('Setup Virtual Environment & Install Dependencies') {
            steps {
                sshagent (credentials: [env.SSH_CREDENTIALS]) {
                    sh """
                        echo "Setting up virtual environment on backend server..."

                        ssh -o StrictHostKeyChecking=no ubuntu@${BACKEND_SERVER_IP} "
                            set -e
                            cd ${DEPLOY_DIR}

                            echo 'Creating venv if missing...'
                            if [ ! -d venv ]; then
                                python3 -m venv venv
                            fi

                            echo 'Activating venv...'
                            source venv/bin/activate

                            echo 'Installing dependencies...'
                            pip install --upgrade pip
                            pip install -r requirements.txt
                        "
                    """
                }
            }
        }
        
        stage('Stop Existing Backend') {
            steps {
                sshagent (credentials: [env.SSH_CREDENTIALS]) {
                    sh """
ssh -o StrictHostKeyChecking=no ubuntu@${BACKEND_SERVER_IP} << EOF
cd ${DEPLOY_DIR}

if pgrep -f app.py > /dev/null; then
    echo "Stopping running backend app..."
    pkill -f app.py
else
    echo "No running backend app found."
fi
EOF
            """
                }
            }
        }

        stage('Start Backend') {
            steps {
                sshagent (credentials: [env.SSH_CREDENTIALS]) {
                    sh '''
                        echo "Starting backend server..."
                        ssh -o StrictHostKeyChecking=no ubuntu@${BACKEND_SERVER_IP} "
                            cd ${DEPLOY_DIR}
                            source ${VENV_DIR}/bin/activate
                            nohup python3 app.py > backend.log 2>&1 &
                        "
                    '''
                }   
            }
        }

        stage('Read Backend Version') {
            steps {
                sshagent (credentials: [env.SSH_CREDENTIALS]) {
                    sh '''
                        echo "Backend Version:"
                        ssh -o StrictHostKeyChecking=no ubuntu@${BACKEND_SERVER_IP} "cat ${DEPLOY_DIR}/backend_version.txt || echo 'backend_version.txt not found'"
                    '''
                }
            }
        }

    }

    post {
        success {
            echo "✅ Backend deployed successfully!"
        }
        failure {
            echo "❌ Backend deployment failed!"
        }
    }
}
