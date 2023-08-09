# POLICY FUNCTIONS
def transfer_agent_allocation(params, substep, state_history, prev_state, **kwargs):
    """
    Policy function to calculate the agent transfer
    """
    # get parameters
    transfer_share = params['transfer_share']/100

    # get state variables
    agents = prev_state['agents'].copy()

    # policy logic
    agent_utility_sum = 0
    agents_transfer_allocations = {}
    for agent in agents:
        utility_tokens = agents[agent]['a_utility_tokens']
        agents_transfer_allocations[agent] = utility_tokens * transfer_share
        agent_utility_sum += agents_transfer_allocations[agent]
    
    return {'transfer_allocation': agent_utility_sum, 'agents_transfer_allocations': agents_transfer_allocations}


# STATE UPDATE FUNCTIONS
def update_transfer_agent_allocation(params, substep, state_history, prev_state, policy_input, **kwargs):
    """
    Function to update agent transfer allocations
    """
    # get parameters

    # get state variables
    updated_agents = prev_state['agents'].copy()

    # get policy input
    agents_transfer_allocations = policy_input['agents_transfer_allocations']

    # update logic
    for agent in updated_agents:
        updated_agents[agent]['a_tokens_transferred'] = agents_transfer_allocations[agent]
        updated_agents[agent]['a_tokens_transferred_cum'] += agents_transfer_allocations[agent]

    return ('agents', updated_agents)

def update_transfer_meta_allocation(params, substep, state_history, prev_state, policy_input, **kwargs):
    """
    Function to update meta transfer allocations
    """
    # get parameters

    # get state variables
    updated_utilities = prev_state['utilities'].copy()

    # get policy input
    transfer_allocation = policy_input['transfer_allocation']

    # update logic
    updated_utilities['transfer_allocation'] = transfer_allocation
    updated_utilities['transfer_allocation_cum'] += transfer_allocation

    return ('utilities', updated_utilities)