from utils import floorf


class PaymentCalculator:
    def __init__(self, founders_map, owners_map, reward_list, total_rewards, service_fee_calculator, cycle):
        self.owners_map = owners_map
        self.total_rewards = total_rewards
        self.cycle = cycle
        self.fee_calc = service_fee_calculator
        self.reward_list = reward_list
        self.founders_map = founders_map
        self.total_service_fee = 0

    #
    # calculation details
    #
    # total reward = delegators reward + owners reward = delegators payment + delegators fee + owners payment
    # delegators reward = delegators payment + delegators fee
    # owners reward = owners payment = total reward - delegators reward
    # founders reward = delegators fee = total reward - delegators reward
    ####
    def calculate(self):
        pymnts = []

        # 1- calculate delegators payments
        delegators_total_pymnt = 0
        delegators_total_ratio = 0
        delegators_total_fee = 0
        for reward_item in self.reward_list:
            reward = reward_item['reward']
            ktAddress = reward_item['address']
            ratio = reward_item['ratio']

            pymnt_amnt = floorf(reward * (1 - self.fee_calc.calculate(ktAddress)), 3)

            # this indicates, service fee is very low (e.g. 0) and pymnt_amnt is rounded up
            if pymnt_amnt - reward > 0:
                pymnt_amnt = reward

            fee = (reward - pymnt_amnt)

            pymnts.append({'payment': pymnt_amnt, 'fee': fee, 'reward': reward, 'address': ktAddress, 'ratio': ratio,
                           'cycle': self.cycle, 'type': 'D'})

            delegators_total_pymnt = delegators_total_pymnt + pymnt_amnt
            delegators_total_ratio = delegators_total_ratio + ratio
            delegators_total_fee = delegators_total_fee + fee

        # 2- calculate deposit owners payments. They share the remaining rewards according to their ratio (check config)
        owners_total_payment = 0
        owners_total_reward = self.total_rewards - (delegators_total_pymnt + delegators_total_fee)
        for address, ratio in self.owners_map.items():
            owner_pymnt_amnt = floorf(ratio * owners_total_reward, 3)
            owners_total_payment = owners_total_payment + owner_pymnt_amnt

            pymnts.append({'payment': owner_pymnt_amnt, 'fee': 0, 'address': address, 'cycle': self.cycle, 'type': 'O',
                           'ratio': ratio, 'reward': owner_pymnt_amnt})

        # move remaining rewards to service fee bucket
        self.total_service_fee = self.total_rewards - delegators_total_pymnt - owners_total_payment

        # 3- service fee is shared among founders according to founders_map ratios
        for address, ratio in self.founders_map.items():
            pymnt_amnt = floorf(ratio * self.total_service_fee, 6)

            pymnts.append(
                {'payment': pymnt_amnt, 'fee': 0, 'address': address, 'cycle': self.cycle, 'type': 'F', 'ratio': ratio,
                 'reward': 0})

        ###
        # sanity check
        #####
        total_sum = 0
        for payment in pymnts:
            total_sum = total_sum + payment['payment']

        # if there is a minor difference due to floor function; it is added to last payment
        if self.total_rewards - total_sum > 1e-6:
            last_payment = pymnts[-1]  # last payment, probably one of the founders
            last_payment['payment'] = last_payment['payment'] + (self.total_rewards - total_sum)

        # this must never return true
        if abs(total_sum - self.total_rewards) > 5e-6:
            raise Exception("Calculated reward {} is not equal total reward {}".format(total_sum, self.total_rewards))

        return pymnts
