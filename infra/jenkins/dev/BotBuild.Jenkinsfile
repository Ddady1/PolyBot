pipeline {
    agent {
        docker {
            // TODO build & push your Jenkins agent image, place the URL here
            image '352708296901.dkr.ecr.eu-west-1.amazonaws.com/ddady-agent-ecr:latest'
            args  '--user root -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }
    environment {
        REGISTRY_URL = "352708296901.dkr.ecr.eu-west-1.amazonaws.com/ddady-jen-dev-botbuild"
        IMAGE_TAG = "0.0.$BUILD_NUMBER"
        IMAGE_NAME = "ddady-dev-botbuild"
    }

    stages {
        stage('Build') {
            steps {
                // TODO dev bot build stage
                sh '''
                docker build -t $IMAGE_NAME .
                docker tag $IMAGE_NAME $REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG
                docker push $REGISTRY_URL/$IMAGE_NAME:$IMAGE_TAG
                '''
            }
        }

        stage('Trigger Deploy') {
            steps {
                build job: 'BotDeploy', wait: false, parameters: [
                    string(name: 'BOT_IMAGE_NAME', value: "352708296901.dkr.ecr.eu-west-1.amazonaws.com/ddady-agent-ecr:latest")
                ]
            }
        }
    }
}