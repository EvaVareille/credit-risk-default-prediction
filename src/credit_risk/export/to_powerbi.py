"""Write star-schema tables (fact_loans, dim_*) to data/processed/ for Power BI,
and small aggregates to app/data/ for the Streamlit app."""


def run() -> None:
    """Pipeline entry point."""
    raise NotImplementedError("to_powerbi.run: build the star schema from sql/schema/")
