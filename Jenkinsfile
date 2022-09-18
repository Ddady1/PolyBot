pipeline {
    agent any

    stages {
        stage('Build') {
            environment {
                REGISTRY_URL = "352708296901.dkr.ecr.eu-north-1.amazonaws.com"
                IMAGE_TAG = "0.0.$BUILD_NUMBER"
                IMAGE_NAME = "alonit-bot"
            }
            steps {
                sh '''
                aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin $REGISTRY_URL
                docker build -t $IMAGE_NAME .
                docker tag $IMAGE_NAME $REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG
                docker push $REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG
                '''
            }
            post {
                always {
                    sh '''
                        if [[ docker images | grep -q alonit-bot.*$IMAGE_TAG ]]; then
                            docker rmi $REGISTRY_URL/$IMAGE_NAME:IMAGE_TAG
                            docker rmi $IMAGE_NAME
                        fi
                    '''
                }
            }
        }
        stage('Trigger Deploy') {
            steps {
                build job: "BotDeploy", parameters: [
                    string(name='image', value: "$IMAGE_NAME:$IMAGE_TAG")
                ]
            }
        }
        stage('Stage III ...') {
            steps {
                sh 'echo echo "stage III..."'
            }
        }
    }
}