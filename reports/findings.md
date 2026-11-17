# Key Findings

Plain-English summary of what the analysis shows, with the "so what" for a lender.

**What was analysed.** 383,782 three-year (36-month) loans to individual borrowers, issued January 2013 to June 2015. 13.8% of them defaulted (ended as Charged Off or Default). The final test period (July to December 2015) was left untouched. The 36 vs 60 month comparison reads the raw data instead, because the modelling table holds only 36-month loans. The charts are in `reports/figures/` and the code is in `notebooks/02_eda.ipynb`. These findings describe who defaulted, not why: none of them proves a cause.

## 1. The grade Lending Club gives a loan sorts risk very well

![Default rate by grade](figures/default_rate_by_grade.png)

Default rises step by step from 5.4% for grade A to 31.3% for grade F (grade G reaches 35.3% but has only 289 loans). A grade F loan is nearly six times as likely to default as a grade A loan.

**So what:** pricing by grade is justified by the data. It also means a model built without grade or interest rate, as the headline model here is, starts with much less information than Lending Club had, so a modest AUC is expected.

## 2. 60-month loans default about twice as often as 36-month loans

![Default rate by term](figures/default_rate_by_term.png)

For loans issued 2010 to 2013, when both terms have fully finished, 60-month loans defaulted 22% to 28% of the time against 11% to 14% for 36-month loans: a ratio of 2.0 to 2.2 in every year (2.0 in 2012 and 2013).

**So what:** a lender should charge much more for 60-month loans or approve fewer of them. It is also why the model uses 36-month loans only: later 60-month loans are still running, and their default rate is understated.

## 3. Defaults rose year on year, even as unemployment fell

![Default rate and unemployment by issue month](figures/default_rate_vs_unemployment.png)

The default rate of loans issued rose from 12.3% (2013) to 13.7% (2014) to 15.1% (first half of 2015), while average state unemployment fell from 7.6% to 5.6%. Loans of the same grade did worse too: grade C went from 15.3% to 19.0% and grade D from 20.4% to 26.0%. Across state and month, unemployment and default rate are unrelated (correlation 0.002).

**So what:** newer loans were riskier than their grade suggested, and the economy was not the cause. Lending standards or the mix of borrowers changed. A lender should track default by issue month and not assume last year's relationship still holds. A model trained on 2013 to 2014 may under-predict on later loans, so check its calibration on the test set.

## 4. Loan purpose matters: small business loans are the riskiest

![Default rate by purpose](figures/default_rate_by_purpose.png)

Small business loans default 23.0% of the time, twice the 11.6% for credit card refinancing. Debt consolidation is 58% of all loans, at 14.4%, close to the average.

**So what:** small business and moving loans (19.8%) deserve stricter terms. Credit card and home improvement loans are the safest sizeable groups.

## 5. Renters, lower earners and heavily indebted borrowers default more

![Default rate by decile of each numeric feature](figures/default_rate_by_decile.png)

- **Housing:** renters default 16.5% of the time, mortgage holders 11.2%.
- **Income:** the lowest-earning tenth of borrowers (about $27,000 a year) default 20.1% of the time, the highest tenth (about $150,000) 9.3%.
- **Debt-to-income:** 10.4% in the lowest tenth, 19.4% in the highest.
- **FICO score:** 18.6% in the lowest tenth against 5.9% in the highest. This is the strongest signal left once Lending Club's own grade and rate are set aside.
- **Revolving credit use:** 10.6% in the lowest tenth against 16.0% in the highest.

Defaulters have a lower median income ($54,000 against $62,000), a higher debt-to-income ratio (19.1% against 16.8%) and a higher interest rate (14.0% against 12.0%).

**So what:** these are the affordability and credit-history signals a lender would expect, and they point the right way. A borrower's income is better judged against the loan size than on its own, which is why the pipeline adds loan-to-income.

## 6. Borrowers who left employment length blank default far more often

![Default rate by borrower profile](figures/default_rate_by_borrower_profile.png)

5.8% of loans have no employment length. They defaulted 20.2% of the time against 13.4% for everyone else, and they did worse within every grade from A to F.

**So what:** a blank answer is itself a warning sign. The model keeps "missing" as its own value rather than filling it in. Separately, borrowers whose income Lending Club verified defaulted more (15.4%) than those it did not (11.9%). That probably reflects Lending Club asking for proof from riskier applicants, not that verification causes default.

## 7. Defaults differ by state, but less than by loan type

![Default rate by state](figures/default_rate_by_state.png)

Among the 46 states with at least 500 loans, default runs from 9.2% in New Hampshire to 18.4% in Mississippi.

**So what:** location is a usable signal, but state differences may reflect the borrowers in each state rather than the place itself. State is also a possible stand-in for protected characteristics, so it is checked in the fairness review in week 6.

## 8. No single feature predicts default strongly, and many features repeat each other

![Correlation matrix](figures/correlation_matrix.png)

The strongest single link with default is the interest rate (rank correlation 0.19), then FICO (-0.12) and income (-0.10). Nothing else is above 0.10. Many features are near copies: the FICO low, high and midpoint, `open_acc` and `num_sats`, `loan_amnt` and `installment`, and `tot_cur_bal` and `tot_hi_cred_lim` correlate above 0.98.

**So what:** the signal is spread across many weak features, which is why a target AUC of 0.68 without grade and rate is realistic. Drop one of each near-duplicate pair for the logistic regression baseline. Gradient boosting can cope with them.
