import click


@click.command()
@click.option("--name", is_flag=False, flag_value="Flag", default="O.")
def main(name):
    """Cli interface for phototracks."""
    click.echo(f"Hello {name} from phototracks")


if __name__ == "__main__":
    main()
