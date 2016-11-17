import click
from .connection import get_db_connection
from .prepare_data import assertions_to_sql_csv, load_sql_csv
from .schema import create_tables, create_indices


@click.group()
def cli():
    pass


@cli.command(name='prepare_data')
@click.argument('input_filename', type=click.Path(readable=True, dir_okay=False))
@click.argument('output_dir', type=click.Path(writable=True, dir_okay=True, file_okay=False))
def prepare_data(input_filename, output_dir):
    assertions_to_sql_csv(input_filename, output_dir)


@cli.command(name='load_data')
@click.argument('input_dir', type=click.Path(readable=True, writable=True, dir_okay=True, file_okay=False))
def load_data(input_dir):
    conn = get_db_connection(building=True)
    create_tables(conn)
    load_sql_csv(conn, input_dir)
    create_indices(conn)
