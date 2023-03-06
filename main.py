import numpy as np
import pandas as pd
import math

rfr = .04 # picking an arbitrary risk-free rate

def dcf(cashflows, rate=rfr + 0.06):
    """Take a list of tuples where the first element is the cash flow and the
    second is the year it arrives, and an interest rate. Return the present
    value of those cash flows at that interest rate."""
    return(sum([cf[0] / (1 + rate) ** cf[1] for cf in cashflows]))

def generate_company(equity = 10,
                     target_leverage = 2,
                     reinvest_rate = 0.5):
    """Generate a company as a dictionary object. The company has the following
    traits:
    - Equity: an arbitrary fixed amount (doesn't change the math if we think of
    it as a $10 stock or a company with a book value of $10bn).
    - Target Leverage, expressed as assets as a % of equity. The company targets 
    this level of leverage, and will borrow more when it's below and will spend 
    profits on paying down debt if it's above the leverage target.
    - Debt: We generate the initial number based on the target leverage, but it
    will be updated each simulated year.
    - Reinvestment rate: what % of profits get reinvested at target leverage. 
    The remaining profits are paid as a dividend.
    - Cash flows: a list of tuples where each tuple represents cash flows to 
    investors (i.e. dividends, not total profits) and the year in which they 
    were received.
    """
    debt = equity * target_leverage - equity
    return {'equity':equity,
            'target_leverage':target_leverage,
            'debt':debt,
            'reinvest_rate':reinvest_rate,
            'cfs':[]}

def gen_profit(company, profit_bump = 0.0):
    """
    Generate one year of simulated profits for a company.

    We start by generating a return on assets, then we factor in debt cost.

    We also include a "profit bump" factor so we can tweak estimated profits to
    get to a breakeven DCF.
    """
    roa = np.random.choice([.3, .2, -.1, -.3],
                           1,
                           [.3, .3, .25, .05]) + profit_bump
    ebit = roa * (company['equity'] + company['debt'])
    net_profit = ebit - (debt_cost(company) * company['debt'])
    return net_profit

def debt_cost(company):
    """
    Estimate an interest rate by assuming that the best borrowers pay 50 bps above
    the risk-free rate and that for every half-turn of leverage they pay 1 point
    more.

    We assume that if the company has negative debt, it earns the risk-free rate 
    on its cash.
    """
    actual_leverage = (company['debt'] + company['equity']) / company['equity']
    if actual_leverage >= 0:
        return rfr + 0.005 + math.floor(actual_leverage * 2) * 0.01
    else:
        return rfr

def generate_company_cfs(company, profit_bump):
    """Generate a series of simulated cash flows for the company, and return a 
    dictionary object with the same company traits and the cash flows. This 
    process continues until the equity is zero.

    We generate randomize profits, then either use them to pay down debt (if
    the company has more leverage than its target) or split the money into a 
    reinvested amount that increases equity (and then the company levers up) and
    a dividend that gets appended to investors' cash flows.
    """
    year = 0
    while company['equity'] >= 0 and year <= 50:
        year += 1
        profit = gen_profit(company, profit_bump)
        actual_leverage = (company['debt'] + company['equity']) / company['equity']
        if profit >= 0:
            if actual_leverage >= company['target_leverage']:
                company['debt'] -= profit
                company['equity'] += profit
                company['cfs'].append([0,year])
            else:
                dividend = profit * (1 - company['reinvest_rate'])
                retained = profit * company['reinvest_rate']
                company['equity'] += retained
                company['debt'] = company['equity'] * company['target_leverage'] - company['equity']
                company['cfs'].append([dividend, year])
        else:
            company['equity'] += profit
            company['cfs'].append([0,year])
    return company

def simulate(rate,
             target_leverage,
             reinvest_rate,
             trials = 1000,
             profit_bump = 0.065): # profit bump estimated through trial and error
    """Runs a series of simulations of company values based on the variable inputs"""
    outcomes = []
    for _ in range(trials):
        co = generate_company_cfs(generate_company(10,
                                                   target_leverage,
                                                   reinvest_rate),
                                  profit_bump)
        outcomes.append(dcf(co['cfs'], rate))
    return outcomes

def deciles(outcomes):
    """Reports characteristics of the DCFs created by the simulation"""
    trials_series = pd.Series(outcomes)
    deciles = np.arange(0.1, 1.0, 0.1)
    result = trials_series.quantile(deciles)
    print(result)
    print("Mean: " + str(np.mean(trials_series)))
          

def test_profit_bump(rate,
                     target_leverage,
                     reinvest_rate,
                     trials = 1000,
                     profit_bump = 0.0):
    """Helper function to figure out how much to tweak up ROA estimates."""
    outcomes = simulate(rate,
                        target_leverage,
                        reinvest_rate,
                        trials = 1000,
                        profit_bump = profit_bump)
    deciles(outcomes)

def test_leverage(rate = 0.095,
                  reinvest_rate = 0.5,
                  levels = [x / 2 for x in list(range(-1, 10))]):
    """Ugly function here but we're testing half-turn leverage multiples from 
    -0.5 (half the balance sheet in cash) to 5x"""
    for i in levels:
        deciles(simulate(target_leverage = i))

## TODO

## Test varying rate, target leverage, reinvest rate
