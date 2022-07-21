from os import stat
import numpy as np
from collections import defaultdict

class QLearning:

    # DEFINING THE ENVIRONMENT
    def __init__(self, env):

        # Q-Learning parameters: discounting factor (gamma), learning rate (alpha) and randomness (epsilon)
        self.gamma=0.75
        self.alpha=0.9
        self.epsilon=0.5

        # Object for enviroment manipolation 
        self.env = env

        # Create an epsilon greedy policy function appropriately for environment action space
        self.policy = self.createEpsilonGreedyPolicy()

        # Action value function: state -> (action -> action-value).
        self.Q = defaultdict(lambda : np.zeros(self.env.getNumOfActions(self.state)))

        # Initial state
        self.state=0


    # Creates an epsilon-greedy policy based a given Q-function and epsilon
    # Returns a function that takes the state as an input and returns the probabilities for each action in the set of possible actions.
    def createEpsilonGreedyPolicy(self):
        
        def policyFunction(state):
            #print("\nQ[{}]={}".format(state,self.Q[state]))
            action_probabilities = np.ones(len(self.Q[state]), dtype = float) * self.epsilon / len(self.env.actions[state])
            best_action = np.argmax(self.Q[state])
            action_probabilities[best_action] += (1.0 - self.epsilon)
            return action_probabilities
        
        return policyFunction

    # Off-policy TD control: finds the optimal greedy policy while improving following an epsilon-greedy policy
    def qLearning(self, max_actions):

        # Variables
        count_actions = 0
        count_state_actions = 0
        count_reset_state = 0
        done = False
        exit = False

        while count_actions != max_actions and not exit:
            
            # Get probabilities of all actions from current state
            action_probabilities = self.policy(self.state)

            # Choose action according to the probability distribution, except for the first action in a new state
            action = np.random.choice(np.arange(
                len(action_probabilities)),
                p = action_probabilities
            )

            # Take action and get reward, transit to next state
            old_state = self.state
            self.state, reward, done = self.env.doAction(self.state, action)

            # TD Update
            best_next_action = np.argmax(self.Q[self.state])	
            td_target = reward + self.gamma * self.Q[self.state][best_next_action]
            td_delta = td_target - self.Q[old_state][action]
            self.Q[old_state][action] += self.alpha * td_delta
            
            # Exploited
            if done:
                exit = True

            # Update counters
            count_actions += 1
            count_state_actions += 1
            if old_state != self.state:
                count_state_actions = 0
                count_reset_state = 0
                continue

            # Resets state after n_actions[state]*(2**attemps)
            if count_state_actions == len(self.env.actions[self.state])*(2**count_reset_state):
                print("\n[!] Reset payload after {} attemps".format(count_state_actions))
                self.env.resetPayload(self.state)
                count_state_actions = 0
                count_reset_state += 1
            
            # Go back after 2*n_actions[state] reset
            if count_reset_state == 2*len(self.env.actions[self.state]):
                print("\n[!] Go back after {} reset".format(count_reset_state))
                self.state, exit = self.env.goBack(self.state)
                count_reset_state = 0

        if done:
            return "\n[+] exploited, payload: {}".format(self.env.xssExploit.payload())
        else:
            return "\n[-] not exploited"