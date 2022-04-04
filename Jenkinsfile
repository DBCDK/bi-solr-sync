#!groovy
node('devel11') {
    def app
    checkout scm

    stage('build'){
        def tag = 'bi-solr-sync'
        app = docker.build("$tag:${env.BUILD_NUMBER}", '--pull --no-cache .')
    }

    stage('push') {
        docker.withRegistry('https://docker-metascrum.artifacts.dbccloud.dk', 'docker') {
            app.push()
            app.push('latest')
        }
    }
}
