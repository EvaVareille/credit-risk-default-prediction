# Cleaning Log

Every cleaning decision, why it was made, and how many rows/columns it affected.

| # | Date | Step | Decision | Reason | Rows / columns affected |
|---|---|---|---|---|---|
| 1 | | Column names | Lower-cased, snake_case | Consistency across Python and SQL | All columns |
| 2 | | `int_rate`, `revol_util` | Stripped `%`, cast to float | Stored as text in the raw file | 2 columns |
| 3 | | `emp_length` | Mapped to years ('< 1 year' = 0, '10+ years' = 10) | Make it numeric | 1 column |
| 4 | | Target | Kept only loans with a final outcome | Running loans have no known outcome | TODO |
