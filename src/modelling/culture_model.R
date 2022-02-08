library(brms)
library(cmdstanr)

MODEL_NAME <- 'culture_model'
dir.create(MODEL_NAME, showWarnings=FALSE) # For storing the sampling process

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
    emotion ~ 1 + RC1 + RC2 + RC3 + RC4 + RC5 + RC6 + RC7 +
    # Deviation of the mapping
    (1 + RC1 + RC2 + RC3 + RC4 + RC5 + RC6 + RC7 | country:language) +
    # Account for corpus differences
    (1 | corpus),
    family = brms::categorical(link = "logit"),
    decomp = "QR"
  ),
  data = dat_list,
  # 2. Family and priors
  family = brms::categorical(link = "logit"),
  prior = c(
    brms::set_prior("normal(0,1)", class = "b", dpar=c("", paste0("mu", EMOTIONS[2:7]))),
    brms::set_prior("normal(0,1)", class = "Intercept", dpar=c("", paste0("mu", EMOTIONS[2:7]))),
    brms::set_prior("normal(0,1)", class = "sd", dpar=paste0("mu", EMOTIONS[2:7]))
  ),

  # 3. Determinism and saving files
  seed = 1234,
  file = paste0('../../results/models/', MODEL_NAME, '.RDS'),

  # 4. Within and across chain parallelization
  threads = brms::threading(4),
  chains = 8,
  cores = 8,
  warmup = 1000,
  iter = 1500,

  # 5. Hyperparameters and speedup
  control = list(adapt_delta = 0.99, max_treedepth = 12),
  backend = "cmdstan",
  output_dir = MODEL_NAME,
  refresh = 15,
  silent=0,
  normalize = FALSE
)
