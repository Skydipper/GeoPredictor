#!groovy

node {

  // Variables
  def tokens = "${env.JOB_NAME}".tokenize('/')
  def appName = tokens[0]
  def dockerUsername = "${DOCKER_USERNAME}"
  def imageTag = "${dockerUsername}/${appName}:${env.BRANCH_NAME}.${env.BUILD_NUMBER}"

  currentBuild.result = "SUCCESS"

  checkout scm
  properties([pipelineTriggers([[$class: 'GitHubPushTrigger'], pollSCM('0 * * * *')])])

  try {

    stage ('Build docker') {
      sh("docker -H :2375 build -t ${imageTag} .")
      sh("docker -H :2375 build -t ${dockerUsername}/${appName}:latest .")
    }

    stage('Push Docker') {
      withCredentials([usernamePassword(credentialsId: 'Skydipper Docker Hub', usernameVariable: 'DOCKER_HUB_USERNAME', passwordVariable: 'DOCKER_HUB_PASSWORD')]) {
        sh("docker -H :2375 login -u ${DOCKER_HUB_USERNAME} -p ${DOCKER_HUB_PASSWORD}")
        sh("docker -H :2375 push ${imageTag}")
        sh("docker -H :2375 push ${dockerUsername}/${appName}:latest")
        sh("docker -H :2375 rmi ${imageTag}")
      }
    }

    stage ("Deploy Application") {
      switch ("${env.BRANCH_NAME}") {

        // Roll out to production
        case "develop":
            sh("echo Deploying to PROD cluster")
            sh("kubectl config use-context gke_${GCLOUD_PROJECT}_${GCLOUD_GCE_ZONE}_${KUBE_PROD_CLUSTER}")
            def service = sh([returnStdout: true, script: "kubectl get deploy ${appName} || echo NotFound"]).trim()
            sh("kubectl apply -f k8s/services/")
            sh("kubectl apply -f k8s/production/")
            sh("kubectl set image deployment ${appName} ${appName}=${imageTag} --record")
          break

        // Default behavior?
        default:
          echo "Default -> do nothing"
          currentBuild.result = "SUCCESS"
      }
    }


  } catch (err) {

    currentBuild.result = "FAILURE"
    throw err
  }

}
