import numpy as np
import math
import uuid
import random
from typing import *

# Helper Functions
def calculate_raised_capital(sys_param):
    """
    Calculate the overall raised capital from the initial investors.
    """

    raised_capital = []
    # get max length of possible raised_capital parameters
    max_length = max([len(sys_param[key]) for key in sys_param if "_raised" in key])
    # calculate the raised capital for all possible parameter list combinations in sys_param where "_raised" is in the key
    for i in range(max_length):
        raised_capital.append(sum([sys_param[key][i] if ("_raised" in key) and (i < len(sys_param[key])) else sys_param[key][-1] if ("_raised" in key) else 0 for key in sys_param]))
    print(raised_capital)
    return raised_capital

# Initialization
def new_agent(stakeholder_type: str, usd_funds: int,
              tokens: int, action_list: list, action_weights: Tuple,
              current_action: str) -> dict:
    """
    Function to create a new agent aka stakeholder for the token ecosystem.
    """

    agent = {'type': stakeholder_type,
             'usd_funds': usd_funds,
             'tokens': tokens,
             'tokens_vested': 0,
             'tokens_locked': 0,
             'action_list': action_list,
             'action_weights': action_weights,
             'current_action': current_action}
    return agent

def initialize_agent_parameters(stakeholder_names):
    """
    Initialize all token ecosystem agent parameters.
    """
    initial_stakeholder_values = {}
    for stakeholder in stakeholder_names:
        initial_stakeholder_values[uuid.uuid4()] = {
            'type': stakeholder,
            'initial_usd_funds': 0,
            'initial_tokens': 0,
            'initial_tokens_vested': 0,
            'initial_tokens_locked': 0,
            'action_list': [],
            'action_weights': [],
            'current_action': 'hold'
        }
    
    return initial_stakeholder_values

def generate_agents(initial_stakeholder_values):
    """
    Initialize all token ecosystem agents aka stakeholders.
    """
    initial_agents = {}
    for a in initial_stakeholder_values:
        initial_agents[a] = new_agent(initial_stakeholder_values[a]['type'],
                                    initial_stakeholder_values[a]['initial_usd_funds'],
                                    initial_stakeholder_values[a]['initial_tokens'],
                                    initial_stakeholder_values[a]['action_list'],
                                    initial_stakeholder_values[a]['action_weights'],
                                    initial_stakeholder_values[a]['current_action'])
    return initial_agents

def create_parameter_list(parameter_name, not_iterable_parameters, init_value, min, max, intervals):
    """
    Create list of parameters for parameter sweep based on the QTM input tab 'cadCAD_inputs'.
    """

    if parameter_name in not_iterable_parameters:
        return [init_value.replace(",","").replace("%","")]
    else:
        try:
            if type(init_value) == str:
                init_value = float(init_value.replace(",","").replace("%",""))
            if type(min) == str:
                min = float(min.replace(",","").replace("%",""))
            if type(max) == str:
                max = float(max.replace(",","").replace("%",""))
            if type(intervals) == str and intervals != '':
                intervals = int(float(intervals.replace(",","")).replace("%",""))
        except ValueError:
            return [init_value]
        if math.isnan(min) or math.isnan(max) or math.isnan(intervals) or max<=min:
            if max<=min:
                print("Maximum parameter boundary is lower than minimum parameter boundary: Min: ", min, "; Max:", max, ". Using initial value ", init_value, " instead.")
            return [float(init_value)]
        else:
            if math.isnan(intervals):
                return [float(init_value)]
            else:
                return list(np.linspace(min, max, int(intervals)))

def compose_initial_parameters(QTM_inputs, not_iterable_parameters):
    """
    Compose all initial parameter sets from the Quantitative Token Model inputs tab 'cadCAD_inputs'.
    """

    initial_parameters = {}
    for index, row in QTM_inputs.iterrows():
        parameter_name = row['Parameter Name'].lower().replace(' ', '_').replace('/', '').replace('(', '').replace(')', '')
        initial_parameters[parameter_name] = create_parameter_list(parameter_name, not_iterable_parameters, row['Initial Value'], row['Min'], row['Max'], row['Interval Steps'])
    return initial_parameters

def calculate_investor_allocation(sys_param, stakeholder_name):
    """
    Calculate the initial token allocation of a specific stakeholder considering bonus amounts.
    """
    token_launch_price = [x / y for x in sys_param["public_sale_valuation"] for y in sys_param["initial_total_supply"]]
    effective_token_price = [np.min([x / (1+y/100), z / a]) for x in token_launch_price for y in sys_param[stakeholder_name+"_bonus"] for z in sys_param[stakeholder_name+"_valuation"] for a in sys_param["initial_total_supply"] for a in sys_param["initial_total_supply"]]
    tokens = [x / y for x in sys_param[stakeholder_name+"_raised"] for y in effective_token_price]
    allocation = [x / y for x in tokens for y in sys_param['initial_total_supply']]
    
    return allocation

def calc_initial_lp_tokens(agent_token_allocations, sys_param):
    """
    Calculate the amount of tokens initially allocated to the DEX liquidity pool.
    """

    allocation_sum = []
    # get max length of possible raised_capital parameters
    max_length = max([len(agent_token_allocations[key]) for key in agent_token_allocations])
    # calculate the raised capital for all possible parameter list combinations in sys_param where "_raised" is in the key
    for i in range(max_length):
        allocation_sum.append(sum([agent_token_allocations[key][i] if (i < len(agent_token_allocations[key])) else agent_token_allocations[key][-1] for key in agent_token_allocations]))
    
    lp_token_allocation = [(1 - x) * y for x in allocation_sum for y in sys_param['initial_total_supply']]

    return lp_token_allocation


def seed_dex_liquidity(agent_token_allocation, initial_stakeholders, funding_bucket_name, sys_param):

    sum_of_raised_capital = calculate_raised_capital(sys_param)

    if required_usdc > sum_of_raised_capital:
        raise ValueError('The required funds to seed the DEX liquidity are '+str(required_usdc)+' and higher than the sum of raised capital '+str(sum_of_raised_capital)+'!')
    else:
        # subtract the required funds from the funding bucket.
        found_stakeholder = False
        for stakeholder in initial_stakeholders:
            if initial_stakeholders[stakeholder]['type'] == funding_bucket_name:
                initial_stakeholders[stakeholder]['initial_usd_funds'] -= required_usdc
                if initial_stakeholders[stakeholder]['initial_usd_funds'] < 0:
                    raise ValueError("The stakeholder "+funding_bucket_name+" has only $"+str(initial_stakeholders[stakeholder]['initial_usd_funds']+required_usdc)+" funds, but $"+str(required_usdc)+" are required for seeding the DEX liquidity pool!")
                found_stakeholder = True
        
        if not found_stakeholder:
            raise ValueError("The DEX liquidity couldn't be funded as there is no stakeholder with name: "+funding_bucket_name)
    
    liquidity_pool = {
        'tokens' : lp_token_allocation,
        'usdc' : required_usdc,
        'constant_product' : lp_token_allocation * required_usdc,
        'token_price' : required_usdc / lp_token_allocation
    }

    return liquidity_pool

def generate_initial_token_economy_metrics(initial_stakeholders, initial_liquidity_pool, sys_param):
    """
    Calculate the initial token economy metrics, such as MC, FDV MC, circ. supply, and tokens locked.
    """

    initial_circulating_tokens = 0
    initial_locked_tokens = 0

    for stakeholder in initial_stakeholders:
        initial_circulating_tokens += initial_stakeholders[stakeholder]['tokens']
        initial_locked_tokens += initial_stakeholders[stakeholder]['tokens_locked']
    
    initial_MC = initial_liquidity_pool['token_price'] * initial_circulating_tokens
    initial_FDV_MC = initial_liquidity_pool['token_price'] * sys_param['initial_total_supply']

    token_economy = {
        'total_supply' : sys_param['initial_total_supply'],
        'circulating_supply' : initial_circulating_tokens,
        'MC' : initial_MC,
        'FDV_MC' : initial_FDV_MC,
        'tokens_locked' : initial_locked_tokens
    }

    return token_economy

