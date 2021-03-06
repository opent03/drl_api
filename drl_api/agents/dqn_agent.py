import numpy as np

from drl_api.agents import Agent
from drl_api.memory import ReplayMemory
import drl_api.utils as utils

class DQN_agent(Agent):
    '''Base class for a DQN agent. Uses target networks and experience replay.'''

    def __init__(self,
                 target_update,
                 batch_size,
                 learn_frequency=4,     # learn something every 4 steps
                 *args,
                 **kwargs
                 ):

        super().__init__(*args,**kwargs)

        # Training data
        self.batch_size = batch_size

        self.target_update = target_update    # Period at which target network is updated
        self.learn_frequency = learn_frequency

        # Logging data
        self.scores = []
        self.avg_scores = []
        self.eps_history = []
        # initialize neural networks
        self.model.init_networks()

        self.max_avg_score = 0


    def train_step(self, render=False):
        '''Sample a 1-episode trajectory and learn simultaneously'''
        score = 0
        obs = self._format_img(self.env_train.reset())
        done = False
        self.model.done = False
        while not done:
            if render:
                self.env_train.render()

            # get action
            action = self.act_train(obs)

            # run action
            obs_, reward, done, info = self.env_train.step(action)
            obs_ = self._format_img(obs_)

            # save score
            score += reward

            # store transition in replay buffer
            self.model.store_transition(obs, action, reward, obs_, done)

            # learn something
            if self.model.get_counter() > self.batch_size and self.agent_step % self.learn_frequency == 0:
                # feed in a random batch
                random_batch = self.model.sample(batch_size=self.batch_size)
                # s, a, r, s_, t = self.feed_dict(random_batch)
                # self.learn(s=s, a=a, r=r, s_=s_, t=t)
                self.learn(random_batch)
            obs = obs_

            # update agent step counter
            self.agent_step += 1

            # update target network
            if self.agent_step % self.target_update == 0:
                self.model.replace_target_network()
                print('Step {}: Target Q-Net replaced!'.format(self.agent_step))

        self.model.done = True
        return score


    def eval_step(self, rounds=10, render=False):
        ''' evaluate model over # rounds, if best then save '''
        avg_score = self.play(rounds=rounds)
        if  avg_score > self.max_avg_score:
            self.max_avg_score = avg_score
            utils.save.save_model(self.model.Q_eval, 'drl_api/saves', self.env_name, self.model.name)
            print('Best score achieved, parameters are saved!')
        print('Evaluation ended. Average score achieved: {}. Best average scores: {}'.format(avg_score, self.max_avg_score))


    def learn(self, *args, **kwargs):
        '''agent learns, determined by agent's model'''
        self.model.learn(*args, **kwargs)


    def act_train(self, state):
        '''Choose an action at training time'''
        if np.random.random() > self.model.eps.get_eps():
            action = self.model.get_action(np.expand_dims(state, axis=0)) #
        else:
            action = np.random.choice(self.model.n_actions)

        return action


    def act_eval(self, state):
        ''' Choose an action at evaluation time '''
        if np.random.uniform(0,1,1) > self.model.eps.get_min_eps():
            action = self.model.get_action(np.expand_dims(state, axis=0))  #
        else:
            action = np.random.choice(self.model.n_actions)
        return action


    def get_env_specs(self, stack_frames):
        ''' gets env_train parameters '''
        n_actions = self.env_train.action_space.n
        obs_shape = self.env_train.observation_space.shape
        obs_shape = list(obs_shape)

        if len(obs_shape) == 3:
            assert stack_frames > 1
            obs_dtype = np.uint8
            obs_len = stack_frames
        else:
            obs_dtype = np.float32
            obs_len = 1

        return obs_shape, obs_dtype, obs_len, n_actions

    def load_save(self, *args, **kwargs):
        self.model.load_save(*args, **kwargs)

    def train(self, episodes, *args, **kwargs):
        self.eval_scores = []
        for episode in range(episodes):
            self.eps_history.append(self.model.eps.get_eps_no_decay())

            score = self.train_step(*args, **kwargs)
            self.scores.append(score)
            avg_score = np.mean(self.scores[-100:])
            self.avg_scores.append(avg_score)

            # evaluate every 100 steps
            if episode % 50 == 0:
                self.eval_step(render=False)
            fmt = 'episode {}, score {:.2f}, avg_score {:.2f}, eps {:.3f}, eval_score {:.2f}'
            print(fmt.format(episode+1,
                             score,
                             avg_score,
                             self.model.eps.get_eps_no_decay(),0))
        with open('drl_api/logs/{}-{}.log'.format(self.env_name, self.model.name), 'w+') as f:
            self.avg_scores = np.array(self.avg_scores)
            np.save(self.avg_scores)
            f.close()