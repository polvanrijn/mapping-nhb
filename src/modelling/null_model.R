library(brms)
library(cmdstanr)

# Set cmdstan path
cmdstanr::set_cmdstan_path('/hpc/users/pol.van-rijn/repositories/cmdstan') # Set path to your local cmdstan

# Read the data
dat_list <- readRDS('../../data/data_all.RDS')

# Make sure emotion is factor
EMOTIONS <- c("NEU", "ANG", "DIS", "FER", "HAP", "SAD", "SUR")
dat_list[['emotion']] <- factor(dat_list[['emotion']], levels = EMOTIONS)

brms::brm(
  # 1. Data and Formula
  brms::bf(
  # Global mapping
    emotion ~ 1 +
    # Account for corpus differences
    (1 | corpus),
    family = brms::categorical(link = "logit"),
    decomp = "QR"
  ),
  data = dat_list,

  # 2. Family and priors
  family = brms::categorical(link = "logit"),
  prior = brms::set_prior("normal(0,1)", class = "Intercept"),

  # 3. Determinism and saving files
  seed = 1234,
  file = '../../results/models/null_model.RDS',

  # 4. Within and across chain parallelization
  chains = 4,
  cores = 4,
  warmup = 1000,
  iter = 2000,

  # 5. Hyperparameters and speedup
  control = list(adapt_delta = 0.99, max_treedepth = 12),
  backend = "cmdstan",
  refresh = 20,
  silent=1,
  normalize = FALSE
)
