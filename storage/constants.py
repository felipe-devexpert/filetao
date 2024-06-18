# Failure mode negative rewards
STORE_FAILURE_REWARD = 0
CHALLENGE_FAILURE_REWARD = 0
MONITOR_FAILURE_REWARD = -0.005  # Incentivize uptime
RETRIEVAL_FAILURE_REWARD = -0.01 # Incentivize keeping all data

# Constants for storage limits in bytes
STORAGE_LIMIT_SUPER_SAIYAN = 1024**5 * 50 # 50 PB
STORAGE_LIMIT_RUBY = 1024**5 * 20         # 20 PB
STORAGE_LIMIT_EMERALD = 1024**5 * 10      # 10 PB
STORAGE_LIMIT_DIAMOND = 1024**5 * 5       # 5 PB
STORAGE_LIMIT_PLATINUM = 1024**5 * 1      # 1 PB
STORAGE_LIMIT_GOLD = 1024**4 * 200        # 200 TB
STORAGE_LIMIT_SILVER = 1024**4 * 50       # 50 TB
STORAGE_LIMIT_BRONZE = 1024**4 * 10       # 10 TB

SUPER_SAIYAN_TIER_REWARD_FACTOR = 1.0
RUBY_TIER_REWARD_FACTOR = 0.9
EMERALD_TIER_REWARD_FACTOR = 0.85
DIAMOND_TIER_REWARD_FACTOR = 0.8
PLATINUM_TIER_REWARD_FACTOR = 0.75
GOLD_TIER_REWARD_FACTOR = 0.7
SILVER_TIER_REWARD_FACTOR = 0.65
BRONZE_TIER_REWARD_FACTOR = 0.6

SUPER_SAIYAN_TIER_TOTAL_SUCCESSES = 10**3 * 15 # 15,000 (estimated 72 epochs to reach this tier)
RUBY_TIER_TOTAL_SUCCESSES = 10**3 * 10         # 10,000 (estimated 56 epochs to reach this tier)
EMERALD_TIER_TOTAL_SUCCESSES = 10**3 * 7       # 8,000  (estimated 48 epochs to reach this tier)
DIAMOND_TIER_TOTAL_SUCCESSES = 10**3 * 5       # 6,000  (estimated 36 epochs to reach this tier)
PLATINUM_TIER_TOTAL_SUCCESSES = 10**3 * 3      # 4,000  (estimated 24 epochs to reach this tier)
GOLD_TIER_TOTAL_SUCCESSES = 10**3 * 2          # 2,000  (estimated 12 epochs to reach this tier)
SILVER_TIER_TOTAL_SUCCESSES = 10**2 * 5        # 500    (estimated 3  epochs to reach this tier)

SUPER_SAIYAN_WILSON_SCORE = 0.85
RUBY_WILSON_SCORE = 0.8
EMERALD_WILSON_SCORE = 0.75
DIAMOND_WILSON_SCORE = 0.7
PLATINUM_WILSON_SCORE = 0.65
GOLD_WILSON_SCORE = 0.6
SILVER_WILSON_SCORE = 0.55

TIER_BOOSTS = {
    b"Super Saiyan": 1.02, # 2%  -> 1.02
    b"Ruby": 1.04,         # 4%  -> 0.936
    b"Emerald": 1.05,      # 6%  -> 0.918
    b"Diamond": 1.08,      # 8%  -> 0.864
    b"Platinum": 1.1,      # 10% -> 0.825
    b"Gold": 1.12,         # 12% -> 0.784
    b"Silver": 1.16,       # 16% -> 0.754
    b"Bronze": 1.2,        # 20% -> 0.72
}
