// vim: filetype=groovy
node('master') {
    def base = load('/var/jenkins_home/workspace/Infra/build-scripts/build/Jenkinsfile')
    base.execute([
        customStages: base.get_pypi_stages(true)
    ])
}