import click

@click.command()
@click.option(
    "--model",
    default="gemini-2.5-flash",
    show_default=True,
    help="LLm model to use in the coding agent",
)

def main(model:str) -> None:
    """ A coding agent built from scratch """
    click.echo(f"Maverick has been initialized. (Model is {model})")
    

if __name__ == "__main__":
    main()
