library(dplyr)
library(brms)

# Grabs a values for a specific key and optionally computes the mean
get_key <- function(params, key, compute_mean) {
  if (!key %in% names(params)) {
    stop(p(key, ' not in `params`'))
  }
  v <- params[[key]]
  if (compute_mean) {
    v <- mean(v)
  }
  v
}

# Shorthand for paste0
p <- function(...) {
  paste0(...)
}

# Obtain the values for all terms for a specific data row for a specific emotion
# Let's unpack this a little bit. The `emotion` is the predicted emotion. This function extracts the coefficients from
# the posterior samples for this specific emotion. We now multiply the extracted coefficients with a specific data point
# (a.k.a. row). The function returns two values:
# - `df` which is the distribution of intercepts and coefficients (i.e. posterior draws, 4000 in total) multiplied with
# a single data point. Each column is a distribution over these coefficients and intercepts. There are two types of
# column names: ones ending with "_coef" which stores the value of the coefficient and column names ending with "_value"
# which are the coefficents multiplied with a given data point or are just the intercepts.
# - `prediction` sums up all "_value" columns for each observation. So for 4000 posterior samples, this gives us 4000
# predictions.
get_values_for_emotion <- function(emotion, params, row, compute_mean = F, global_intercept = T, group_intercepts = c(), group_slopes = c()) {
  stopifnot(nrow(row) == 1)

  df <- list()
  df[['computed_emotion']] <- emotion
  if (global_intercept) {
    df[['intercept_global_value']] <- get_key(params, p('b_mu', emotion, '_Intercept'), compute_mean)
  }

  # Add slopes
  for (rc in p('RC', 1:7)) {
    # Global slope
    RC_coef <- get_key(params, p('b_mu', emotion, '_', rc), compute_mean)
    df[[p(rc, '_global_coef')]] <- RC_coef
    df[[p(rc, '_global_value')]] <- RC_coef * row[[rc]]
    for (group_name in group_slopes) {
      # Group slope
      group_value <- row[[group_name]]
      RC_coef <- get_key(params, p("r_", group_name, "__mu", emotion, "[", group_value, ",", rc, "]"), compute_mean)
      df[[p(rc, '_', group_name, '_coef')]] <- RC_coef
      df[[p(rc, '_', group_name, '_value')]] <- RC_coef * row[[rc]]
    }
  }
  # Add intercepts
  for (group_name in group_intercepts) {
    group_value <- row[[group_name]]
    df[[p('intercept_', group_name, '_value')]] <- get_key(params, p("r_", group_name, "__mu", emotion, "[", group_value, ",Intercept]"), compute_mean)
  }

  df <- as.data.frame(df)
  list(
    prediction = df %>%
      select(ends_with("_value")) %>%
      apply(1, sum),
    df = df
  )
}

# This function computes how much percent each element of a row contributes to the sum of the row
process_abs_df <- function(abs_df, predicted_emotion) {
  # Compute the sum per iteration
  abs_df$sum <- apply(abs_df, 1, sum)

  # Compute the percent per coefficient and intercept
  rel_df <- abs_df[1:(ncol(abs_df) - 1)] / abs_df$sum
  rel_df$iteration <- 1:nrow(rel_df)
  rel_df_long <- rel_df %>% tidyr::gather(key, value, -iteration)

  # Annotate the the long table
  anno_df <- data.frame(stringr::str_split_fixed(rel_df_long$key, '_', 3)[, 1:2])
  names(anno_df) <- c('type', 'group_level')
  anno_df$predicted_emotion <- predicted_emotion

  cbind(rel_df_long, anno_df)
}

# This function computes for each prediction how much percent of the total prediction was influenced by one term in the
# prediction equation. It does it for the terms in the equation -- so intercepts + coef * value -- (`percent_values`)
# and it does it for each coefficient separately.
# IT IS IMPORTANT TO NOTE HERE THAT OUR TERMS AND COEFFICIENTS MUST FIRST BE CONVERTED TO ABSOLUTE NUMBERS. Why? Cause
# we want to find out the contribution of each term to the final prediction. If we wouldn't do this, positive and
# negative terms or coefficients would cancel each other out giving a biased impression contributions to the prediction.
relative_estimates <- function(estimates_df, predicted_emotion) {
  out <- list()
  out[['percent_values']] <- process_abs_df(
    estimates_df %>%
      select(ends_with("_value")) %>%
      abs(),
    predicted_emotion
  )

  for (rc in paste0('RC', 1:7)) {
    out[[p('percent_', rc)]] <- process_abs_df(
      estimates_df %>%
        select(starts_with(rc) & ends_with("_coef")) %>%
        abs(),
      predicted_emotion
    )
  }

  out
}

# Computes the percentual contribution of each term to the prediction for a specific data point
get_single_estimate <- function(dat, params, r, predicted_emotion, include_intercept) {
  # Grab the row
  row <- dat[r,]
  estimate_df <- get_values_for_emotion(predicted_emotion, params, row, F, include_intercept, group_intercepts, group_slopes)$df
  long_relative_estimates <- relative_estimates(estimate_df, predicted_emotion)
  long_relative_estimates
}

logsumexp <- function(x) { max(x) + log(sum(exp(x - max(x)))) }
softmax <- function(x) { exp(x - logsumexp(x)) }

EMOTIONS <- c("ANG", "DIS", "FER", "HAP", "SAD", "SUR")


# Load model
big_model <- readRDS('../../results/models/big_model.RDS')
params <- brms::posterior_samples(big_model)
data <- big_model$data

# Get the predictions
probability_prediction <- predict(big_model, data)
emotion_predictions <- factor(apply(probability_prediction, 1, function(x) { levels(big_model$data$emotion)[which.max(x)] }), levels = levels(big_model$data$emotion))

# Rename the data and the predictions to 'culture'
data$culture <- stringr::str_replace_all(paste0(data$country, '_', data$language), ' ', '.')
names(params) <- stringr::str_replace_all(names(params), 'country:language', 'culture')

INCLUDE_INTERCEPT <- T  # Also compute coefficients
group_slopes <- c('culture', 'sex', 'speaker')

# For corpus we only compute an intercept, as corpora differ in their used emotions
group_intercepts <- c('sex', 'speaker', 'culture', 'corpus')

# Grab the indexes of not NEU predictions
bool_idx <- emotion_predictions != 'NEU'
idxs <- (1:length(emotion_predictions))[bool_idx]

# Use this to normalize per emotion
emo_tab <- table(emotion_predictions)

results_list <- list()
i <- 0
prev_perc <- ''
# Look at each emotional stimulus
for (r in idxs) {
  i <- i + 1

  # Grab the predicted emotion by the model
  predicted_emotion <- as.character(emotion_predictions[r])

  # Performing many rbinds in a row would lead to very slow results
  # We therefore already average per iteration and emotion
  scalar <- 1 / emo_tab[[predicted_emotion]]
  relative_estimates_list <- get_single_estimate(data, params, r, emotion_predictions[r], INCLUDE_INTERCEPT)

  for (g in names(relative_estimates_list)) {
    # Make sure an entry exists
    if (!g %in% names(results_list)) {
      results_list[[g]] <- list()
    }
    # Grab all contributions for each term or for the single coefficients
    estimates <- relative_estimates_list[[g]]

    # Now multiply all estimates with the scalar, such that the given emotion get's scaled proportional to it's overall
    # frequency
    estimates$value <- estimates$value * scalar

    # This is not so pretty, but what we do here is to append the estimates for a given emotion if it is the first time
    # we process the emotion. If we already have observations for a given emotion, we simply add our normalized
    # percentages to our previous estimates
    if (!predicted_emotion %in% names(results_list[[g]])) {
      results_list[[g]][[predicted_emotion]] <- estimates
    } else {
      results_list[[g]][[predicted_emotion]]$value <- results_list[[g]][[predicted_emotion]]$value + estimates$value
    }
  }

  # This is just to print the percentages, as this function can take a while to compute...
  percentage <- p(round(100 * (i / length(idxs))), '%\n')
  if (percentage != prev_perc) {
    cat(percentage)
  }
  prev_perc <- percentage
}

saveRDS(results_list, 'big_with_all_params.RDS')


