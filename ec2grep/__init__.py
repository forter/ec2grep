#!/usr/bin/env python

import sys
import threading
import subprocess
import itertools
from concurrent.futures import ThreadPoolExecutor as Executor
from functools import partial
from operator import itemgetter

import boto3
import click
import six

executor = Executor(4)
name = (lambda i: {tag['Key']: tag['Value'] for tag in i.get('Tags', [])}.get('Name', ''))
public_ip = itemgetter('PublicIpAddress')
private_ip = itemgetter('PrivateIpAddress')
extended_public = (lambda i: '{} ({})'.format(name(i), public_ip(i)))
extended_private = (lambda i: '{} ({})'.format(name(i), private_ip(i)))
DEFAULT_ATTRIBUTES = [
    'tag:Name',
    'network-interface.addresses.association.public-ip',
    'network-interface.addresses.private-ip-address',
    'network-interface.private-dns-name'
]


def _get_instances(ec2, filter_):
    response = ec2.describe_instances(Filters=[filter_])
    reservations = response['Reservations']
    return list(itertools.chain.from_iterable(r['Instances'] for r in reservations))


def match_instances(region_name, query, attributes=DEFAULT_ATTRIBUTES):
    ec2 = boto3.client('ec2', region_name=region_name)
    get_instances = partial(_get_instances, ec2)
    instance_lists = executor.map(get_instances, [
        {'Name': attr, 'Values': ['*{}*'.format(query)]} for attr in attributes
    ])
    chained = (i for i in itertools.chain.from_iterable(instance_lists) if 'PublicIpAddress' in i)
    return sorted(chained, key=name)


def die(*args):
    click.echo(*args, err=True)
    sys.exit(1)


def read_numbers(min_value, max_value):
    while True:
        try:
            choices = six.moves.input()
            choices = [int(c.strip()) for c in choices.split(',')]
            if not (all(min_value <= c <= max_value for c in choices)):
                raise ValueError('Invalid input')
            if len(choices) != 1 and 0 in choices:
                raise ValueError('Invalid input')
            return choices
        except ValueError as e:
            click.echo(str(e), err=True)
            continue


formatters = {
    'extended_public': extended_public,
    'extended_private': extended_private,
    'public_ip': public_ip,
    'private_ip': private_ip,
    'name': name
}


@click.group()
@click.option('--region', '-r', default='us-east-1')
@click.pass_context
def cli(ctx, region):
    ctx.obj = {'region': region}


class OutputConsumer(object):

    def __init__(self, out_read, out_write, prefix):
        self.prefix = prefix
        self.out_read = out_read
        self.out_write = out_write
        self.consumer = threading.Thread(target=self.consume_output)
        self.consumer.daemon = True
        self.consumer.start()

    def consume_output(self):
        for line in iter(self.out_read.readline, b''):
            self.out_write.write('[{}] {}'.format(self.prefix, line))

    def join(self):
        self.consumer.join()


@cli.command()
@click.option('--key', '-i')
@click.option('--prefer-public-ip', '-p', is_flag=True, default=False)
@click.option('--parallel', is_flag=True, default=False)
@click.argument('query')
@click.argument('ssh_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def ssh(ctx, key, prefer_public_ip, query, ssh_args, parallel):
    get_ip = public_ip if prefer_public_ip else private_ip
    fmt_match = extended_public if prefer_public_ip else extended_private

    matches = match_instances(ctx.obj['region'], query)
    if not matches:
        die('No matches found')

    if len(matches) > 1:
        click.echo('[0] All')
        for i, inst in enumerate(matches):
            click.echo('[{}] {}'.format(i+1, fmt_match(inst)))
        click.echo('pick an option [0-{}] '.format(len(matches)), nl=False)
        indices = read_numbers(0, len(matches))
        if len(indices) == 1 and indices[0] == 0:
            choices = matches
        else:
            choices = [matches[index - 1] for index in indices]
        click.echo()
    else:
        choices = [matches[0]]

    command = ['ssh', '-oStrictHostKeyChecking=no']
    if key:
        command.extend(['-i', key])

    if parallel and len(choices) > 1:
        message = 'sshing {}'.format([fmt_match(c) for c in choices])
        click.echo(message)
        click.echo()
        processes = []
        for choice in choices:
            ip = get_ip(choice)
            p = subprocess.Popen(command + [ip] + list(ssh_args),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            stdout_consumer = OutputConsumer(out_read=p.stdout, out_write=sys.stdout, prefix=ip)
            stderr_consumer = OutputConsumer(out_read=p.stderr, out_write=sys.stderr, prefix=ip)
            processes.append({'out': stdout_consumer, 'err': stderr_consumer, 'p': p})
        for p in processes:
            p['p'].wait()
            p['out'].join()
            p['err'].join()
    else:
        for choice in choices:
            message = 'sshing {}'.format(fmt_match(choice))
            click.echo()
            click.echo(message)
            click.echo('-' * len(message))
            subprocess.call(command + [get_ip(choice)] + list(ssh_args))


@cli.command()
@click.argument('query')
@click.option('--delim', '-d', default='\n')
@click.option('--formatter', '-f', default='extended_private')
@click.option('--custom-format', '-c', is_flag=True, default=False)
@click.pass_context
def ls(ctx, query, formatter, delim, custom_format):
    matches = match_instances(ctx.obj['region'], query)
    if not custom_format:
        formatter = formatter.join('{}')
    if not matches:
        die('No matches found')

    click.echo(delim.join(formatter.format(**{k: f(m) for k, f in formatters.iteritems()}) for m in matches))


if __name__ == '__main__':
    cli()
