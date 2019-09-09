node() {
  stage('pipenv') {
    sh($/
      pipenv install --dev
    /$)
  }
  stage('pytest') {
    sh($/
      pytest -s -l --junit-xml=${BUILD_NUMBER}-results.xml || true
    /$)
    archive("${BUILD_NUMBER}-results.xml")
  }
}