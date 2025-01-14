#!/usr/bin/env python
# coding: utf-8
import logging
import utils
from utils import *
import datetime
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("economic-test")
logger.setLevel(logging.INFO)
filename = "./logs/report_log_{}.log".format(datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S_%f'))
file_handler = logging.FileHandler(filename)
formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def E1_test(single):
    logger.info(f"Test-E1: A staked validator whose stake is in the top #slots stakes is always considered for election")
    try:
        committees = getCommittees()
        slot = committees['external-slot-count']
        block, last_block = getCurrentAndLastBlock()
        logger.info(f"current and last block numbers: {block}, {last_block}")
        if block == last_block:
            logger.info(f"current block is the last block in epoch, waiting for the new epoch...")
            new_block = block+1
            while block < new_block:
                block = getBlockNumber()
            block, last_block = getCurrentAndLastBlock()
            logger.info(f"current and last block numbers: {block}, {last_block}")
        logger.info(f"current block, {block}, begin collecting eligible validators...")
        # get top #slots nodes who are eligible to elected next epoch
        validator_infos = getAllValidatorInformation()
        eligible = []
        stake = dict()
        for i in validator_infos:
            if i['epos-status'] == 'currently elected' or i['epos-status'] == 'eligible to be elected next epoch':
                address = i['validator']['address']
                eligible.append(address)
                stake[address] = i['total-delegation']

        if len(eligible) > slot:
            sorted_stake = sorted(stake.items(), key=lambda kv: kv[1], reverse = True)
            eligible = [kv[0] for kv in sorted_stake[:slot]]

        # wait for epoch changes
        while block < last_block+1:
            block = getBlockNumber()
        logger.info(f"first block in new epoch reached, {block}, will wait for 5 seconds to begin testing...")
        time.sleep(5)
        # check whether the eligible validators are selected
        validator_infos = getAllValidatorInformation()
        flag = True
        for i in validator_infos:
            if i in eligible:  
                if i['epos-status'] != 'currently elected':
                    logger.warning(f"Test E1: Fail")
                    logger.warning(f"validator {i['validator']['address']} who is eligible to be elected is not elected\n")
                    flag = False
    except TypeError as e:
        logger.error(f"error: {e}")
    if single:
        curr_test = None
    else:
        curr_test = E2_test
    if flag:
        logger.info(f"Test E1: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test

def E2_test(single):
    logger.info(f"Test-E2: Joining after the election start must not consider the validator")
    if single:
        curr_test = None
    else:
        curr_test = E3_test
    flag = True
    num = 1
    iterations = 0
    new_count = 0
    try:
        while iterations < num:
            # get the last block in current epoch
            block, last_block = getCurrentAndLastBlock()
            logger.info(f"current and last block numbers: {block}, {last_block}")
            logger.info(f"wait for the last second block ...")
            while block < last_block - 1:
                block = getBlockNumber()
            logger.info(f"last second block in the current epoch reached {block} will begin collecting existing eligible validators after 5 seconds")
            time.sleep(5)
            eligible_old = getEligibleValidator()

            while block < last_block:
                block = getBlockNumber()
            logger.info(f"last block in the current epoch reached {block} will begin collecting new eligible validators after 5 seconds")
            time.sleep(5)
            eligible_current = getEligibleValidator()

            logger.info(f"checking whether we have validators who set their status active after election starts")
            eligible_new = set(eligible_current) - set(eligible_old)
            if not eligible_new:
                logger.info(f"no validator joined after the election start in current test")
            else:
                new_count += 1
                while block < last_block + 1:
                    block = getBlockNumber()
                logger.info(f"first block in the current epoch reached {block} will wait for 5 seconds to begin collecting elected infos")
                time.sleep(3)
                logger.info(f"begin checking validators who joined after the election was elected...")
                validators = getAllValidatorInformation()
                for i in validators:
                    if i['validator']['address'] in eligible_new:
                        if i['currently-in-committee']:
                            logger.warning(f"Test-E2: Fail")
                            logger.warning(f"Validator  {i} joining after the election was considered for election\n")
                            flag = False
            iterations += 1
    except TypeError as e:
        logger.error(f"error: {e}")
    if new_count == 0:
        logger.info(f"Test-E2: No validator joined after the election in all tests, need more tests\n")
        return "Need More Tests", curr_test
    if flag:
        logger.info(f"Test-E2: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test

def E3_test(single):
    logger.info(f"Test-E3: Joining before election start must consider the validator for election")
    try:
        committees = getCommittees()
        slot = committees['external-slot-count']
        iterations = 0
        num = 1
        while iterations < num:
            block, last_block = getCurrentAndLastBlock()
            logger.info(f"current and last block numbers: {block}, {last_block}")
            if block == last_block:
                logger.info(f"current block is the last block in epoch, waiting for the new epoch...")
                new_block = block+1
                while block < new_block:
                    block = getBlockNumber()
                block, last_block = getCurrentAndLastBlock()
                logger.info(f"current and last block numbers: {block}, {last_block}")
            second_last_block = last_block - 1
            while block < second_last_block:
                block = getBlockNumber()
            logger.info(f"second last block in current epoch reached, {block}, wait for 6 seconds to reach the end of the block")
            time.sleep(6)
            logger.info("begin collecting eligible validators...")
            # get top #slots nodes who are eligible to elected next epoch
            validator_infos = getAllValidatorInformation()
            eligible = []
            stake = dict()
            for i in validator_infos:
                if i['epos-status'] == 'currently elected' or i['epos-status'] == 'eligible to be elected next epoch':
                    address = i['validator']['address']
                    eligible.append(address)
                    stake[address] = i['total-delegation']

            if len(eligible) > slot:
                sorted_stake = sorted(stake.items(), key=lambda kv: kv[1], reverse = True)
                eligible = [kv[0] for kv in sorted_stake[:slot]]

            # wait for epoch changes
            new_block = block + 2
            while block < new_block:
                block = getBlockNumber()
            logger.info(f"first block in new epoch reached, {block}, will wait for 5 seconds to begin testing...")
            time.sleep(5)
            # check whether the eligible validators are selected
            validator_infos = getAllValidatorInformation()
            flag = True
            for i in validator_infos:
                if i in eligible:  
                    if i['epos-status'] != 'currently elected':
                        logger.warning(f"Test-E3: Fail")
                        logger.warning(f"Validator {i} joined before election was not considered as the validator for election\n")
                        flag = False
            iterations += 1
    except TypeError as e:
        logger.error(f"error: {e}")
    if single:
        curr_test = None
    else:
        curr_test = E4_test
    if flag:
        logger.info(f"Test E3: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test

def E4_test(single):
    logger.info(f"Test-E4: Low staker will never get elected over high staker")
    # the number of epoches you want to test
    num = 1
    iterations = 0
    flag = True
    try:
        while iterations < num:
            block, last_block = getCurrentAndLastBlock()
            logger.info(f"current and last block numbers: {block}, {last_block}")
            if block == last_block:
                logger.info(f"current block is the last block in epoch, waiting for the new epoch...")
                new_block = block+1
                while block < new_block:
                    block = getBlockNumber()
                block, last_block = getCurrentAndLastBlock()
                logger.info(f"current and last block numbers: {block}, {last_block}")
            second_last_block = last_block - 1
            while block < second_last_block:
                block = getBlockNumber()
            logger.info(f"second last block in current epoch reached, {block}, wait for 6 seconds to reach the end of the block")
            time.sleep(6)
            logger.info(f"begin collecting eligible validators...")
            validator_infos = getAllValidatorInformation()
            eligible_stake = dict()
            for i in validator_infos:
                if i['epos-status'] == 'currently elected' or i['epos-status'] == 'eligible to be elected next epoch':
                    address = i['validator']['address']
                    eligible_stake[address] = i['total-delegation']
            # reach the first block in next epoch and check the status of all eligible validators
            new_epoch_block = block + 1
            while block < new_epoch_block:
                block = getBlockNumber()
            logger.info(f"first block of new epoch reached, {new_epoch_block}, will begin checking all the elgible validators' election result...")
            elected = dict()
            non_elected = dict()
            validator_infos = getAllValidatorInformation()
            for i in validator_infos:
                if i['metrics']:
                    address = i['validator']['address']
                    by_key_metrics = i['metrics']['by-bls-key']
                    slots = len(by_key_metrics)
                    if address in eligible_stake:
                        if i['currently-in-committee']:
                            elected[address] = float(eligible_stake[address] / slots)
                        else:
                            non_elected[address] = float(eligible_stake[address] / slots)
            sorted_elected = sorted(elected.items(), key = lambda kv: kv[1])
            sorted_non_elected = sorted(non_elected.items(), key = lambda kv: kv[1], reverse = True)

            # get the lowest elected validator and highest non-elected validator
            if not sorted_elected:
                lowest_elected = 0
            else:
                lowest_elected = sorted_elected[0][1]
            if not sorted_non_elected:
                highest_unelected = 0
            else:
                highest_unelected = sorted_non_elected[0][1]
            if lowest_elected < highest_unelected:
                logger.warning(f"Test-E4: Fail")
                logger.warning(f"lowest stake in elected eligible validators: {sorted_elected[0]}" )
                logger.warning(f"highest stake in unelected eligible validators: {sorted_non_elected[0]}\n")
                flag = False
            iterations += 1
    except TypeError as e:
        logger.error(f"error: {e}")
    curr_test = None
    if flag:
        logger.info(f"Test-E4: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test

def M2_test(single):
    logger.info(f"Test-M2: Median is correctly computed for even and odd number of available slots")
    num = 1
    iterations = 0
    flag = True
    block, last_block = getCurrentAndLastBlock()
    logger.info(f"current and last block numbers: {block}, {last_block}")
    if block == last_block:
        logger.info(f"currently at the last block, wait for new epoch starts...")
        while block < last_block+1:
            block = getBlockNumber()
    while iterations < num:
        epoch = getEpoch()
        logger.info(f"current epoch: {epoch}, begin testing...")
        # get the median from rpc call
        median = getEposMedian()
        # calculate the median manually
        slot_winners = getMedianRawStakeSnapshot()['epos-slot-winners']
        stake = []
        for i in slot_winners:
            stake.append((float(i['raw-stake'])))
        cal_median = float(get_median(stake))
        # compare the calculated median and rpc median
        if cal_median != median:
            logger.warning(f"Test-M2: Fail")
            logger.warning(f"calculated median: {cal_median}")
            logger.warning(f"rpc median: {median}\n")
            flag = False
        iterations += 1  
        new_epoch = epoch + 1
        if num == 1:
            break
        logger.info(f"wait for new epoch starts...")
        while epoch < new_epoch:
            epoch = getEpoch()
        logger.info(f"wait for 3 seconds to begin testing...")    
        time.sleep(3)
    if single:
        curr_test = None
    else:
        curr_test = M3_test
    if flag:
        logger.info(f"Test-M2: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test
    
def M3_test(single):
    logger.info(f"Test-M3: Median function stability: run median computation for x number of epoch to verify stability")
    num = 2
    iterations = 0
    flag = True
    while iterations < num:
        logger.info(f"test {iterations+1} will begin ...")
        block, last_block = getCurrentAndLastBlock()
        logger.info(f"current and last block numbers: {block}, {last_block}")
        time.sleep(5)
        # get the median from rpc call
        median = getEposMedian()
        # calculate the median manually
        slot_winners = getMedianRawStakeSnapshot()['epos-slot-winners']
        stake = []
        for i in slot_winners:
            stake.append((float(i['raw-stake'])))
        cal_median = float(get_median(stake))
        # compare the calculated median and rpc median
        if cal_median != median:
            logger.warning(f"Test-M3: Fail")
            logger.warning(f"manually calculated median stake: {cal_median}")
            logger.warning(f"harmony apr call median stake: {median}\n")    
        iterations += 1  
        
        logger.info(f"wait until the new epoch begins ...")
        getBlockNumber()
        while block < last_block+1:
            block = getBlockNumber()
        logger.info(f"new epoch first block reached {block}, will wait for 5 secondss to begin testing...")
    if single:
        curr_test = None
    else:
        curr_test = M5_test
    if flag:
        logger.info(f"Test-M3: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test

def M5_test(single):
    logger.info(f"Test-M5: No effective stake is out of range: [median-0.15*median, median+0.15*median]")
    flag = True
    curr_test = None
    # get the median stake and the upper and lower level 
    result = getCommittees()
    median = float(result['epos-median-stake'])
    lower = (median- 0.15*median)
    upper = (median + 0.15*median)
    logger.info("median stake is " + str(median))
    logger.info("lower bond is " + str(lower))
    logger.info("upper bond is " + str(upper))
    
    shards = result['quorum-deciders']
    count = 0
    for k, v in shards.items():
        members = v['committee-members']
        for i in members:
            if not i['is-harmony-slot']:
                count += 1
                stake = float(i['effective-stake'])
                bls_key = i['bls-public-key']
                addr = i['earning-account']
                if stake > upper or stake < lower:
                    logger.warning(f"Test-M5: Fail")
                    logger.warning(f"validator: {addr} bls public key: {bls_key}") 
                    logger.warning(f"effective stake is out of range. The effective stake is {stake}\n")
                    flag = False
                
    logger.info(f"total slots verified: {count}" )
    if flag:
        logger.info(f"Test-M5: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test

def R1_test(single):
    logger.info("Test R1: Harmony nodes should not earn block rewards")
    committees = getCommittees()
    harmony_nodes = []
    for k,v in committees['quorum-deciders'].items():
        for i in v['committee-members']:
            if i['is-harmony-slot'] == True:
                harmony_nodes.append(i['earning-account'])
    num = 0
    for i in harmony_nodes:
        if "error" in getValidatorInfo(i):
            num += 1
    if single:
        curr_test = None
    else:
        curr_test = R2_test
    if num == len(harmony_nodes):
        logger.info("Test-R1: Succeed\n")
        return True, curr_test
    else:
        logger.warning("Test-R1: Fail\n")
        return False, curr_test

def R2_test(single):
    logger.info(f"Test-R2: Not elected validators should not earn reward")
    block, last_block = getCurrentAndLastBlock()
    logger.info(f"current and last block numbers: {block}, {last_block}")
    if block == last_block or block + 1 == last_block:
        logger.info(f"current at the last block or last second block, wait until the 5th/6th block in the new epoch")
        while block < last_block+6:
            block = getBlockNumebr()
        logger.info(f"current block {block}, will wait for 3 seconds to begin collecting infos...")
        time.sleep(3)
    validator_infos = getAllValidatorInformation()
    not_elected = []
    rewards = dict()
    for i in validator_infos:
        if i['currently-in-committee'] == False:
            not_elected.append(i)
            address = i['validator']['address']
            amount = i['lifetime']['reward-accumulated']
            rewards[address] = amount
    new_block = block + 1
    while block < new_block:
        block = getBlockNumber()
    logger.info(f"new block reached, {block}, will wait for 3 seconds to begin testing...")
    time.sleep(3)
    # check the rewards
    failures = 0
    validator_infos = getAllValidatorInformation()
    for i in validator_infos:
        address = i['validator']['address']
        if address in not_elected:
            amount = i['lifetime']['reward-accumulated']
            if rewards[address] != amount:
                logger.warning(f"Error: reward not same for {address}, previous: {rewards[address]} new: {amount}")
                failures = failures + 1
    if single:
        curr_test = None
    else:
        curr_test = R3_test
    if failures > 0:
        logger.warning(f"Test-R2: Fail\n")
        return False, curr_test
    else:
        logger.info(f"Test-R2: Succeed\n")
        return True, curr_test

def R3_test(single):
    logger.info(f"Test-R3: High stakers earn more reward than low stakers")
    
    block, last_block = getCurrentAndLastBlock()
    logger.info(f"current and last block numbers: {block}, {last_block}")
    if block == last_block or block+1 == last_block:
        logger.info(f"current at the last block or last second block, wait until the 5th/6th block in the new epoch")
        while block < last_block+6:
            block = getBlockNumber()
    logger.info(f"current block {block}, will wait for 3 seconds to begin collecting infos...")
    time.sleep(3)
    rewards, stakes, delegations, shards = getStakeRewardsDelegateAndShards()
    logger.info(f"obtained block stakes and rewards, total stakes found = {len(stakes)}, total rewards found = {len(rewards)}")
    new_epoch_block = block + 1
    while block < new_epoch_block:
        block = getBlockNumber()
    logger.info(f"new block reached, {block}, will wait for 5 seconds to begin comparing stakes and rewards")  
    time.sleep(3)
    flag = True
    new_rewards, new_stakes, new_delegations, new_shards = getStakeRewardsDelegateAndShards()
    key_to_stake = dict()
    key_to_reward = dict()
    key_to_shard = dict()
    for addr, reward in new_rewards.items():
        # we will not compare those who change their delegations since it will make confusing for the test
        if new_delegations[addr] != delegations[addr]:
            continue
        if addr in rewards:
            addr_reward = reward - rewards[addr]
            slots = len(stakes[addr])
            per_slot_reward = addr_reward / slots
            for key, stake in stakes[addr].items():
                key_to_reward[key] = per_slot_reward
                if key in stakes[addr]:
                    key_to_stake[key] = stakes[addr][key]
                if key in shards[addr]:
                    key_to_shard[key] = shards[addr][key]
    shard_rewards = dict()
    shard_stakes = dict()
    for key, shard in key_to_shard.items():
        if shard not in shard_stakes:
            shard_stakes[shard] = dict()
        if shard not in shard_rewards:
            shard_rewards[shard] = dict()
        shard_stakes[shard][key] = key_to_stake[key]
        shard_rewards[shard][key] = key_to_reward[key]
    for shard in shard_rewards.keys():
        sorted_stakes = sorted(shard_stakes[shard].items(), key=lambda kv: kv[1], reverse = True)
        sorted_rewards = sorted(shard_rewards[shard].items(), key=lambda kv: kv[1], reverse = True)
        stake_keys = extract(sorted_stakes)
        reward_keys = extract(sorted_rewards)
        logger.info(f"comparison to begin, two lengths: {len(stake_keys)}, {len(reward_keys)}")
        if check(sorted_stakes, sorted_rewards) == False:
            logger.warning(f"on shard {shard}: Fail")
            logger.warning(f"validators sorted by stakes: {stake_keys}")
            logger.warning(f"validators sorted by reward: {reward_keys}")
            flag = False
        else:
            logger.info(f"on shard {shard}: Succeed")      
    if single:
        curr_test = None
    else:
        curr_test = R4_test
    if flag:
        logger.info(f"Test-R3: Succeed\n")
        return True, curr_test
    else:
        logger.warning(f"Test-R3: Fail\n")
        return False, curr_test

def R4_test(single):
    logger.info(f"Test-R4: Reward given out to delegators sums up to the total delegation reward for each validator")
    
    block, last_block = getCurrentAndLastBlock()
    logger.info(f"current and last block numbers: {block}, {last_block}")
    if block == last_block or block + 1 == last_block:
        logger.info(f"current at the last block or last second block, wait until the 5th/6th block in the new epoch")
        while block < last_block+6:
            block = getBlockNumber()
    logger.info(f"current block {block}, will begin collecting infos...")
    acc_rewards_prev = dict()
    delegations_prev = dict()
    validator_infos = getAllValidatorInformation()
    for i in validator_infos:
        if i['currently-in-committee'] == True:
            address = i['validator']['address']
            reward_accumulated = i['lifetime']['reward-accumulated']
            acc_rewards_prev[address] = reward_accumulated
            ds = i['validator']['delegations']
            dels = dict()
            for d in ds:
                d_addr = d['delegator-address']
                d_reward = d['reward']
                dels[d_addr] = d_reward
            delegations_prev[address] = dels  
    next_block = block + 1
    while block < next_block:
        block = getBlockNumber()
    logger.info(f"new block reached, {block}, will begin testing...")
    flag = True
    logger.info(f"current block: {block}")
    # get the validator info and compute validator rewards
    acc_rewards_curr = dict()
    delegations_curr = dict()
    validator_infos = getAllValidatorInformation()
    for i in validator_infos:
        if i['currently-in-committee'] == True:
            address = i['validator']['address']
            reward_accumulated = i['lifetime']['reward-accumulated']
            acc_rewards_curr[address] = reward_accumulated
            if address not in acc_rewards_prev:
                continue
            reward = reward_accumulated - acc_rewards_prev[address]
            if reward == 0:
                continue
            del_rewards = 0
            dels = delegations_prev[address]
            ds = i['validator']['delegations']
            for d in ds:
                d_addr = d['delegator-address']
                d_reward = d['reward']
                del_rewards += d['reward']
                if d_addr in dels:
                    del_rewards -= dels[d_addr]
            if format(del_rewards, '.20e') != format(reward, '.20e'):
                logger.warning(f"Test-R4:Fail")
                logger.warning(f"for validator {address}, validator reward: {reward:.20e}, delegators reward: {del_rewards:.20e}\n")
                flag = False
    if single:
        curr_test = None
    else:       
        curr_test = R5_test
    if flag:
        logger.info(f"Test-R4: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test

def R5_test(single):
    logger.info(f"Test-R5: Reward given out to block signers sums up to the total block reward")
    logger.info(f"check sum over earned-reward diff of all keys per shard = 28")
    block, last_block = getCurrentAndLastBlock()
    logger.info(f"current and last block numbers: {block}, {last_block}")
    if block == last_block or block == last_block -1:
        logger.info(f"current at the last block or last second block, wait until the first block in the new epoch")
        while block < last_block+1:
            block = getBlockNumber()
                    
    next_block = block + 1
    while block < next_block:
        block = getBlockNumber()
    time.sleep(3)
    logger.info(f"current block {block}, will begin collecting infos...")

    earn_rewards_prev = defaultdict(dict)
    validator_infos = getAllValidatorInformation()
    for i in validator_infos:
        if i['metrics']:
            for k in i['metrics']['by-bls-key']:
                key = k['key']
                shard = key['shard-id']
                bls_key = key['bls-public-key']
                earn_reward = k['earned-reward']
                earn_rewards_prev[shard][bls_key] = earn_reward
                
    next_block = block + 1
    while block < next_block:
        block = getBlockNumber()
    time.sleep(3)
    logger.info(f"new block {block} reached, will begin testing...")
    flag = True
    # get the validator info and compute validator rewards
    earn_rewards_curr = defaultdict(dict)
    validator_infos = getAllValidatorInformation()
    block_reward = 28e18
    for i in validator_infos:
        if i['metrics']:
            for k in i['metrics']['by-bls-key']:
                key = k['key']
                shard = key['shard-id']
                bls_key = key['bls-public-key']
                earn_reward = k['earned-reward']
                earn_rewards_curr[shard][bls_key] = earn_reward
    earn_reward_diff = diffAndFilter2(earn_rewards_prev, earn_rewards_curr) 
    for shard, diff in earn_reward_diff.items():
        reward = sum(diff.values())
        if format(reward, '.20e') != format(block_reward, '.20e'):
            logger.warning(f"Test-R5: Fail")
            logger.warning(f"shard: {shard}, block: {block}, sum of earned reward: {reward:.20e}, block reward: {block_reward:.20e}\n")
            flag = False
    
    if single:
        curr_test = None
    else:
        curr_test = R6_test
    if flag:
        logger.info(f"Test-R5: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test

def R6_test(single):
    logger.info(f"Test-R6: Tests whether the delegation reward is distributed correctly")
    
    block, last_block = getCurrentAndLastBlock()
    logger.info(f"current and last block numbers: {block}, {last_block}")

    if block != last_block:
        while block < last_block:
            block = getBlockNumber()
        logger.info(f"current block {block}, will begin collecting delegator infos...")
        time.sleep(4)
    
    acc_rewards_prev = dict()
    delegations_prev = dict()
    total_stake = dict()
    validator_infos = getAllValidatorInformation()
    for i in validator_infos:
        if i['currently-in-committee'] == True:
            address = i['validator']['address']
            reward_accumulated = i['lifetime']['reward-accumulated']
            acc_rewards_prev[address] = reward_accumulated
            ds = i['validator']['delegations']
            dels = dict()
            for d in ds:
                d_addr = d['delegator-address']
                d_reward = d['reward']
                dels[d_addr] = d_reward
            delegations_prev[address] = dels
            total_stake[address] = i['total-delegation']

    next_block = block + 1
    while block < next_block:
        block = getBlockNumber()
    logger.info(f"new block {block} reached, will begin testing...")
    flag = True
    # get the validator info and compute validator rewards
    acc_rewards_curr = dict()
    delegations_curr = dict()
    validator_infos = getAllValidatorInformation()
    for i in validator_infos:
        if i['currently-in-committee'] == True:
            address = i['validator']['address']
            reward_accumulated = i['lifetime']['reward-accumulated']
            acc_rewards_curr[address] = reward_accumulated
            if address not in acc_rewards_prev:
                continue
            reward = reward_accumulated - acc_rewards_prev[address]
            if reward == 0:
                continue
            commission = float(i['validator']['rate']) * reward
            total_delegation_reward = reward - commission
            total_delegation = total_stake[address]
            ds = i['validator']['delegations']
            del_rewards = 0
            dels = delegations_prev[address]
            dels_curr = dict()
            for d in ds:
                d_addr = d['delegator-address']
                if d_addr not in dels:
                    continue
                d_reward = d['reward']
                dels_curr[d_addr] = d_reward
                d_amount = d['amount']
                delegation_reward_actual = d_reward
                if d_addr in dels:
                    delegation_reward_actual = delegation_reward_actual - dels[d_addr]
                percentage = d_amount / total_delegation
                delegation_reward_expected = percentage * total_delegation_reward
                if d_addr == address:
                    delegation_reward_expected = delegation_reward_expected + commission
                if format(delegation_reward_actual, '.15e') != format(delegation_reward_expected, '.15e'):
                    logger.warning(f"Test-R6: Fail")
                    logger.warning(f"for validator {address} delegation {d_addr}, expected: {delegation_reward_expected:.15e}, actual: {delegation_reward_actual:.15e}\n")
                    flag = False
    if single:
        curr_test = None
    else:
        curr_test = R7_test
    if flag:
        logger.info(f"Test-R6: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test

def R7_test(single):
    logger.info(f"Test-R7: Sum of validator and delegator earning should match the block reward")
    
    block, last_block = getCurrentAndLastBlock()
    logger.info(f"current and last block numbers: {block}, {last_block}")
    if block == last_block or block + 1 == last_block:
        logger.info(f"current at the last block (or last block - 1), wait until the 5th/6th block in the new epoch")
        while block < last_block+6:
            block = getBlockNumber()
            time.sleep (5)
    logger.info(f"current block {block}, will begin collecting infos...")

    acc_rewards_prev = dict()
    delegations_prev = dict()
    validator_infos = getAllValidatorInformation()
    for i in validator_infos:
        if i['currently-in-committee'] == True:
            address = i['validator']['address']
            reward_accumulated = i['lifetime']['reward-accumulated']
            acc_rewards_prev[address] = reward_accumulated
            ds = i['validator']['delegations']
            dels = dict()
            for d in ds:
                d_addr = d['delegator-address']
                d_reward = d['reward']
                dels[d_addr] = d_reward
            delegations_prev[address] = dels
    iterations = 0
    num = 2
    flag = True
    while iterations < num:
        next_block = block+1
        while block < next_block:
            block = getBlockNumber()
        logger.info(f"new block {block} reached, will begin testing...")
            # get the validator info and compute validator rewards
        acc_rewards_curr = dict()
        delegations_curr = dict()
        validator_infos = getAllValidatorInformation()
        block_reward = 28e18
        validator_rewards = 0
        total_reward = 0
        signers = 0
        for i in validator_infos:
            if i['metrics']:
                signers = signers + 1
                # block reward of the validator
                shard_metrics = i['metrics']['by-bls-key']
                validator_reward = 0
                for by_shard in shard_metrics:
                    validator_addr = by_shard['key']['earning-account']
                    by_shard_reward = block_reward * float(by_shard['key']['overall-percent']) / 0.32
                    validator_reward = validator_reward + by_shard_reward

                address = i['validator']['address']
                reward_accumulated = i['lifetime']['reward-accumulated']
                acc_rewards_curr[address] = reward_accumulated
                reward = reward_accumulated
                if address not in acc_rewards_prev:
                    continue
                reward = reward_accumulated - acc_rewards_prev[address]
                # this reward should match sum of delegation rewards
                ds = i['validator']['delegations']
                del_rewards = 0
                dels_prev = delegations_prev[address]
                dels = dict()
                for d in ds:
                    d_addr = d['delegator-address']
                    d_reward = d['reward']
                    dels[d_addr] = d_reward
                    del_rewards = del_rewards + d_reward
                    if d_addr in dels:
                        del_rewards = del_rewards - dels_prev[d_addr]
                delegations_curr[address] = dels
                if format(del_rewards, '.20e') != format(reward, '.20e'):
                    logger.warning(f"Test-R7: Fail")
                    logger.warning(f"for validator {address}, expected block reward, {validator_reward:.20e}, validator block reward, {reward:.20e}, delegation reward, {del_rewards:.20e}\n")
                    flag = False
        acc_rewards_prev = acc_rewards_curr
        delegations_prev = delegations_curr
        iterations += 1
    if single:
        curr_test = None
    else:
        curr_test = R8_test
    if flag:
        logger.info(f"Test-R7: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test

def R8_test(single):
    logger.info(f"Test-R8: Block reward inversely proportional to staked amount")
    logger.warning(f"Test-R8: Not Applicable")
    curr_test = R9_test
    return "Not Applicable", curr_test

def R9_test(single):
    logger.info(f"Test-R9: Block reward never drops below minimum or raises above maximum block reward")
    
    block, last_block = getCurrentAndLastBlock()
    logger.info(f"current and last block numbers: {block}, {last_block}")
    if block == last_block or block+1 == last_block:
        logger.info(f"current at the last block or last second block, wait until the 5th/6th block in the new epoch")
        while block < last_block+6: 
            block = getBlockNumber()
    logger.info(f"current block: {block}, will begin collecting infos...")
    acc_rewards_prev = dict()
    validator_infos = getAllValidatorInformation()
    for i in validator_infos:
        if i['currently-in-committee'] == True:
            address = i['validator']['address']
            reward_accumulated = i['lifetime']['reward-accumulated']
            acc_rewards_prev[address] = reward_accumulated        
    next_block = block + 1
    while block < next_block:
        block = getBlockNumber()
    logger.info(f"new block reached: {block}, will begin testing...")        
    # per-shard
    # default reward = 18 ONEs
    # min reward = 0, when >= 80% staked instead of 35% (of the circulating supply)
    # max reward = 32, when ~0% staked instead of 35% (of the circulating supply)
    # so, for four shards, (min, max) = (0, 128)
    min_total_reward = 0
    max_total_reward = 128e18

    flag = True
    # get the validator info and compute validator rewards
    acc_rewards_curr = dict()
    validator_infos = getAllValidatorInformation()
    total_reward = 0
    for i in validator_infos:
        if i['currently-in-committee'] == True:
            address = i['validator']['address']
            reward_accumulated = i['lifetime']['reward-accumulated']
            acc_rewards_curr[address] = reward_accumulated
            if address not in acc_rewards_prev:
                continue
            reward = reward_accumulated - acc_rewards_prev[address]
            total_reward = total_reward + reward   
    if total_reward < min_total_reward or total_reward > max_total_reward:
        logger.warning(f"Test R9: Fail")
        logger.warning(f"block reward below minimum or above maximum, block reward: {format(total_reward, '.20e')}, minimum: {min_total_reward}, maximum: {max_total_reward}\n")
        flag = False
    if single:
        curr_test = None
    else:
        curr_test = R11_test    
    if flag:
        logger.info(f"Test R9: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test
    
def R11_test(single):
    logger.info(f"Test-R11: Earning is proportional to effective stake ")
    logger.warning(f"Test-R11: Not Applicable")
    curr_test = R14_test
    return "Not Applicable", curr_test
    
    
def R14_test(single):
    logger.info(f"Test-R14: Shard fairness: rate of earning on shards is similar if the block time are same")
    num = 1
    iterations = 0
    
    while iterations < num:
        block = getBlockNumber()
        logger.info(f"current block number, {block}")
        next_block = block + 1
        while block < next_block:
            block = getBlockNumber()
        # get the average apr for each shard 
        logger.info(f"next block reached, {block}, will begin testing")
        apr_avg = getAprByShards()
        apr_avg = sorted(apr_avg.items(), key=lambda kv: kv[0])
        logger.info(f"the average apr for each shard: {apr_avg}\n")
        iterations += 1  

    curr_test = None
    return "Need Manually Check", curr_test

def CN1_test(single):
    logger.info(f"Test-CN1: Slow validator is never starved (should be able to sign blocks)")
    curr_test = None
    
    block, last_block = getCurrentAndLastBlock()
    logger.info(f"current and last block numbers: {block}, {last_block}")
    if block == last_block or block == last_block -1:
        logger.info(f"current at the last block or last second block, wait until the 5th block in the new epoch")
        while block < last_block+5:
            block = getBlockNumber()
    logger.info(f"current block: {block}, will begin collecting infos...")
    signer_address = getBlockSigner(block)
    acc_rewards_prev = dict()
    validator_infos = getAllValidatorInformation()
    for i in validator_infos:
        address = i['validator']['address']
        if address in signer_address:
            reward_accumulated = i['lifetime']['reward-accumulated']
            acc_rewards_prev[address] = reward_accumulated

    next_block = block + 1
    while block < next_block:
        block = getBlockNumber()
    logger.info(f"new block {block} reached, will begin testing...")
    flag = True
    # get the validator info and compute validator rewards
    new_signer_address = getBlockSigner(block)
    validator_infos = getAllValidatorInformation()
    for i in validator_infos:
        address = i['validator']['address']
        if address in new_signer_address:           
            reward_accumulated = i['lifetime']['reward-accumulated']
            if address not in acc_rewards_prev:
                continue
            reward = reward_accumulated - acc_rewards_prev[address]
            if reward == 0:
                flag = False
                logger.warning(f"Test-CN1: Fail")
                logger.warning(f"validator {address} who is a signer doesn't get reward\n")
    if flag:
        logger.info(f"Test-CN1: All signers get rewards")
    
    while block < last_block:
        block = getBlockNumber()
    logger.info(f"last block in this epoch reached, {block}")
    validator_infos = getAllValidatorInformation()
    for i in validator_infos:
        if i['current-epoch-performance']:
            sign = i['current-epoch-performance']['current-epoch-signing-percent']
            if sign['current-epoch-to-sign'] == 0:
                continue
            perc = float(sign['current-epoch-signing-percentage'])
            if perc > 2/3:
                address = i['validator']['address']
                epos_status = i['epos-status']
                if epos_status == 'not eligible to be elected next epoch':
                    flag = False
                    logger.warning(f"Test-CN1: Fail")
                    logger.warning(f"validator {address} who is a signer is not eligible to be elected next epoch\n")

    if flag:
        logger.info(f"Test-CN1: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test

def U1_test(single):
    logger.info("Test-U1: Delegator/validator stake locked until undelegate")
    num = 1
    
    block, last_block = getCurrentAndLastBlock()
    logger.info(f"current and last block numbers: {block}, {last_block}")
    if block + num > last_block:  
        logger.info(f"wait until new epoch starts ...")
        new_block = last_block + 1
        while block < new_block:
            block = getBlockNumber()
    iterations = 0
    flag = True
    total_reduce_num = 0
    while iterations < num:
        epoch = getEpoch()
        logger.info(f"current epoch number, {epoch}, current block number, {block}, will begin testing...")
        stake, undelegate = getStakeAndUndelegate2(epoch)
        next_block = block + 1
        while block < next_block:
            block = getBlockNumber()
        epoch = getEpoch()
        logger.info(f"next block reached, {block}, current epoch, {epoch}, will compare the stakes")
        new_stake, new_undelegate = getStakeAndUndelegate2(epoch)
        diff_stake = diffAndFilter2(stake, new_stake)
        diff_undelegate = diffAndFilter2(undelegate, new_undelegate)

        reduce_num = 0
        for key, val in diff_stake.items():
            for k,v in diff_stake[key].items():
                if v < 0:
                    reduce_num += 1
                    total_reduce_num +=1
                    if diff_undelegate[key][k] <= 0:
                        logger.warning(f"Test-U1: Fail")
                        logger.warning(f"Delgeator stake reduces without undelegate")
                        logger.warning(f"undelegate changes:  {diff_undelegate[key][k]}")
                        logger.warning(f"stake changes: {v}\n")
                        flag = False        
        if reduce_num == 0:
            logger.info(f"No stake reduces at current test, need more tests\n")
        iterations += 1  
    if single:
        curr_test = None
    else:        
        curr_test = U2_test
    if total_reduce_num == 0:
        return "Need More Tests", curr_test
    if flag:
        logger.info(f"Test-U1: Succeed\n")
        return True, curr_test
    if not flag:
        return False, curr_test

def U2_test(single):
    logger.info(f"Test-U2: After undelegate, the total stake amount for that validator should subtract the undelegation amount before next epoch")
    num = 1
    iterations = 0
    flag = True
    curr_test = None
    while iterations < num:
        block, last_block = getCurrentAndLastBlock()
        logger.info(f"current and last block numbers: {block}, {last_block}")
        # need at least 2 blocks left to compare difference
        if block == last_block:
            new_block = last_block + 1
            while block < new_block:
                block = getBlockNumber()
            block, last_block = getCurrentAndLastBlock()
            logger.info(f"current and last block numbers: {block}, {last_block}")
        epoch = getEpoch()
        logger.info(f"current epoch numebr: {epoch}, block number: , {block}, will begin testing...")
        stake, undelegate = getStakeAndUndelegate(epoch)

        while block < last_block:
            block = getBlockNumber()
        logger.info(f"last block number reaches, {block}, will compare the stakes and undelegations")
        new_stake, new_undelegate = getStakeAndUndelegate(epoch)
        diff_stake = diffAndFilter(stake, new_stake)
        diff_undelegate = diffAndFilter(undelegate, new_undelegate)

        if not diff_undelegate:
            logger.info(f"no undelegation happens in current test, need more tests\n")
            return "Need More Tests", curr_test
        
        for k,v in diff_undelegate.items():
            if k in diff_stake:
                if v != -(diff_stake[k]):
                    logger.warning(f"Test-U2: Fail")
                    logger.warning(f"Validator {k}: the stake change doesn't meet the undelegation change\n")
                    flag = False
            else:
                logger.warning(f"Test-U2: Fail")
                logger.warning(f"Validator: {k}: total stakes doesn't change after undelegation\n")
                flag = False
        iterations += 1 
           
    if flag:
        logger.info("Test-U2: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test

def S1_test(single):
    logger.info(f"Test-S1: Equilibrium: percentage of external validators on each shard is balanced")
    try:
        committees = getCommittees()['quorum-deciders']
        perc = dict()
        for k,v in committees.items():
            members = v['committee-members']
            count = v['count']
            num = 0
            for i in members:
                if not i['is-harmony-slot']:
                    num += 1
            perc[k] = num/count
        logger.info(f"the percentage for each shard: {perc}\n")
    except TypeError as e:
        logger.error(f"error: {e}")
    if single:
        curr_test = None
    else:        
        curr_test = S6_test
    return "Need Manually Check", curr_test

def S6_test(single):
    global curr_test
    logger.info(f"Test-S6: Total staked tokens cannot exceed circulating supply")
    flag = True
    current_block = getBlockNumber()
    try:
        logger.info(f"current block, {current_block}")
        supply, stake = getStakingMetrics()

        logger.info(f"supply: {supply}")
        logger.info(f"stake: {stake}")

        if stake > supply:
            logger.warning(f"Test-S6: Fail")
            logger.warning(f"stake is higher than supply. stake: {stake}, supply: {supply}\n")
            flag = False

    except TypeError as e:
        logger.error(f"error: {e}")
    if single:
        curr_test = None
    else:    
        curr_test = S7_test
    if flag:    
        logger.info("Test-S6: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test

def S7_test(single):
    logger.info(f"Test-S7: Stake is equally distributed across slots")
    num = 1
    try:        
        current_block = getBlockNumber()
        iterations = 0
        flag = True
        while iterations < num:
            counters = [0, 0, 0, 0]
            effect_stakes = [0.0, 0.0, 0.0, 0.0]
            logger.info(f"current block: {current_block}")

            validator_infos = getAllValidatorInformation()
            total_reward = 0
            for i in validator_infos:
                if i['metrics']:
                    addr = i['validator']['address']
                    by_shard_metrics = i['metrics']['by-bls-key']
                    e_stake = float(by_shard_metrics[0]['key']['effective-stake'])
                    for by_shard_metric in by_shard_metrics:
                        stake = float(by_shard_metric['key']['effective-stake'])
                        if stake != e_stake:
                            logger.warning(f"Test-S7: Fail")
                            logger.warning(f"for validator {addr}\n")
                            flag = False
            last_block = current_block
            current_block = getBlockNumber()
            while current_block == last_block:
                current_block = getBlockNumber()
                
            iterations += 1
    except TypeError as e:
        logger.error(f"error: {e}")
    curr_test = None    
    if flag:
        logger.info(f"Test-S7: Succeed\n")
        return True, curr_test
    else:
        return False, curr_test
    
def M4_test(single):
    global no_external_test
    logger.info(f"Test-M4: Zero median when no external validators")
    no_external_test = R13_test
    try:
        if not getAllValidatorInformation():
            median = getEposMedian()
            if median != 0:
                logger.warning(f"Test-M4: Fail")
                logger.warning(f"epos median when no external validators: {median}\n")
            else:
                logger.info(f"Test-M4: Succeed\n")
        else:
            logger.info(f"currently there are external validators, doesn't meet the testing needs\n")
            return "Need More Tests", no_external_test
    except TypeError as e:
        logger.error(f"error: {e}")
    

def R13_test(single):
    logger.info(f"Test-R13: In case of no external validators, no block reward is given out")
    try:
        committees = getCommittees()
        testing_status = True
        for k,v in committees['quorum-deciders'].items():
            for i in v['committee-members']:
                if not i['is-harmony-slot']:
                    testing_status = False
                    logger.info(f"currently there are external validators, doesn't meet the testing needs\n")
                    no_external_test = None
                    return "Need More Tests"
        no_external_test = None
        if not getAllValidatorInformation():
            logger.info(f"Test-R13: Succeed\n")
            return True, no_external_test
        else:
            logger.warning(f"Test-R13: Fail")
            logger.warning(f"there is block reward when no external validators\n")
            return False, no_external_test
    except TypeError as e:
        logger.error(f"error: {e}")
        