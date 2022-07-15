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

        # Action value function: state -> (action -> action-value).TODO dimensione in basa alle azioni per stato
        self.Q = defaultdict(lambda: np.zeros(self.env.n_actions))

        # Create an epsilon greedy policy function appropriately for environment action space
        self.policy = self.createEpsilonGreedyPolicy()

        # Initial state
        self.state=0

    # Creates an epsilon-greedy policy based a given Q-function and epsilon
    # Returns a function that takes the state as an input and returns the probabilities for each action in the set of possible actions.
    def createEpsilonGreedyPolicy(self):
        
        def policyFunction(state):
            action_probabilities = np.ones(len(self.env.actions[state]), dtype = float) * self.epsilon / len(self.env.actions[state])
            best_action = np.argmax(self.Q[state])
            action_probabilities[best_action] += (1.0 - self.epsilon)
            return action_probabilities
        
        return policyFunction

    # Off-policy TD control: finds the optimal greedy policy while improving following an epsilon-greedy policy
    def qLearning(self, max_actions):

        # Variables
        count_actions = 0
        count_actions_for_state = 0
        done = False

        while count_actions != max_actions and not done:

            # Get probabilities of all actions from current state
            action_probabilities = self.policy(self.state)

            # Choose action according to the probability distribution, except for the first action in a new state
            action = 0
            if count_actions_for_state != 0:
                action = np.random.choice(np.arange(
                    len(action_probabilities)),
                    p = action_probabilities
                )

            # Take action and get reward, transit to next state
            next_state, reward, done = self.env.doAction(self.state, action)
            
            # TD Update
            best_next_action = np.argmax(self.Q[next_state])	
            td_target = reward + self.gamma * self.Q[next_state][best_next_action]
            td_delta = td_target - self.Q[self.state][action]
            self.Q[self.state][action] += self.alpha * td_delta

            # Update counters
            count_actions += 1
            count_actions_for_state += 1

            # Updates the counter if the status changes and go back after 15 attemps
            if self.state != next_state:
                self.state = next_state
                count_actions_for_state = 0
            elif count_actions == 15:
                self.state -= 1
                count_actions_for_state = 0

        if done:
            return "\n[+] exploited, payload: {}".format(self.env.payload)
        else:
            return "\n[-] terminated attempts"