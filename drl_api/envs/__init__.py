from drl_api.envs.atari import wrap_deepmind_atari
from drl_api.envs.linear_agent import LinearMDP
from drl_api.envs.riverswim import RiverSwim
import numpy as np
import bsuite
import gym
from bsuite.utils import gym_wrapper

gym_envs = [env_specs.id for env_specs in gym.envs.registry.all()]

def get_env_specs(env, stack_frames):
    ''' gets env parameters '''
    n_actions = env.action_space.n
    obs_shape = env.observation_space.shape
    obs_shape = list(obs_shape)

    if len(obs_shape) == 3:             # atari
        assert stack_frames > 1
        obs_dtype = np.uint8
        obs_len = stack_frames
        in_dims = obs_shape[2]
    else:                               # bsuite
        obs_dtype = np.float32
        obs_len = 1
        in_dims = int(obs_shape[0] * obs_shape[1])

    print('obs_shape: {}\nobs_dtype: {}\nobs_len: {}\nn_actions:{}'.format(obs_shape, obs_dtype, obs_len, n_actions))
    return {'obs_shape': obs_shape,
            'obs_dtype': obs_dtype,
            'obs_len': obs_len,
            'n_actions': n_actions,
            'in_dims': in_dims}


def get_linear_specs(lin_env):
    ''' get params of the linear environment '''
    return {'n_states': lin_env.n_states, 'n_actions': lin_env.n_actions}


def make_env(env_id, stack):
    #    # atari env
    if env_id in gym_envs:
        return wrap_deepmind_atari(env_id, stack)

    else: # bsuite env
        env = bsuite.load_from_id(env_id)
        env = gym_wrapper.GymFromDMEnv(env)

        return {'env_train': env, 'env_eval': env}

