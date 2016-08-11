import click
from .engine import ENGINE
from .schema import METADATA
from .prepare_data import assertions_to_sql_csv, load_sql_csv


@click.group()
def cli():
    pass


@cli.command(name='create')
def create_tables():
    METADATA.drop_all(ENGINE)
    METADATA.create_all(ENGINE)


@cli.command(name='prepare_data')
@click.argument('input_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_nodes', type=click.Path(writable=True, dir_okay=False))
@click.argument('output_edges', type=click.Path(writable=True, dir_okay=False))
@click.argument('output_sources', type=click.Path(writable=True, dir_okay=False))
@click.argument('output_prefixes', type=click.Path(writable=True, dir_okay=False))
def prepare_data(input_filename, output_nodes, output_edges, output_sources, output_prefixes):
    assertions_to_sql_csv(input_filename, output_nodes, output_edges, output_sources, output_prefixes)


@cli.command(name='load_data')
@click.argument('input_nodes', type=click.Path(readable=True, dir_okay=False))
@click.argument('input_edges', type=click.Path(readable=True, dir_okay=False))
@click.argument('input_sources', type=click.Path(readable=True, dir_okay=False))
@click.argument('input_prefixes', type=click.Path(readable=True, dir_okay=False))
def load_data(input_nodes, input_edges, input_sources, input_prefixes):
    load_sql_csv(ENGINE, input_nodes, input_edges, input_sources, input_prefixes)
