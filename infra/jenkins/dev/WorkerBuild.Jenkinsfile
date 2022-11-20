pipeline {
    agent {
        docker {
            // TODO build & push your Jenkins agent image, place the URL here
            image '352708296901.dkr.ecr.eu-west-1.amazonaws.com/ddady-agent-ecr:latest'
            args  '--user root -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    // TODO dev worker build stage
}