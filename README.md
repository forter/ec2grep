## ec2grep - EC2 cli tool

### Install

Make sure you have `pipx` available in your system (`brew install pipx` if not).

```bash
pipx install ec2grep --index-url https://artifactory.frdstr.com/artifactory/api/pypi/pypi/simple
```

### Usage

##### ls
Basic usage, find by name tag, external / internal IP, DNS

```bash
ec2 ls my-hostname
```

Using a custom formatter (name, ip, extended)

```bash
ec2 ls --format=name my-hostname
```

##### ssh

Open an SSH session
```bash
ec2 ssh my-hostname
```

With arguments
```bash
ec2 ssh my-hostname -- w
```

##### custom region

```bash
ec2 --region us-west-2 ls my-hostname
```
