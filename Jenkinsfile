// vim: filetype=groovy
node('general') {
    def base = load('/var/jenkins_home/workspace/Infra/build-scripts/build/Jenkinsfile')
    base.execute([
        customStages: base.get_pypi_stages(
            /* is_poetry */true,
            /* python_version */'3.8',
            /* should_bump_version */true,
            /* additional_package_roots */null,
            /* is_wheel */true,
        ),
    ])
}