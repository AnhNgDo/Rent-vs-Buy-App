# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 16:16:45 2021

Streamlit App compares financial outcomes Rent vs Buy

use cd command in terminal to move to current folder
use streamlit run <file> to start the app
use Ctrl + C to stop the app

@author: anhng
"""

from mortgage import Loan
from decimal import Decimal
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker
import math


def read_loan_inputs():
    """
    Read user inputs for Buying Home and return tuple of parameters

    """
    house_price = st.sidebar.number_input('House Price $:',
                                    min_value=300000,
                                    max_value=5000000,
                                    value=800000,
                                    step=10000)
    
    deposit_pct = st.sidebar.slider('Initial Deposit (% of House Price):',
                                    min_value=0,
                                    max_value=100,
                                    value=10)
    
    term = st.sidebar.slider('Home Loan Term (Years):',
                                    min_value=5,
                                    max_value=30,
                                    value=30)
    
    home_loan_rate = st.sidebar.number_input('Home Loan Rate (%):',
                                    min_value=1.0,
                                    max_value=10.0,
                                    value=2.79,
                                    step=0.01)
    
    home_loan_rate_daily_compound = math.pow((1 + home_loan_rate/100/365), 365) - 1
    
    return house_price, deposit_pct/100, term, home_loan_rate_daily_compound

    
def read_ownership_cost_input():
    """
    Read user inputs for Cost of Owning a Home and return tuple of parameters

    """
    strata_council_cost = st.sidebar.slider('Quaterly Strata, Council, Water rates $:', 
                                            min_value=0,
                                            max_value=10000,
                                            value=1500,
                                            step=100)
    
    home_insurance = st.sidebar.slider('Monthly Home Insurance $:', 
                                       min_value=0, 
                                       max_value=2000,
                                       value=60,
                                       step=10)
    
    transport_cost = st.sidebar.slider('Weekly Additional Transport Cost $ (e.g. new car):', 
                                       min_value=0, 
                                       max_value=1000,
                                       value=200,
                                       step=10)
    
    return strata_council_cost, home_insurance, transport_cost

def read_rent_inputs():
    """ 
    Read and return user input for weekly rental cost

    """
    weekly_rent = st.sidebar.slider('Weekly Rental Cost $:', 
                                    min_value=100,
                                    max_value=5000,
                                    value=690,
                                    step=10)
    
    return weekly_rent

def read_investment_inputs():
    """ 
    Read and return user input for weekly rental cost

    """
    property_return = st.sidebar.slider('House Prices annual return %:', 
                                        min_value=0, 
                                        max_value=20, 
                                        value=3,
                                        step=1) # max 20% pa, default 3% pa
    
    portfolio_return = st.sidebar.slider('Investment Portfolio annual return %:', 
                                        min_value=0, 
                                        max_value=20, 
                                        value=5,
                                        step=1) # max 20% pa, default 5 % pa
    
    return property_return / 100, portfolio_return / 100
    

def main():
    st.title('Rent vs Buy')
    st.write('This App compares financial outcomes between \
             **Buying House** and **Renting House** over the long term (50 years)')
    st.text('')  # empty line for spacing           
                 
    
    # default market rates
    inflation = 0.02
    rent_inflation = 0.03
    property_return = 0.03
    portfolio_return = 0.05
    
    # App parameters
    time_frame = 50 # compare outcomes over 50 years period
    max_rent = 100000 # max annual rent before moving place
    
    # read user inputs in sidebar   
    st.sidebar.header('Home Loan Details:')
    house_price, deposit_pct, term, home_loan_rate = read_loan_inputs()
    deposit_amt = house_price * deposit_pct
    home_loan = Loan(principal=house_price - deposit_amt, 
                     interest= home_loan_rate, term=term)
    
    st.sidebar.header('Home ownership expenses:')
    strata_council_cost, home_insurance, transport_cost = read_ownership_cost_input()
    maintenance_cost = 0.01 * house_price # Guideline: 1% of total house price for annual cost
    total_ownership_cost = maintenance_cost + strata_council_cost * 4 + home_insurance * 12 + transport_cost * 52
    
    st.sidebar.header('Home rental expenses:')
    weekly_rent = read_rent_inputs()
    
    change_default_investment_setting = st.sidebar.checkbox('Change default Investment Returns setting', value=False)
    if change_default_investment_setting:
        property_return, portfolio_return = read_investment_inputs()
        
    ##############################################
    # prepare data for visualisation
    ##############################################
    years = pd.Series(data=np.arange(time_frame+1))  # x-axis, timeline over home 50 years horizon
    
    cumulative_inflation = years.apply(lambda x: math.pow(1+inflation, x))
    cumulative_rent_inflation = years.apply(lambda x: math.pow(1+rent_inflation, x))
    
    loan_payments = pd.Series(data=np.zeros(time_frame+1))
    loan_payments.iloc[1 : term+1] = float(home_loan.monthly_payment * 12)
    loan_payments.iloc[0] = deposit_amt
    
    ownership_costs = pd.Series(data=np.zeros(time_frame+1))
    ownership_costs.iloc[1:] = total_ownership_cost
    ownership_costs.iloc[0] = 0 # initial cost of owning house is zero
    ownership_costs = ownership_costs * cumulative_inflation # adjusted for general inflation
    
    rent_costs = pd.Series(data=np.zeros(time_frame+1))
    rent_costs.iloc[1:] = weekly_rent * 52
    rent_costs.iloc[0] = 0
    rent_costs = rent_costs * cumulative_rent_inflation # adjusted for rent inflation
    rent_costs.loc[rent_costs > max_rent] = max_rent
    
    savings_rent_vs_buy = ownership_costs + loan_payments - rent_costs
    
    yearly_property_returns = pd.Series(data=np.zeros(time_frame+1))
    yearly_property_returns[0] = 1 # zero return at the start of series
    yearly_property_returns[1:] = 1 + property_return # return factor = 1 + rate of return
    cumulative_property_return = yearly_property_returns.cumprod()
    
    yearly_portfolio_returns = pd.Series(data=np.zeros(time_frame+1))
    yearly_portfolio_returns[0] = 1 # zero return at the start of series
    yearly_portfolio_returns[1:] = 1 + portfolio_return # return factor = 1 + rate of return
    cumulative_portfolio_return = yearly_portfolio_returns.cumprod()
    
    balances = pd.Series(data=np.zeros(time_frame+1))
    for year in range(term):
        balance = float(home_loan.schedule(12*year + 1).balance)
        balances.iloc[year] = balance
    
    asset_values_owning = cumulative_property_return * house_price - balances
    
    asset_values_renting = pd.Series(data=np.zeros(time_frame+1))
    asset_value = 0 # initial asset value is zero
    for year in years:
        asset_value = (asset_value * (1+portfolio_return)) + savings_rent_vs_buy[year]
        asset_values_renting[year] = asset_value
    
    ################################################
    # plotting 
    ################################################
    bar_width = 0.5
    
    # plot cost of owning house & home loan balances
    fig1, axs1 = plt.subplots(nrows=1, ncols=2, figsize=(12, 4))
    # cost of owning house
    axs1[0].bar(x=years, height=ownership_costs, width=bar_width, label='Ownership Expenses')
    axs1[0].bar(x=years, height=loan_payments, width=bar_width, label='Loan Payments',  bottom=ownership_costs)
    axs1[0].set_title('Annual Expenses - Owning a House')
    axs1[0].legend(loc='best', fontsize='small')
    axs1[0].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    # home loan balances
    axs1[1].bar(x=years, height=balances, width=bar_width, label='Home Loan Balances')
    axs1[1].set_title('Home Loan Balances over Loan Term')
    axs1[1].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    
    
    # plot cost of renting house & expenses difference
    fig2, axs2 = plt.subplots(nrows=1, ncols=2, figsize=(12, 4))
    # plot cost of renting house
    axs2[0].bar(x=years, height=rent_costs, width=bar_width, label='Rental expenses')
    axs2[0].set_title('Annual Expenses - Renting a House')
    axs2[0].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    # plot expenses different
    axs2[1].bar(x=years, height = savings_rent_vs_buy, 
               width=bar_width, label='Expenses Difference - Renting vs Buying')
    axs2[1].set_title('Annual Expenses Differences - Renting vs Buying')
    axs2[1].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    
    # plot asset values owning house vs renting
    fig3, axs3 = plt.subplots(nrows=1, ncols=2, figsize=(12, 4))
    # plot asset values - owning house
    axs3[0].bar(x=years, height=asset_values_owning, width=bar_width, color='forestgreen')
    axs3[0].set_title('Total Assets - Owning House')
    axs3[0].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    # plot asset values - renting house and invest in investment portfolio
    axs3[1].bar(x=years, height=asset_values_renting, width=bar_width, color='teal')
    axs3[1].set_title('Total Assets - Renting House')
    axs3[1].get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
   
    ################################################
    # display cost of owning a house section
    ################################################
    st.header('Cost of Buying a House:')
    st.write('The main expenses from Owning a House are: \
             **Home Loan payments** (interest + principles) and \
                 **cost of living in the house** (maintenance, insurance, additional cars, etc.)')
    st.write('*Here are the summary of these costs:*')
    
    # Summarize home loan info
    loan_info = {'Initial Deposit': deposit_amt, 
                 'Initial Loan Amt': home_loan.principal,
                 'Weekly Payment': home_loan.monthly_payment*12/52,
                 'Total payments': float(home_loan.total_paid) + deposit_amt, 
                 'Total interest': home_loan.total_interest}
    
    loan_info_df = pd.DataFrame(loan_info, index=['Home loan'])
    st.dataframe(loan_info_df.style.format('${:,.0f}'))
    st.text('E.g.: 2 Bedroom Units in Western Sydney is approx $800,000 before Stamp Duty in 2021')
    
    st.text('') # spacing
    # Summarize home ownership expense info
    
    ownership_cost_info = {'Annual Cost (initial)': total_ownership_cost, 
                           'Weekly Cost (initial)': total_ownership_cost / 52 
                           }
    
    ownership_cost_df = pd.DataFrame(ownership_cost_info, index=['cost of living in the house'])
    st.dataframe(ownership_cost_df.style.format('${:,.0f}'))
    st.text('Note: includes home maintenance cost of 1% of house value per year (Guide line)')
    
    st.pyplot(fig1)
    st.text('Note: cost estimates based on long-term inflation of 3% pa')
    
    ################################################
    # display cost of renting a house section
    ################################################
    st.header('Cost of Renting a House:')
    st.write('Main expenses from Renting a House is **weekly rental** - which currently is ${:,.0f} or ${:,.0f} per year.'
             .format(weekly_rent,weekly_rent*52 ))
             
    years_with_savings = savings_rent_vs_buy[savings_rent_vs_buy > 0].index # years when rent expenses less than owning house
    st.write('* Renting can result in lower housing expenses for {} years'.format(years_with_savings[-1]))
 
    st.pyplot(fig2)
    st.text('Note: based on long-term inflation of 3% pa & max rent of ${:,} per Year (relocating required)'.format(max_rent))
    
    ################################################
    # display asset values comparison section
    ################################################
    st.header('Assets over time - Buying vs Renting:')
    st.write('* **Owning House**: Asset is the house itself - and any appreciatetion in values over time')
    st.write('* **Renting House**: Asset is the investment porfolio - made from any savings from renting instead of buying')
    st.write('* Over {} years term, the Wealth difference between Owning and Renting is ${:,.0f} '.format(
        time_frame, asset_values_owning.iloc[-1] - asset_values_renting.iloc[-1])) 
    
    st.pyplot(fig3)
    st.text('Base case: house price increases 3% pa, while overall market return is 5% pa.')
    
    # conclusion
    st.header('**In conclusion:**')
    st.write('Renting typically mean lower housing expenses in the medium term (20 years). However, over longer term,\
             Owning a House can result in better financial outcomes (more assets & lower housing expenses).')
    st.write('* This of course is based on assumption that house prices (and rents) continue to raise over the next {} years.'.format(time_frame))
    st.write('* There are also other non-financial outcomes to consider - E.g. flexibility of renting, stability of owning house, \
             quality of life differences (E.g. CBD vs Western Suburbs)')         
  
if __name__ == '__main__':
    main()
    